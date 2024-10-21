from django.contrib import admin
from .models import Company, Category, Product, BusinessHours, Order, OrderItem, TopBurgerSection, TopBurgerItem, CompanyCategory, Country
from django.utils.html import format_html

class BusinessHoursInline(admin.StackedInline):
    model = BusinessHours
    extra = 1
    
    fieldsets = (
        ('Lunes', {
            'fields': ('monday_open', 'monday_close'),
        }),
        ('Martes', {
            'fields': ('tuesday_open', 'tuesday_close'),
        }),
        ('Miércoles', {
            'fields': ('wednesday_open', 'wednesday_close'),
        }),
        ('Jueves', {
            'fields': ('thursday_open', 'thursday_close'),
        }),
        ('Viernes', {
            'fields': ('friday_open', 'friday_close'),
        }),
        ('Sábado', {
            'fields': ('saturday_open', 'saturday_close'),
        }),
        ('Domingo', {
            'fields': ('sunday_open', 'sunday_close'),
        }),
    )

@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    inlines = [BusinessHoursInline]
    list_display = ['name', 'get_business_hours']

    def get_business_hours(self, obj):
        try:
            hours = obj.business_hours
            schedule = []
            days_map = {
                'monday': 'Lunes',
                'tuesday': 'Martes',
                'wednesday': 'Miércoles',
                'thursday': 'Jueves',
                'friday': 'Viernes',
                'saturday': 'Sábado',
                'sunday': 'Domingo'
            }
            
            for day in days_map:
                open_time = getattr(hours, f'{day}_open')
                close_time = getattr(hours, f'{day}_close')
                if open_time and close_time:
                    schedule.append(f"{days_map[day]}: {open_time.strftime('%H:%M')} - {close_time.strftime('%H:%M')}")
            
            return format_html("<br>".join(schedule)) if schedule else "Sin horarios definidos"
        except BusinessHours.DoesNotExist:
            return "Sin horarios definidos"
    
    get_business_hours.short_description = "Horarios de Atención"

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

