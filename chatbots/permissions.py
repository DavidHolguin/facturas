# chatbots/permissions.py
from rest_framework import permissions

class ChatbotPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        # Permitir lectura (GET) a todos los usuarios
        if request.method in permissions.SAFE_METHODS:
            return True
            
        # Para modificaciones, requerir autenticación
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        # Permitir lectura a todos
        if request.method in permissions.SAFE_METHODS:
            return True
            
        # Para modificaciones, verificar si el usuario pertenece a la compañía del chatbot
        return request.user and request.user.is_authenticated and obj.company == request.user.company