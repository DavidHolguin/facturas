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
            serializer = self.get_serializer(queryset, many=True)
            return Response({
                'status': 'success',
                'data': serializer.data
            })
        except Exception as e:
            logger.error(f"Error in list view: {str(e)}", exc_info=True)
            return Response({
                'status': 'error',
                'message': 'Error interno del servidor',
                'detail': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def get_queryset(self):
        # Retornar todos los chatbots activos
        return Chatbot.objects.filter(is_active=True)