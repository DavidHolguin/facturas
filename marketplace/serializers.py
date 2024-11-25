from rest_framework import serializers
from .models import Company, Category, Product, BusinessHours, Promotion

class BusinessHoursSerializer(serializers.ModelSerializer):
    day_name = serializers.SerializerMethodField()

    class Meta:
        model = BusinessHours
        fields = ['id', 'day', 'day_name', 'opening_time', 'closing_time', 'is_closed']

    def get_day_name(self, obj):
        return dict(BusinessHours.DAYS_OF_WEEK)[obj.day]

class PromotionSerializer(serializers.ModelSerializer):
    discount_type_display = serializers.CharField(source='get_discount_type_display', read_only=True)

    class Meta:
        model = Promotion
        fields = [
            'id',
            'name',
            'description',
            'discount_type',
            'discount_type_display',
            'discount_value',
            'start_date',
            'end_date',
            'terms_conditions',
            'is_active'
        ]

class CategorySerializer(serializers.ModelSerializer):
    category_type_display = serializers.CharField(source='get_category_type_display', read_only=True)

    class Meta:
        model = Category
        fields = ['id', 'name', 'category_type', 'category_type_display']

class CompanySerializer(serializers.ModelSerializer):
    profile_picture_url = serializers.SerializerMethodField()
    cover_photo_url = serializers.SerializerMethodField()
    business_hours = BusinessHoursSerializer(many=True, read_only=True)
    
    class Meta:
        model = Company
        fields = [
            'id', 
            'user',
            'name', 
            'description',
            'nit',
            'phone',
            'whatsapp',
            'email',
            'address',
            'google_maps_link',
            'latitude',
            'longitude',
            'profile_picture_url',
            'cover_photo_url',
            'business_hours'
        ]

    def get_profile_picture_url(self, obj):
        if obj.profile_picture:
            return obj.profile_picture.url
        return None

    def get_cover_photo_url(self, obj):
        if obj.cover_photo:
            return obj.cover_photo.url
        return None

class ProductSerializer(serializers.ModelSerializer):
    main_image_url = serializers.SerializerMethodField()
    additional_images_url = serializers.SerializerMethodField()
    company_name = serializers.SerializerMethodField()
    categories = CategorySerializer(many=True, read_only=True)
    promotion = PromotionSerializer(read_only=True)
    discounted_price = serializers.SerializerMethodField()
    
    class Meta:
        model = Product
        fields = [
            'id',
            'company',
            'company_name',
            'categories',
            'name',
            'description',
            'price',
            'promotion',
            'discounted_price',
            'main_image_url',
            'additional_images_url'
        ]

    def get_main_image_url(self, obj):
        if obj.main_image:
            return obj.main_image.url
        return None

    def get_additional_images_url(self, obj):
        if obj.additional_images:
            return obj.additional_images.url
        return None

    def get_company_name(self, obj):
        return obj.company.name if obj.company else None

    def get_discounted_price(self, obj):
        return obj.get_discounted_price()

# Serializer para creación/actualización de productos
class ProductWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = [
            'company',
            'categories',
            'name',
            'description',
            'price',
            'promotion',
            'main_image',
            'additional_images'
        ]

    def validate_price(self, value):
        if value <= 0:
            raise serializers.ValidationError("El precio debe ser mayor que 0.")
        return value

    def validate_promotion(self, value):
        if value and not value.is_active:
            raise serializers.ValidationError("La promoción seleccionada no está activa.")
        return value