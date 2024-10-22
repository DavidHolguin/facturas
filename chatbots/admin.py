# chatbots/admin.py
from django.contrib import admin
from .models import Chatbot, Conversation, Message

@admin.register(Chatbot)
class ChatbotAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_public', 'model', 'created_at')
    search_fields = ('name', 'model__model_identifier')
    list_filter = ('is_public', 'created_at')

@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ('user', 'chatbot', 'started_at')
    search_fields = ('user__username', 'chatbot__name')
    list_filter = ('started_at',)

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('conversation', 'role', 'timestamp', 'content')
    search_fields = ('conversation__id', 'role', 'content')
    list_filter = ('role', 'timestamp')

