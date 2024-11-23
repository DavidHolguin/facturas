from django.contrib import admin
from django.utils.html import format_html
from .models import Company, Category, Product

@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'phone', 'nit', 'display_profile_picture')
    list_filter = ('user',)
    search_fields = ('name', 'description', 'nit', 'phone')
    readonly_fields = ('display_profile_picture', 'display_cover_photo')
    fieldsets = (
        ('Información Básica', {
            'fields': ('user', 'name', 'description', 'nit')
        }),
        ('Contacto', {
            'fields': ('phone', 'address')
        }),
        ('Imágenes', {
            'fields': ('profile_picture', 'display_profile_picture', 
                      'cover_photo', 'display_cover_photo'),
        }),
    )

    def display_profile_picture(self, obj):
        if obj.profile_picture:
            return format_html('<img src="{}" width="50" height="50" />', obj.profile_picture.url)
        return "Sin imagen"
    display_profile_picture.short_description = 'Imagen de Perfil'

    def display_cover_photo(self, obj):
        if obj.cover_photo:
            return format_html('<img src="{}" width="100" height="50" />', obj.cover_photo.url)
        return "Sin imagen"
    display_cover_photo.short_description = 'Foto de Portada'

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'category_type')
    list_filter = ('category_type',)
    search_fields = ('name',)

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'company', 'category', 'display_price', 'display_image')
    list_filter = ('company', 'category', 'is_weight_based')
    search_fields = ('name', 'description', 'company__name')
    readonly_fields = ('display_image',)
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('company', 'category', 'name', 'description')
        }),
        ('Precios', {
            'fields': (
                'price',
                'is_weight_based',
                ('base_weight', 'weight_unit'),
            ),
            'description': 'Configure el precio base y, si aplica, la información de precio por peso'
        }),
        ('Imagen', {
            'fields': ('image', 'display_image'),
        }),
    )

    def display_price(self, obj):
        if obj.is_weight_based and obj.base_weight:
            return f"${obj.price} por {obj.base_weight}{obj.get_weight_unit_display()}"
        return f"${obj.price}"
    display_price.short_description = 'Precio'

    def display_image(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="50" height="50" />', obj.image.url)
        return "Sin imagen"
    display_image.short_description = 'Imagen'

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        if 'base_weight' in form.base_fields:
            form.base_fields['base_weight'].help_text = 'Peso base para el cálculo del precio (ej: 500 para 500g)'
        return form