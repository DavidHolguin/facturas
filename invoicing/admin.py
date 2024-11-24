from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Sum
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import Invoice, InvoiceItem, TaxItem

class InvoiceItemInline(admin.TabularInline):
    model = InvoiceItem
    extra = 1
    readonly_fields = ('total',)
    autocomplete_fields = ['product']
    fields = ('product', 'quantity', 'unit_price', 'total', 'description')

class TaxItemInline(admin.TabularInline):
    model = TaxItem
    extra = 1
    readonly_fields = ('amount',)
    fields = ('tax_type', 'percentage', 'amount')

@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ('invoice_number', 'internal_id', 'company', 'customer_name', 
                   'formatted_total', 'status', 'issue_date', 'due_date')
    list_filter = ('status', 'company', 'issue_date', 'customer_identification_type')
    search_fields = ('invoice_number', 'internal_id', 'customer_name', 
                    'customer_email', 'customer_identification_number')
    readonly_fields = ('invoice_number', 'internal_id', 'created_at', 'updated_at',
                      'subtotal', 'total')
    inlines = [InvoiceItemInline, TaxItemInline]
    date_hierarchy = 'issue_date'
    ordering = ('-issue_date',)

    fieldsets = (
        ('Información de Factura', {
            'fields': (('invoice_number', 'internal_id'), 
                      'company', 
                      'status',
                      ('issue_date', 'due_date'))
        }),
        ('Información del Cliente', {
            'fields': ('customer_name', 
                      'customer_email',
                      ('customer_identification_type', 'customer_identification_number'))
        }),
        ('Totales', {
            'fields': (('subtotal', 'total'),)
        }),
        ('Notas', {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
        ('Información del Sistema', {
            'fields': (('created_at', 'updated_at'),),
            'classes': ('collapse',)
        })
    )

    def formatted_total(self, obj):
        return format_html('<b>${:,.2f}</b>', obj.total)
    formatted_total.short_description = 'Total'
    formatted_total.admin_order_field = 'total'

    def save_model(self, request, obj, form, change):
        if not change:  # Si es una nueva factura
            obj.internal_id = Invoice.generate_internal_id(obj.company_id)
        super().save_model(request, obj, form, change)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if not request.user.is_superuser:
            return qs.filter(company__user=request.user)
        return qs

    def has_change_permission(self, request, obj=None):
        if obj and obj.status in ['PAGADA', 'ANULADA']:
            return False
        return super().has_change_permission(request, obj)

    def has_delete_permission(self, request, obj=None):
        if obj and obj.status in ['PAGADA', 'ANULADA']:
            return False
        return super().has_delete_permission(request, obj)

    class Media:
        css = {
            'all': ('css/admin/invoice.css',)
        }
        js = ('js/admin/invoice.js',)

@admin.register(InvoiceItem)
class InvoiceItemAdmin(admin.ModelAdmin):
    list_display = ('invoice_link', 'product', 'quantity', 'unit_price', 'total')
    list_filter = ('invoice__status', 'product')
    search_fields = ('invoice__invoice_number', 'product__name')
    readonly_fields = ('total',)
    autocomplete_fields = ['invoice', 'product']

    def invoice_link(self, obj):
        url = reverse('admin:app_invoice_change', args=[obj.invoice.id])
        return mark_safe(f'<a href="{url}">{obj.invoice}</a>')
    invoice_link.short_description = 'Factura'

@admin.register(TaxItem)
class TaxItemAdmin(admin.ModelAdmin):
    list_display = ('invoice_link', 'tax_type', 'percentage', 'amount')
    list_filter = ('tax_type', 'invoice__status')
    search_fields = ('invoice__invoice_number',)
    readonly_fields = ('amount',)
    autocomplete_fields = ['invoice']

    def invoice_link(self, obj):
        url = reverse('admin:app_invoice_change', args=[obj.invoice.id])
        return mark_safe(f'<a href="{url}">{obj.invoice}</a>')
    invoice_link.short_description = 'Factura'