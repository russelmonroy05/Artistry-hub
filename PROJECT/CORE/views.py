from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.hashers import check_password
from django.contrib import messages
from .models import Post,User,Profile, Comment, LikePost,PostImage , AddFriend,Convsersation,Notifications, CoverPhoto
from .forms import PostForm,UserForm,ProfileForm, CommentForm, EditUserForm,ConvsersationForm,MessageForm, CoverPhotoForm
from django.http import JsonResponse
from django.db.models import Q
from django.urls import reverse_lazy
from django.utils import timezone


def update_post(request, post_id):
    if 'user_id' not in request.session:
        return redirect('login')
    
    user = get_object_or_404(User, id=request.session['user_id'])
    post = get_object_or_404(Post, id=post_id)

    # Ensure the logged-in user is the owner of the post
    if post.user != user:
        return HttpResponseForbidden("You are not allowed to edit this post.")

    if request.method == "POST":
        post_form = PostForm(request.POST, request.FILES, instance=post)
        if post_form.is_valid():
            post_form.save()

            # Handle updating post images
            if 'post_images' in request.FILES:
                # Clear existing images
                PostImage.objects.filter(post=post).delete()
                # Add new images
                for image in request.FILES.getlist('post_images'):
                    PostImage.objects.create(post=post, image=image)

            messages.success(request, "Post updated successfully!")
            return redirect('dashboard')
    else:
        post_form = PostForm(instance=post)

    return render(request, 'update_post.html', {'post_form': post_form, 'post': post})

def update_comment(request, post_id, comment_id):
    if 'user_id' not in request.session:
        return redirect('login')

    user = get_object_or_404(User, id=request.session['user_id'])
    comment = get_object_or_404(Comment, id=comment_id, post_id=post_id)

    # Ensure the logged-in user is the owner of the comment
    if comment.user != user:
        return HttpResponseForbidden("You are not allowed to edit this comment.")

    if request.method == "POST":
        comment_form = CommentForm(request.POST, instance=comment)
        if comment_form.is_valid():
            comment_form.save()
            messages.success(request, "Comment updated successfully!")
            return redirect('dashboard')  # Redirect to the homepage or post detail page
    else:
        comment_form = CommentForm(instance=comment)

    return render(request, 'update_comment.html', {'comment_form': comment_form, 'comment': comment})


def delete_post(request, post_id):
    if 'user_id' not in request.session:
        return redirect('login')
    
    user = get_object_or_404(User, id=request.session['user_id'])
    post = get_object_or_404(Post, id=post_id)

    # Ensure the logged-in user is the owner of the post
    if post.user != user:
        return HttpResponseForbidden("You are not allowed to delete this post.")

    if request.method == "POST":
        post.delete()
        messages.success(request, "Post deleted successfully!")
        return redirect('dashboard')


def welcome_view(request):
    return render(request, 'welcomepage.html')

def signup_view(request):
    if request.method == "POST":
        form = UserForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')
    else:
        form = UserForm()
    return render(request, 'signup.html', {'form': form})


def login_view(request):
    if request.method == "POST":
        username = request.POST.get('username')
        password = request.POST.get('password')

        try:
            user = User.objects.get(username=username)
            if check_password(password, user.password):
                request.session['user_id'] = user.id
                return redirect('dashboard')
            else:
                messages.error(request, "Invalid password.")
        except User.DoesNotExist:
            messages.error(request, "User does not exist.")
    return render(request, 'login.html')


def logout_view(request):
    request.session.flush()
    return redirect('login')

