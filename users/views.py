"""users views module."""

from django.contrib.auth import logout
from rest_framework.response import Response
from rest_framework import permissions, status
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from dj_rest_auth.views import LoginView
from drf_spectacular.utils import extend_schema
from abc import ABC, abstractmethod

from users.models import OTP, User
from .utils import activate_user_account, generate_otp
from users.serializers import (
    RequestOTPSerializer,
    UserSerializer,
    LogoutSerializer,
    UserAuthSerializer,
    UserLoginSerializer,
    VerifyOTPSerializer,
)


class RegisterView(APIView):
    """User registration view."""

    permission_classes = [permissions.AllowAny]

    @extend_schema(request=UserSerializer, responses={201: UserSerializer})
    def post(self, request):
        """Post request for user registration."""
        serializer = UserSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        generate_otp(serializer.instance)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class VerifyOTPView(APIView):
    """User OTP verification view."""

    permission_classes = [permissions.AllowAny]

    @extend_schema(request=VerifyOTPSerializer)
    def post(self, request):
        """Post request for OTP verification."""
        email = request.data.get("email") or request.query_params.get("email")
        otp = request.data.get("otp")

        if not email or not otp:
            return Response(
                {"detail": "Email and OTP are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        otp_in_db = OTP.objects.filter(user__email=email).last()
        if not otp_in_db:
            return Response(
                {"detail": "OTP does not exist!"}, status=status.HTTP_404_NOT_FOUND
            )

        if str(otp) == str(otp_in_db.code):
            if otp_in_db.is_used:
                return Response(
                    {"detail": "OTP is already used!"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            otp_in_db.is_used = True
            otp_in_db.save()
            activate_user_account.enqueue(otp_in_db.pk)
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


@extend_schema(request=UserLoginSerializer, responses={200: UserAuthSerializer})
class LoginView(LoginBaseView):
    """User login view."""

    def login(self):
        """Login use."""
        self.user = self.serializer.validated_data["user"]
        return self.user

    def get_extra_payload(self):
        """Get extra payload for login view."""
        return {"user": UserSerializer(self.user).data}


class LogoutView(APIView):
    """User logout view."""

    permission_classes = [permissions.AllowAny]
    serializer_class = LogoutSerializer

    @extend_schema(request=LogoutSerializer, responses={204: None})
    def post(self, request):
        """Post request for user logout."""
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        refresh = serializer.validated_data.pop("refresh")

        try:
            token = RefreshToken(refresh)
            token.blacklist()
            logout(request)
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class RequestOTPView(APIView):
    """
    Request user OTP view.

    Allow users to request an OTP in an instance where OTP verification
    failed during registration process.
    """

    permission_classes = [permissions.AllowAny]

    @extend_schema(request=RequestOTPSerializer)
    def post(self, request) -> Response:
        """Post request for user OTP verification."""
        email = request.data.get("email")

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response(
                {"detail": "User does not exist!"}, status=status.HTTP_404_NOT_FOUND
            )

        if user and not user.is_active:
            generate_otp(user)

        return Response(
            {"detail": "OTP sent to your email."}, status=status.HTTP_200_OK
        )
