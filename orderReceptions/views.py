"""order receptions views."""

from django.conf import settings
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema
from secrets import compare_digest

from orderReceptions.serializers import OrderDetailSerializer
from orderReceptions.models import OrderDetails, OrderStatusHistory
from orderReceptions.utils import (
    send_order_received_confirmation,
    send_order_status_update_email,
    send_order_deleted_email,
)
from base.permissions import IsVerifiedUser
from users.models import User


class WebhookOrderView(APIView):
    """Webhook endpoint for receiving order data from e-commerce platform."""

    permission_classes = [AllowAny]

    def post(self, request):
        """
        Handle incoming webhook data.

        Verifies webhook signature, auto-regenerates expired secrets,
        and auto-creates secrets for KYC-verified businesses.
        """
        token = request.headers.get("X-Webhook-Signature")
        if not token or not compare_digest(token, settings.WEBHOOK_API_TOKEN):
            return Response(
                {"detail": "Invalid webhook signature."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Verify customer account
        customer_email = request.headers.get("X-Customer-Email")
        if not User.objects.filter(email=customer_email, is_active=True).exists():
            return Response(
                {"detail": "Customer account not found or inactive."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = OrderDetailSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class OrderDetailListView(APIView):
    """Order detail list view."""

    permission_classes = [IsVerifiedUser]

    @extend_schema(responses={200: OrderDetailSerializer(many=True)})
    def get(self, request) -> Response:
        """Get all order details."""
        order_receptions = OrderDetails.objects.all().select_related("customer_details")
        serializer = OrderDetailSerializer(order_receptions, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        request=OrderDetailSerializer, responses={201: OrderDetailSerializer}
    )
    def post(self, request) -> Response:
        """Create an order detail object."""
        serializer = OrderDetailSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        send_order_received_confirmation.enqueue(str(serializer.instance.pk))
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class OrderDetailView(APIView):
    """Order detail view."""

    permission_classes = [IsVerifiedUser]

    @extend_schema(responses={200: OrderDetailSerializer})
    def get(self, request, pk=None) -> Response:
        """Get an order detail object."""
        order_detail = get_object_or_404(OrderDetails, pk=pk)
        serializer = OrderDetailSerializer(order_detail)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(responses={200: OrderDetailSerializer})
    def patch(self, request, pk=None) -> Response:
        """Update an order detail object."""
        order_detail = get_object_or_404(OrderDetails, pk=pk)
        old_status = order_detail.tracking_status

        serializer = OrderDetailSerializer(order_detail, request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        new_status = serializer.instance.tracking_status

        if new_status != old_status:
            OrderStatusHistory.objects.create(status=new_status, order=order_detail)
            send_order_status_update_email.enqueue(str(serializer.instance.pk))
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(responses={204: None})
    def delete(self, request, pk=None) -> Response:
        """Delete an order detail object."""
        order_detail = get_object_or_404(OrderDetails, pk=pk)
        order_pk = str(order_detail.pk)
        customer_email = order_detail.customer_details.email
        order_detail.delete()
        send_order_deleted_email.enqueue(order_pk, customer_email)
        return Response(status=status.HTTP_204_NO_CONTENT)
