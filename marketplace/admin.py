from django.contrib import admin
from django.utils.html import format_html
from .models import Company, Category, Product

@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ['name', 'user', 'phone', 'preview_images']
    list_filter = ['user']
    search_fields = ['name', 'description', 'address']
    readonly_fields = ['preview_images']
    fieldsets = (
        ('Información Básica', {
            'fields': ('user', 'name', 'description')
        }),
        ('Imágenes', {
            'fields': ('profile_picture', 'cover_photo', 'preview_images'),
        }),
        ('Contacto', {
            'fields': ('phone', 'address'),
        }),
    )

    def preview_images(self, obj):
        """Vista previa de las imágenes de perfil y portada."""
        html = ""
        if obj.profile_picture:
            html += f'<img src="{obj.profile_picture.url}" style="max-height: 100px; margin-right: 10px;"/>'
        if obj.cover_photo:
            html += f'<img src="{obj.cover_photo.url}" style="max-height: 100px;"/>'
        return format_html(html) if html else "Sin imágenes"
    
    preview_images.short_description = "Vista previa de imágenes"

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'category_type']
    list_filter = ['category_type']
    search_fields = ['name']
    fieldsets = (
        (None, {
            'fields': ('name', 'category_type')
        }),
    )

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'company', 'category', 'price', 'preview_image']
    list_filter = ['company', 'category']
    search_fields = ['name', 'description', 'company__name']
    readonly_fields = ['preview_image']
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('company', 'category', 'name', 'description')
        }),
        ('Precio', {
            'fields': ('price',),
        }),
        ('Imagen', {
            'fields': ('image', 'preview_image'),
        }),
    )

    def preview_image(self, obj):
        """Vista previa de la imagen del producto."""
        if obj.image:
            return format_html(
                '<img src="{}" style="max-height: 100px;"/>',
                obj.image.url
            )
        return "Sin imagen"
    
    preview_image.short_description = "Vista previa"

