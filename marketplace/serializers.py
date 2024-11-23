# serializers.py
from rest_framework import serializers
from .models import Company, Category, Product

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'category_type']

class CompanySerializer(serializers.ModelSerializer):
    profile_picture_url = serializers.SerializerMethodField()
    cover_photo_url = serializers.SerializerMethodField()

    class Meta:
        model = Company
        fields = [
            'id', 
            'user',
            'name', 
            'description',
            'nit',
            'profile_picture_url',
            'cover_photo_url',
            'phone',
            'address'
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
    image_url = serializers.SerializerMethodField()
    company_name = serializers.SerializerMethodField()
    category_name = serializers.SerializerMethodField()
    formatted_price = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            'id',
            'company',
            'company_name',
            'category',
            'category_name',
            'name',
            'description',
            'price',
            'is_weight_based',
            'base_weight',
            'weight_unit',
            'image_url',
            'formatted_price'
        ]

    def get_image_url(self, obj):
        if obj.image:
            return obj.image.url
        return None

    def get_company_name(self, obj):
        return obj.company.name if obj.company else None

    def get_category_name(self, obj):
        return obj.category.name if obj.category else None

    def get_formatted_price(self, obj):
        if obj.is_weight_based and obj.base_weight:
            return f"${obj.price} por {obj.base_weight}{obj.weight_unit}"
        return f"${obj.price}"