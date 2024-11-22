from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator

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
    issue_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=INVOICE_STATUS, default='BORRADOR')
    
    subtotal = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=15, decimal_places=2, default=0)

    def calculate_totals(self):
        """Calcula subtotal y total de la factura"""
        invoice_items = self.invoice_items.all()
        self.subtotal = sum(item.total for item in invoice_items)
        
        # Calcular impuestos
        tax_items = self.taxes.all()
        total_taxes = sum(tax.amount for tax in tax_items)
        
        self.total = self.subtotal + total_taxes
        self.save()

    def __str__(self):
        return f"Factura {self.invoice_number} - {self.customer_name}"

class InvoiceItem(models.Model):
    invoice = models.ForeignKey(Invoice, related_name='invoice_items', on_delete=models.CASCADE)
    product = models.ForeignKey('marketplace.Product', on_delete=models.CASCADE)
    quantity = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0.01)])
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    total = models.DecimalField(max_digits=15, decimal_places=2)

    def save(self, *args, **kwargs):
        """Calcula el total antes de guardar"""
        self.total = self.quantity * self.unit_price
        super().save(*args, **kwargs)
        # Recalcular totales de la factura
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
        """Calcula el monto del impuesto"""
        invoice_subtotal = self.invoice.subtotal
        self.amount = invoice_subtotal * (self.percentage / 100)
        super().save(*args, **kwargs)
        # Recalcular totales de la factura
        self.invoice.calculate_totals()

    def __str__(self):
        return f"{self.get_tax_type_display()} - {self.percentage}%"