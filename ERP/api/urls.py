# from rest_framework.routers import DefaultRouter
# from django.urls import path, include
# import rest_framework
# from rest_framework_simplejwt.views import (
#     TokenObtainPairView,
#     TokenRefreshView,
# )
# from .views import FiscalYearViewSet

# router = DefaultRouter()
# router.register(r'fiscalyears', FiscalYearViewSet, basename='fiscalyear')

# urlpatterns = [
#     path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
#     path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
#     path('', include(router.urls)),
# ]