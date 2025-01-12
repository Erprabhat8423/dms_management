# users/urls.py

from django.urls import path
from .views import (
    RegisterView,
    RegisterVerifyView,
    SendOTPView,
    LoginView
)

urlpatterns = [
    path('register', RegisterView.as_view(), name='register'),
    path('verify-otp', RegisterVerifyView.as_view(), name='verify-otp'),
    path('send-otp', SendOTPView.as_view(), name='send-otp'),
    path('login', LoginView.as_view(), name='login'),
]
