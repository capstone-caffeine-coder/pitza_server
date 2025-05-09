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
    last_message = serializers.SerializerMethodField()
    last_message_at = serializers.SerializerMethodField()
    participant = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()

    class Meta:
        model = ChatRoom
        fields = ['id', 'participant', 'last_message', 'last_message_at', 'unread_count']

    def get_last_message(self, obj):
        last_msg = obj.messages.order_by('-timestamp').first()
        return last_msg.content if last_msg else ""

    def get_last_message_at(self, obj):
        last_msg = obj.messages.order_by('-timestamp').first()
        return last_msg.timestamp.isoformat() if last_msg else None

    def get_participant(self, obj):
        user = self.context['request'].user
        other = obj.participants.exclude(id=user.id).first()
        return other.username if other else "알 수 없음"

        '''
        # user 모델 변경 필요
        profile_image_url = None
        if hasattr(other, 'profile_image') and other.profile_image: # 프로필 이미지 존재 유저
            request = self.context.get('request')
            if request:
                profile_image_url = request.build_absolute_uri(other.profile_image.url)

        return {
            "id": other.id,
            "username": other.username,
            "image": profile_image_url
        }
        '''

    def get_unread_count(self, obj):
        user = self.context['request'].user
        return obj.messages.filter(is_read=False).exclude(sender=user).count()

class MessageSerializer(serializers.ModelSerializer):
    sender = serializers.CharField(source='sender.username')
    message = serializers.CharField(source='content')
    sent_at = serializers.DateTimeField(source='timestamp')

    class Meta:
        model = Message
        fields = ['sender', 'message', 'sent_at', 'is_read']

class ChatRoomDetailSerializer(serializers.ModelSerializer):
    messages = MessageSerializer(many=True)
    participants = serializers.SlugRelatedField(
        many=True, slug_field='username', read_only=True
    )
    room_id = serializers.IntegerField(source='id')

    class Meta:
        model = ChatRoom
        fields = ['room_id', 'messages', 'participants']