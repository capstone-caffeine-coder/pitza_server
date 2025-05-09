from django.urls import path
# from .views import ChatRoomCreateView, ChatRoomListView
from .views import ChatRoomCreateView, chatroom_list, chat_room_detail

urlpatterns = [
    path('rooms', ChatRoomCreateView.as_view(), name='chatroom-create'),
    path('rooms/list', chatroom_list, name='chat-room-list'),
    path('rooms/<int:room_id>', chat_room_detail, name='chat-room-detail'),
]