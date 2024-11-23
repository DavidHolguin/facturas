# models.py
from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from django.db.models import Sum, Count

class Invoice(models.Model):
    INVOICE_STATUS = [
        ('BORRADOR', 'Borrador'),
        ('EMITIDA', 'Emitida'),
        ('PAGADA', 'Pagada'),
        ('ANULADA', 'Anulada')
    ]

    IDENTIFICATION_TYPES = [
        ('CC', 'Cédula de Ciudadanía'),
        ('NIT', 'Número de Identificación Tributaria'),
        ('RUT', 'Registro Único Tributario')
    ]

    company = models.ForeignKey('marketplace.Company', on_delete=models.CASCADE, related_name='invoices')
    customer_name = models.CharField(max_length=200)
    customer_email = models.EmailField()
    customer_identification_type = models.CharField(max_length=10, choices=IDENTIFICATION_TYPES)
    customer_identification_number = models.CharField(max_length=50)
    
    invoice_number = models.CharField(max_length=50, unique=True)
    internal_id = models.CharField(max_length=20, unique=True, null=True)  # Nuevo campo para ID interno
    issue_date = models.DateTimeField(auto_now_add=True)
    due_date = models.DateTimeField(null=True, blank=True)  # Nueva fecha de vencimiento
    status = models.CharField(max_length=20, choices=INVOICE_STATUS, default='BORRADOR')
    
    subtotal = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    notes = models.TextField(blank=True, null=True)  # Campo para notas adicionales

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def calculate_totals(self):
        """Calcula subtotal y total de la factura"""
        invoice_items = self.invoice_items.all()
        self.subtotal = sum(item.total for item in invoice_items)
        
        tax_items = self.taxes.all()
        total_taxes = sum(tax.amount for tax in tax_items)
        
        self.total = self.subtotal + total_taxes
        self.save()

    @classmethod
    def generate_internal_id(cls, company_id):
        """Genera un ID interno único para la factura basado en la empresa"""
        last_invoice = cls.objects.filter(company_id=company_id).order_by('-internal_id').first()
        if last_invoice and last_invoice.internal_id:
            last_number = int(last_invoice.internal_id.split('-')[-1])
            new_number = last_number + 1
        else:
            new_number = 1
        return f"INV-{company_id}-{new_number:06d}"

    @classmethod
    def get_company_statistics(cls, company_id):
        """Obtiene estadísticas detalladas de facturación por empresa"""
        invoices = cls.objects.filter(company_id=company_id)
        return {
            'total_invoices': invoices.count(),
            'total_amount': invoices.aggregate(total=Sum('total'))['total'] or 0,
            'pending_amount': invoices.filter(status='EMITIDA').aggregate(total=Sum('total'))['total'] or 0,
            'paid_amount': invoices.filter(status='PAGADA').aggregate(total=Sum('total'))['total'] or 0,
            'status_summary': invoices.values('status').annotate(count=Count('id')),
            'monthly_totals': invoices.filter(status='PAGADA')\
                .values('issue_date__month')\
                .annotate(total=Sum('total'))\
                .order_by('issue_date__month')
        }

    def __str__(self):
        return f"Factura {self.invoice_number} - {self.customer_name}"

class InvoiceItem(models.Model):
    invoice = models.ForeignKey(Invoice, related_name='invoice_items', on_delete=models.CASCADE)
    product = models.ForeignKey('marketplace.Product', on_delete=models.CASCADE)
    quantity = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0.01)])
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    total = models.DecimalField(max_digits=15, decimal_places=2)
    description = models.TextField(blank=True, null=True)  # Campo para descripción adicional

    def save(self, *args, **kwargs):
        self.total = self.quantity * self.unit_price
        super().save(*args, **kwargs)
        self.invoice.calculate_totals()

    def __str__(self):
        return f"{self.product.name} - {self.quantity} unidades"

class TaxItem(models.Model):
    TAX_TYPES = [
        ('IVA', 'Impuesto al Valor Agregado'),
        ('ICA', 'Impuesto de Industria y Comercio'),
        ('RENTA', 'Retención en la Fuente')
    ]

    invoice = models.ForeignKey(Invoice, related_name='taxes', on_delete=models.CASCADE)
    tax_type = models.CharField(max_length=20, choices=TAX_TYPES)
    percentage = models.DecimalField(max_digits=5, decimal_places=2)
    amount = models.DecimalField(max_digits=15, decimal_places=2)

    def save(self, *args, **kwargs):
        invoice_subtotal = self.invoice.subtotal
        self.amount = invoice_subtotal * (self.percentage / 100)
        super().save(*args, **kwargs)
        self.invoice.calculate_totals()

    def __str__(self):
        return f"{self.get_tax_type_display()} - {self.percentage}%"