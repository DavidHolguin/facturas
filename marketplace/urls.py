from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CompanyViewSet, CategoryViewSet, ProductViewSet

router = DefaultRouter()
router.register(r'companies', CompanyViewSet)
router.register(r'categories', CategoryViewSet)
router.register(r'products', ProductViewSet)

urlpatterns = [
    path('', include(router.urls)),
]