require('dotenv').config();

const express = require('express');
const { createServer } = require('http');
const { Server } = require('socket.io');
const { createAdapter } = require('@socket.io/redis-adapter');
const { createClient } = require('redis');
const mysql = require('mysql2');
const Minio = require('minio');
const axios = require('axios');
const { pathToFileURL } = require('url');
const { log } = require('console');

async function authenticate(socket, next) {
  const cookieHeader = socket.handshake.headers.cookie;
  console.log('Received cookies:', cookieHeader);
    try {
      if (!cookieHeader) {
        console.log('쿠키가 없습니다. 인증 실패');
        return next(new Error('Authentication failed: No cookies'));
      }

      const response = await axios.get('http://web:8000/get_user_by_session/', {
        headers: {
          cookie: cookieHeader
        },
        withCredentials: true 
      });

      socket.data.user = response.data;
      console.log('인증 성공 - 사용자 ID:', socket.data.user.id);
      next();

    } catch (err) {
      console.error('인증 오류:', err.message || err);
      next(new Error('Authentication failed'));
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
    origin: [
      "http://localhost:5173",
      "http://localhost:8000", // 테스트목적
      "http://127.0.0.1:5500"
    ],
    methods: ["GET", "POST"],
    credentials: true
  },
  maxHttpBufferSize: 20 * 1024 * 1024
});

io.use(authenticate);

// timestamp 포맷 함수
function formatTimestampForMySQL(date) {
  return new Date(date).toISOString().slice(0, 19).replace('T', ' ');
}

// 메시지 전송
function sendChatMessage({ socket, roomId, message, messageType, timestamp = null, imageUrl = null }) {
  const userId = socket.data.user.id;
  const formattedTimestamp = formatTimestampForMySQL(new Date());

  const payload = {
    roomId,
    userId,
    message,
    timestamp: formattedTimestamp,
    messageType,
    imageUrl,
    is_read: false
  };

  pubClient.publish(`room_${roomId}_channel`, JSON.stringify(payload));
  socket.broadcast.to(roomId).emit('chat message', payload);

  return payload;
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


    socket.on('text', async (payload) => {
      const { roomId, message } = payload;
      const userId = socket.data.user.id;
      console.log(`텍스트 메시지 수신: ${message} | 방: ${roomId} | 사용자: ${userId}`)

      const finalPayload = sendChatMessage({
        socket,
        roomId,
        message,
        messageType: 'text'
      });

      const query = `
        INSERT INTO chat_message (chatroom_id, sender_id, content, message_type, timestamp, is_read)
        VALUES (?, ?, ?, ?, ?, ?)
      `;

      const values = [
        roomId, 
        userId, 
        finalPayload.message, 
        finalPayload.messageType, 
        finalPayload.timestamp, 
        finalPayload.is_read
      ];

      db.query(query, values, (err, result) => {
        if (err) {
          console.error('MySQL 텍스트 메시지 저장 오류:', err.message);
        } else {
          console.log('MySQL에 텍스트 메시지 저장 성공:', result.insertId);
        }
      });
    });

    socket.on('image', async (payload) => {
      const {roomId, imageUrl } = payload;
      const userId = socket.data.user.id;
      try {
        if (!imageUrl) {
          throw new Error('이미지 데이터가 없습니다.');
        }

        const buffer = Buffer.from(imageUrl, 'base64');
        const filename = `chat-images/${Date.now()}_${userId}.png`;

        await uploadImageToMinio(buffer, filename);

        const finalImageUrl = `http://${process.env.HOST_PUBLIC_MINIO}:${process.env.MINIO_PORT}/${bucketName}/${filename}`;

        const finalPayload = sendChatMessage({
          socket,
          roomId,
          message: '[이미지]',
          messageType: 'image',
          imageUrl: finalImageUrl,
        });

        const query = `
          INSERT INTO chat_message (chatroom_id, sender_id, content, message_type, timestamp, is_read, image_url)
          VALUES (?, ?, ?, ?, ?, ?, ?)
        `;
        const values = [
          roomId, 
          userId, 
          finalPayload.message, 
          finalPayload.messageType, 
          finalPayload.timestamp, 
          finalPayload.is_read, 
          finalPayload.imageUrl];

        db.query(query, values, (err, result) => {
          if (err) {
            throw new Error(`MySQL 이미지 메시지 저장 오류: ${err.message}`);
          } else {
            console.log('MySQL에 이미지 메시지 저장 성공:', result.insertId);            
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
