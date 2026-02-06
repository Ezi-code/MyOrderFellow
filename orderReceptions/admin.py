"""order receptions admin."""

from django.contrib import admin
from orderReceptions.models import (
    OrderDetails,
    OrderCustomerDetails,
    OrderStatusHistory,
)


@admin.register(OrderDetails)
class OrderDetailsAdmin(admin.ModelAdmin):
    """Order details admin."""

    list_display = ("id", "item_summary", "created_at")
    search_fields = ("item_summary",)
    ordering = ("-created_at",)


@admin.register(OrderCustomerDetails)
class OrderCustomerDetailsAdmin(admin.ModelAdmin):
    """Order customer details admin."""

    list_display = ("name", "email", "phone")
    search_fields = ("name", "email", "phone")
    ordering = ("-created_at",)


@admin.register(OrderStatusHistory)
class OrderStatusHistoryAdmin(admin.ModelAdmin):
    """Order customer details admin."""

    list_display = ("order__id", "status")
    search_fields = ("status", "order__id")
    ordering = ("-created_at",)
