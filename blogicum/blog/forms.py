from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserChangeForm
from django.utils.timezone import localtime

from .models import Post, Comments


User = get_user_model()


class MyUserChangeForm(UserChangeForm):
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'username', 'email',)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'password' in self.fields:
            del self.fields['password']


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = (
            'title',
            'text',
            'image',
            'pub_date',
            'location',
            'category',
        )
        widgets = {
            'pub_date': forms.DateTimeInput(
                attrs={'type': 'datetime-local'},
                format='%m/%d/%Y %H:%M'
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pub_date:
            self.fields['pub_date'].initial = localtime(self.instance.pub_date).strftime('%m/%d/%Y %H:%M')


class CommentForm(forms.ModelForm):

    class Meta:
        model = Comments
        fields = ('text',)
