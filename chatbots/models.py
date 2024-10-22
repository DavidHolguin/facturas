# chatbots/models.py

from django.db import models
from django.contrib.auth.models import User
from cloudinary.models import CloudinaryField

class ChatbotModel(models.TextChoices):
    GPT_3_5_TURBO = 'gpt-3.5-turbo', 'GPT-3.5 Turbo'
    GPT_4 = 'gpt-4', 'GPT-4'
    GPT_4_TURBO = 'gpt-4-turbo-preview', 'GPT-4 Turbo'

class Chatbot(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    company = models.ForeignKey('marketplace.Company', on_delete=models.CASCADE, related_name='chatbots')
    model = models.CharField(
        max_length=50,
        choices=ChatbotModel.choices,
        default=ChatbotModel.GPT_3_5_TURBO
    )
    api_key = models.CharField(max_length=255)
    system_prompt = models.TextField(
        help_text="El prompt inicial que define el comportamiento del chatbot"
    )
    logo = CloudinaryField('logo', null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} - {self.company.name}"

class Conversation(models.Model):
    chatbot = models.ForeignKey(Chatbot, on_delete=models.CASCADE, related_name='conversations')
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    session_id = models.CharField(max_length=100, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        return f"Conversation with {self.chatbot.name}"

class Message(models.Model):
    ROLE_CHOICES = [
        ('user', 'User'),
        ('assistant', 'Assistant'),
        ('system', 'System'),
    ]

    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['timestamp']

    def __str__(self):
        return f"{self.role}: {self.content[:50]}..."