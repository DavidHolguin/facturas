# chatbots/serializers.py
from rest_framework import serializers
from .models import ChatGPTModel, Chatbot, Conversation, Message

class ChatGPTModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatGPTModel
        fields = ['id', 'name', 'model_identifier']

class ChatbotSerializer(serializers.ModelSerializer):
    model_name = serializers.CharField(source='model.name', read_only=True)
    company_name = serializers.CharField(source='company.name', read_only=True)
    
    class Meta:
        model = Chatbot
        fields = ['id', 'name', 'description', 'logo', 'company', 'company_name', 
                 'model', 'model_name', 'is_public', 'created_at']

class ConversationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Conversation
        fields = ['id', 'chatbot', 'title', 'created_at']

class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = ['id', 'conversation', 'role', 'content', 'timestamp']


