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
import boto3
from django.conf import settings
from botocore.config import Config
from rest_framework.decorators import action
from django.core.exceptions import ValidationError
import urllib.parse

class S3Helper:
    def __init__(self):
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_S3_REGION_NAME,
            config=Config(signature_version='s3v4')
        )
        self.bucket_name = settings.AWS_STORAGE_BUCKET_NAME

    def generate_presigned_url(self, object_key, expiration=3600):
        try:
            # Decodificar la URL por si viene codificada
            object_key = urllib.parse.unquote(object_key)
            # Eliminar el nombre del bucket y cualquier prefijo de la URL si existe
            object_key = object_key.replace(f'{self.bucket_name}.s3.amazonaws.com/', '')
            object_key = object_key.replace('media/', '')
            
            url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': self.bucket_name,
                    'Key': object_key
                },
                ExpiresIn=expiration
            )
            return url
        except Exception as e:
            print(f"Error generating presigned URL: {str(e)}")
            return None

class CompanyViewSet(viewsets.ModelViewSet):
    queryset = Company.objects.all()
    serializer_class = CompanySerializer
    permission_classes = [AllowAny]

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

    @action(detail=False, methods=['get'], url_path='get-presigned-url')
    def get_presigned_url(self, request):
        object_key = request.query_params.get('key')
        if not object_key:
            return Response({'error': 'No key provided'}, status=400)
        
        s3_helper = S3Helper()
        presigned_url = s3_helper.generate_presigned_url(object_key)
        
        if presigned_url:
            return Response({'url': presigned_url})
        return Response({'error': 'Failed to generate URL'}, status=500)

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

    @action(detail=False, methods=['get'], url_path='get-presigned-url')
    def get_presigned_url(self, request):
        object_key = request.query_params.get('key')
        if not object_key:
            return Response({'error': 'No key provided'}, status=400)
        
        s3_helper = S3Helper()
        presigned_url = s3_helper.generate_presigned_url(object_key)
        
        if presigned_url:
            return Response({'url': presigned_url})
        return Response({'error': 'Failed to generate URL'}, status=500)

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