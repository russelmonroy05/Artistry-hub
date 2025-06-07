from django.urls import path
from . import views



urlpatterns = [
    path('', views.welcome_view, name='welcome'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('signup/', views.signup_view, name='signup'),
    path('profile/', views.profile_view, name='Profile'),
    path('edit_profile/', views.edit_profile, name='edit_profile'),
    path('create_profile/', views.create_profile, name='create_profile'),
    path('like_post/<int:post_id>', views.like_post, name='like_post'),
    path('view-profile/<int:user_id>/', views.view_profile, name='view_profile'),
    path('blank-profile/<int:user_id>/', views.view_blank_profile, name='blank_profile'),
    path('add_friend/<int:user_id>', views.add_friend, name='add_friend'),
    path('friend_request/<int:user_id>', views.friend_request, name='friend_request'),
    path('friend_request_list/', views.friend_request_list, name='friend_request_list'),
    path('conversations/<int:conversation_id>/',views.conversation_detail, name='conversation_detail'),
    path('create_conversation/<int:recipient_id>/', views.create_conversation, name='create_conversation'),
    path('send_message/<int:recipient_id>', views.send_message, name='send_message'),
    path('check_like/<int:post_id>', views.check_like, name='check_like'),
    path('post/<int:post_id>/comment/<int:comment_id>/delete/', views.delete_comment, name='delete_comment'),
    path('edit_cover_photo/', views.edit_cover_photo, name='edit_cover'),
    path('post/update/<int:post_id>/', views.update_post, name='update_post'),
    path('post/delete/<int:post_id>/', views.delete_post, name='delete_post'),
    path('post/<int:post_id>/comment/update/<int:comment_id>/', views.update_comment, name='update_comment'),
    path('message/update/<int:message_id>/', views.update_message, name='update_message'),
    path('message/delete/<int:message_id>/', views.delete_message, name='delete_message'),
    





    # path('conversation/<int:user_id>/', views.conversation, name='Conversation'),
    # path('messages/', views.messages, name='messages'),
    # path('conversations/', views.conversations, name='conversations'),
    # path('conversations/<int:conversation_id>/', views.conversation, name='conversation'),
    # path('conversations/create/<int:recipient_id>/', views.create_conversation, name='create_conversation'),




]