def dashboard_view(request):
    if 'user_id' not in request.session:
        return redirect('login')
    user = get_object_or_404(User, id=request.session['user_id'])
    posts = Post.objects.all().order_by('-created_at')
    friend_requests = AddFriend.objects.filter(friend=user)
    conversations = Convsersation.objects.filter(sender=user)|Convsersation.objects.filter(recipient=user)
    followers = AddFriend.objects.filter(friend=user).count()

    post_form = PostForm()
    comment_form = CommentForm()

    post_comments = []
    for post in posts:
        comments = Comment.objects.filter(post=post)
        post_comments.append((post, comments))
    
    today = timezone.now().date()
    user_stats = {
        'posts_created_today': Post.objects.filter( created_at__date=today).count(),
        'users_online':User.objects.all().count(),
        'total_posts':Post.objects.filter(user=user).count(),
        'followers':followers
    }

    if request.method == "POST":
        if 'post' in request.POST:
            post_form = PostForm(request.POST, request.FILES)
            if post_form.is_valid():
                post = post_form.save(commit=False)
                post.user = user
                post.no_of_likes = 0  # Initialize no_of_likes field to 0
                post.save()
                for image in request.FILES.getlist('post_images'):
                    PostImage.objects.create(post=post, image=image)
                return redirect('dashboard')
        elif 'comment-form' in request.POST:
            comment_form = CommentForm(request.POST)
            if comment_form.is_valid():
                comment = comment_form.save(commit=False)
                comment.user = user
                comment.post = Post.objects.get(id=request.POST['post_id'])
                comment.save()
                Notifications.objects.create(user=comment.post.user, post = comment.post,content=f"{user.f_name} {user.l_name} commented on your post.")
                return redirect('dashboard')
        else:
            
            return render(request, 'homepage.html', {'post_comments': post_comments, 'user': user, 'post_form': post_form, 'comment_form': comment_form, 'friend_requests': friend_requests, 'conversations': conversations, 'followers': followers, 'user_stats': user_stats} )
    else:
        return render(request, 'homepage.html', {'post_comments': post_comments, 'user': user, 'post_form': post_form, 'comment_form': comment_form,   'friend_requests': friend_requests, 'conversations': conversations, 'followers': followers, 'user_stats': user_stats} )

def profile_view(request):
    if 'user_id' not in request.session:
        return redirect('login')
    user = get_object_or_404(User, id=request.session['user_id'])
    if Profile.objects.filter(user=user).exists():
        profile = Profile.objects.get(user=user)
        friend_requests = AddFriend.objects.filter(friend=user)
        posts = user.posts.all().order_by('-created_at')
        post_images = PostImage.objects.filter(post__in=posts)
        try:
            cover_photo = CoverPhoto.objects.filter(user=user).latest('id')
        except CoverPhoto.DoesNotExist:
            cover_photo = None
        return render(request, 'profile.html', {
            'user': user,
            'profile': profile,
            'posts': posts,
            'post_images': post_images,
            'friend_requests': friend_requests,
            'cover_photo': cover_photo
        })
    else:
        return redirect('create_profile')

def edit_profile(request):
    if 'user_id' not in request.session:
        return redirect('login')
    user = get_object_or_404(User, id=request.session['user_id'])
    if request.method == "POST":
        profile_form = ProfileForm(request.POST, instance=user.profile, files=request.FILES)
        user_form = EditUserForm(request.POST, instance=user)
        if profile_form.is_valid() and user_form.is_valid():
            profile_form.save()
            user_form.save()
            # Get the uploaded image
            image = request.FILES.get('profile_picture')
            if image:
                # Create a new post with the uploaded image
                post = Post.objects.create(user=user, content = f"{user.f_name} {user.l_name} has updated their profile picture.")
                post.post_image.set([PostImage.objects.create(post=post, image=image)])
                post.save()
            return redirect('Profile')
    else:
        profile_form = ProfileForm(instance=user.profile)
        user_form = EditUserForm(instance=user)
    return render(request, 'edit_profile.html', {'profile_form': profile_form, 'user_form': user_form, 'user': user})
def edit_cover_photo(request):
    if 'user_id' not in request.session:
        return redirect('login')
    user = get_object_or_404(User, id=request.session['user_id'])
    if request.method == "POST":
        form = CoverPhotoForm(request.POST, request.FILES)
        if form.is_valid():
            cover_photo = form.save(commit=False)
            cover_photo.user = user
            cover_photo.save()
            # Update the cover_photo variable
            user.coverphoto = cover_photo
            user.save()
            return redirect('Profile')
    else:
        form = CoverPhotoForm()
    return render(request, 'edit_cover.html', {'form': form, 'user': user})

