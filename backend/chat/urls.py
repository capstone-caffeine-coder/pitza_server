from django.urls import path
from .views import ChatRoomCreateView, chatroom_list, chat_room_detail, leave_chat_room

urlpatterns = [
    path('rooms', ChatRoomCreateView.as_view(), name='chatroom-create'),
    path('rooms/list', chatroom_list, name='chat-room-list'),
    path('rooms/<int:room_id>', chat_room_detail, name='chat-room-detail'),
    path('rooms/<int:room_id>/leave', leave_chat_room, name='chat-room-leave'),
]