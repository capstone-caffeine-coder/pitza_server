from django.db import models
from django.contrib.auth.models import User

class ChatRoom(models.Model):
    participants = models.ManyToManyField(User)
    post_id = models.CharField(max_length=100)  # 게시글 ID (string으로 저장)
    created_at = models.DateTimeField(auto_now_add=True)

class Message(models.Model):
    chatroom = models.ForeignKey(ChatRoom, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)