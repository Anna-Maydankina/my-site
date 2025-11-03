from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser

class RegistrationForm(UserCreationForm):
    nickname = forms.CharField(max_length=50, required=True)
    
    class Meta:
        model = CustomUser
        fields = ['username', 'nickname', 'password1', 'password2']

class LoginForm(forms.Form):
    username = forms.CharField()
    password = forms.CharField(widget=forms.PasswordInput)