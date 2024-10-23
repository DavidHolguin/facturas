# chatbots/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ChatbotViewSet

router = DefaultRouter()
router.register(r'', ChatbotViewSet, basename='chatbot')  # Cambiamos 'chatbots' a ''

urlpatterns = [
    path('', include(router.urls)),
]