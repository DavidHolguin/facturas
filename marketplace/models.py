from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MaxValueValidator, MinValueValidator
from cloudinary.models import CloudinaryField
from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError

class CompanyCategory(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Categoría de empresa"
        verbose_name_plural = "Categorías de empresas"

class Country(models.Model):
    COUNTRY_CHOICES = [
        ('AR', '🇦🇷 Argentina'),
        ('BO', '🇧🇴 Bolivia'),
        ('BR', '🇧🇷 Brasil'),
        ('CL', '🇨🇱 Chile'),
        ('CO', '🇨🇴 Colombia'),
        ('CR', '🇨🇷 Costa Rica'),
        ('CU', '🇨🇺 Cuba'),
        ('DO', '🇩🇴 República Dominicana'),
        ('EC', '🇪🇨 Ecuador'),
        ('SV', '🇸🇻 El Salvador'),
        ('GT', '🇬🇹 Guatemala'),
        ('HN', '🇭🇳 Honduras'),
        ('MX', '🇲🇽 México'),
        ('NI', '🇳🇮 Nicaragua'),
        ('PA', '🇵🇦 Panamá'),
        ('PY', '🇵🇾 Paraguay'),
        ('PE', '🇵🇪 Perú'),
        ('PR', '🇵🇷 Puerto Rico'),
        ('US', '🇺🇸 Estados Unidos'),
        ('UY', '🇺🇾 Uruguay'),
        ('VE', '🇻🇪 Venezuela'),
    ]

    name = models.CharField(max_length=100)
    code = models.CharField(
        max_length=2,
        choices=COUNTRY_CHOICES,
        unique=True,
        validators=[
            RegexValidator(
                regex='^[A-Z]{2}$',
                message='El código del país debe ser de 2 letras mayúsculas',
            ),
        ]
    )
    flag_icon = CloudinaryField(
        'image',
        folder='country_flags/',
        null=True,
        blank=True,
        help_text="Icono de la bandera del país (opcional)"
    )

    def get_flag_emoji(self):
        if self.code:
            return next((choice[1].split()[0] for choice in self.COUNTRY_CHOICES if choice[0] == self.code), '')
        return ''

    def __str__(self):
        return f"{self.get_flag_emoji()} {self.name}"

    class Meta:
        verbose_name = "País"
        verbose_name_plural = "Países"
        ordering = ['name']

class Company(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    category = models.ForeignKey(
        CompanyCategory, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='companies',
        verbose_name="Categoría"
    )
    country = models.ForeignKey(
        Country,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='companies',
        verbose_name="País"
    )
    name = models.CharField(max_length=100)
    description = models.TextField()
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
        ('EMPRESA', 'Categoría Empresa'),
        ('SERVICIOS', 'Categoría Servicios'),
        ('PRODUCTOS', 'Categoría Productos'),
        ('PAIS', 'Categoría País'),
    ]

    name = models.CharField(max_length=50)
    category_type = models.CharField(max_length=20, choices=CATEGORY_TYPES, null=True, blank=True)

    def __str__(self):
        return f"{self.name} - {self.get_category_type_display() if self.category_type else 'Sin tipo'}"

class Product(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    category = models.ForeignKey('Category', on_delete=models.SET_NULL, null=True)
    name = models.CharField(max_length=100)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    image = CloudinaryField(
        'image',
        folder='products/',
        help_text="Imagen del producto"
    )

    def __str__(self):
        return self.name

class Order(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    total = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"Order {self.id} - {self.user.username}"

class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.quantity} x {self.product.name}"
    
class TopBurgerSection(models.Model):
    title = models.CharField(max_length=100, default="TOP 3 BURGUERS")
    location = models.CharField(max_length=100, default="en San Jose")
    position = models.IntegerField(default=0, help_text="Orden de posición para mostrar secciones")
    
    class Meta:
        ordering = ['position']

    def __str__(self):
        return f"{self.title} {self.location}"

class TopBurgerItem(models.Model):
    ITEM_TYPE_CHOICES = [
        ('COMPANY', 'Company'),
        ('BANNER', 'Banner'),
    ]

    section = models.ForeignKey(
        TopBurgerSection, 
        related_name='items', 
        on_delete=models.CASCADE
    )
    company = models.ForeignKey(
        'Company', 
        on_delete=models.CASCADE,
        related_name='top_burger_items',
        null=True,
        blank=True
    )
    item_type = models.CharField(
        max_length=10,
        choices=ITEM_TYPE_CHOICES,
        default='COMPANY'
    )
    custom_url = models.URLField(
        max_length=255,
        null=True,
        blank=True,
        help_text="URL personalizada para elementos de banner"
    )
    order = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(3)],
        help_text="Posición en el top (1-3)"
    )
    featured_image = CloudinaryField(
        'image',
        folder='top_burgers/',
        help_text="Imagen destacada de la hamburguesa"
    )

    class Meta:
        ordering = ['order']
        unique_together = ['section', 'order']

    def __str__(self):
        if self.item_type == 'COMPANY':
            return f"{self.company.name if self.company else 'Sin compañía'} - Posición {self.order}"
        return f"Banner - Posición {self.order}"

