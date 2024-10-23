# chatbots/serializers.py
from rest_framework import serializers
from .models import Chatbot, Conversation, Message


class ChatbotSerializer(serializers.ModelSerializer):
    avatar = serializers.SerializerMethodField()
    
    class Meta:
        model = Chatbot
        fields = ['id', 'name', 'description', 'model', 'avatar', 'is_active', 'created_at']
        read_only_fields = ['created_at']
        
    def get_fields(self):
        fields = super().get_fields()
        request = self.context.get('request')
        
        # Si el usuario no está autenticado, eliminar campos sensibles
        if not request or not request.user.is_authenticated:
            fields.pop('api_key', None)
            fields.pop('system_prompt', None)
            
        return fields
    
    def get_avatar(self, obj):
        if obj.logo and hasattr(obj.logo, 'url'):
            return obj.logo.url
        return None

class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = ['id', 'role', 'content', 'timestamp']
        read_only_fields = ['timestamp']

class ConversationSerializer(serializers.ModelSerializer):
    messages = MessageSerializer(many=True, read_only=True)
    
    class Meta:
        model = Conversation
        fields = ['id', 'chatbot', 'user', 'session_id', 'created_at', 'messages']
        read_only_fields = ['created_at']
