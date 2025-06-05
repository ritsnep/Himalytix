# usermanagement/forms.py
from django import forms
from .models import CustomUser, Module, Entity
from django.contrib.auth.forms import UserCreationForm

from django import forms
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
# usermanagement/forms.py
from allauth.account.forms import LoginForm
from django import forms

class DasonLoginForm(LoginForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['login'].widget = forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your username',
            'id': 'input-username'
        })
        self.fields['password'].widget = forms.PasswordInput(attrs={
            'class': 'form-control pe-5',
            'placeholder': 'Enter your password',
            'id': 'password-input'
        })
        self.fields['remember'].widget.attrs.update({
            'class': 'form-check-input',
            'id': 'remember-check'
        })


class LoginForm(forms.Form):
    username = forms.CharField(max_length=255)
    password = forms.CharField(max_length=255, widget=forms.PasswordInput)

    def clean(self):
        username = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')
        user = authenticate(username=username, password=password)
        if not user:
            raise forms.ValidationError('Invalid username or password')
        return self.cleaned_data
class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = CustomUser
        fields = ('username', 'email', 'full_name', 'role', 'organization')

class ModuleForm(forms.ModelForm):
    class Meta:
        model = Module
        fields = '__all__'

class EntityForm(forms.ModelForm):
    class Meta:
        model = Entity
        fields = '__all__'
