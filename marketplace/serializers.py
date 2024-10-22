from rest_framework import serializers
from .models import Company, Category, Product, Order, OrderItem, CompanyCategory, Country, TopBurgerSection, Promotion, TopBurgerItem
from .models import BusinessHours
from django.db import transaction
from django.utils import timezone
from django.db.models import Q



class BusinessHoursSerializer(serializers.ModelSerializer):
    class Meta:
        model = BusinessHours
        exclude = ('id', 'company')

    def to_representation(self, instance):
        data = super().to_representation(instance)
        formatted_hours = {}
        days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
        
        for day in days:
            open_time = data.get(f'{day}_open')
            close_time = data.get(f'{day}_close')
            if open_time and close_time:
                formatted_hours[day] = {
                    'open': open_time,
                    'close': close_time
                }
            else:
                formatted_hours[day] = None
                
        return formatted_hours


class CompanyCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = CompanyCategory
        fields = ['id', 'name', 'description']


class CountrySerializer(serializers.ModelSerializer):
    flag_emoji = serializers.SerializerMethodField()
    flag_icon_url = serializers.SerializerMethodField()

    class Meta:
        model = Country
        fields = ['id', 'name', 'code', 'flag_emoji', 'flag_icon_url']

    def get_flag_emoji(self, obj):
        return obj.get_flag_emoji()

    def get_flag_icon_url(self, obj):
        if obj.flag_icon:
            return obj.flag_icon.url
        return None


class PromotionSerializer(serializers.ModelSerializer):
    banner_url = serializers.SerializerMethodField()
    company_name = serializers.SerializerMethodField()
    product_name = serializers.SerializerMethodField()
    category_name = serializers.SerializerMethodField()
    discount_display = serializers.SerializerMethodField()

    class Meta:
        model = Promotion
        fields = [
            'id',
            'company',
            'company_name',
            'product',
            'product_name',
            'category',
            'category_name',
            'title',
            'description',
            'terms_conditions',
            'discount_type',
            'discount_value',
            'discount_display',
            'banner_url',
            'start_date',
            'end_date',
            'is_active',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']

    def get_banner_url(self, obj):
        if obj.banner:
            return obj.banner.url
        return None

    def get_company_name(self, obj):
        return obj.company.name if obj.company else None

    def get_product_name(self, obj):
        return obj.product.name if obj.product else None

    def get_category_name(self, obj):
        return obj.category.name if obj.category else None

    def get_discount_display(self, obj):
        if obj.discount_type == 'PERCENTAGE':
            return f"{obj.discount_value}%"
        return f"${obj.discount_value}"

    def validate(self, data):
        # Convertir el valor del descuento a entero si está presente
        if 'discount_value' in data:
            try:
                data['discount_value'] = int(round(float(data['discount_value'])))
            except (TypeError, ValueError):
                raise serializers.ValidationError({
                    'discount_value': 'El valor del descuento debe ser un número válido'
                })

        # Validar que el producto pertenezca a la compañía
        if 'product' in data and data.get('product') and data.get('company'):
            if data['product'].company != data['company']:
                raise serializers.ValidationError({
                    'product': 'El producto debe pertenecer a la compañía seleccionada'
                })

        # Validar el porcentaje máximo
        if data.get('discount_type') == 'PERCENTAGE' and data.get('discount_value', 0) > 100:
            raise serializers.ValidationError({
                'discount_value': 'El porcentaje de descuento no puede ser mayor a 100%'
                })

        # Validar las fechas
        if data.get('end_date') and data.get('start_date'):
            if data['end_date'] <= data['start_date']:
                raise serializers.ValidationError({
                    'end_date': 'La fecha de finalización debe ser posterior a la fecha de inicio'
                })

        return data

    def create(self, validated_data):
        # Asegurar que el valor del descuento sea entero
        if 'discount_value' in validated_data:
            validated_data['discount_value'] = int(round(float(validated_data['discount_value'])))
        return super().create(validated_data)

    def update(self, instance, validated_data):
        # Asegurar que el valor del descuento sea entero
        if 'discount_value' in validated_data:
            validated_data['discount_value'] = int(round(float(validated_data['discount_value'])))
        return super().update(instance, validated_data)

class CompanySerializer(serializers.ModelSerializer):
    profile_picture_url = serializers.SerializerMethodField()
    cover_photo_url = serializers.SerializerMethodField()
    category = CompanyCategorySerializer(read_only=False, required=False)
    country = CountrySerializer(read_only=False, required=False)
    business_hours = BusinessHoursSerializer(read_only=False, required=False)
    active_promotions = serializers.SerializerMethodField()

    class Meta:
        model = Company
        fields = '__all__'

    def get_profile_picture_url(self, obj):
        if obj.profile_picture:
            return obj.profile_picture.url
        return None

    def get_cover_photo_url(self, obj):
        if obj.cover_photo:
            return obj.cover_photo.url
        return None

    def get_active_promotions(self, obj):
        promotions = obj.promotions.filter(is_active=True)
        return PromotionSerializer(promotions, many=True).data

    @transaction.atomic
    def create(self, validated_data):
        try:
            category_data = validated_data.pop('category', None)
            country_data = validated_data.pop('country', None)
            business_hours_data = validated_data.pop('business_hours', None)
            
            if category_data:
                category, _ = CompanyCategory.objects.get_or_create(**category_data)
                validated_data['category'] = category
                
            if country_data:
                country, _ = Country.objects.get_or_create(**country_data)
                validated_data['country'] = country
            
            company = Company.objects.create(**validated_data)
            
            if business_hours_data:
                BusinessHours.objects.create(company=company, **business_hours_data)
            
            return company
        except Exception as e:
            raise serializers.ValidationError(f"Error creating company: {str(e)}")

    @transaction.atomic
    def update(self, instance, validated_data):
        try:
            category_data = validated_data.pop('category', None)
            country_data = validated_data.pop('country', None)
            business_hours_data = validated_data.pop('business_hours', None)
            
            if category_data:
                category, _ = CompanyCategory.objects.get_or_create(**category_data)
                validated_data['category'] = category
                
            if country_data:
                country, _ = Country.objects.get_or_create(**country_data)
                validated_data['country'] = country
            
            if business_hours_data:
                business_hours, created = BusinessHours.objects.get_or_create(company=instance)
                for attr, value in business_hours_data.items():
                    setattr(business_hours, attr, value)
                business_hours.save()
            
            for attr, value in validated_data.items():
                setattr(instance, attr, value)
            instance.save()
            
            return instance
        except Exception as e:
            raise serializers.ValidationError(f"Error updating company: {str(e)}")


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'


class ProductSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()
    active_promotions = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = '__all__'

    def get_image_url(self, obj):
        if obj.image:
            return obj.image.url
        return None

    def get_active_promotions(self, obj):
        now = timezone.now()
        promotions = Promotion.objects.filter(
            product=obj,
            is_active=True,
            start_date__lte=now
        ).filter(
            Q(end_date__gte=now) | Q(end_date__isnull=True)
        )
        return PromotionSerializer(promotions, many=True, context=self.context).data



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
