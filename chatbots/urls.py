# chatbots/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ChatbotViewSet

router = DefaultRouter()
router.register(r'chatbots', ChatbotViewSet)

urlpatterns = [
    path('', include(router.urls)),
]

# En backend/urls.py añadir:
path('api/', include('chatbots.urls')),