from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.contrib.auth.models import User
from .models import ChatRoom, ChatParticipant, Message
from .serializers import ChatRoomSerializer, ChatRoomListSerializer, ChatRoomDetailSerializer

from rest_framework.permissions import AllowAny
from rest_framework.decorators import api_view, permission_classes


class ChatRoomCreateView(APIView):
    permission_classes = [AllowAny]
    #permission_classes = [IsAuthenticated]

    def post(self, request):
        post_id = request.data.get("post_id")
        receiver_id = request.data.get("receiver_id")
        sender = User.objects.get(id=1)
        #sender = request.user
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

    # 테스트 편의상 sender_id 쿼리 파라미터로 사용자 ID를 받아 처리
    user_id = request.query_params.get('user_id')
    if not user_id:
        return Response({"error": "required user_id"}, status=400)
    
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return Response({"error": "Invalid user_id"}, status=400)

    chatrooms = ChatRoom.objects.filter(participants=user).order_by('-created_at')
    serializer = ChatRoomListSerializer(chatrooms, many=True, context={'request': request, 'user': user})
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([AllowAny])
def chat_room_detail(request, room_id):
    # user = request.user
    user_id = request.query_params.get('user_id')
    if not user_id:
        return Response({"error": "required user_id"}, status=400)

    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return Response({"error": "Invalid user_id"}, status=400)

    try:
        room = ChatRoom.objects.prefetch_related('messages__sender', 'participants').get(id=room_id)
        
        # 요청 유저가 이 방의 참가자인지 확인
        if user not in room.participants.all():
            return Response({"error": "not a participant"}, status=403)

        serializer = ChatRoomDetailSerializer(room)
        return Response(serializer.data)
    except ChatRoom.DoesNotExist:
        return Response({'error': 'ChatRoom not found'}, status=404)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return Response({'error': str(e)}, status=500)

class ReadMessageUpdateView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, room_id):
        try:
            user_id = request.data.get("user_id")  # 추후 request.user로 대체
            last_read_message_id = request.data.get("last_read_message_id")

            if not last_read_message_id:
                return Response({"error": "last_read_message_id is required"}, status=400)

            user = User.objects.get(id=user_id)
            chatroom = ChatRoom.objects.get(id=room_id)
            message = Message.objects.get(id=last_read_message_id, chatroom=chatroom)

            participant, created = ChatParticipant.objects.get_or_create(user=user, chatroom=chatroom)
            participant.last_read_message = message
            participant.save()

            message.is_read = True
            message.save()

            return Response({"success": True})

        except User.DoesNotExist:
            return Response({"error": "Invalid user ID"}, status=400)
        except ChatRoom.DoesNotExist:
            return Response({"error": "ChatRoom not found"}, status=404)
        except Message.DoesNotExist:
            return Response({"error": "Message not found in room"}, status=404)
        except Exception as e:
            return Response({"error": str(e)}, status=500)

@api_view(['POST'])
@permission_classes([AllowAny])
def leave_chat_room(request, room_id):
    try:
        user_id = request.data.get('user_id')
        user = User.objects.get(id=user_id)
        room = ChatRoom.objects.get(id=room_id)
        
        if user in room.participants.all():
            room.participants.remove(user)
            return Response({'message': '채팅방에서 나갔습니다.'}, status=200)
        else:
            return Response({'error': '채팅방에 없는 사용자입니다.'}, status=400)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return Response({'error': str(e)}, status=500)
