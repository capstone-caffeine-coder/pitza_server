from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status, serializers
# from django.contrib.auth.models import User
from django.contrib.auth import get_user_model
from .models import ChatRoom, ChatParticipant, Message, Report
from .serializers import ChatRoomSerializer, ChatRoomListSerializer, ChatRoomDetailSerializer, ChatRoomCreateRequestSerializer, ReadMessageUpdateRequestSerializer, ReportSerializer

from rest_framework.permissions import AllowAny
from rest_framework.decorators import api_view, permission_classes
from django.shortcuts import get_object_or_404
from django.db.models import Prefetch

import re

PROFANITY_REGEX = re.compile(r"[시씨씪슈쓔쉬쉽쒸쓉](?:[0-9]*|[0-9]+ *)[바발벌빠빡빨뻘파팔펄]|[섊좆좇졷좄좃좉졽썅춍봊]|[ㅈ조][0-9]*까|ㅅㅣㅂㅏㄹ?|ㅂ[0-9]*ㅅ|[ㅄᄲᇪᄺᄡᄣᄦᇠ]|[ㅅㅆᄴ][0-9]*[ㄲㅅㅆᄴㅂ]|[존좉좇][0-9 ]*나|[자보][0-9]+지|보빨|[봊봋봇봈볻봁봍] *[빨이]|[후훚훐훛훋훗훘훟훝훑][장앙]|[엠앰]창|애[미비]|애자|[가-탏탑-힣]색기|(?:[샊샛세쉐쉑쉨쉒객갞갟갯갰갴겍겎겏겤곅곆곇곗곘곜걕걖걗걧걨걬] *[끼키퀴])|새 *[키퀴]|[병븅][0-9]*[신딱딲]|미친[가-닣닥-힣]|[믿밑]힌|[염옘][0-9]*병|[샊샛샜샠섹섺셋셌셐셱솃솄솈섁섂섓섔섘]기|[섹섺섻쎅쎆쎇쎽쎾쎿섁섂섃썍썎썏][스쓰]|[지야][0-9]*랄|니[애에]미|갈[0-9]*보[^가-힣]|[뻐뻑뻒뻙뻨][0-9]*[뀨큐킹낑)|꼬[0-9]*추|곧[0-9]*휴|[가-힣]슬아치|자[0-9]*박꼼|빨통|[사싸](?:이코|가지|[0-9]*까시)|육[0-9]*시[랄럴]|육[0-9]*실[알얼할헐]|즐[^가-힣]|찌[0-9]*(?:질이|랭이)|찐[0-9]*따|찐[0-9]*찌버거|창[녀놈]|[가-힣]{2,}충[^가-힣]|[가-힣]{2,}츙|부녀자|화냥년|환[양향]년|호[0-9]*[구모]|조[선센][징]|조센|[쪼쪽쪾](?:[발빨]이|[바빠]리)|盧|무현|찌끄[레래]기|(?:하악){2,}|하[앍앜]|[낭당랑앙항남담람암함][ ]?[가-힣]+[띠찌]|느[금급]마|文在|在寅|(?<=[^\n])[家哥]|속냐|[tT]l[qQ]kf|Wls|[ㅂ]신|[ㅅ]발|[ㅈ]밥", re.IGNORECASE)

from drf_yasg.utils import swagger_auto_schema

User = get_user_model()

class ChatRoomCreateView(APIView):

    @swagger_auto_schema(request_body=ChatRoomCreateRequestSerializer,responses={201: ChatRoomSerializer})
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
@swagger_auto_schema(responses={200: ChatRoomListSerializer(many=True)})
def chatroom_list(request):
    user = request.user

    chatrooms = ChatRoom.objects.filter(participants=user).order_by('-created_at')
    serializer = ChatRoomListSerializer(chatrooms, many=True, context={'request': request, 'user': user})
    return Response(serializer.data)

