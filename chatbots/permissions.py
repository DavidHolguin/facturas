# chatbots/permissions.py
from rest_framework import permissions

class ChatbotPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        # Permitir acceso público para listar y recuperar chatbots individuales
        if request.method in permissions.SAFE_METHODS:  # GET, HEAD, OPTIONS
            return True
            
        # Para otras operaciones (CREATE, UPDATE, DELETE) requerir autenticación
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        # Permitir lectura pública
        if request.method in permissions.SAFE_METHODS:
            return True
            
        # Verificar si el usuario es el propietario del chatbot (a través de la compañía)
        if request.user and hasattr(request.user, 'company'):
            return obj.company == request.user.company
            
        return False