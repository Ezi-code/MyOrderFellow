"""users urls file."""

from django.urls import path
from . import views

app_name = "users"

urlpatterns = [
    path("users/auth/login/", views.LoginView.as_view(), name="login"),
    path("users/auth/logout/", views.LogoutView.as_view(), name="logout"),
    path("users/auth/register/", views.RegisterView.as_view(), name="register"),
    path("users/verify-otp/", views.VerifyOTPView.as_view(), name="verify-otp"),
    path("users/request-otp/", views.RequestOTPView.as_view(), name="request-otp"),
]
