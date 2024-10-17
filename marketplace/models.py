from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MaxValueValidator, MinValueValidator
from cloudinary_storage.storage import MediaCloudinaryStorage
from cloudinary.models import CloudinaryField

class Company(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)  # Add missing closing parenthesis
    description = models.TextField()

    profile_picture = CloudinaryField(
        'image',
        folder='company_profiles/findoutpwa/',
        null=True,
        blank=True
    )
    cover_photo = CloudinaryField(
        'image',
        folder='company_covers/findoutpwa/',
        null=True,
        blank=True
    )
    phone = models.CharField(max_length=20)
    address = models.TextField()

    def __str__(self):
        return self.name


class Category(models.Model):
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name

class Product(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    category = models.ForeignKey('Category', on_delete=models.SET_NULL, null=True)
    name = models.CharField(max_length=100)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    image = CloudinaryField(
        'image',
        folder='products/findoutpwa/',
        null=True,
        blank=True
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
    position = models.IntegerField(default=0)
    
    class Meta:
        ordering = ['position']

    def __str__(self):
        return f"{self.title} {self.location}"
    title = models.CharField(max_length=100, default="TOP 3 BURGUERS")
    location = models.CharField(max_length=100, default="en San Jose")
    position = models.IntegerField(default=0, help_text="Position order for displaying sections")
    
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
        help_text="Custom URL for banner items"
    )
    order = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(3)],
        help_text="Position in the top (1-3)"
    )
    featured_image = CloudinaryField(
        'image',
        folder='top_burgers/',
        help_text="Featured burger image"
    )

    class Meta:
        ordering = ['order']
        unique_together = ['section', 'order']

    def __str__(self):
        if self.item_type == 'COMPANY':
            return f"{self.company.name if self.company else 'No company'} - Position {self.order}"
        return f"Banner - Position {self.order}"