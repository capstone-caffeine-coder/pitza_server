from rest_framework import serializers
from .models import ChatRoom, Message
from django.contrib.auth.models import User

class ChatRoomSerializer(serializers.ModelSerializer):
    participants = serializers.SlugRelatedField(
        many=True,
        read_only=True,
        slug_field='username'  # 혹은 id로 바꿔도 됨
    )

    class Meta:
        model = ChatRoom
        fields = ['id', 'participants', 'post_id', 'created_at']
        read_only_fields = ['id', 'participants', 'created_at']

class ChatRoomListSerializer(serializers.ModelSerializer):
    chatroom_id = serializers.SerializerMethodField()
    last_message = serializers.SerializerMethodField()
    last_message_at = serializers.SerializerMethodField()
    partner = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()

    class Meta:
        model = ChatRoom
        fields = ['chatroom_id', 'partner', 'last_message', 'last_message_at', 'unread_count']
    
    def get_chatroom_id(self, obj):
        return str(obj.id)

    def get_last_message(self, obj):
        last_msg = obj.messages.order_by('-timestamp').first()
        return last_msg.content if last_msg else ""

    def get_last_message_at(self, obj):
        last_msg = obj.messages.order_by('-timestamp').first()
        return last_msg.timestamp.isoformat() if last_msg else None

    def get_partner(self, obj):
        user = self.context['request'].user  # 현재 요청한 사용자
        # user = self.context.get('user') # 테스트를 위함
        other = obj.participants.exclude(id=user.id).first()  # 현재 사용자를 제외한 상대방
        return {
            "id": other.id,
            "name": other.username,  # 상대방의 ID와 닉네임
            "profileImage": getattr(other, 'profile_picture', '')  # 없으면 빈 문자열
        } if other else None

    def get_unread_count(self, obj):
        user = self.context.get('user')
        if user is None:
            return 0
        return obj.messages.filter(is_read=False).exclude(sender=user).count()

class MessageSerializer(serializers.ModelSerializer):
    sender = serializers.CharField(source='sender.username')
    message = serializers.CharField(source='content')
    sent_at = serializers.DateTimeField(source='timestamp')

    class Meta:
        model = Message
        fields = ['sender', 'message', 'message_type', 'image_url', 'sent_at', 'is_read']

class ChatRoomDetailSerializer(serializers.ModelSerializer):
    messages = MessageSerializer(many=True)
    participants = serializers.SlugRelatedField(
        many=True, slug_field='username', read_only=True
    )
    room_id = serializers.IntegerField(source='id')

    class Meta:
        model = ChatRoom
        fields = ['room_id', 'messages', 'participants']