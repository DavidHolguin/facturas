# marketplace/admin.py

from django.contrib import admin
from .models import Company, Category, Product, BusinessHours, Order, OrderItem, TopBurgerSection, TopBurgerItem, CompanyCategory, Country


class BusinessHoursInline(admin.StackedInline):
    model = BusinessHours
    can_delete = False
    verbose_name_plural = 'Horario de atención'

@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'phone', 'address', 'get_business_hours')
    search_fields = ('name', 'user__username')
    inlines = [BusinessHoursInline]

    def get_business_hours(self, obj):
        try:
            hours = obj.business_hours
            return f"{', '.join(hours.open_days)} {hours.open_time} - {hours.close_time}"
        except BusinessHours.DoesNotExist:
            return "No establecido"
    get_business_hours.short_description = 'Horario de atención'

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