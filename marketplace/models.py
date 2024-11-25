# models.py
from django.db import models
from django.contrib.auth.models import User
from cloudinary.models import CloudinaryField
from django.core.validators import MinValueValidator, MaxValueValidator

class BusinessHours(models.Model):
    DAYS_OF_WEEK = [
        (0, 'Lunes'),
        (1, 'Martes'),
        (2, 'Miércoles'),
        (3, 'Jueves'),
        (4, 'Viernes'),
        (5, 'Sábado'),
        (6, 'Domingo'),
    ]
    
    company = models.ForeignKey('Company', on_delete=models.CASCADE, related_name='business_hours')
    day = models.IntegerField(choices=DAYS_OF_WEEK)
    opening_time = models.TimeField()
    closing_time = models.TimeField()
    is_closed = models.BooleanField(default=False)

    class Meta:
        unique_together = ['company', 'day']
        ordering = ['day']

class Company(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    description = models.TextField()
    nit = models.CharField(max_length=20, null=True, blank=True, help_text="Número de Identificación Tributaria")
    
    # Campos de contacto y ubicación
    phone = models.CharField(max_length=20)
    whatsapp = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    address = models.TextField()
    google_maps_link = models.URLField(blank=True, null=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    
    # Imágenes
    profile_picture = CloudinaryField(
        'image',
        folder='company_profiles/',
        null=True,
        blank=True,
        help_text="Imagen de perfil de la compañía"
    )
    cover_photo = CloudinaryField(
        'image',
        folder='company_covers/',
        null=True,
        blank=True,
        help_text="Foto de portada de la compañía"
    )

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

class Promotion(models.Model):
    DISCOUNT_TYPE_CHOICES = [
        ('PERCENTAGE', 'Porcentaje'),
        ('AMOUNT', 'Monto Fijo'),
    ]

    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    discount_type = models.CharField(max_length=10, choices=DISCOUNT_TYPE_CHOICES)
    discount_value = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    terms_conditions = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} ({self.get_discount_type_display()})"

class Product(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    categories = models.ManyToManyField(Category, related_name='products')
    name = models.CharField(max_length=100)
    description = models.TextField()
    price = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        help_text="Precio en COP"
    )
    promotion = models.ForeignKey(
        Promotion, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='products'
    )
    
    # Imágenes del producto
    main_image = CloudinaryField(
        'image',
        folder='products/main/',
        null=True,
        blank=True,
        help_text="Imagen principal del producto"
    )
    additional_images = CloudinaryField(
        'image',
        folder='products/additional/',
        null=True,
        blank=True,
        help_text="Imágenes adicionales del producto"
    )

    def get_discounted_price(self):
        if not self.promotion or not self.promotion.is_active:
            return self.price
            
        if self.promotion.discount_type == 'PERCENTAGE':
            discount = self.price * (self.promotion.discount_value / 100)
        else:  # AMOUNT
            discount = self.promotion.discount_value
            
        return max(self.price - discount, 0)

    def __str__(self):
        return self.name