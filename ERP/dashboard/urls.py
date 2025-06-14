"""dason URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include, re_path
from dashboard import views
from django.contrib.auth.decorators import login_required
from usermanagement.views import CustomLoginView

urlpatterns = [
    path("admin/", admin.site.urls),
    # Dashboard
    path('manage/', include('usermanagement.urls')),
    
    path('accounting/', include('accounting.urls')),
    # path('admin/', admin.site.urls),
    path('accounts/', include('allauth.urls')),  # Important!
    path("accounts/login/", CustomLoginView.as_view(), name="account_login"),
    
    path("", views.DashboardView.as_view(), name="dashboard"),
    path("settings", views.Settings.as_view(), name="settings"),
    # # Custum change password done page redirect
    # path(
    #     "account/password/change/",
    #     login_required(views.MyPasswordChangeView.as_view()),
    #     name="account_change_password",
    # ),
    # # Custum set password done page redirect
    # path(
    #     "account/password/set/",
    #     login_required(views.MyPasswordSetView.as_view()),
    #     name="account_set_password",
    # ),
    # Apps
    path("apps/", include("apps.urls")),
    # Components
    path("components/", include("components.urls")),
    # Pages
    path("pages/", include("pages.urls")),
    # # Include the allauth and 2FA urls from their respective packages.
    # path("/", include("allauth_2fa.urls")),
    # path("account/", include("allauth.urls")),
    path("api/v1/", include("api.urls")),
]
