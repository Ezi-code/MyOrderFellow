"""custom user permissions."""

from rest_framework.permissions import BasePermission
from users.models import UserKYC


class IsVerifiedUser(BasePermission):
    """Verified user permission.
    a user is said to be verified if their KYC is approved.
    """

    def has_permission(self, request, view):
        if request.user and request.user.is_authenticated:
            try:
                return UserKYC.objects.get(user=request.user).approved
            except UserKYC.DoesNotExist:
                return False
        return False

    def has_object_permission(self, request, view, obj):
        return self.has_permission(request, view)
