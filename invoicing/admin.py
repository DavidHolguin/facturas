from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.db.models import Sum
from .models import CustomerUser, Invoice, InvoiceItem


from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _
from .models import CustomerUser

@admin.register(CustomerUser)
class CustomerUserAdmin(UserAdmin):
    list_display = ('email', 'first_name', 'last_name', 'identification_number', 'is_active', 'is_staff')
    list_filter = ('is_active', 'is_staff', 'identification_type')
    search_fields = ('email', 'first_name', 'last_name', 'identification_number')
    ordering = ('email',)
    
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        (_('Personal info'), {
            'fields': (
                'first_name',
                'last_name',
                'identification_type',
                'identification_number',
                'phone_number',
            )
        }),
        (_('Permissions'), {
            'fields': (
                'is_active',
                'is_staff',
                'is_superuser',
                'groups',
                'user_permissions',
            )
        }),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'email',
                'password1',
                'password2',
                'first_name',
                'last_name',
                'identification_type',
                'identification_number',
                'phone_number',
                'is_staff',
                'is_active',
            ),
        }),
    )

    def get_fieldsets(self, request, obj=None):
        if not obj:
            return self.add_fieldsets
        return super().get_fieldsets(request, obj)

class InvoiceItemInline(admin.TabularInline):
    model = InvoiceItem
    extra = 1
    readonly_fields = ('total',)
    autocomplete_fields = ['product']

@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ('invoice_number', 'company', 'get_customer_name', 
                   'issue_date', 'due_date', 'total', 'status', 'created_at')
    list_filter = ('status', 'company', 'issue_date', 'created_at')
    search_fields = ('invoice_number', 'internal_id', 'customer__first_name', 
                    'customer__last_name', 'customer__email')
    readonly_fields = ('invoice_number', 'internal_id', 'subtotal', 'total', 
                      'created_at', 'updated_at')
    ordering = ('-created_at',)
    inlines = [InvoiceItemInline]
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('company', 'customer', 'invoice_number', 'internal_id',
                      'issue_date', 'due_date', 'status')
        }),
        ('Totales', {
            'fields': ('subtotal', 'total')
        }),
        ('Notas', {
            'fields': ('notes',)
        }),
        ('Información del Sistema', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def get_customer_name(self, obj):
        return obj.customer.get_full_name()
    get_customer_name.short_description = 'Cliente'
    get_customer_name.admin_order_field = 'customer__first_name'

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if not request.user.is_superuser:
            return qs.filter(company__user=request.user)
        return qs

    def get_readonly_fields(self, request, obj=None):
        if obj and obj.status != 'BORRADOR':  # Si la factura ya existe y no está en borrador
            return self.readonly_fields + ('company', 'customer', 'status')
        return self.readonly_fields

    def save_model(self, request, obj, form, change):
        if not change:  # Si es una nueva factura
            # Generate invoice_number if it's not set
            if not obj.invoice_number:
                obj.invoice_number = Invoice.generate_invoice_number(obj.company_id)
            
            # Generate internal_id if it's not set
            if not obj.internal_id:
                obj.internal_id = Invoice.generate_internal_id(obj.company_id)
        
        super().save_model(request, obj, form, change)
        
@admin.register(InvoiceItem)
class InvoiceItemAdmin(admin.ModelAdmin):
    list_display = ('invoice', 'product', 'quantity', 'unit_price', 'total')
    list_filter = ('invoice__status', 'product')
    search_fields = ('invoice__invoice_number', 'product__name')
    readonly_fields = ('total',)
    autocomplete_fields = ['invoice', 'product']

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if not request.user.is_superuser:
            return qs.filter(invoice__company__user=request.user)
        return qs

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "invoice" and not request.user.is_superuser:
            kwargs["queryset"] = Invoice.objects.filter(company__user=request.user)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)