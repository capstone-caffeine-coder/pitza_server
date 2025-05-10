require('dotenv').config();
const express = require('express');
const { createServer } = require('http');
const { Server } = require('socket.io');
const { createAdapter } = require('@socket.io/redis-adapter');
const { createClient } = require('redis');

const app = express();
const httpServer = createServer(app);
const io = new Server(httpServer, {
  cors: {
    origin: "*",  // 개발 시에는 *로, 배포 시에는 프론트 주소 명시
    methods: ["GET", "POST"]
  }
});

// Redis 클라이언트 설정
const pubClient = createClient({ url: `redis://${process.env.REDIS_HOST}:${process.env.REDIS_PORT}` });
const subClient = pubClient.duplicate();

Promise.all([pubClient.connect(), subClient.connect()])
  .then(() => {
    io.adapter(createAdapter(pubClient, subClient));
    console.log('Redis 어댑터 연결 완료');
  });

io.on('connection', (socket) => {
  console.log(`새 연결됨: ${socket.id}`);

  socket.on('join', (roomId) => {
    socket.join(roomId);
    console.log(`${socket.id} joined room ${roomId}`);
  });

  
  // socket.on('chat message', ({ roomId, message }) => {
  //   io.to(roomId).emit('chat message', { sender: socket.id, message });
  // });

  socket.on('chat message', (msg) => {  // 수정된 부분
    console.log(`받은 메시지: ${msg}`);  // 받은 메시지를 서버 로그에 출력
    io.emit('chat message', msg);  // 모든 클라이언트에 메시지 전송
  });


  socket.on('disconnect', () => {
    console.log(`연결 종료됨: ${socket.id}`);
  });
});

httpServer.listen(3000, () => {
  console.log('Socket.IO 서버가 3000번 포트에서 실행 중');
});
