"""order receptions views."""

from rest_framework.views import APIView
from rest_framework import status
from rest_framework.response import Response
from orderReceptions.serializers import OrderDetailSerializer
from orderReceptions.models import OrderDetails
from drf_spectacular.utils import extend_schema
from orderReceptions.utils import send_order_received_confirmation
from base.permissions import IsVerifiedUser


class OrderDetailListView(APIView):
    """order detail list view."""

    permission_classes = [IsVerifiedUser]

    @extend_schema(responses={200: OrderDetailSerializer(many=True)})
    def get(self, request) -> Response:
        """get all order details."""
        order_receptions = OrderDetails.objects.all().prefetch_related(
            "customer_details"
        )
        serializer = OrderDetailSerializer(order_receptions)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        request={200: OrderDetailSerializer}, responses={201: OrderDetailSerializer}
    )
    def post(self, request) -> Response:
        """create an order detail object."""
        serializer = OrderDetailSerializer(request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        send_order_received_confirmation.enqueu(serializer.instance)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
