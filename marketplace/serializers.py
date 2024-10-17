from rest_framework import serializers
from .models import Company, Category, Product, Order, OrderItem, TopBurgerSection, TopBurgerItem


class CompanySerializer(serializers.ModelSerializer):
    profile_picture_url = serializers.SerializerMethodField()
    cover_photo_url = serializers.SerializerMethodField()

    class Meta:
        model = Company
        fields = '__all__'

    def get_profile_picture_url(self, obj):
        if obj.profile_picture:
            return obj.profile_picture.url  # Cambiado para usar Cloudinary
        return None

    def get_cover_photo_url(self, obj):
        if obj.cover_photo:
            return obj.cover_photo.url  # Cambiado para usar Cloudinary
        return None

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'

class ProductSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = '__all__'

    def get_image_url(self, obj):
        if obj.image:
            return obj.image.url  # Cambiado para usar Cloudinary
        return None

class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = '__all__'

class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = '__all__'

class TopBurgerItemSerializer(serializers.ModelSerializer):
    company_name = serializers.CharField(source='company.name')
    company_logo = serializers.ImageField(source='company.logo')
    company_profile_url = serializers.CharField(source='company.profile_url')

    class Meta:
        model = TopBurgerItem
        fields = ['company_name', 'company_logo', 'company_profile_url', 'featured_image', 'order']

class TopBurgerSectionSerializer(serializers.ModelSerializer):
    items = TopBurgerItemSerializer(many=True, read_only=True)

    class Meta:
        model = TopBurgerSection
        fields = ['title', 'location', 'items']