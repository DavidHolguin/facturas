# chatbots/serializers.py
from rest_framework import serializers
from .models import Chatbot, Conversation, Message

class ChatbotSerializer(serializers.ModelSerializer):
    logo_url = serializers.URLField(source='logo.url', read_only=True)
    
    class Meta:
        model = Chatbot
        fields = ['id', 'name', 'description', 'company', 'model', 
                 'system_prompt', 'logo_url', 'is_active', 'created_at']
        read_only_fields = ['created_at']

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
