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
from .utils import activate_user_account, generate_otp

from users.serializers import (
    RequestOTPSerializer,
    UserSerializer,
    LogoutSerializer,
    UserOurSerializer,
    UserLoginSerializer,
    VerifyOTPSerializer,
    UserKYCSerializer,
)
from drf_spectacular.utils import extend_schema
from abc import ABC, abstractmethod


class RegisterView(APIView):
    """user registration view."""

    permission_classes = [permissions.AllowAny]

    @extend_schema(request=UserSerializer, responses={201: UserSerializer})
    def post(self, request):
        """
        Register a new user account.

        How it works:
        1. Validates the incoming registration data (email, password, name, etc.)
        2. Creates a new user account in the database
        3. Automatically generates and sends an OTP to the user's email
        4. Returns the created user details with a 201 Created status

        Background tasks:
        - Generates an OTP and sends it to the user's email for verification

        Errors:
        - 400 Bad Request: If email already exists or validation fails
        - 400 Bad Request: If password doesn't meet requirements

        Next steps:
        - User should call the VerifyOTP endpoint with the OTP received in their email
        """
        serializer = UserSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        generate_otp(serializer.instance)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


# @method_decorator(csrf_exempt, name='dispatch')
class VerifyOTPView(APIView):
    """user OTP verification view."""

    permission_classes = [permissions.AllowAny]

    @extend_schema(request=VerifyOTPSerializer)
    def post(self, request):
        """
        Verify user's OTP and activate their account.

        How it works:
        1. Retrieves the email and OTP from the request
        2. Finds the most recent OTP record for that email in the database
        3. Validates that the provided OTP matches the stored OTP
        4. Checks that the OTP hasn't already been used
        5. Marks the OTP as used
        6. Enqueues a background task to activate the user's account
        7. Returns a success message with 200 OK status

        Background tasks:
        - Activates the user account asynchronously (marks is_active=True)

        Errors:
        - 404 Not Found: If no OTP exists for the email
        - 400 Bad Request: If OTP is invalid or incorrect
        - 404 Not Found: If OTP has already been used

        Next steps:
        - After successful verification, user can login using the LoginView endpoint
        """
        email = request.data.get("email")
        otp = request.data.get("otp")

        otp_in_db = OTP.objects.filter(user__email=email).last()
        if not otp_in_db:
            return Response("OTP does not exist!", status=status.HTTP_404_NOT_FOUND)

        if str(otp) == str(otp_in_db.code):
            if otp_in_db.is_used:
                raise Http404("OTP is already used!")
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


@extend_schema(request={200: UserLoginSerializer}, responses={204: UserOurSerializer})
class LoginView(LoginBaseView):
    """
    User login endpoint.

    How it works:
    1. Validates user credentials (email and password)
    2. Authenticates the user against the database
    3. Generates JWT tokens (access and refresh) for the authenticated user
    4. Includes user details in the response
    5. Returns tokens and user information with 200 OK status

    These JWT tokens are used for subsequent authenticated API requests.
    """

    def login(self):
        """Authenticate user and return user object for token generation."""
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
        """
        Logout user by blacklisting their refresh token.

        How it works:
        1. Receives the user's refresh token in the request
        2. Validates the refresh token
        3. Blacklists the token (adds it to a blocked list) to prevent reuse
        4. Clears the user's session
        5. Returns a 204 No Content response indicating successful logout

        What happens:
        - The refresh token becomes invalid and cannot be used to get new access tokens
        - The user's session is cleared on the server
        - User is logged out across all devices if tokens were shared

        Errors:
        - 400 Bad Request: If refresh token is invalid or malformed
        - 400 Bad Request: If token has already been blacklisted

        Security:
        - Frontend should delete stored tokens after logout
        - Subsequent API requests without valid access token will be rejected
        """
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        refresh = serializer.validated_data.pop("refresh")

        try:
            token = RefreshToken(refresh)
            token.blacklist()
            logout(request)
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class RequestOTPView(APIView):
    """Request OTP for user verification or re-verification.

    Allows users to request a new OTP in scenarios such as:
    - OTP verification failed during initial registration
    - OTP code has expired
    - User lost their OTP code
    """

    permission_classes = [permissions.AllowAny]

    @extend_schema(request=RequestOTPSerializer)
    def post(self, request) -> Response:
        """
        Generate and send a new OTP to the user's email.

        How it works:
        1. Retrieves the email address from the request
        2. Looks up the user by email in the database
        3. Checks if the user account exists and is inactive (not verified)
        4. Generates a new OTP code and saves it to the database
        5. Sends the OTP via email to the user
        6. Returns a success message with 200 OK status

        When OTP is sent:
        - Only sent if user is not already active (not verified yet)
        - New OTP overwrites the previous OTP
        - User should receive it in their inbox or spam folder

        Errors:
        - 404 Not Found: If user with the email doesn't exist
        - 200 OK: Even if user is already active (for security, doesn't reveal account status)

        Next steps:
        - User receives OTP in email
        - User calls VerifyOTPView with the OTP code
        """

        email = request.data.get("email")

        try:
            from users.models import User

            user = User.objects.get(email=email)
            print(user.is_active)
        except User.DoesNotExist:
            return Response("User does not exist!", status=status.HTTP_404_NOT_FOUND)

        if user and not user.is_active:
            generate_otp(user)

        return Response("OTP sent to your email.", status=status.HTTP_200_OK)


class UserKYCView(APIView):
    """User KYC submission view."""

    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(request=UserKYCSerializer, responses={201: UserKYCSerializer})
    def post(self, request):
        """
        Submit Know-Your-Customer (KYC) information.

        How it works:
        1. Checks if the user has already submitted KYC information
        2. Validates the KYC data (identification, address, business info, etc.)
        3. Saves the KYC information to the database linked to the authenticated user
        4. Returns the saved KYC details with a 201 Created status

        Errors:
        - 400 Bad Request: If KYC has already been submitted
        - 400 Bad Request: If any required field is missing or invalid
        - 401 Unauthorized: If user is not authenticated

        Important:
        - User must be logged in (authenticated) to submit KYC
        - Only one KYC submission is allowed per user
        - KYC information typically undergoes manual or automated verification
        - Status changes from "pending" to "verified" after admin review
        """
        from users.models import UserKYC

        # Check if KYC already exists
        if UserKYC.objects.filter(user=request.user).exists():
            return Response(
                {"detail": "KYC information already submitted."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = UserKYCSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(user=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
