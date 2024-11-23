from django.contrib import admin
from .models import Invoice, InvoiceItem, TaxItem

class InvoiceItemInline(admin.TabularInline):
    model = InvoiceItem
    extra = 1
    raw_id_fields = ('product',)
    fields = ('product', 'quantity', 'unit_price', 'total')
    readonly_fields = ('total',)

class TaxItemInline(admin.TabularInline):
    model = TaxItem
    extra = 1
    fields = ('tax_type', 'percentage', 'amount')
    readonly_fields = ('amount',)

@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = (
        'invoice_number', 
        'company', 
        'customer_name', 
        'customer_email',
        'status', 
        'issue_date', 
        'subtotal', 
        'total'
    )
    list_filter = ('status', 'company', 'issue_date')
    search_fields = (
        'invoice_number', 
        'customer_name', 
        'customer_email',
        'customer_identification_number'
    )
    readonly_fields = ('invoice_number', 'issue_date', 'subtotal', 'total')
    raw_id_fields = ('company',)
    fieldsets = (
        ('Información de Empresa', {
            'fields': ('company', 'invoice_number', 'status')
        }),
        ('Información del Cliente', {
            'fields': (
                'customer_name', 
                'customer_email',
                'customer_identification_type',
                'customer_identification_number'
            )
        }),
        ('Información de Factura', {
            'fields': ('issue_date', 'subtotal', 'total')
        }),
    )
    inlines = [InvoiceItemInline, TaxItemInline]

@admin.register(InvoiceItem)
class InvoiceItemAdmin(admin.ModelAdmin):
    list_display = ('invoice', 'product', 'quantity', 'unit_price', 'total')
    list_filter = ('invoice__status', 'product')
    search_fields = ('invoice__invoice_number', 'product__name')
    raw_id_fields = ('invoice', 'product')
    readonly_fields = ('total',)

@admin.register(TaxItem)
class TaxItemAdmin(admin.ModelAdmin):
    list_display = ('invoice', 'tax_type', 'percentage', 'amount')
    list_filter = ('tax_type', 'invoice__status')
    search_fields = ('invoice__invoice_number',)
    raw_id_fields = ('invoice',)
    readonly_fields = ('amount',)