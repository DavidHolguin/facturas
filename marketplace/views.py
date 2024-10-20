from rest_framework import serializers  # Asegúrate de importar serializers
from rest_framework import viewsets
from .models import Company, Category, Product, Order, OrderItem, CompanyCategory, Country, TopBurgerSection, TopBurgerItem
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly, AllowAny
from .serializers import OrderSerializer, OrderItemSerializer, CompanyCategorySerializer, CountrySerializer, \
    OrderItem, CompanySerializer, CategorySerializer, ProductSerializer, TopBurgerSectionSerializer, TopBurgerItemSerializer
from django.conf import settings
from rest_framework.decorators import action
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404
import logging

class CompanyCategoryViewSet(viewsets.ModelViewSet):
    queryset = CompanyCategory.objects.all()
    serializer_class = CompanyCategorySerializer
    permission_classes = [AllowAny]

class CountryViewSet(viewsets.ModelViewSet):
    queryset = Country.objects.all()
    serializer_class = CountrySerializer
    permission_classes = [AllowAny]

class CompanyViewSet(viewsets.ModelViewSet):
    queryset = Company.objects.all()
    serializer_class = CompanySerializer
    permission_classes = [AllowAny]

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

    def get_queryset(self):
        queryset = Company.objects.all()
        category = self.request.query_params.get('category', None)
        country = self.request.query_params.get('country', None)
        
        if category is not None:
            queryset = queryset.filter(category__id=category)
        if country is not None:
            queryset = queryset.filter(country__id=country)
            
        return queryset

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
    permission_classes = [AllowAny]

    def get(self, request):
        # Verificar si el usuario está autenticado mediante el token
        if request.user.is_authenticated:
            return Response({
                'user_id': request.user.id,
                'username': request.user.username,
                'email': request.user.email
            })
        return Response(
            {'error': 'Usuario no autenticado'},
            status=status.HTTP_401_UNAUTHORIZED
        )

    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        
        if not username or not password:
            return Response(
                {'error': 'Por favor proporcione usuario y contraseña'},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        user = authenticate(username=username, password=password)
        
        if user:
            token, _ = Token.objects.get_or_create(user=user)
            return Response({
                'token': token.key,
                'user_id': user.id,
                'username': user.username,
                'email': user.email
            })
            
        return Response(
            {'error': 'Credenciales inválidas'},
            status=status.HTTP_401_UNAUTHORIZED
        )

    def put(self, request):
        # Actualizar datos del usuario
        if request.user.is_authenticated:
            user = request.user
            username = request.data.get('username')
            email = request.data.get('email')
            
            if username:
                user.username = username
            if email:
                user.email = email
                
            try:
                user.save()
                return Response({
                    'user_id': user.id,
                    'username': user.username,
                    'email': user.email
                })
            except Exception as e:
                return Response(
                    {'error': str(e)},
                    status=status.HTTP_400_BAD_REQUEST
                )
                
        return Response(
            {'error': 'Usuario no autenticado'},
            status=status.HTTP_401_UNAUTHORIZED
        )

    def delete(self, request):
        # Eliminar usuario
        if request.user.is_authenticated:
            try:
                request.user.delete()
                return Response(
                    {'message': 'Usuario eliminado correctamente'},
                    status=status.HTTP_204_NO_CONTENT
                )
            except Exception as e:
                return Response(
                    {'error': str(e)},
                    status=status.HTTP_400_BAD_REQUEST
                )
                
        return Response(
            {'error': 'Usuario no autenticado'},
            status=status.HTTP_401_UNAUTHORIZED
        )

class RegisterView(APIView):
    permission_classes = [AllowAny]  # Asegúrate de que esta línea esté presente
 
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
            'order',
            'item_type',  # Añadimos el campo item_type aquí
            'custom_url'  # También incluimos custom_url para elementos de tipo banner
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