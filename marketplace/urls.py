from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from .views import SearchView, LoginView, RegisterView, OrderViewSet, CompanyCategoryViewSet, CountryViewSet
from .views import TopBurgerSectionView



router = DefaultRouter()
router.register(r'companies', views.CompanyViewSet)
router.register(r'categories', views.CategoryViewSet)
router.register(r'products', views.ProductViewSet)
router.register(r'orders', OrderViewSet)
router.register(r'company-categories', CompanyCategoryViewSet)
router.register(r'countries', CountryViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('search/', SearchView.as_view(), name='search'),
    path('login/', LoginView.as_view(), name='login'),
    path('register/', RegisterView.as_view(), name='register'),
    path('top-burgers/', TopBurgerSectionView.as_view(), name='top-burgers'),
]