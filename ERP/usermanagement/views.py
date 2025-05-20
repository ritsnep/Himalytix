# usermanagement/views.py
from uuid import UUID
from django.utils import timezone
from django.http import HttpResponseForbidden
from django.shortcuts import render, redirect, get_object_or_404
from .models import  Module, Entity, CustomUser
from .forms import  ModuleForm, EntityForm, CustomUserCreationForm
from django.contrib.auth.decorators import login_required
# accounts/views.py or usermanagement/views.py
from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render, redirect
from django.contrib import messages
from .models import LoginLog
def custom_login(request):
    if request.method == "POST":
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user,)
            # return redirect('dashboard')  # Or whatever landing page
            return render(request, 'dashboard.html')  # Redirect to the dashboard
        else:
            messages.error(request, 'Invalid username or password.')
    # return render(request, 'usermanagement/login.html')
    return render(request, 'account/login.html')
@login_required

def logout_view(request):
    """
    Logs out the current user and updates their LoginLog entry.
    """
    custom_session_id = request.session.get('custom_session_id')

    # Try converting to UUID safely
    try:
        session_uuid = UUID(custom_session_id) if custom_session_id else None
    except ValueError:
        session_uuid = None

    if session_uuid:
        login_log = LoginLog.objects.filter(session_id=session_uuid).order_by('-login_datetime').first()

        if login_log:
            logout_time = timezone.now()
            login_log.logout_time = logout_time
            login_log.session_time = logout_time - login_log.login_datetime
            login_log.save(update_fields=["logout_time", "session_time"])

    logout(request)
    return redirect('login')
# def logout_view(request):
#     currentsession = request.session.get('session_id')

#     login_log = LoginLog.objects.filter(session_id=currentsession).order_by('-login_datetime').first()
#     login_datetime = login_log.login_datetime
#     logout_time = timezone.now()
#     login_log.logout_time = logout_time
#     # Calculate session time
#     login_log.session_time = login_log.logout_time - login_datetime
#     login_log.save()
#     logout(request)
#     return redirect('login')  # Redirect to the login page after logout
# --- User CRUD ---
@login_required
def create_user(request):
    form = CustomUserCreationForm(request.POST or None)
    if form.is_valid():
        form.save()
        return redirect('user_list')
    return render(request, 'usermanagement/user_form.html', {'form': form})

@login_required
def user_list(request):
    users = CustomUser.objects.all()
    return render(request, 'usermanagement/user_list.html', {'users': users})

@login_required
def delete_user(request, pk):
    user = get_object_or_404(CustomUser, pk=pk)
    user.delete()
    return redirect('user_list')
