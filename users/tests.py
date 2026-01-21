"""Tests for the users app."""

from django.test import TestCase

from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core import mail
from rest_framework import status
from rest_framework.test import APITestCase
from users.models import OTP, UserKYC

User = get_user_model()


class AuthenticationTests(APITestCase):
    """Test suite for user authentication flow."""

    def setUp(self):
        """Set up test data."""
        self.register_url = reverse("users:register")
        self.login_url = reverse("users:login")
        self.verify_otp_url = reverse("users:verify-otp")
        self.logout_url = reverse("users:logout")

        self.user_data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "testpassword123",
        }

    def test_registration_success(self):
        """Test successful user registration."""
        response = self.client.post(self.register_url, self.user_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Check user creation
        self.assertEqual(User.objects.count(), 1)
        user = User.objects.get(email=self.user_data["email"])
        self.assertFalse(user.is_active)  # Should be inactive until OTP verified

        # Check OTP creation
        self.assertEqual(OTP.objects.count(), 1)

        # Check email sent (Task runs immediately in tests via ImmediateBackend)
        self.assertEqual(len(mail.outbox), 1)
        assert "Your OTP is" in mail.outbox[0].body
        assert self.user_data["email"] in mail.outbox[0].to

    def test_registration_duplicate_email(self):
        """Test registration with existing email."""
        User.objects.create_user(**self.user_data)
        response = self.client.post(self.register_url, self.user_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_verify_otp_success(self):
        """Test successful OTP verification."""
        # Register first
        self.client.post(self.register_url, self.user_data)
        user = User.objects.get(email=self.user_data["email"])
        otp = OTP.objects.get(user=user)

        # Verify OTP
        url = f"{self.verify_otp_url}?email={user.email}"
        data = {"otp": otp.code}
        response = self.client.post(url, data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        user.refresh_from_db()
        otp.refresh_from_db()
        self.assertTrue(user.is_active)
        self.assertTrue(otp.is_used)

    def test_verify_otp_invalid_code(self):
        """Test OTP verification with wrong code."""
        self.client.post(self.register_url, self.user_data)
        user = User.objects.get(email=self.user_data["email"])

        url = f"{self.verify_otp_url}?email={user.email}"
        data = {"otp": "000000"}  # Wrong OTP
        response = self.client.post(url, data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["detail"], "Invalid OTP.")

    def test_verify_otp_already_used(self):
        """Test verifying an already used OTP."""
        self.client.post(self.register_url, self.user_data)
        user = User.objects.get(email=self.user_data["email"])
        otp = OTP.objects.get(user=user)
        otp.is_used = True
        otp.save()

        url = f"{self.verify_otp_url}?email={user.email}"
        data = {"otp": otp.code}
        response = self.client.post(url, data)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_verify_otp_missing_email(self):
        """Test verification without email query param."""
        url = self.verify_otp_url
        data = {"otp": "123456"}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_login_success(self):
        """Test successful login."""
        user = User.objects.create_user(**self.user_data)
        user.is_active = True
        user.save()

        response = self.client.post(
            self.login_url,
            {"email": self.user_data["email"], "password": self.user_data["password"]},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        assert "access" in response.data
        assert "refresh" in response.data

    def test_login_invalid_credentials(self):
        """Test login with wrong password."""
        User.objects.create_user(**self.user_data)
        response = self.client.post(
            self.login_url,
            {"email": self.user_data["email"], "password": "wrongpassword"},
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_logout_success(self):
        """Test successful logout."""
        user = User.objects.create_user(**self.user_data)
        user.is_active = True
        user.save()

        # Login to get refresh token
        login_resp = self.client.post(
            self.login_url,
            {"email": self.user_data["email"], "password": self.user_data["password"]},
        )
        refresh_token = login_resp.data["refresh"]

        # Logout
        response = self.client.post(self.logout_url, {"refresh": refresh_token})
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)


class TestUserKYC(TestCase):
    """test user kyc model."""

    def setUp(self):
        """setup test user."""
        self.user_data = {
            "email": "testuser@mail.com",
            "password": "password",
            "username": "testuser",
        }
        self.user = User.objects.create_user(**self.user_data)

    def test_user_kyc_creation(self):
        """test user kyc creation."""
        kyc = UserKYC.objects.create(
            users=self.user,
            business_registration_number="1234567890",
            business_address="123 Main St",
            contact_person_details="John Doe",
        )
        self.assertEqual(kyc.users, self.user)
        self.assertEqual(kyc.business_registration_number, "1234567890")
        self.assertFalse(kyc.approved)

    def test_user_kyc_str(self):
        """test user kyc string representation."""
        kyc = UserKYC.objects.create(
            users=self.user,
            business_registration_number="1234567890",
            business_address="123 Main St",
            contact_person_details="John Doe",
        )
        self.assertEqual(str(kyc), "1234567890")

    def test_user_kyc_unique_constraints(self):
        """test user kyc unique constraints."""
        UserKYC.objects.create(
            users=self.user,
            business_registration_number="1234567890",
            business_address="123 Main St",
            contact_person_details="John Doe",
        )

        user2 = User.objects.create_user(
            email="testuser2@mail.com",
            password="password",
            username="testuser2",
        )

        # Duplicate business_registration_number
        with self.assertRaises(Exception):
            UserKYC.objects.create(
                users=user2,
                business_registration_number="1234567890",
                business_address="456 Other St",
                contact_person_details="Jane Doe",
            )

        # Duplicate business_address
        with self.assertRaises(Exception):
            UserKYC.objects.create(
                users=user2,
                business_registration_number="0987654321",
                business_address="123 Main St",
                contact_person_details="Jane Doe",
            )

        # Duplicate contact_person_details
        with self.assertRaises(Exception):
            UserKYC.objects.create(
                users=user2,
                business_registration_number="0987654321",
                business_address="456 Other St",
                contact_person_details="John Doe",
            )
