from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MaxValueValidator, MinValueValidator

class Company(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)  # Add missing closing parenthesis
    description = models.TextField()

    profile_picture = models.ImageField(upload_to='company_profiles/findoutpwa/', null=True, blank=True)
    cover_photo = models.ImageField(upload_to='company_covers/findoutpwa/', null=True, blank=True)
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
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True)
    name = models.CharField(max_length=100)
    description = models.TextField()

    price = models.DecimalField(max_digits=10, decimal_places=2)
    image = models.ImageField(upload_to='products/findoutpwa/', null=True, blank=True)

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

class TopBurgerItem(models.Model):
    section = models.ForeignKey(TopBurgerSection, related_name='items', on_delete=models.CASCADE)
    company = models.ForeignKey('Company', on_delete=models.CASCADE)
    order = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(3)])
    featured_image = models.ImageField(upload_to='top_burgers/')

    class Meta:
        ordering = ['order']