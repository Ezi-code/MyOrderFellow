"""order receptions serializers."""

from rest_framework import serializers
from orderReceptions.models import OrderCustomerDetails, OrderDetails
from drf_writable_nested.serializers import WritableNestedModelSerializer


class OrderCustomerDetailSerializer(serializers.ModelSerializer):
    """order customer detail serializer."""

    class Meta:
        """meta options."""

        model = OrderCustomerDetails
        exclude = ["created_at", "updated_at"]


class OrderDetailSerializer(WritableNestedModelSerializer):
    """order detail serializer."""

    customer_details = OrderCustomerDetailSerializer(many=False, required=False)

    class Meta:
        """meta options."""

        model = OrderDetails
        exclude = ["created_at", "updated_at"]