@api_view(['GET'])
@swagger_auto_schema(responses={200: ChatRoomDetailSerializer})
def chat_room_detail(request, room_id):
    user = request.user

    try:
        room = ChatRoom.objects.prefetch_related(
            'participants',
            Prefetch('messages', queryset=Message.objects.select_related('sender').order_by('timestamp'))
        ).get(id=room_id)
        
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
    @swagger_auto_schema(request_body=ReadMessageUpdateRequestSerializer, responses={200: 'Success'})
    def post(self, request, room_id):
        try:
            user = request.user
            last_read_message_id = request.data.get("last_read_message_id")

            if not last_read_message_id:
                return Response({"error": "last_read_message_id is required"}, status=400)

            chatroom = ChatRoom.objects.get(id=room_id)
            message = Message.objects.get(id=last_read_message_id, chatroom=chatroom)

            participant, created = ChatParticipant.objects.get_or_create(user=user, chatroom=chatroom)
            participant.last_read_message = message
            participant.save()

            Message.objects.filter(
                chatroom=chatroom,
                id__lte=last_read_message_id
            ).exclude(sender=user).update(is_read=True)

            return Response({"success": True})

        except ChatRoom.DoesNotExist:
            return Response({"error": "ChatRoom not found"}, status=404)
        except Message.DoesNotExist:
            return Response({"error": "Message not found in room"}, status=404)
        except Exception as e:
            return Response({"error": str(e)}, status=500)

@api_view(['POST'])
@swagger_auto_schema(responses={200: 'Success'})
def leave_chat_room(request, room_id):
    try:
        user = request.user
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

def detect_auto_reason(content):
    if PROFANITY_REGEX.search(content):
        return "자동 감지: 욕설 및 성희롱"
    return None


@swagger_auto_schema(method='post', request_body=ReportSerializer, responses={201: 'Success'})
@api_view(['POST'])
def report_message(request, room_id):
    try:
        chatroom = get_object_or_404(ChatRoom, id=room_id)

        # user_id = request.data.get('user_id')
        message_ids = request.data.get('message_id')
        reason = request.data.get('reason')
        description = request.data.get('description')

        if not message_ids or not reason or not description:
            return Response({
                "error": "required message_id, reason, description"
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            # reporter = User.objects.get(id=user_id)
            reporter = request.user
        except User.DoesNotExist:
            return Response({"error": "Invalid user ID"}, status=400)

        # 메시지 유효성 검증
        messages = Message.objects.filter(id__in=message_ids, chatroom=chatroom)
        if messages.count() != len(message_ids):
            return Response({
                "error": "일부 메시지가 존재하지 않거나 채팅방에 속하지 않습니다."
            }, status=status.HTTP_400_BAD_REQUEST)

        # 신고 저장 (중복 신고 방지)
        created_reports = []
        for message in messages:
            already_reported = Report.objects.filter(
                chatroom=chatroom,
                message=message,
                reporter=reporter
            ).exists()

            if already_reported:
                continue

            # 자동 필터링 적용
            auto_reason = detect_auto_reason(message.content)
            final_reason = auto_reason if auto_reason else reason
            final_description = "자동 감지된 메시지입니다." if auto_reason else description

            report = Report.objects.create(
                chatroom=chatroom,
                message=message,
                reporter=reporter,
                reason=final_reason,
                description=final_description
            )
            created_reports.append(report)

            # print(f"[신고 저장됨] report_id={report.id}, reason={report.reason}, description={report.description}")

        if not created_reports:
            return Response({
                "status": "skipped",
                "message": "이미 모든 메시지가 신고된 상태입니다."
            }, status=status.HTTP_200_OK)

        return Response({
            "report_id": str(created_reports[0].id),
            "status": "received",
            "message": "신고가 접수되었습니다."
        }, status=status.HTTP_201_CREATED)

    except Exception as e:
        import traceback
        traceback.print_exc()
        return Response({'error': str(e)}, status=500)
