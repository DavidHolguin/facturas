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

    @action(detail=True, methods=['post'])
    def chat(self, request, pk=None):
        chatbot = self.get_object()
        user = request.user if request.user.is_authenticated else None
        session_id = request.data.get('session_id')
        message_content = request.data.get('message')

        # Obtener o crear conversación
        conversation, created = Conversation.objects.get_or_create(
            chatbot=chatbot,
            user=user,
            session_id=session_id
        )

        # Guardar mensaje del usuario
        Message.objects.create(
            conversation=conversation,
            role='user',
            content=message_content
        )

        # Preparar mensajes para OpenAI
        messages = [
            {"role": "system", "content": chatbot.system_prompt}
        ]
        for msg in conversation.messages.all():
            messages.append({
                "role": msg.role,
                "content": msg.content
            })

        try:
            # Configurar cliente OpenAI
            openai.api_key = chatbot.api_key
            
            # Realizar llamada a OpenAI
            response = openai.ChatCompletion.create(
                model=chatbot.model,
                messages=messages
            )

            # Guardar respuesta del asistente
            assistant_message = Message.objects.create(
                conversation=conversation,
                role='assistant',
                content=response.choices[0].message.content
            )

            return Response({
                'message': MessageSerializer(assistant_message).data
            })

        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)