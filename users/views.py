"""users views module."""

from django.http import Http404
from rest_framework.response import Response
from rest_framework import permissions
from rest_framework.views import APIView
from rest_framework import status
from django.contrib.auth import logout
from rest_framework_simplejwt.tokens import RefreshToken
from dj_rest_auth.views import LoginView

from users.models import OTP
from .utils import generate_otp

from users.serializers import (
    UserSerializer,
    LogoutSerializer,
    UserOurSerializer,
    UserLoginSerializer,
)
from drf_spectacular.utils import extend_schema
from abc import ABC, abstractmethod


class RegisterView(APIView):
    """user registration view."""

    permission_classes = [permissions.AllowAny]

    @extend_schema(request=UserSerializer, responses={201: UserSerializer})
    def post(self, request):
        """post request for user login."""
        serializer = UserSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        generate_otp(serializer.instance)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


# @method_decorator(csrf_exempt, name='dispatch')
class VerifyOTPView(APIView):
    """user OTP verification view."""

    permission_classes = [permissions.AllowAny]

    @extend_schema(request=None, responses={200: None})
    def post(self, request):
        """post request for OTP verification."""
        email = request.query_params.get("email")
        otp = request.data.get("otp")

        try:
            otp_in_db = OTP.objects.filter(user__email=email).last()
        except OTP.DoesNotExist:
            raise Http404("OTP does not exist!")

        if str(otp) == str(otp_in_db.code):
            if otp_in_db.is_used:
                raise Http404("OTP is already used!")
            otp_in_db.is_used = True
            otp_in_db.save()
            return Response(
                {"detail": "OTP verified successfully."}, status=status.HTTP_200_OK
            )
        else:
            return Response(
                {"detail": "Invalid OTP."}, status=status.HTTP_400_BAD_REQUEST
            )


class LoginBaseView(ABC, LoginView):
    """Login base view."""

    def get_extra_payload(self):
        """return extra payload for login view."""
        return {}

    def get_token(self, user):
        """return refresh token for user."""
        refresh_token = RefreshToken.for_user(user)
        for key, value in self.get_extra_payload().items():
            refresh_token[key] = value
        return refresh_token

    @abstractmethod
    def login(self):
        """login use."""

    def get_response(self):
        data = {}

        refresh = self.get_token(self.user)

        data["refresh"] = str(refresh)
        data["access"] = str(refresh.access_token)
        data.update(self.get_extra_payload())

        return Response(data)


@extend_schema(request={200: UserLoginSerializer}, responses={204: UserOurSerializer})
class LoginView(LoginBaseView):
    """user login view."""

    def login(self):
        """login use."""
        self.user = self.serializer.validated_data["user"]
        return self.user

    def get_extra_payload(self):
        """get extra payload for login view."""
        return UserSerializer(self.user).data


class LogoutView(APIView):
    """user logout view."""

    permission_classes = [permissions.AllowAny]
    serializer_class = LogoutSerializer

    @extend_schema(request=LogoutSerializer, responses={204: None})
    def post(self, request):
        """post request for user logout."""
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        refresh = serializer.validated_data.pop("refresh")

        try:
            token = RefreshToken(refresh)
            token.blacklist()
            logout(request)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
