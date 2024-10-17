from rest_framework import viewsets
from .models import Company, Category, Product, Order
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly, AllowAny
from .models import Order, OrderItem
from .serializers import OrderSerializer, OrderItemSerializer, CompanySerializer, CategorySerializer, ProductSerializer
from django.conf import settings
from rest_framework.decorators import action
from django.core.exceptions import ValidationError
from .models import TopBurgerSection, TopBurgerItem
from .serializers import TopBurgerSectionSerializer
from django.shortcuts import get_object_or_404

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
    
class TopBurgerSectionView(APIView):
    permission_classes = [AllowAny]
    
    def get(self, request):
        try:
            # Obtener la primera sección o crearla si no existe
            section, created = TopBurgerSection.objects.get_or_create(
                defaults={
                    'title': "TOP 3 BURGUERS",
                    'location': "en San Jose"
                }
            )
            
            # Usar el serializer con los items relacionados
            serializer = TopBurgerSectionSerializer(section)
            return Response(serializer.data)
            
        except Exception as e:
            return Response(
                {"error": f"Error al obtener los datos: {str(e)}"}, 
                status=500
            )

# Vista adicional para manejar los items individualmente
class TopBurgerItemView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        try:
            section = TopBurgerSection.objects.first()
            if not section:
                section = TopBurgerSection.objects.create()

            # Crear un nuevo item
            TopBurgerItem.objects.create(
                section=section,
                company_id=request.data.get('company_id'),
                order=request.data.get('order'),
                featured_image=request.data.get('featured_image')
            )
            
            # Devolver la sección actualizada
            serializer = TopBurgerSectionSerializer(section)
            return Response(serializer.data, status=201)
            
        except Exception as e:
            return Response(
                {"error": f"Error al crear el item: {str(e)}"}, 
                status=400
            )