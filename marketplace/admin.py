# admin.py
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.db.models import Count
from .models import Company, Category, Product, Promotion, BusinessHours

class BusinessHoursInline(admin.TabularInline):
    model = BusinessHours
    extra = 7  # Para mostrar todos los días de la semana
    max_num = 7
    ordering = ['day']

@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'phone', 'email', 'show_profile_picture', 'total_products', 'is_currently_open')
    list_filter = ('user', 'business_hours__is_closed')
    search_fields = ('name', 'description', 'nit', 'phone', 'email', 'address')
    inlines = [BusinessHoursInline]
    readonly_fields = ('show_profile_picture', 'show_cover_photo')

    def show_profile_picture(self, obj):
        if obj.profile_picture:
            return format_html(
                '<img src="{}" width="50" height="50" style="border-radius: 50%;" />',
                obj.profile_picture.url
            )
        return "Sin imagen"
    show_profile_picture.short_description = "Foto de perfil"

    def show_cover_photo(self, obj):
        if obj.cover_photo:
            return format_html(
                '<img src="{}" width="300" height="100" style="object-fit: cover;" />',
                obj.cover_photo.url
            )
        return "Sin imagen de portada"
    show_cover_photo.short_description = "Foto de portada"

    def total_products(self, obj):
        return obj.product_set.count()
    total_products.short_description = "Total productos"

    def is_currently_open(self, obj):
        from django.utils import timezone
        current_time = timezone.localtime().time()
        current_day = timezone.localtime().weekday()
        is_open = obj.business_hours.filter(
            day=current_day,
            opening_time__lte=current_time,
            closing_time__gte=current_time,
            is_closed=False
        ).exists()
        return format_html(
            '<span style="color: {};">●</span> {}',
            'green' if is_open else 'red',
            'Abierto' if is_open else 'Cerrado'
        )
    is_currently_open.short_description = "Estado actual"

    fieldsets = (
        ('Información básica', {
            'fields': ('user', 'name', 'description', 'nit')
        }),
        ('Contacto', {
            'fields': ('phone', 'whatsapp', 'email')
        }),
        ('Ubicación', {
            'fields': ('address', 'google_maps_link', 'latitude', 'longitude')
        }),
        ('Imágenes', {
            'fields': ('profile_picture', 'show_profile_picture', 'cover_photo', 'show_cover_photo'),
            'classes': ('collapse',)
        })
    )

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'category_type', 'total_products')
    list_filter = ('category_type',)
    search_fields = ('name',)

    def total_products(self, obj):
        return obj.products.count()
    total_products.short_description = "Total productos"

@admin.register(Promotion)
class PromotionAdmin(admin.ModelAdmin):
    list_display = ('name', 'discount_type', 'discount_value', 'start_date', 'end_date', 
                   'is_active', 'total_products', 'is_current')
    list_filter = ('discount_type', 'is_active')
    search_fields = ('name', 'description')
    date_hierarchy = 'start_date'

    def total_products(self, obj):
        return obj.products.count()
    total_products.short_description = "Productos con promoción"

    def is_current(self, obj):
        from django.utils import timezone
        now = timezone.now()
        is_current = obj.start_date <= now <= obj.end_date and obj.is_active
        return format_html(
            '<span style="color: {};">●</span> {}',
            'green' if is_current else 'red',
            'Vigente' if is_current else 'No vigente'
        )
    is_current.short_description = "Estado actual"

    fieldsets = (
        ('Información básica', {
            'fields': ('name', 'description')
        }),
        ('Configuración del descuento', {
            'fields': ('discount_type', 'discount_value')
        }),
        ('Vigencia', {
            'fields': ('start_date', 'end_date', 'is_active')
        }),
        ('Términos y condiciones', {
            'fields': ('terms_conditions',),
            'classes': ('collapse',)
        })
    )

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'company', 'show_main_image', 'price', 'discounted_price_display', 
                   'show_categories', 'has_promotion')
    list_filter = ('company', 'categories', 'promotion__is_active')
    search_fields = ('name', 'description', 'company__name')
    filter_horizontal = ('categories',)
    readonly_fields = ('show_main_image', 'show_additional_images', 'discounted_price_display')
    
    def show_main_image(self, obj):
        if obj.main_image:
            return format_html(
                '<img src="{}" width="50" height="50" style="object-fit: cover;" />',
                obj.main_image.url
            )
        return "Sin imagen"
    show_main_image.short_description = "Imagen principal"

    def show_additional_images(self, obj):
        if obj.additional_images:
            return format_html(
                '<img src="{}" width="100" height="100" style="object-fit: cover;" />',
                obj.additional_images.url
            )
        return "Sin imágenes adicionales"
    show_additional_images.short_description = "Imágenes adicionales"

    def show_categories(self, obj):
        return ", ".join([cat.name for cat in obj.categories.all()])
    show_categories.short_description = "Categorías"

    def has_promotion(self, obj):
        has_active = bool(obj.promotion and obj.promotion.is_active)
        return format_html(
            '<span style="color: {};">●</span> {}',
            'green' if has_active else 'red',
            'Sí' if has_active else 'No'
        )
    has_promotion.short_description = "Promoción activa"

    def discounted_price_display(self, obj):
        original_price = obj.price
        discounted_price = obj.get_discounted_price()
        
        if original_price != discounted_price:
            return format_html(
                '<span style="text-decoration: line-through; color: #999;">COP ${}</span> '
                '<span style="color: #28a745; font-weight: bold;">COP ${}</span>',
                original_price, discounted_price
            )
        return f'COP ${original_price}'
    discounted_price_display.short_description = "Precio"

    fieldsets = (
        ('Información básica', {
            'fields': ('company', 'name', 'description', 'price')
        }),
        ('Categorización y promociones', {
            'fields': ('categories', 'promotion')
        }),
        ('Imágenes', {
            'fields': ('main_image', 'show_main_image', 'additional_images', 'show_additional_images'),
            'classes': ('collapse',)
        })
    )