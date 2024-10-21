# marketplace/admin.py

from django.contrib import admin
from .models import Company, Category, Product, BusinessHours, Order, OrderItem, TopBurgerSection, TopBurgerItem, CompanyCategory, Country


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'phone', 'address')
    search_fields = ('name', 'user__username')

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'company', 'category', 'price')
    list_filter = ('company', 'category')
    search_fields = ('name', 'company__name')

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'company', 'created_at', 'total')
    search_fields = ('user__username', 'company__name')
    list_filter = ('company', 'created_at')

@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('order', 'product', 'quantity', 'price')
    search_fields = ('order__id', 'product__name')

admin.site.register(TopBurgerSection)
admin.site.register(TopBurgerItem)

@admin.register(CompanyCategory)
class CompanyCategoryAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name', 'description')

@admin.register(Country)
class CountryAdmin(admin.ModelAdmin):
    list_display = ('name', 'code')
    search_fields = ('name', 'code')
    list_per_page = 20

@admin.register(BusinessHours)
class BusinessHoursAdmin(admin.ModelAdmin):
    list_display = ('company', 'open_time', 'close_time')
    search_fields = ('company__name',)
    list_filter = ('open_days',)

    def get_open_days(self, obj):
        return ", ".join(obj.open_days)
    get_open_days.short_description = 'Open Days'
