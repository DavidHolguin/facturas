from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token  # Añade esta línea
from rest_framework import serializers, viewsets, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly, AllowAny
from rest_framework.decorators import action
from django.contrib.auth import authenticate
from django.shortcuts import get_object_or_404
from .models import Company, Category, Product, Order, OrderItem, BusinessHours, CompanyCategory, Country, TopBurgerSection, TopBurgerItem
from .serializers import OrderSerializer, OrderItemSerializer, CompanyCategorySerializer, CountrySerializer, \
    CompanySerializer, CategorySerializer, ProductSerializer, TopBurgerSectionSerializer, TopBurgerItemSerializer

import logging

logger = logging.getLogger(__name__)

class CompanyCategoryViewSet(viewsets.ModelViewSet):
    queryset = CompanyCategory.objects.all()
    serializer_class = CompanyCategorySerializer
    permission_classes = [AllowAny]

class CountryViewSet(viewsets.ModelViewSet):
    queryset = Country.objects.all()
    serializer_class = CountrySerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    @action(detail=False, methods=['get'])
    def available_countries(self, request):
        try:
            countries = [
                {
                    'code': code,
                    'name': name.split(maxsplit=1)[1],
                    'flag_emoji': name.split()[0]
                }
                for code, name in Country.COUNTRY_CHOICES
            ]
            return Response(countries)
        except Exception as e:
            logger.error(f"Error in available_countries: {str(e)}")
            return Response({'error': 'An unexpected error occurred'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def create(self, request, *args, **kwargs):
        code = request.data.get('code')
        if code not in dict(Country.COUNTRY_CHOICES):
            return Response(
                {'error': 'Invalid country code. Must be one of the available countries.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        return super().create(request, *args, **kwargs)

class CompanyViewSet(viewsets.ModelViewSet):
    queryset = Company.objects.all()
    serializer_class = CompanySerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        queryset = Company.objects.prefetch_related(
            'business_hours',
            'category',
            'country'
        )
        category = self.request.query_params.get('category', None)
        country = self.request.query_params.get('country', None)
        
        if category is not None:
            queryset = queryset.filter(category__id=category)
        if country is not None:
            queryset = queryset.filter(country__id=country)
           
        return queryset

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

    def perform_create(self, serializer):
        company = serializer.save()
        self._handle_business_hours(company, self.request.data.get('business_hours', {}))
        return company

    def perform_update(self, serializer):
        company = serializer.save()
        self._handle_business_hours(company, self.request.data.get('business_hours', {}))
        return company

    def _handle_business_hours(self, company, business_hours_data):
        if not business_hours_data:
            return

        business_hours, created = BusinessHours.objects.get_or_create(
            company=company,
            defaults={
                'open_days': business_hours_data.get('open_days', []),
                'open_time': business_hours_data.get('open_time'),
                'close_time': business_hours_data.get('close_time')
            }
        )

        if not created:
            business_hours.open_days = business_hours_data.get('open_days', business_hours.open_days)
            business_hours.open_time = business_hours_data.get('open_time', business_hours.open_time)
            business_hours.close_time = business_hours_data.get('close_time', business_hours.close_time)
            business_hours.save()

    def create(self, request, *args, **kwargs):
        try:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            company = self.perform_create(serializer)
            headers = self.get_success_headers(serializer.data)
            return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
        except Exception as e:
            logger.error(f"Error creating company: {str(e)}")
            return Response({'error': 'An error occurred while creating the company'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def update(self, request, *args, **kwargs):
        try:
            partial = kwargs.pop('partial', False)
            instance = self.get_object()
            serializer = self.get_serializer(instance, data=request.data, partial=partial)
            serializer.is_valid(raise_exception=True)
            self.perform_update(serializer)

            if getattr(instance, '_prefetched_objects_cache', None):
                instance._prefetched_objects_cache = {}

            return Response(serializer.data)
        except Exception as e:
            logger.error(f"Error updating company: {str(e)}")
            return Response({'error': 'An error occurred while updating the company'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def retrieve(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            serializer = self.get_serializer(instance)
            return Response(serializer.data)
        except Company.DoesNotExist:
            return Response({'error': 'Company not found'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error retrieving company: {str(e)}", exc_info=True)
            return Response({'error': 'An unexpected error occurred'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
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

    def create(self, request):
        try:
            data = request.data
            user = request.user
            company_id = data.get('company')
            items = data.get('items', [])

            if not company_id or not items:
                return Response({"error": "Incomplete order data"}, status=status.HTTP_400_BAD_REQUEST)

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
        except Exception as e:
            logger.error(f"Error creating order: {str(e)}")
            return Response({'error': 'An error occurred while creating the order'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def get_queryset(self):
        user = self.request.user
        return Order.objects.filter(user=user)

class SearchView(APIView):
    def get(self, request):
        try:
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
        except Exception as e:
            logger.error(f"Error in search: {str(e)}")
            return Response({'error': 'An error occurred during search'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class LoginView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        if request.user.is_authenticated:
            return Response({
                'user_id': request.user.id,
                'username': request.user.username,
                'email': request.user.email
            })
        return Response(
            {'error': 'User not authenticated'},
            status=status.HTTP_401_UNAUTHORIZED
        )

    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        
        if not username or not password:
            return Response(
                {'error': 'Please provide both username and password'},
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
            {'error': 'Invalid credentials'},
            status=status.HTTP_401_UNAUTHORIZED
        )

    def put(self, request):
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
            {'error': 'User not authenticated'},
            status=status.HTTP_401_UNAUTHORIZED
        )

    def delete(self, request):
        if request.user.is_authenticated:
            try:
                request.user.delete()
                return Response(
                    {'message': 'User deleted successfully'},
                    status=status.HTTP_204_NO_CONTENT
                )
            except Exception as e:
                return Response(
                    {'error': str(e)},
                    status=status.HTTP_400_BAD_ERROR
                )
                
        return Response(
            {'error': 'User not authenticated'},
            status=status.HTTP_401_UNAUTHORIZED
        )

class RegisterView(APIView):
    permission_classes = [AllowAny]
 
    def post(self, request):
        try:
            username = request.data.get('username')
            email = request.data.get('email')
            password = request.data.get('password')
            if User.objects.filter(username=username).exists():
                return Response({'error': 'Username already exists'}, status=status.HTTP_400_BAD_REQUEST)
            user = User.objects.create_user(username=username, email=email, password=password)
            return Response({'message': 'User created successfully'}, status=status.HTTP_201_CREATED)
        except Exception as e:
            logger.error(f"Error in user registration: {str(e)}")
            return Response({'error': 'An error occurred during registration'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class TopBurgerSectionView(APIView):
    permission_classes = [AllowAny]
    
    def get(self, request):
        try:
            sections = TopBurgerSection.objects.all().order_by('position')
            serializer = TopBurgerSectionSerializer(
                sections, 
                many=True,
                context={'request': request}
            )
            return Response(serializer.data)
        except Exception as e:
            logger.error(f"Error in TopBurgerSectionView: {str(e)}")
            return Response({
                "error": "An error occurred while fetching top burger sections"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

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
            'item_type',
            'custom_url'
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
        representation = super().to_representation(instance)
        if not representation.get('items'):
            representation['items'] = []
        return representation