from django.contrib import admin
from .models import Post,User,Profile,PostImage, Comment,AddFriend,LikePost,Convsersation,Message,Notifications,CoverPhoto


admin.site.register(Post)
admin.site.register(User)
admin.site.register(Profile)
admin.site.register(Comment)
admin.site.register(AddFriend)
admin.site.register(LikePost)
admin.site.register(Convsersation)
admin.site.register(Message)
admin.site.register(Notifications)
admin.site.register(CoverPhoto)
admin.site.register(PostImage)