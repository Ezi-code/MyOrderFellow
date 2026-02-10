"""order receptions filters."""

from django_filters import rest_framework as filters
from orderReceptions.models import OrderDetails


class OrderDetailsFilter(filters.FilterSet):
    """order details filter."""

    customer_name = filters.CharFilter(
        field_name="customer_details__name", lookup_expr="icontains"
    )
    customer_email = filters.CharFilter(
        field_name="customer_details__email", lookup_expr="icontains"
    )
    customer_phone = filters.CharFilter(
        field_name="customer_details__phone", lookup_expr="icontains"
    )

    tracking_status = filters.CharFilter(
        field_name="tracking_status", lookup_expr="iexact"
    )
    address = filters.CharFilter(field_name="address", lookup_expr="icontains")
    id = filters.UUIDFilter(field_name="id", lookup_expr="exact")

    class Meta:
        model = OrderDetails
        fields = [
            "customer_details__name",
            "tracking_status",
            "address",
            "id",
            "customer_details__email",
            "customer_details__phone",
        ]
