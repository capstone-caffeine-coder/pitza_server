from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.contrib.auth.models import User
from .models import ChatRoom
from .serializers import ChatRoomSerializer, ChatRoomDetailSerializer

from rest_framework.permissions import AllowAny
from rest_framework.decorators import api_view, permission_classes


class ChatRoomCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        post_id = request.data.get("post_id")
        receiver_id = request.data.get("receiver_id")
        sender = request.user

        try:
            receiver = User.objects.get(id=receiver_id)
        except User.DoesNotExist:
            return Response({"error": "Invalid receiver_id"}, status=status.HTTP_400_BAD_REQUEST)

        # 중복 채팅방이 있는지 확인하고 없으면 새로 생성
        existing_room = ChatRoom.objects.filter(
            post_id=post_id,
            participants=sender
        ).filter(participants=receiver).first()

        if existing_room:
            room = existing_room
        else:
            room = ChatRoom.objects.create(post_id=post_id)
            room.participants.set([sender, receiver])
            room.save()

        response_data = {
            "chatroom_id": str(room.id),
            "participants": [str(user.id) for user in room.participants.all()],
            "created_at": room.created_at.isoformat()
        }

        return Response(response_data, status=status.HTTP_201_CREATED)

@api_view(['GET'])
@permission_classes([AllowAny])
def chatroom_list(request):
    # user = request.user
    # chatrooms = ChatRoom.objects.filter(participants=user).order_by('-created_at')
    chatrooms = ChatRoom.objects.all()

    serializer = ChatRoomSerializer(chatrooms, many=True, context={'request': request})
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([AllowAny])
def chat_room_detail(request, room_id):
    try:
        room = ChatRoom.objects.prefetch_related('messages__sender', 'participants').get(id=room_id)
        serializer = ChatRoomDetailSerializer(room)
        return Response(serializer.data)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return Response({'error': str(e)}, status=500)

'''
@api_view(['POST'])
@permission_classes([AllowAny])  # WebSocket 서버에서 요청하므로 인증 생략 가능
def save_message(request):
    try:
        room_id = request.data.get("room_id")
        sender_id = request.data.get("sender_id")
        content = request.data.get("content")

        chatroom = ChatRoom.objects.get(id=room_id)
        sender = User.objects.get(id=sender_id)

        message = Message.objects.create(
            chatroom=chatroom,
            sender=sender,
            content=content
        )
        serializer = MessageSerializer(message)
        return Response(serializer.data, status=201)
    except Exception as e:
        return Response({"error": str(e)}, status=400)
    '''