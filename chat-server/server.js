require('dotenv').config();

const express = require('express');
const { createServer } = require('http');
const { Server } = require('socket.io');
const { createAdapter } = require('@socket.io/redis-adapter');
const { createClient } = require('redis');
const mysql = require('mysql2');
const Minio = require('minio');
const { log } = require('console');

// 인증 미들웨어
function authenticate(socket, next) {
  socket.user = { id: 1, name: "TestUser" }; // TODO: 실제 인증 구현 필요
  next();
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
function sendChatMessage({ roomId, userId, message, messageType, imageUrl = null }) {
  const timestamp = new Date();

  pubClient.publish(`room_${roomId}_channel`, JSON.stringify({
    message,
    userId,
    timestamp,
    messageType
  }));

  io.to(roomId).emit('chat message', {
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
    console.log(`새로운 연결: ${socket.id}`);

    socket.on('join', (roomId) => {
      socket.join(roomId);
      console.log(`${socket.id} -> 방 참가: ${roomId}`);
    });

    // 메시지 읽음 처리
    // socket.on('read_message', ({ roomId, messageId, userId }) => {
    //   console.log(`메시지 읽음 처리 수신: 메시지 ID = ${messageId} | 방 = ${roomId} | 사용자 = ${userId}`);

    //   // MySQL에서 읽음 처리 로직
    //   const query = `
    //     UPDATE chat_message
    //     SET is_read = true
    //     WHERE id = ? AND chatroom_id = ? AND sender_id != ?
    //   `;
    //   const values = [messageId, roomId, userId]; // 자기 자신이 보낸 메시지는 제외

    //   db.query(query, values, (err, result) => {
    //     if (err) {
    //       console.error('MySQL 읽음 처리 오류:', err.message);
    //       socket.emit('error', { message: '읽음 처리 오류' });
    //     } else {
    //       console.log('MySQL에서 메시지 읽음 처리 성공');
    //       // ChatParticipant 테이블의 마지막 읽은 메시지 갱신
    //       const updateLastReadQuery = `
    //         UPDATE chat_participant
    //         SET last_read_message_id = ?
    //         WHERE chatroom_id = ? AND user_id = ?
    //       `;
    //       db.query(updateLastReadQuery, [messageId, roomId, userId], (err) => {
    //         if (err) {
    //           console.error('MySQL에서 ChatParticipant 읽음 처리 오류:', err.message);
    //           socket.emit('error', { message: 'ChatParticipant 읽음 처리 오류' });
    //         } else {
    //           console.log('ChatParticipant의 마지막 읽은 메시지 갱신 성공');
    //           // 메시지를 읽었음을 클라이언트에 알림
    //           io.to(roomId).emit('message_read', { messageId, userId });
    //         }
    //       });
    //     }
    //   });
    // });

    socket.on('chat message:text', async ({ roomId, message, userId }) => {
      console.log(`텍스트 메시지 수신: ${message} | 방: ${roomId} | 사용자: ${userId}`);

      const timestamp = sendChatMessage({
        roomId,
        userId,
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

    socket.on('chat message:image', async ({ roomId, imageBase64, userId }) => {
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
          roomId,
          userId,
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
