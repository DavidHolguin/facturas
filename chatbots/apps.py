from django.apps import AppConfig

class ChatbotsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'chatbots'

# chatbots/models.py
from django.db import models
from django.contrib.auth.models import User
from cloudinary.models import CloudinaryField

class ChatGPTModel(models.Model):
    """Modelo para almacenar las diferentes versiones de ChatGPT disponibles"""
    name = models.CharField(max_length=100)
    model_identifier = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return self.name

class Chatbot(models.Model):
    """Modelo principal para los chatbots"""
    name = models.CharField(max_length=200)
    description = models.TextField()
    logo = CloudinaryField('logo', null=True, blank=True)
    company = models.ForeignKey('marketplace.Company', on_delete=models.CASCADE)
    model = models.ForeignKey(ChatGPTModel, on_delete=models.PROTECT)
    api_key = models.CharField(max_length=255)
    system_prompt = models.TextField(help_text="Prompt inicial para personalizar el comportamiento del chatbot")
    is_public = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class Conversation(models.Model):
    """Modelo para almacenar conversaciones de usuarios con chatbots"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    chatbot = models.ForeignKey(Chatbot, on_delete=models.CASCADE)
    title = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.chatbot.name} - {self.created_at}"

class Message(models.Model):
    """Modelo para almacenar mensajes individuales en una conversación"""
    ROLE_CHOICES = [
        ('user', 'User'),
        ('assistant', 'Assistant'),
        ('system', 'System'),
    ]
    
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['timestamp']

# chatbots/admin.py
from django.contrib import admin
from .models import ChatGPTModel, Chatbot, Conversation, Message

@admin.register(ChatGPTModel)
class ChatGPTModelAdmin(admin.ModelAdmin):
    list_display = ('name', 'model_identifier', 'is_active')
    search_fields = ('name', 'model_identifier')

@admin.register(Chatbot)
class ChatbotAdmin(admin.ModelAdmin):
    list_display = ('name', 'company', 'model', 'is_public', 'created_at')
    list_filter = ('is_public', 'model', 'company')
    search_fields = ('name', 'description')
    readonly_fields = ('created_at', 'updated_at')

@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ('chatbot', 'user', 'created_at')
    list_filter = ('chatbot', 'user')
    search_fields = ('chatbot__name', 'user__username')

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('conversation', 'role', 'timestamp')
    list_filter = ('role', 'conversation__chatbot')
    search_fields = ('content',)