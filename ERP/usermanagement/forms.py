# usermanagement/forms.py
from django import forms
from .models import CustomUser, Module, Entity
from django.contrib.auth.forms import UserCreationForm

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
