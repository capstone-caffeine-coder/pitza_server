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

    message_type = models.CharField(max_length=10, default='text')  # 'text' or 'image'
    image_url = models.URLField(blank=True, null=True)  # 이미지 저장용 URL

class ChatParticipant(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    chatroom = models.ForeignKey(ChatRoom, on_delete=models.CASCADE)
    last_read_message = models.ForeignKey(Message, null=True, blank=True, on_delete=models.SET_NULL)

    class Meta:
        unique_together = ('user', 'chatroom')

class Report(models.Model):
    chatroom = models.ForeignKey(ChatRoom, on_delete=models.CASCADE)
    message = models.ForeignKey(Message, on_delete=models.CASCADE)
    reporter = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reports')
    reason = models.CharField(max_length=255)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Report {self.id} for message {self.message.id} in chatroom {self.chatroom.id}"
