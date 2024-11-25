# views.py
from rest_framework import viewsets, filters
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q
from .models import Company, Category, Product
from .serializers import CompanySerializer, CategorySerializer, ProductSerializer
from rest_framework import viewsets, filters, status
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from django.db.models import Q
from .models import Company, Category, Product
from .serializers import ProductSerializer, ProductWriteSerializer


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
    search_fields = ['name', 'description', 'nit']

    def get_queryset(self):
        queryset = Company.objects.all()
        category = self.request.query_params.get('category', None)
       
        if category:
            queryset = queryset.filter(
                product__category__id=category
            ).distinct()
           
        return queryset


class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'description']
    parser_classes = [MultiPartParser, FormParser]

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return ProductWriteSerializer
        return ProductSerializer

    def get_queryset(self):
        queryset = Product.objects.all()
        company = self.request.query_params.get('company', None)
        category = self.request.query_params.get('category', None)

        if company:
            queryset = queryset.filter(company=company)
        if category:
            queryset = queryset.filter(categories=category)

        return queryset

    def create(self, request, *args, **kwargs):
        # Validate or create category if not exists
        category_name = request.data.get('category_name')
        if category_name:
            category, _ = Category.objects.get_or_create(
                name=category_name, 
                category_type='PRODUCTOS'
            )
            request.data['categories'] = [category.id]

        # Ensure company is set (you might want to get this from authenticated user)
        if not request.data.get('company'):
            return Response(
                {'error': 'Se requiere especificar la empresa'}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        # Handle image uploads
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Add main image if provided
        if 'main_image' in request.FILES:
            serializer.validated_data['main_image'] = request.FILES['main_image']
        
        # Add additional images if provided
        if 'additional_images' in request.FILES:
            serializer.validated_data['additional_images'] = request.FILES['additional_images']
        
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(
            serializer.data, 
            status=status.HTTP_201_CREATED, 
            headers=headers
        )

    @action(detail=True, methods=['get'])
    def calculate_price(self, request, pk=None):
        product = self.get_object()
        weight = request.query_params.get('weight', None)

        if not weight:
            return Response({'error': 'Se requiere especificar el peso'}, status=400)

        try:
            weight = float(weight)
            price = product.price * (weight / 0.5)  # Price per 500g
            return Response({
                'weight': weight,
                'unit': '500g',
                'calculated_price': price
            })
        except ValueError:
            return Response({'error': 'Peso inválido'}, status=400)