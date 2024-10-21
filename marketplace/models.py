from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MaxValueValidator, MinValueValidator
from cloudinary.models import CloudinaryField
from django.core.validators import RegexValidator

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
        # Convierte el código de país a emoji de bandera
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
    company = models.OneToOneField(
        Company,
        on_delete=models.CASCADE,
        related_name='business_hours'
    )
    WEEKDAYS = [
        ('mon', 'Lunes'),
        ('tue', 'Martes'),
        ('wed', 'Miércoles'),
        ('thu', 'Jueves'),
        ('fri', 'Viernes'),
        ('sat', 'Sábado'),
        ('sun', 'Domingo'),
    ]
    open_days = models.JSONField(default=list)
    open_time = models.TimeField()
    close_time = models.TimeField()

    def __str__(self):
        return f"{self.company.name} - Horario de atención"