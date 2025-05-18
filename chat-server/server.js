require('dotenv').config();

const express = require('express');
const { createServer } = require('http');
const { Server } = require('socket.io');
const { createAdapter } = require('@socket.io/redis-adapter');
const { createClient } = require('redis');
const mysql = require('mysql2');
const Minio = require('minio');
const axios = require('axios');

async function authenticate(socket, next) {
  const sessionKey = socket.handshake.auth?.session_key;
  console.log('세션 키 수신: ', sessionKey);

  if (!sessionKey) return next(new Error("No session key provided"));

  try {
    const response = await axios.post('http://web:8000/get_user_by_session/', {
      session_key: sessionKey
    });

    // socket.user 대신 socket.data.user 에 저장
    socket.data.user = response.data;
    console.log('인증 성공 - 사용자: ', socket.data.user.id);
    next();
  } catch (err) {
    console.error("Authentication error:", err.message || err);
    next(new Error("Authentication failed"));
  }
}


// MySQL 연결
const db = mysql.createConnection({
  host: process.env.DB_HOST,
  port: process.env.DB_PORT,
  user: process.env.DB_USER,
  password: process.env.DB_PASS,
  database: process.env.DB_NAME,
});

// Redis 클라이언트
const pubClient = createClient({
  url: `redis://${process.env.REDIS_HOST}:${process.env.REDIS_PORT}`,
});
const subClient = pubClient.duplicate();

// MinIO 클라이언트
const minioClient = new Minio.Client({
  endPoint: process.env.MINIO_HOST,
  port: parseInt(process.env.MINIO_PORT, 10),
  useSSL: false,
  accessKey: process.env.MINIO_ACCESS_KEY,
  secretKey: process.env.MINIO_SECRET_KEY,
});

const bucketName = 'chat-bucket';

// 비동기 버킷 준비 함수
function ensureMinioBucketReady() {
  return new Promise((resolve, reject) => {
    minioClient.bucketExists(bucketName, (err, exists) => {
      if (err) return reject(err);
      if (exists) {
        console.log(`버킷 ${bucketName}이 이미 존재합니다.`);
        return resolve();
      }

      minioClient.makeBucket(bucketName, 'ap-northeast-2', (err) => {
        if (err) return reject(err);
        console.log(`버킷 ${bucketName}이 생성되었습니다.`);
        resolve();
      });
    });
  });
}

function isUserInRoom(userId, roomId) {
  return new Promise((resolve, reject) => {
    const query = `
      SELECT COUNT(*) as count
      FROM chat_chatroom_participants
      WHERE chatroom_id = ? AND user_id = ?
    `;
    db.query(query, [roomId, userId], (err, results) => {
      if (err) return reject(err);
      const count = results[0].count;
      resolve(count > 0);  // true = 참여중
    });
  });
}

// 이미지 업로드 함수
async function uploadImageToMinio(buffer, filename) {
  try {
    await minioClient.putObject(bucketName, filename, buffer);
    console.log(`이미지 업로드 완료: ${filename}`);
  } catch (err) {
    console.error('MinIO 이미지 업로드 오류:', err.message);
    throw err;
  }
}

// Express 및 Socket.IO 설정
const app = express();
app.use(express.static('public'));
const httpServer = createServer(app);
const io = new Server(httpServer, {
  cors: {
    origin: "*",
    methods: ["GET", "POST"]
  },
  maxHttpBufferSize: 20 * 1024 * 1024
});

io.use(authenticate);

// 메시지 전송
function sendChatMessage({ socket, roomId, message, messageType, imageUrl = null }) {
  const timestamp = new Date();
  const userId = socket.data.user.id;

  pubClient.publish(`room_${roomId}_channel`, JSON.stringify({
    message,
    userId,
    timestamp,
    messageType
  }));

  socket.broadcast.to(roomId).emit('chat message', {
    userId,
    message,
    timestamp: timestamp.toISOString(),
    messageType,
    imageUrl,
    is_read: false
  });

  return timestamp;
}

