from django.urls import path
from . import views

app_name = 'chat'

urlpatterns = [
    # Chat room list and specific room
    path('', views.ChurchChatListView.as_view(), name='church_list'),
    path('<int:church_id>/', views.ChatView.as_view(), name='chat_room'),

    # API for getting new messages
    path('<int:church_id>/messages/',
         views.GetMessagesView.as_view(), name='get_messages'),

    # API for sending a new message
    path('incharge/create/', views.create_incharge_profile_view,
         name='create_incharge'),


]
