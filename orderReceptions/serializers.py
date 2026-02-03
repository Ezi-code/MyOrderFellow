"""order receptions serializers."""

from rest_framework import serializers
from orderReceptions.models import OrderCustomerDetails, OrderDetails
from drf_writable_nested.serializers import WritableNestedModelSerializer


class OrderCustomerDetailSerializer(serializers.ModelSerializer):
    """Order customer detail serializer."""

    class Meta:
        """Meta options."""

        model = OrderCustomerDetails
        exclude = ["created_at", "updated_at"]


class OrderDetailSerializer(WritableNestedModelSerializer):
    """Order detail serializer."""

    customer_details = OrderCustomerDetailSerializer(required=True)

    class Meta:
        """Meta options."""

        model = OrderDetails
        exclude = ["created_at", "updated_at"]
