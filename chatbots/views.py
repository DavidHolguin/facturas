# chatbots/views.py
from rest_framework import viewsets, status
from rest_framework.response import Response
from .permissions import IsAuthenticatedOrReadOnlySafe
from .models import Chatbot
from .serializers import ChatbotSerializer

class ChatbotViewSet(viewsets.ModelViewSet):
    queryset = Chatbot.objects.filter(is_active=True)
    serializer_class = ChatbotSerializer
    permission_classes = [IsAuthenticatedOrReadOnlySafe]

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