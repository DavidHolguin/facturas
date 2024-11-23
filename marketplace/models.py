# models.py
from django.db import models
from django.contrib.auth.models import User
from cloudinary.models import CloudinaryField

class Company(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    description = models.TextField()
    nit = models.CharField(max_length=20, null=True, blank=True, help_text="Número de Identificación Tributaria")
    profile_picture = CloudinaryField(
        'image',
        folder='company_profiles/',
        help_text="Imagen de perfil de la compañía"
    )
    cover_photo = CloudinaryField(
        'image',
        folder='company_covers/',
        help_text="Foto de portada de la compañía"
    )
    phone = models.CharField(max_length=20)
    address = models.TextField()

    def __str__(self):
        return self.name

class Category(models.Model):
    CATEGORY_TYPES = [
        ('SERVICIOS', 'Categoría Servicios'),
        ('PRODUCTOS', 'Categoría Productos'),
    ]

    name = models.CharField(max_length=50)
    category_type = models.CharField(max_length=20, choices=CATEGORY_TYPES, null=True, blank=True)

    def __str__(self):
        return f"{self.name} - {self.get_category_type_display() if self.category_type else 'Sin tipo'}"

class Product(models.Model):
    WEIGHT_UNIT_CHOICES = [
        ('g', 'Gramos'),
        ('kg', 'Kilogramos'),
    ]

    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    category = models.ForeignKey('Category', on_delete=models.SET_NULL, null=True)
    name = models.CharField(max_length=100)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    # Nuevos campos para el precio basado en peso
    is_weight_based = models.BooleanField(default=False)
    base_weight = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, 
                                    help_text="Peso base para el precio (ej: 500 para 500g)")
    weight_unit = models.CharField(max_length=2, choices=WEIGHT_UNIT_CHOICES, default='g',
                                 null=True, blank=True)
    image = CloudinaryField(
        'image',
        folder='products/',
        help_text="Imagen del producto"
    )

    def get_price_for_weight(self, weight):
        """Calcula el precio para un peso específico"""
        if not self.is_weight_based or not self.base_weight:
            return self.price
        
        weight_ratio = weight / self.base_weight
        return self.price * weight_ratio

    def __str__(self):
        return self.name