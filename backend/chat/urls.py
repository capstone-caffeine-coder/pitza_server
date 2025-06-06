from django.urls import path
from .views import ChatRoomCreateView, chatroom_list, chat_room_detail, ReadMessageUpdateView, leave_chat_room, report_message, ChatTestView

urlpatterns = [
    path('rooms', ChatRoomCreateView.as_view(), name='chatroom-create'),
    path('rooms/list', chatroom_list, name='chat-room-list'),
    path('rooms/<int:room_id>', chat_room_detail, name='chat-room-detail'),
    path('rooms/<int:room_id>/messages/read', ReadMessageUpdateView.as_view(), name='read-message-update'),
    path('rooms/<int:room_id>/leave', leave_chat_room, name='chat-room-leave'),
    path('rooms/<int:room_id>/reports', report_message, name='report-message'),
    path('chat-test/', ChatTestView.as_view(), name='chat_test') # 테스트 목적
]