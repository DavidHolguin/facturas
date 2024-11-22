# views.py
from rest_framework import viewsets, filters
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from django.db.models import Q
from .models import Company, Category, Product
from .serializers import CompanySerializer, CategorySerializer, ProductSerializer

class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [filters.SearchFilter]
    search_fields = ['name']

class CompanyViewSet(viewsets.ModelViewSet):
    queryset = Company.objects.all()
    serializer_class = CompanySerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'description']

    def get_queryset(self):
        queryset = Company.objects.all()
        category = self.request.query_params.get('category', None)
        
        if category:
            queryset = queryset.filter(
                Q(products__category__id=category)
            ).distinct()
            
        return queryset

class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'description']

    def get_queryset(self):
        queryset = Product.objects.all()
        company = self.request.query_params.get('company', None)
        category = self.request.query_params.get('category', None)
        
        if company:
            queryset = queryset.filter(company__id=company)
        if category:
            queryset = queryset.filter(category__id=category)
            
        return queryset
