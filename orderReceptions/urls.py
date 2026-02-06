"""order receptions urls."""

from django.urls import path
from orderReceptions import views

app_name = "orderReceptions"


urlpatterns = [
    path("webhook/", views.WebhookOrderListView.as_view(), name="webhook-orders")
]
