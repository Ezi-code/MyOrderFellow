"""custom user permissions."""

from rest_framework.permissions import BasePermission
from users.models import UserKYC


class IsVerifiedUser(BasePermission):
    """Verified user permission.
    a user is said to be verified if their KYC is approved.
    """

    def has_object_permission(self, request, view, obj):
        if request.user and request.user.is_authenticated:
            return True if UserKYC.objects.get(users=request.user).approved else False
        return False
