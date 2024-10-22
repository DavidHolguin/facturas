# chatbots/admin.py
from django.contrib import admin
from .models import Chatbot, Conversation, Message

@admin.register(Chatbot)
class ChatbotAdmin(admin.ModelAdmin):
    list_display = ('name', 'company', 'model', 'is_active', 'created_at')
    list_filter = ('is_active', 'model', 'company')
    search_fields = ('name', 'description', 'company__name')
    readonly_fields = ('created_at', 'updated_at')

@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ('chatbot', 'user', 'session_id', 'created_at')
    list_filter = ('chatbot', 'created_at')
    search_fields = ('chatbot__name', 'user__username', 'session_id')

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('conversation', 'role', 'timestamp')
    list_filter = ('role', 'timestamp')
    search_fields = ('content', 'conversation__chatbot__name')