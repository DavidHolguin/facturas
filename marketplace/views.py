from rest_framework import serializers  # Asegúrate de importar serializers
from rest_framework import viewsets
from .models import Company, Category, Product, Order, TopBurgerSection, TopBurgerItem
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly, AllowAny
from .serializers import OrderSerializer, OrderItemSerializer, OrderItem, CompanySerializer, CategorySerializer, ProductSerializer, TopBurgerSectionSerializer, TopBurgerItemSerializer
from django.conf import settings
from rest_framework.decorators import action
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404
import logging

class CompanyViewSet(viewsets.ModelViewSet):
    queryset = Company.objects.all()
    serializer_class = CompanySerializer
    permission_classes = [AllowAny]

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [AllowAny]

class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [AllowAny]

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

class SearchView(APIView):
    def get(self, request):
        query = request.query_params.get('q', '')
        companies = Company.objects.filter(name__icontains=query)
        products = Product.objects.filter(name__icontains=query)
        categories = Category.objects.filter(name__icontains=query)

        company_serializer = CompanySerializer(companies, many=True, context={'request': request})
        product_serializer = ProductSerializer(products, many=True, context={'request': request})
        category_serializer = CategorySerializer(categories, many=True)

        results = (
            company_serializer.data +
            product_serializer.data +
            category_serializer.data
        )

        return Response(results)
    
class LoginView(APIView):
    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        user = authenticate(username=username, password=password)
        if user:
            token, _ = Token.objects.get_or_create(user=user)
            return Response({'token': token.key})
        return Response({'error': 'Credenciales inválidas'}, status=status.HTTP_400_BAD_REQUEST)

class RegisterView(APIView):
    def post(self, request):
        username = request.data.get('username')
        email = request.data.get('email')
        password = request.data.get('password')
        if User.objects.filter(username=username).exists():
            return Response({'error': 'El nombre de usuario ya existe'}, status=status.HTTP_400_BAD_REQUEST)
        user = User.objects.create_user(username=username, email=email, password=password)
        return Response({'message': 'Usuario creado exitosamente'}, status=status.HTTP_201_CREATED)

class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

    def create(self, request):
        data = request.data
        user = request.user
        company_id = data.get('company')
        items = data.get('items', [])

        if not company_id or not items:
            return Response({"error": "Datos de pedido incompletos"}, status=status.HTTP_400_BAD_REQUEST)

        total = sum(item['price'] * item['quantity'] for item in items)
        order = Order.objects.create(user=user, company_id=company_id, total=total)

        for item in items:
            OrderItem.objects.create(
                order=order,
                product_id=item['product'],
                quantity=item['quantity'],
                price=item['price']
            )

        serializer = self.get_serializer(order)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def get_queryset(self):
        user = self.request.user
        return Order.objects.filter(user=user)

logger = logging.getLogger(__name__)

class TopBurgerSectionView(APIView):
    permission_classes = [AllowAny]
    
    def get(self, request):
        try:
            # Obtener todas las secciones ordenadas por posición
            sections = TopBurgerSection.objects.all()
            
            serializer = TopBurgerSectionSerializer(
                sections, 
                many=True,
                context={'request': request}
            )
            return Response(serializer.data)
            
        except Exception as e:
            logger.error(f"Error in TopBurgerSectionView: {str(e)}")
            return Response({
                "error": str(e)
            }, status=500)

class TopBurgerItemSerializer(serializers.ModelSerializer):
    company_name = serializers.SerializerMethodField()
    company_logo = serializers.SerializerMethodField()
    company_profile_url = serializers.SerializerMethodField()
    featured_image = serializers.SerializerMethodField()

    class Meta:
        model = TopBurgerItem
        fields = [
            'company_name',
            'company_logo',
            'company_profile_url',
            'featured_image',
            'order'
        ]

    def get_company_name(self, obj):
        return obj.company.name if obj.company else ""

    def get_company_logo(self, obj):
        if obj.company and obj.company.profile_picture:
            return self.context['request'].build_absolute_uri(obj.company.profile_picture.url)
        return ""

    def get_company_profile_url(self, obj):
        if obj.company:
            return f"/company/{obj.company.id}"
        return ""

    def get_featured_image(self, obj):
        if obj.featured_image:
            return self.context['request'].build_absolute_uri(obj.featured_image.url)
        return ""

class TopBurgerSectionSerializer(serializers.ModelSerializer):
    items = TopBurgerItemSerializer(many=True, read_only=True)

    class Meta:
        model = TopBurgerSection
        fields = ['title', 'location', 'items']

    def to_representation(self, instance):
        # Asegurarnos de que items sea una lista vacía si no hay items
        representation = super().to_representation(instance)
        if not representation.get('items'):
            representation['items'] = []
        return representation