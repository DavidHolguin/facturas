# chatbots/permissions.py
from rest_framework import permissions

class ChatbotPermission(permissions.BasePermission):
    """
    Custom permission for Chatbot viewset:
    - Allow read-only access to anyone
    - Require authentication for create/update/delete operations
    """
    def has_permission(self, request, view):
        # Allow GET, HEAD, OPTIONS requests without authentication
        if request.method in permissions.SAFE_METHODS:
            return True
        # Require authentication for other methods
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        # Allow GET, HEAD, OPTIONS requests without authentication
        if request.method in permissions.SAFE_METHODS:
            return True
        # For other methods, only allow if user is authenticated and is admin or owns the company
        return bool(request.user and request.user.is_authenticated and 
                   (request.user.is_staff or obj.company.owner == request.user))