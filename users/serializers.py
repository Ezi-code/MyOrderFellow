"""user serializers."""

from rest_framework import serializers
from users.models import User, UserKYC


class UserSerializer(serializers.ModelSerializer):
    """User serializer class."""

    company_name = serializers.CharField(source="username")

    class Meta:
        """Meta class."""

        model = User
        fields = ["id", "company_name", "email", "password"]
        extra_kwargs = {"password": {"write_only": True}}
        read_only_fields = ["id"]


class UserKYCSerializer(serializers.ModelSerializer):
    """User KYC serializer."""

    class Meta:
        """Meta class."""

        model = UserKYC
        fields = [
            "id",
            "business_registration_number",
            "business_address",
            "contact_person_details",
            "approved",
        ]
        read_only_fields = ["id", "approved"]


class LogoutSerializer(serializers.Serializer):
    """Logout serializer class."""

    refresh = serializers.CharField(write_only=True)


class UserOutSerializer(serializers.Serializer):
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