class BusinessHours(models.Model):
    DAYS_OF_WEEK = [
        ('monday', 'Lunes'),
        ('tuesday', 'Martes'),
        ('wednesday', 'Miércoles'),
        ('thursday', 'Jueves'),
        ('friday', 'Viernes'),
        ('saturday', 'Sábado'),
        ('sunday', 'Domingo'),
    ]

    company = models.OneToOneField('Company', on_delete=models.CASCADE, related_name='business_hours')
    
    monday_open = models.TimeField(null=True, blank=True)
    monday_close = models.TimeField(null=True, blank=True)
    tuesday_open = models.TimeField(null=True, blank=True)
    tuesday_close = models.TimeField(null=True, blank=True)
    wednesday_open = models.TimeField(null=True, blank=True)
    wednesday_close = models.TimeField(null=True, blank=True)
    thursday_open = models.TimeField(null=True, blank=True)
    thursday_close = models.TimeField(null=True, blank=True)
    friday_open = models.TimeField(null=True, blank=True)
    friday_close = models.TimeField(null=True, blank=True)
    saturday_open = models.TimeField(null=True, blank=True)
    saturday_close = models.TimeField(null=True, blank=True)
    sunday_open = models.TimeField(null=True, blank=True)
    sunday_close = models.TimeField(null=True, blank=True)

    def clean(self):
        for day in [day[0] for day in self.DAYS_OF_WEEK]:
            open_time = getattr(self, f'{day}_open')
            close_time = getattr(self, f'{day}_close')
            if (open_time and not close_time) or (close_time and not open_time):
                raise ValidationError(f'{day.capitalize()}: Debe especificar tanto la hora de apertura como la de cierre.')
            if open_time and close_time and open_time >= close_time:
                raise ValidationError(f'{day.capitalize()}: La hora de cierre debe ser posterior a la hora de apertura.')

    def __str__(self):
        return f"Horario de {self.company.name}"
    
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from cloudinary.models import CloudinaryField
from django.core.exceptions import ValidationError

from django.db import models
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError
from cloudinary.models import CloudinaryField

class Promotion(models.Model):
    DISCOUNT_TYPE_CHOICES = [
        ('VALUE', 'Valor'),
        ('PERCENTAGE', 'Porcentaje'),
    ]

    company = models.ForeignKey(
        'Company',
        on_delete=models.CASCADE,
        related_name='promotions',
        verbose_name="Empresa"
    )
    product = models.ForeignKey(
        'Product',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='promotions',
        verbose_name="Producto"
    )
    category = models.ForeignKey(
        'Category',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='promotions',
        verbose_name="Categoría"
    )
    title = models.CharField(
        max_length=200,
        verbose_name="Título"
    )
    description = models.TextField(
        verbose_name="Descripción"
    )
    terms_conditions = models.TextField(
        verbose_name="Términos y Condiciones"
    )
    discount_type = models.CharField(
        max_length=10,
        choices=DISCOUNT_TYPE_CHOICES,
        verbose_name="Tipo de Descuento"
    )
    discount_value = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        verbose_name="Valor del Descuento"
    )
    banner = CloudinaryField(
        'image',
        folder='promotions/',
        help_text="Banner de la promoción"
    )
    start_date = models.DateTimeField(
        verbose_name="Fecha de Inicio"
    )
    end_date = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Fecha de Finalización"
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="Activa"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha de Creación"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Última Actualización"
    )

    class Meta:
        verbose_name = "Promoción"
        verbose_name_plural = "Promociones"
        ordering = ['-created_at']

    def clean(self):
        if self.discount_type == 'PERCENTAGE' and self.discount_value > 100:
            raise ValidationError({
                'discount_value': 'El porcentaje de descuento no puede ser mayor a 100%'
            })
        
        if self.end_date and self.start_date and self.end_date <= self.start_date:
            raise ValidationError({
                'end_date': 'La fecha de finalización debe ser posterior a la fecha de inicio'
            })

    def save(self, *args, **kwargs):
        # Asegurarse de que el valor del descuento siempre sea positivo
        self.discount_value = abs(self.discount_value)
        super().save(*args, **kwargs)

    def get_formatted_discount(self):
        """
        Retorna el valor del descuento formateado según el tipo:
        - Para porcentajes: '30%'
        - Para valores: '$30.00'
        """
        if self.discount_type == 'PERCENTAGE':
            return f"{abs(self.discount_value):.0f}%"
        return f"${abs(self.discount_value):.2f}"

    def __str__(self):
        return f"{self.title} - {self.company.name}"
