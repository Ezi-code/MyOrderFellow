"""order receptions admin."""

from django.contrib import admin
from orderReceptions.models import OrderDetails, OrderCustomerDetails, OrderStatusHistory


@admin.register(OrderDetails)
class OrderDetailsAdmin(admin.ModelAdmin):
    """Order details admin."""

    list_display = ("id", "customer_details", "tracking_status", "created_at")
    list_filter = ("tracking_status",)
    search_fields = ("id", "customer_details__name", "item_summary")
    ordering = ("-created_at",)


@admin.register(OrderCustomerDetails)
class OrderCustomerDetailsAdmin(admin.ModelAdmin):
    """Order customer details admin."""

    list_display = ("name", "email", "phone")
    search_fields = ("name", "email", "phone")
    ordering = ("-created_at",)


@admin.register(OrderStatusHistory)
class OrderStatusHistoryAdmin(admin.ModelAdmin):
    """Order status history admin."""

    list_display = ("order", "status", "created_at")
    list_filter = ("status",)
    search_fields = ("order__id", "status")
    ordering = ("-created_at",)
