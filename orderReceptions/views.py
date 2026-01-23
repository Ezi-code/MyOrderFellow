"""order receptions views."""

from django.http import Http404
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.response import Response
from orderReceptions.serializers import OrderDetailSerializer
from orderReceptions.models import OrderDetails, OrderStatusHistory
from drf_spectacular.utils import extend_schema
from orderReceptions.utils import (
    send_order_received_confirmation,
    send_order_status_update_email,
    send_order_deleted_email,
)
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
        serializer = OrderDetailSerializer(order_receptions, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        request=OrderDetailSerializer, responses={201: OrderDetailSerializer}
    )
    def post(self, request) -> Response:
        """create an order detail object."""
        serializer = OrderDetailSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        send_order_received_confirmation.enqueue(str(serializer.instance.pk))
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class OrderDetailView(APIView):
    """order detail view."""

    permission_classes = [IsVerifiedUser]

    def get_object(self, pk):
        """get an order detail object."""
        try:
            return OrderDetails.objects.get(pk=pk)
        except OrderDetails.DoesNotExist as err:
            raise Http404 from err

    extend_schema(responses={200: OrderDetailSerializer})

    def get(self, request, pk=None) -> Response:
        """get an order detail object."""
        order_detail = self.get_object(pk)
        serializer = OrderDetailSerializer(order_detail)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(responses={200: OrderDetailSerializer})
    def patch(self, request, pk=None) -> Response:
        """update an order detail object."""
        order_detail = self.get_object(pk)
        old_status = order_detail.tracking_status

        serializer = OrderDetailSerializer(order_detail, request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        new_status = serializer.instance.tracking_status

        if new_status != old_status:
            OrderStatusHistory.objects.create(status=new_status, order=order_detail)
            send_order_status_update_email.enqueue(str(serializer.instance.pk))
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(responses={200: OrderDetailSerializer})
    def delete(self, request, pk=None) -> Response:
        """delete an order detail object."""
        order_detail = self.get_object(pk)
        order_pk = str(order_detail.pk)
        customer_email = order_detail.customer_details.email
        order_detail.delete()
        send_order_deleted_email.enqueue(order_pk, customer_email)
        return Response(status=status.HTTP_204_NO_CONTENT)
