# usermanagement/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('users/', views.user_list, name='user_list'),
    path('users/create/', views.create_user, name='user_create'),
    path('users/delete/<int:pk>/', views.delete_user, name='user_delete'),
# usermanagement/urls.py
    path('login/', views.custom_login, name='login'),
    # path('login/', views.login_view, name='login'),

    path("logout/", views.logout_view, name="logout"),
    # path('companies/', views.company_list, name='company_list'),
    # path('companies/create/', views.company_create, name='company_create'),
    # path('companies/edit/<int:pk>/', views.company_edit, name='company_edit'),
    # path('companies/delete/<int:pk>/', views.company_delete, name='company_delete'),
]
