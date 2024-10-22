# chatbots/views.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticatedOrReadOnly
import openai
from .models import Chatbot, Conversation, Message
from .serializers import ChatbotSerializer, ConversationSerializer, MessageSerializer

class ChatbotViewSet(viewsets.ModelViewSet):
    queryset = Chatbot.objects.filter(is_public=True)
    serializer_class = ChatbotSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    @action(detail=True, methods=['post'])
    def chat(self, request, pk=None):
        chatbot = self.get_object()
        user = request.user if request.user.is_authenticated else None
        message_content = request.data.get('message')
        
        # Crear o obtener conversación
        conversation_id = request.data.get('conversation_id')
        if conversation_id:
            conversation = Conversation.objects.get(id=conversation_id)
        else:
            conversation = Conversation.objects.create(
                user=user,
                chatbot=chatbot
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
        
        # Agregar historial de mensajes
        previous_messages = Message.objects.filter(conversation=conversation).order_by('timestamp')
        for msg in previous_messages:
            messages.append({"role": msg.role, "content": msg.content})

        try:
            # Configurar OpenAI
            openai.api_key = chatbot.api_key
            
            # Realizar llamada a OpenAI
            response = openai.ChatCompletion.create(
                model=chatbot.model.model_identifier,
                messages=messages
            )

            # Guardar respuesta del asistente
            assistant_message = response.choices[0].message.content
            Message.objects.create(
                conversation=conversation,
                role='assistant',
                content=assistant_message
            )

            return Response({
                'conversation_id': conversation.id,
                'message': assistant_message
            })
            
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