def create_profile(request):
    if 'user_id' not in request.session:
        return redirect('login')
    user = get_object_or_404(User, id=request.session['user_id'])
    if request.method == "POST":
        form = ProfileForm(request.POST, request.FILES)
        if form.is_valid():
            profile = form.save(commit=False)
            profile.user = user
            profile.save()
            return redirect('Profile')
    else:
        form = ProfileForm()
    return render(request, 'create_profile.html', {'form': form, 'user': user})




def like_post(request, post_id):
    if 'user_id' not in request.session:
        return redirect('login')
    user = get_object_or_404(User, id=request.session['user_id'])
    post = get_object_or_404(Post, id=post_id)

    like_filter = LikePost.objects.filter(post=post, user=user).first()

    if like_filter is None:
        LikePost.objects.create(user=user, post=post)
        post.no_of_likes += 1
        post.save()
        messages.success(request, "Post liked successfully!")
        Notifications.objects.create(user=post.user,post = post, content=f"{user.f_name} {user.l_name} liked your post.")
    else:
        like_filter.delete()
        post.no_of_likes -= 1
        post.save()

    return JsonResponse({'no_of_likes': post.no_of_likes})

def view_profile(request, user_id):
    # Check if the user is logged in
    if 'user_id' not in request.session:
        return redirect('login')
    
    user = get_object_or_404(User, id=user_id)

    # If the logged-in user is viewing their own profile
    if request.session['user_id'] == user_id:
        if Profile.objects.filter(user=user).exists():
            profile = Profile.objects.get(user=user)
            posts = user.posts.all().order_by('-created_at')
            post_images = PostImage.objects.filter(post__in=posts)
            friend_requests = AddFriend.objects.filter(friend=user)
            try:
                cover_photo = CoverPhoto.objects.filter(user=user).latest('id')
            except CoverPhoto.DoesNotExist:
                cover_photo = None
            return render(request, 'profile.html', {'user': user, 'profile': profile, 'posts': posts, 'post_images': post_images, 'friend_requests': friend_requests, 'cover_photo': cover_photo})
        else:
            return render(request, 'blank_profile.html', {'user': user})
    else:
        # If another user is viewing the profile
        if Profile.objects.filter(user=user).exists():
            profile = Profile.objects.get(user=user)
            posts = user.posts.all().order_by('-created_at')
            post_images = PostImage.objects.filter(post__in=posts)
            friend_requests = AddFriend.objects.filter(friend=user)
            try:
                cover_photo = CoverPhoto.objects.filter(user=user).latest('id')
            except CoverPhoto.DoesNotExist:
                cover_photo = None

            return render(request, 'view_profile.html', {'user': user, 'profile': profile, 'posts': posts, 'post_images': post_images, 'friend_requests': friend_requests, 'cover_photo': cover_photo})
        else:
            return render(request, 'blank_profile.html', {'user': user})
        


def view_blank_profile(request, user_id):
    user = get_object_or_404(User, id=user_id)
    if not Profile.objects.filter(user=user).exists():
        return render(request, 'blank_profile.html')
    else:
        return redirect('view_profile', user_id=user_id)
    


def add_friend(request, user_id):
    if 'user_id' not in request.session:
        return redirect('login')
    user = get_object_or_404(User, id=request.session['user_id'])
    friend = get_object_or_404(User, id=user_id)
    if user.id == friend.id:
        messages.info(request, "You cannot add yourself as a friend!")
        return redirect('dashboard')
    if AddFriend.objects.filter(user=user, friend=friend).exists():
        messages.info(request, "Friend is already added!")
        return redirect('view_profile', user_id=user_id)
    else:
        AddFriend.objects.create(user=user, friend=friend)
       
    return redirect('Profile')

def delete_message(request, message_id):
    if 'user_id' not in request.session:
        return redirect('login')

    user = get_object_or_404(User, id=request.session['user_id'])
    message = get_object_or_404(Message, id=message_id)

    # Ensure the logged-in user is the owner of the message
    if message.user != user:
        return HttpResponseForbidden("You are not allowed to delete this message.")

    if request.method == "POST":
        conversation_id = message.conversation.id
        message.delete()
        messages.success(request, "Message deleted successfully!")
        return redirect('conversation_detail', conversation_id=conversation_id)