// 서버 실행
Promise.all([
  ensureMinioBucketReady(),
  pubClient.connect(),
  subClient.connect()
]).then(() => {
  io.adapter(createAdapter(pubClient, subClient));
  console.log('Redis 및 MinIO 준비 완료');

  io.on('connection', (socket) => {
    if (!socket.data.user || !socket.data.user.id) {
      console.error('인증 안된 연결입니다. 연결 종료:', socket.id);
      socket.disconnect(true);
      return;
    }
    console.log(`인증된 연결: ${socket.id}, 사용자 ID: ${socket.data.user.id}`);

    socket.on('join', async (roomId) => {
      const userId = socket.data.user.id;

        try {
          const allowed = await isUserInRoom(userId, roomId);
          if (!allowed) {
            console.warn(`접근 불가: 사용자 ${userId}가 방 ${roomId}에 참가하려 함`);
            socket.emit('error', { message: '해당 채팅방에 접근 권한이 없습니다.' });
            return;
          }

          socket.join(roomId);
          console.log(`${socket.id} -> 방 참가: ${roomId}`);
        } catch (err) {
          console.error('방 참가 중 오류:', err.message);
          socket.emit('error', { message: '서버 오류로 방 참가에 실패했습니다.' });
        }
    });


    socket.on('text', async ({ roomId, message}) => {
      const userId = socket.data.user.id;
      console.log(`텍스트 메시지 수신: ${message} | 방: ${roomId} | 사용자: ${userId}`)

      const timestamp = sendChatMessage({
        socket,
        userId,
        roomId,
        message,
        messageType: 'text'
      });

      const query = `
        INSERT INTO chat_message (chatroom_id, sender_id, content, message_type, timestamp, is_read)
        VALUES (?, ?, ?, ?, ?, ?)
      `;
      const values = [roomId, userId, message, 'text', timestamp, false];

      db.query(query, values, (err, result) => {
        if (err) {
          console.error('MySQL 텍스트 메시지 저장 오류:', err.message);
        } else {
          console.log('MySQL에 텍스트 메시지 저장 성공:', result.insertId);
        }
      });
    });

    socket.on('image', async ({ roomId, imageBase64 }) => {
      const userId = socket.data.user.id;
      try {
        if (!imageBase64) {
          throw new Error('이미지 데이터가 없습니다.');
        }

        const buffer = Buffer.from(imageBase64, 'base64');
        const filename = `chat-images/${Date.now()}_${userId}.png`;

        await uploadImageToMinio(buffer, filename);

        // const imageUrl = `http://${process.env.MINIO_HOST}:${process.env.MINIO_PORT}/${bucketName}/${filename}`;
        const imageUrl = `http://${process.env.HOST_PUBLIC_MINIO}:${process.env.MINIO_PORT}/${bucketName}/${filename}`;

        const timestamp = sendChatMessage({
          socket,
          userId,
          roomId,
          message: '[이미지]',
          messageType: 'image',
          imageUrl
        });

        const query = `
          INSERT INTO chat_message (chatroom_id, sender_id, content, message_type, timestamp, is_read, image_url)
          VALUES (?, ?, ?, ?, ?, ?, ?)
        `;
        const values = [roomId, userId, '[이미지]', 'image', timestamp, false, imageUrl];

        db.query(query, values, (err, result) => {
          if (err) {
            throw new Error(`MySQL 이미지 메시지 저장 오류: ${err.message}`);
          } else {
            console.log('MySQL에 이미지 메시지 저장 성공:', result.insertId);
            console.log(`imageUrl: ${imageUrl}`);
            
          }
        });

      } catch (err) {
        console.error('이미지 메시지 처리 중 오류:', err.message);
      }
    });

    socket.on('disconnect', () => {
      console.log(`연결 종료: ${socket.id}`);
    });
  });

  const PORT = process.env.SOCKET_PORT || 3000;
  httpServer.listen(PORT, () => {
    console.log(`Socket.IO 서버 실행 중 (포트: ${PORT})`);
  });

}).catch(err => {
  console.error('서버 시작 중 오류:', err);
});
