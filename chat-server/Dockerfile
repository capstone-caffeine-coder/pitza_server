# 기존에 있는 내용
FROM node:18

# 작업 디렉토리 설정
WORKDIR /usr/src/app

# 패키지 설치
COPY package*.json ./
RUN npm install  # 여기에 redis 패키지가 포함될 것입니다.

# 서버 코드 복사
COPY . .

# 애플리케이션 실행
CMD ["node", "server.js"]

COPY package*.json ./
RUN npm install