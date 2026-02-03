"""user serializers."""

from rest_framework import serializers
from users.models import User


class UserSerializer(serializers.ModelSerializer):
    """User serializer class."""

    class Meta:
        """Meta class."""

        model = User
        fields = ["id", "username", "email", "password"]
        extra_kwargs = {"password": {"write_only": True}}
        read_only_fields = ["id"]


class LogoutSerializer(serializers.Serializer):
    """Logout serializer class."""

    refresh = serializers.CharField(write_only=True)


class UserOurSerializer(serializers.Serializer):
    """User serializer class."""

    refresh = serializers.CharField(read_only=True)
    access = serializers.CharField(read_only=True)
    User = UserSerializer(read_only=True)


class UserLoginSerializer(serializers.Serializer):
    """User login serializer class."""

    email = serializers.EmailField(required=True)
    password = serializers.CharField(write_only=True, required=True)


class VerifyOTPSerializer(serializers.Serializer):
    """verify otp serializer."""

    email = serializers.EmailField(required=True)
    otp = serializers.CharField(required=True)


class RequestOTPSerializer(serializers.Serializer):
    """request otp serializer."""

    email = serializers.EmailField(required=True)
