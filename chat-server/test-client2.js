const { io } = require("socket.io-client");

const socket = io("http://localhost:3000");

// 서버 연결 시
socket.on("connect", () => {
  console.log("서버에 연결됨:", socket.id);

  // 방에 입장
  socket.emit("join", "2");  // "1"번 방에 입장

  // 메시지 전송
  const message = "테스트 메시지입니다2";  // 보낼 메시지
  const userId = "2";  // 메시지 보낼 사용자 ID

  // 서버로 chat message 이벤트 발생
  socket.emit("chat message", {
    roomId: "2",  // 방 ID
    message: message,  // 메시지
    userId: userId,  // 사용자 ID
    // messageType: "text"  // 메시지 타입
  });

  // 1초 후 메시지 확인
  setTimeout(() => {
    console.log("서버로부터 메시지 수신:");
  }, 1000);
});

// 서버로부터 수신한 메시지 처리
socket.on("chat message", (data) => {
  console.log("수신된 메시지:", data);
});

// 연결 종료 시
socket.on("disconnect", () => {
  console.log("서버와의 연결이 종료되었습니다.");
});

// 에러 처리
socket.on("connect_error", (error) => {
  console.error("서버 연결 오류:", error);
});

socket.on("error", (error) => {
  console.error("소켓 오류:", error);
});