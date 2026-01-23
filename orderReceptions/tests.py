"""order receptions tests."""

from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from unittest.mock import patch
from users.models import User, UserKYC
from orderReceptions.models import OrderCustomerDetails, OrderDetails
from orderReceptions.serializers import (
    OrderCustomerDetailSerializer,
    OrderDetailSerializer,
)
from orderReceptions.choices import OrderTrackingStatusChoices
import uuid


class OrderReceptionsModelsTestCase(TestCase):
    """Order receptions tests."""

    def setUp(self):
        """Set up the test client."""
        self.customer = OrderCustomerDetails.objects.create(
            name="John Doe", phone="1234567890", email="john@example.com"
        )

    def test_order_customer_details_creation(self):
        """Order customer details creation."""
        self.assertEqual(self.customer.name, "John Doe")
        self.assertEqual(str(self.customer), "John Doe")

    def test_order_details_creation(self):
        """Order details creation."""
        order = OrderDetails.objects.create(
            customer_details=self.customer,
            address="123 Street",
            item_summary="Items list",
            tracking_status=OrderTrackingStatusChoices.PENDING,
        )
        self.assertIsInstance(order.id, uuid.UUID)
        self.assertEqual(order.address, "123 Street")
        self.assertEqual(str(order), f"John Doe >> {order.id}")


class OrderReceptionsSerializersTestCase(TestCase):
    """Order receptions serializers tests."""

    def setUp(self):
        """Set up the test client."""
        self.customer_data = {
            "name": "Jane Doe",
            "phone": "0987654321",
            "email": "jane@example.com",
        }
        self.customer = OrderCustomerDetails.objects.create(**self.customer_data)

    def test_order_customer_detail_serializer(self):
        """Order customer detail serializer."""
        serializer = OrderCustomerDetailSerializer(self.customer)
        expected_data = {
            "id": self.customer.id,
            "name": "Jane Doe",
            "phone": "0987654321",
            "email": "jane@example.com",
        }
        self.assertEqual(serializer.data, expected_data)

    def test_order_detail_serializer_nested_create(self):
        """Order detail serializer."""
        data = {
            "customer_details": {
                "name": "New Customer",
                "phone": "1112223333",
                "email": "new@example.com",
            },
            "address": "New Address",
            "item_summary": "New Summary",
            "tracking_status": OrderTrackingStatusChoices.PENDING,
        }
        serializer = OrderDetailSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        order = serializer.save()
        self.assertEqual(order.customer_details.name, "New Customer")
        self.assertEqual(OrderCustomerDetails.objects.count(), 2)


class OrderReceptionsViewsTestCase(APITestCase):
    """Order receptions views tests."""

    def setUp(self):
        """Set up the test client."""
        self.user = User.objects.create_user(
            email="test@example.com",
            username="testuser",
            password="password123",
            is_active=True,
        )
        self.kyc = UserKYC.objects.create(
            users=self.user,
            business_registration_number="1234567890",
            business_address="Business Address",
            contact_person_details="Contact Details",
            approved=True,
        )
        self.client.force_authenticate(user=self.user)

        self.customer = OrderCustomerDetails.objects.create(
            name="Customer One", phone="1234567890", email="cust1@example.com"
        )
        self.order = OrderDetails.objects.create(
            customer_details=self.customer,
            address="Address One",
            item_summary="Summary One",
        )
        self.list_url = reverse("orderReceptions:orderreceptions-list")
        self.detail_url = reverse(
            "orderReceptions:orderreceptions-detail", kwargs={"pk": self.order.pk}
        )

    @patch("orderReceptions.views.send_order_received_confirmation")
    def test_list_orders(self, mock_task):
        """List orders view."""
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    @patch("orderReceptions.views.send_order_received_confirmation")
    def test_create_order(self, mock_task):
        """Create order view."""
        data = {
            "customer_details": {
                "name": "Post Customer",
                "phone": "5555555555",
                "email": "post@example.com",
            },
            "address": "Post Address",
            "item_summary": "Post Summary",
        }
        response = self.client.post(self.list_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(OrderDetails.objects.count(), 2)
        mock_task.enqueue.assert_called_once()

    @patch("orderReceptions.views.send_order_received_confirmation")
    def test_retrieve_order(self, mock_task):
        """Retrieve order view."""
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["address"], "Address One")

    @patch("orderReceptions.views.send_order_status_update_email")
    def test_patch_order(self, mock_task):
        """Patch order view."""
        data = {"address": "Updated Address"}
        response = self.client.patch(self.detail_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.order.refresh_from_db()
        self.assertEqual(self.order.address, "Updated Address")
        mock_task.enqueue.assert_called_once()

    @patch("orderReceptions.views.send_order_status_update_email")
    def test_delete_order(self, mock_task):
        """Delete order view."""
        response = self.client.delete(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(OrderDetails.objects.count(), 0)
        mock_task.enqueue.assert_called_once()

    def test_unverified_user_access(self):
        """Unverified user access."""
        self.kyc.approved = False
        self.kyc.save()
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
