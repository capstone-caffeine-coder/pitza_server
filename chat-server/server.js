require('dotenv').config();  // 환경 변수 로드

const express = require('express');  // express 모듈을 먼저 require
const { createServer } = require('http');
const { Server } = require('socket.io');
const { createAdapter } = require('@socket.io/redis-adapter');
const { createClient } = require('redis');
const mysql = require('mysql2');

// 인증 미들웨어 (현재는 인증 생략)
function authenticate(socket, next) {
  // 테스트용 사용자 정보 직접 부여
  socket.user = { id: 1, name: "TestUser" };
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
  url: `redis://${process.env.REDIS_HOST}:${process.env.REDIS_PORT}`
});
const subClient = pubClient.duplicate();

// Express 애플리케이션 생성
const app = express();
const httpServer = createServer(app);

// io는 httpServer가 생성된 후에 선언되어야 합니다
const io = new Server(httpServer, {
  cors: {
    origin: "*",
    methods: ["GET", "POST"]
  }
});

io.use(authenticate);  // Socket.IO에 인증 미들웨어 추가

// Redis 어댑터 연결
Promise.all([pubClient.connect(), subClient.connect()])
  .then(() => {
    io.adapter(createAdapter(pubClient, subClient));
    console.log('Redis 어댑터 연결 완료');

    // io.on은 Redis 어댑터 연결 이후에 안전하게 실행
    io.on('connection', (socket) => {
      console.log(`새로운 연결: ${socket.id}`);

      socket.on('join', (roomId) => {
        socket.join(roomId);
        console.log(`${socket.id} -> 방 참가: ${roomId}`);
      });

      socket.on('chat message', async ({ roomId, message, userId }) => {
        const timestamp = new Date();
        console.log(`메시지 수신: ${message} | 방: ${roomId} | 사용자: ${userId} | 사용자 ID 길이: ${userId.length}`);

        // Redis에 메시지 전송
        pubClient.publish(`room_${roomId}_channel`, JSON.stringify({ message, userId, timestamp }));

        io.to(roomId).emit('chat message', {
          userId,
          message,
          timestamp: timestamp.toISOString(),
          is_read: false
        });

        const query = `
          INSERT INTO chat_message (chatroom_id, sender_id, content, timestamp, is_read)
          VALUES (?, ?, ?, ?, ?)
        `;
        const values = [roomId, userId, message, timestamp, false];

        db.query(query, values, (err, result) => {
          if (err) {
            console.error('MySQL 메시지 저장 오류:', err.message);
          } else {
            console.log('MySQL에 메시지 저장 성공:', result.insertId);
          }
        });
      });

      socket.on('disconnect', () => {
        console.log(`연결 종료: ${socket.id}`);
      });
    });

    // 서버 실행
    const PORT = process.env.SOCKET_PORT || 3000;
    httpServer.listen(PORT, () => {
      console.log(`Socket.IO 서버 실행 중 (포트: ${PORT})`);
    });
  })
  .catch(err => {
    console.error('Redis 연결 실패:', err);
  });
