from django import forms
from .models import Post, Profile, User, Comment, AddFriend, LikePost,Convsersation,Message, CoverPhoto
from django.core.exceptions import ValidationError
from django.contrib.auth.hashers import make_password, check_password


class UserForm(forms.ModelForm):
    comfirm_password = forms.CharField(widget=forms.PasswordInput(attrs={'placeholder': 'Confirm your password'}))

    class Meta:
        model = User
        fields = ('username', 'email', 'password', 'f_name', 'l_name', 'm_name')
        widgets = {
            'username': forms.TextInput(attrs={'placeholder': 'Enter your username'}),
            'email': forms.EmailInput(attrs={'placeholder': 'Enter your email'}),
            'password': forms.PasswordInput(attrs={'placeholder': 'Enter your password'}),
            'f_name': forms.TextInput(attrs={'placeholder': 'First name'}),
            'l_name': forms.TextInput(attrs={'placeholder': 'Last name'}),
            'm_name': forms.TextInput(attrs={'placeholder': 'Middle name'}),
        }
        def clean(self):
            cleaned_data = super().clean()
            password = cleaned_data.get('password')
            comfirm_password = cleaned_data.get('comfirm_password')
            if password != comfirm_password:
                raise forms.ValidationError('Passwords do not match')
            return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.password = make_password(self.cleaned_data['password']) 
        if commit:
            user.save()
        return user


class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['profile_picture', 'bio', 'b_day', 'phone_number', 'address', 'gender']

class CoverPhotoForm(forms.ModelForm):
    class Meta:
        model = CoverPhoto
        fields = ['coverphoto']

class CoverForm(forms.ModelForm):
    class Meta:
        model = CoverPhoto
        fields = ['coverphoto']


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ['title', 'content']



class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['content']


class EditUserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('f_name', 'l_name')

class ConvsersationForm(forms.ModelForm):
    class Meta:
        model = Convsersation
        fields = ['message']


class MessageForm(forms.ModelForm):
    class Meta:
        model = Message
        fields = ['message']
        