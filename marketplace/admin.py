from django.contrib import admin
from .models import Company, Category, Product, BusinessHours,  CompanyCategory
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


@admin.register(CompanyCategory)
class CompanyCategoryAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name', 'description')



@admin.register(Promotion)
class PromotionAdmin(admin.ModelAdmin):
    list_display = (
        'title',
        'company',
        'product',
        'category',
        'discount_display',
        'date_range',
        'is_active',
        'banner_preview'
    )
    
    list_filter = (
        'is_active',
        'discount_type',
        'company',
        'category',
        ('start_date', admin.DateFieldListFilter),
        ('end_date', admin.DateFieldListFilter),
    )
    
    search_fields = (
        'title',
        'description',
        'company__name',
        'product__name',
        'category__name'
    )
    
    readonly_fields = (
        'created_at',
        'updated_at',
        'banner_preview'
    )
    
    fieldsets = (
        ('Información Básica', {
            'fields': (
                'company',
                'title',
                'description',
                'terms_conditions',
            )
        }),
        ('Detalles de la Promoción', {
            'fields': (
                ('product', 'category'),
                ('discount_type', 'discount_value'),
                'banner',
                'banner_preview',
            )
        }),
        ('Fechas y Estado', {
            'fields': (
                ('start_date', 'end_date'),
                'is_active',
                ('created_at', 'updated_at'),
            )
        }),
    )
    
    def discount_display(self, obj):
        if obj.discount_type == 'PERCENTAGE':
            return f"{obj.discount_value}%"
        return f"${obj.discount_value}"
    discount_display.short_description = "Descuento"
    
    def date_range(self, obj):
        end_date = obj.end_date.strftime('%d/%m/%Y') if obj.end_date else "Sin fecha fin"
        return f"{obj.start_date.strftime('%d/%m/%Y')} - {end_date}"
    date_range.short_description = "Período"
    
    def banner_preview(self, obj):
        if obj.banner:
            return format_html(
                '<img src="{}" style="max-height: 100px;"/>',
                obj.banner.url
            )
        return "Sin banner"
    banner_preview.short_description = "Vista previa del banner"