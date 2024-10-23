# chatbots/permissions.py
from rest_framework import permissions

class IsAuthenticatedOrReadOnlySafe(permissions.BasePermission):
    """
    Custom permission to allow unauthenticated users to view chatbots
    but require authentication for other operations
    """
    def has_permission(self, request, view):
        # Allow GET, HEAD and OPTIONS requests
        if request.method in permissions.SAFE_METHODS:
            return True
        # Require authentication for other methods
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        # Allow GET, HEAD and OPTIONS requests
        if request.method in permissions.SAFE_METHODS:
            return True
        # Require authentication for other methods
        return bool(request.user and request.user.is_authenticated)