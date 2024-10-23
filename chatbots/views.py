from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticatedOrReadOnly
import openai
from django.conf import settings

from .models import Chatbot, Conversation, Message
from .serializers import ChatbotSerializer, ConversationSerializer, MessageSerializer

class ChatbotViewSet(viewsets.ModelViewSet):
    queryset = Chatbot.objects.filter(is_active=True)
    serializer_class = ChatbotSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def list(self, request, *args, **kwargs):
        try:
            queryset = self.get_queryset()
            serializer = self.get_serializer(queryset, many=True)
            return Response({
                'status': 'success',
                'data': serializer.data
            })
        except Exception as e:
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)