from django.db import models

class User(models.Model):
    username = models.CharField(max_length=50, unique=True)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=128)
    f_name = models.CharField(max_length=50)
    l_name = models.CharField(max_length=50)    
    m_name = models.CharField(max_length=50, null=True, blank=True)

    def __str__(self):
        return self.username
    
class Profile(models.Model):
    GENDER_CHOICES = [ 
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE)  # Changed from ForeignKey to OneToOneField
    profile_picture = models.ImageField(upload_to='profile_pictures/', null=True, blank=True)
    bio = models.TextField(null=True, blank=True)
    b_day = models.DateField(null=True, blank=True)
    phone_number = models.CharField(max_length=20, null=True, blank=True)
    address = models.CharField(max_length=200, null=True, blank=True)
    gender = models.CharField(max_length=10, null=True, blank=True , choices=GENDER_CHOICES)

    def __str__(self):
        return  self.user.username
    
class CoverPhoto(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    coverphoto = models.ImageField(upload_to='cover_pictures/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Cover photo for {self.user.f_name}  {self.user.l_name}'


class PostImage(models.Model):
    post = models.ForeignKey('Post', on_delete=models.CASCADE)
    image = models.ImageField(upload_to='post_images/')
    
class Post(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='posts')
    title = models.CharField(max_length=255)
    post_image = models.ManyToManyField(PostImage, blank=True, related_name='posts')
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    no_of_likes = models.IntegerField(default=0)
    

    def __str__(self):
        return self.title

class LikePost(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    post = models.ForeignKey(Post, on_delete=models.CASCADE)

    def __str__(self):
      return f"{self.user.username} liked {self.post.title}"
    
class Comment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)




class AddFriend(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    friend = models.ForeignKey(User, on_delete=models.CASCADE, related_name='friends')

    class Meta:
        unique_together = ('user', 'friend')
        constraints = [
            models.CheckConstraint(
                check=~models.Q(user=models.F('friend')),
                name='prevent_self_friendship'
            )
        ]



class Convsersation(models.Model):
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_conversations')
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_conversations')
    message = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('sender', 'recipient')

    def __str__(self):
        return f"Conversation between {self.sender.username} and {self.recipient.username}"
    

class Message(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    conversation = models.ForeignKey(Convsersation, on_delete=models.CASCADE, related_name='messages')
    message = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.message


class Notifications(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    post = models.ForeignKey(Post, on_delete=models.CASCADE,related_name='notifications')
    content = models.CharField(max_length=255)
    timestamp = models.DateTimeField(auto_now_add=True)