def update_message(request, message_id):
    if 'user_id' not in request.session:
        return redirect('login')

    user = get_object_or_404(User, id=request.session['user_id'])
    message = get_object_or_404(Message, id=message_id)

    # Ensure the logged-in user is the owner of the message
    if message.user != user:
        return HttpResponseForbidden("You are not allowed to edit this message.")

    if request.method == "POST":
        message_form = MessageForm(request.POST, instance=message)
        if message_form.is_valid():
            message_form.save()
            messages.success(request, "Message updated successfully!")
            return redirect('conversation_detail', conversation_id=message.conversation.id)
    else:
        message_form = MessageForm(instance=message)

    return render(request, 'update_message.html', {'message_form': message_form, 'message': message})



def friend_request_list(request):
    if 'user_id' not in request.session:
        return redirect('login')
    user = get_object_or_404(User, id=request.session['user_id'])
    friend_requests = AddFriend.objects.filter(friend=user)
    return render(request, 'friend_request_list.html', {'friend_requests': friend_requests})

def friend_request(request, user_id):
    if 'user_id' not in request.session:
        return redirect('login')
    user = get_object_or_404(User, id=request.session['user_id'])
    friend = get_object_or_404(User, id=user_id)
    if AddFriend.objects.filter(user=friend, friend=user).exists():
        AddFriend.objects.create(user=user, friend=friend)
        AddFriend.objects.filter(user=friend, friend=user).delete()
        
    else:
        messages.info(request, "Friend request not found!")
    return redirect('Profile')


def conversation_detail(request, conversation_id):
    if 'user_id' not in request.session:
        return redirect('login')
    user = get_object_or_404(User, id=request.session['user_id'])
    conversation = get_object_or_404(Convsersation, id=conversation_id)
    messages = conversation.messages.all()  # corrected to get messages related to the conversation
    if request.method == 'POST':
        form = MessageForm(request.POST)  # corrected to use MessageForm
        if form.is_valid():
            message = form.save(commit=False)
            message.user = user
            message.conversation = conversation
            message.save()
            return redirect('conversation_detail', conversation_id=conversation_id)
    else:
        form = MessageForm()
    return render(request, 'conversation_detail.html', {'conversation': conversation, 'messages': messages, 'form': form,})

def create_conversation(request, recipient_id):
    if 'user_id' not in request.session:
        return redirect('login')
    user = get_object_or_404(User, id=request.session['user_id'])
    recipient = get_object_or_404(User, id=recipient_id)
    conversation = Convsersation.objects.filter(
        Q(sender=user, recipient=recipient) | Q(sender=recipient, recipient=user)
    ).first()
    if conversation:
        return redirect('conversation_detail', conversation_id=conversation.id)
    else:
        conversation = Convsersation.objects.create(sender=user, recipient=recipient)
        return redirect('conversation_detail', conversation_id=conversation.id)
    
def send_message(request, recipient_id):
    if 'user_id' not in request.session:
        return redirect('login')
    user = get_object_or_404(User, id=request.session['user_id'])
    recipient = get_object_or_404(User, id=recipient_id)
    conversation = Convsersation.objects.filter(
        Q(sender=user, recipient=recipient) | Q(sender=recipient, recipient=user)
    ).first()
    if conversation:
        if request.method == 'POST':
            form = MessageForm(request.POST)
            if form.is_valid():
                message = form.save(commit=False)
                message.user = user
                message.conversation = conversation
                message.save()
                return redirect('conversation_detail', conversation_id=conversation.id)
        else:
            form = MessageForm()
        return render(request, 'send_message.html', {'recipient': recipient, 'form': form})
    else:
        return redirect('create_conversation', recipient_id=recipient_id)


def check_like(request, post_id):
    post = Post.objects.get(id=post_id)
    user = request.user
    like = LikePost.objects.filter(post=post, user=user).exists()
    return JsonResponse({'liked': like})



def delete_comment(request, post_id, comment_id):
    if 'user_id' not in request.session:
        return redirect('login')
    user = get_object_or_404(User, id=request.session['user_id'])
    post = get_object_or_404(Post, id=post_id)
    comment = get_object_or_404(Comment, id=comment_id)

    if comment.user == user:
        comment.delete()
        messages.success(request, "Comment deleted successfully!")
    else:
        messages.error(request, "You don't have permission to delete this comment!")

    return redirect('dashboard')