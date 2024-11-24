from django.db import models
from django.core.validators import MinValueValidator
from django.db.models import Sum, Count
from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _

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

    company = models.ForeignKey(
        'marketplace.Company',
        on_delete=models.CASCADE,
        related_name='invoices'
    )
    customer_name = models.CharField(max_length=200)
    customer_email = models.EmailField()
    customer_identification_type = models.CharField(
        max_length=10,
        choices=IDENTIFICATION_TYPES
    )
    customer_identification_number = models.CharField(max_length=50)

    invoice_number = models.CharField(max_length=50, unique=True)
    internal_id = models.CharField(
        max_length=20,
        unique=True,
        null=True,
        blank=True
    )
    issue_date = models.DateTimeField(default=now)  # Campo editable
    due_date = models.DateTimeField(null=True, blank=True)
    status = models.CharField(
        max_length=20,
        choices=INVOICE_STATUS,
        default='BORRADOR'
    )

    subtotal = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0
    )
    total = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0
    )
    notes = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = _("Invoice")
        verbose_name_plural = _("Invoices")

    def calculate_totals(self):
        """Calcula subtotal y total de la factura."""
        invoice_items = self.invoice_items.all()
        self.subtotal = sum(item.total for item in invoice_items)
        tax_items = self.taxes.all()
        total_taxes = sum(tax.amount for tax in tax_items)
        self.total = self.subtotal + total_taxes
        self.save()

    @classmethod
    def generate_internal_id(cls, company_id):
        """Genera un ID interno único para la factura basado en la empresa."""
        last_invoice = cls.objects.filter(company_id=company_id).order_by('-internal_id').first()
        if last_invoice and last_invoice.internal_id:
            last_number = int(last_invoice.internal_id.split('-')[-1])
            new_number = last_number + 1
        else:
            new_number = 1
        return f"INV-{company_id}-{new_number:06d}"

    def __str__(self):
        return f"Factura {self.invoice_number} - {self.customer_name}"


class InvoiceItem(models.Model):
    invoice = models.ForeignKey(
        Invoice,
        related_name='invoice_items',
        on_delete=models.CASCADE
    )
    product = models.ForeignKey(
        'marketplace.Product',
        on_delete=models.CASCADE
    )
    quantity = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0.01)]
    )
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    total = models.DecimalField(max_digits=15, decimal_places=2)
    description = models.TextField(blank=True, null=True)

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

    invoice = models.ForeignKey(
        Invoice,
        related_name='taxes',
        on_delete=models.CASCADE
    )
    tax_type = models.CharField(
        max_length=20,
        choices=TAX_TYPES
    )
    percentage = models.DecimalField(max_digits=5, decimal_places=2)
    amount = models.DecimalField(max_digits=15, decimal_places=2)

    def save(self, *args, **kwargs):
        self.amount = self.invoice.subtotal * (self.percentage / 100)
        super().save(*args, **kwargs)
        self.invoice.calculate_totals()

    def __str__(self):
        return f"{self.get_tax_type_display()} - {self.percentage}%"
