"""order receptions views."""

from django.http import Http404
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.response import Response
from orderReceptions.serializers import OrderDetailSerializer
from orderReceptions.models import OrderDetails
from drf_spectacular.utils import extend_schema
from orderReceptions.utils import (
    send_order_deleted_email,
    send_order_received_confirmation,
    send_order_status_update_email,
    verify_webhook_signature,
)
from base.permissions import IsVerifiedUser
from rest_framework.throttling import ScopedRateThrottle


@extend_schema(responses=OrderDetailSerializer)
class WebhookOrderListView(APIView):
    """Webhook endpoint for receiving order data from e-commerce platform."""

    permission_classes = [IsVerifiedUser]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "webhook"

    def get_object(self, pk):
        """Retrieve a single order by its unique ID (pk)."""
        try:
            return OrderDetails.objects.get(pk=pk)
        except OrderDetails.DoesNotExist as err:
            raise Http404 from err

    def get_objects(self):
        """Retrieve all orders from the database."""
        try:
            return OrderDetails.objects.all()
        except OrderDetails.DoesNotExist:
            raise Http404

    def get(self, request):
        """
        Retrieve order details - either a single order or all orders.

        How it works:
        - Verifies the webhook signature to ensure the request is legitimate
        - Checks if a specific order ID is provided in the request
        - If an order ID is provided: returns that single order's details
        - If no ID is provided: returns all orders in the system
        - Serializes the response data for the frontend

        Security:
        - Requires a valid webhook signature
        - Only authenticated verified users can access this endpoint
        """
        request = verify_webhook_signature(request)
        order_id = request.query_params.get("id") or request.data.get("id")
        if order_id:
            order_instance = self.get_object(order_id)
            serializer = OrderDetailSerializer(order_instance)
            return Response(serializer.data, status=status.HTTP_200_OK)
        orders = self.get_objects()
        serializer = OrderDetailSerializer(orders, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        """
        Create a new order from webhook data.

        How it works:
        1. Verifies the webhook signature to authenticate the request (ensures it's from a trusted e-commerce platform)
        2. Validates the incoming order data against OrderDetailSerializer
        3. Saves the order to the database if validation passes
        4. Enqueues a background task to send a confirmation email to the customer
        5. Returns the created order with a 201 Created status

        Background tasks:
        - Sends an order confirmation email to the customer asynchronously

        Errors:
        - 400 Bad Request: If order data validation fails
        - 401 Unauthorized: If webhook signature is invalid
        - 500 Server Error: If email task fails to enqueue
        """
        request = verify_webhook_signature(request)
        serializer = OrderDetailSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        send_order_received_confirmation.enqueue(str(serializer.instance.pk))
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def patch(self, request):
        """
        Update an existing order (partial update).

        How it works:
        1. Retrieves the order by ID from the request data
        2. Validates the partial update data (only changed fields need to be provided)
        3. Updates only the fields that were provided in the request
        4. Saves the updated order to the database
        5. Enqueues a background task to send a status update email to the customer
        6. Returns the updated order with a 200 OK status

        Common use cases:
        - Updating order status (pending → shipped → delivered)
        - Adding tracking information
        - Modifying delivery address
        - Updating estimated delivery date

        Background tasks:
        - Sends order status update email to the customer asynchronously

        Errors:
        - 400 Bad Request: If data validation fails
        - 404 Not Found: If order with the given ID doesn't exist
        - 401 Unauthorized: If webhook signature is invalid
        """
        request = verify_webhook_signature(request)
        order_instance = self.get_object(request.data.get("id"))
        serializer = OrderDetailSerializer(
            order_instance, data=request.data, partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        send_order_status_update_email.enqueue(str(serializer.instance.pk))
        return Response(serializer.data, status=status.HTTP_200_OK)

    def delete(self, request):
        """
        Delete an existing order.

        How it works:
        1. Retrieves the order ID from the request data
        2. Fetches the order from the database
        3. Extracts the customer's email address from the order
        4. Deletes the order from the database
        5. Enqueues a background task to send a deletion notification email to the customer
        6. Returns a 204 No Content response (indicating successful deletion)

        What happens:
        - The order is removed from the system
        - All related order items and records are deleted
        - Customer receives a notification email explaining the order was deleted

        Background tasks:
        - Sends order cancellation/deletion email to the customer asynchronously

        Errors:
        - 404 Not Found: If order with the given ID doesn't exist
        - 401 Unauthorized: If webhook signature is invalid
        """
        request = verify_webhook_signature(request)
        order_id = request.data.get("id")
        order_detail = self.get_object(order_id)
        customer_email = order_detail.customer_details.email
        order_detail.delete()
        send_order_deleted_email.enqueue(order_id, customer_email)
        return Response(status=status.HTTP_204_NO_CONTENT)
