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
    company_name = serializers.SerializerMethodField()
    company_logo = serializers.SerializerMethodField()
    company_profile_url = serializers.SerializerMethodField()
    featured_image = serializers.SerializerMethodField()
    click_url = serializers.SerializerMethodField()

    class Meta:
        model = TopBurgerItem
        fields = [
            'company_name',
            'company_logo',
            'company_profile_url',
            'featured_image',
            'order',
            'item_type',
            'click_url'
        ]

    def get_company_name(self, obj):
        return obj.company.name if obj.company and obj.item_type == 'COMPANY' else ""

    def get_company_logo(self, obj):
        if obj.company and obj.company.profile_picture and obj.item_type == 'COMPANY':
            return self.context['request'].build_absolute_uri(obj.company.profile_picture.url)
        return ""

    def get_company_profile_url(self, obj):
        if obj.company and obj.item_type == 'COMPANY':
            return f"/company/{obj.company.id}"
        return ""

    def get_featured_image(self, obj):
        if obj.featured_image:
            return self.context['request'].build_absolute_uri(obj.featured_image.url)
        return ""

    def get_click_url(self, obj):
        if obj.item_type == 'BANNER':
            return obj.custom_url
        return obj.company_profile_url if obj.company else ""

class TopBurgerSectionSerializer(serializers.ModelSerializer):
    items = TopBurgerItemSerializer(many=True, read_only=True)

    class Meta:
        model = TopBurgerSection
        fields = ['id', 'title', 'location', 'position', 'items']
