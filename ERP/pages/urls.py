from django.urls import path

from .views import (
    pages_authentication_login_view,
    pages_authentication_register_view,
    pages_authentication_recoverpw_view,
    pages_authentication_lockscreen_view,
    pages_authentication_logout_view,
    pages_authentication_confirm_mail_view,
    pages_authentication_email_verification_view,
    pages_authentication_two_step_verification_view,
    pages_starter_page_view,
    pages_maintenance_view,
    pages_comingsoon_view,
    pages_timeline_view,
    pages_faqs_view,
    pages_pricing_view,
    pages_error_404_view,
    pages_error_500_view,
    pages_horizontal_layout_view,
)
from .import views

app_name = "pages"

urlpatterns = [
    # Authentication
    path(
        "authentication/login",
        view=pages_authentication_login_view,
        name="pages.authentication.login",
    ),
    
    # login url
    path('accounts/login/', views.LoginView, name="acc_login"),
    path(
        "authentication/register/",
        view=pages_authentication_register_view,
        name="pages.authentication.register",
    ),
    path(
        "authentication/recoverpw/",
        view=pages_authentication_recoverpw_view,
        name="pages.authentication.recoverpw",
    ),
    path(
        "authentication/lock-screen/",
        view=pages_authentication_lockscreen_view,
        name="pages.authentication.lockscreen",
    ),
    path(
        "authentication/logout/",
        view=pages_authentication_logout_view,
        name="pages.authentication.logout",
    ),
    path(
        "authentication/confirm_mail/",
        view=pages_authentication_confirm_mail_view,
        name="pages.authentication.confirm_mail",
    ),
    path(
        "forms/email_verification/",
        view=pages_authentication_email_verification_view,
        name="pages.authentication.email_verification",
    ),
    path(
        "forms/two_step_verification/",
        view=pages_authentication_two_step_verification_view,
        name="pages.authentication.two_step_verification",
    ),
    # pages
    path(
        "starter-page/",
        view=pages_starter_page_view,
        name="pages.starter_page",
    ),
    path(
        "maintenance/",
        view=pages_maintenance_view,
        name="pages.maintenance",
    ),
    path(
        "comingsoon/",
        view=pages_comingsoon_view,
        name="pages.comingsoon",
    ),
    path(
        "timeline/",
        view=pages_timeline_view,
        name="pages.timeline",
    ),
    path(
        "faqs/",
        view=pages_faqs_view,
        name="pages.faqs",
    ),
    path(
        "pricing/",
        view=pages_pricing_view,
        name="pages.pricing",
    ),
    path(
        "error-404/",
        view=pages_error_404_view,
        name="pages.error_404",
    ),
    path(
        "error-500/",
        view=pages_error_500_view,
        name="pages.error_500",
    ),
    #  Layout
    path(
        "layout/horizontal/",
        view=pages_horizontal_layout_view,
        name="pages.layout.horizontal",
    ),
]
