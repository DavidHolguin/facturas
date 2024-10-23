# chatbots/views.py
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from .models import Chatbot
from .serializers import ChatbotSerializer
from .permissions import ChatbotPermission
import logging

logger = logging.getLogger(__name__)

class ChatbotViewSet(viewsets.ModelViewSet):
    queryset = Chatbot.objects.filter(is_active=True)
    serializer_class = ChatbotSerializer
    permission_classes = [ChatbotPermission]

    def list(self, request, *args, **kwargs):
        try:
            queryset = self.get_queryset()
            page = self.paginate_queryset(queryset)
            
            if page is not None:
                serializer = self.get_serializer(page, many=True)
                return self.get_paginated_response(serializer.data)

            serializer = self.get_serializer(queryset, many=True)
            return Response({
                'status': 'success',
                'data': serializer.data
            })
        except Exception as e:
            logger.error(f"Error in list view: {str(e)}", exc_info=True)
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def create(self, request, *args, **kwargs):
        try:
            # Add the company based on the authenticated user
            if request.user.is_authenticated and hasattr(request.user, 'company'):
                request.data['company'] = request.user.company.id
            return super().create(request, *args, **kwargs)
        except Exception as e:
            logger.error(f"Error in create view: {str(e)}", exc_info=True)
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)