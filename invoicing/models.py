from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator

from django.db.models import Sum, Count
from django.utils.timezone import now

from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings

class CustomerUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('Users must have an email address')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(email, password, **extra_fields)

class CustomerUser(AbstractUser):
    username = models.CharField(
        _('username'),
        max_length=150,
        blank=True,
        null=True,
        unique=False
    )
    
    email = models.EmailField(
        _('email address'), 
        unique=True
    )
    
    identification_choices = [
        ('CC', 'Cédula de Ciudadanía'),
        ('CE', 'Cédula de Extranjería'),
        ('PS', 'Pasaporte'),
        ('NIT', 'NIT'),
    ]
    
    identification_type = models.CharField(
        max_length=3,
        choices=identification_choices,
        verbose_name=_('Tipo de Identificación')
    )
    
    identification_number = models.CharField(
        max_length=20,
        verbose_name=_('Número de Identificación')
    )
    
    phone_number = models.CharField(
        max_length=15,
        verbose_name=_('Número de Teléfono'),
        blank=True
    )

    objects = CustomerUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['identification_type', 'identification_number']

    class Meta:
        verbose_name = _('Cliente Usuario')
        verbose_name_plural = _('Clientes Usuarios')

    def __str__(self):
        return self.email

    def save(self, *args, **kwargs):
        if not self.username:
            self.username = self.email.split('@')[0]
        super().save(*args, **kwargs)

    def get_total_invoices(self):
        return self.invoice_set.count()

    def get_total_amount(self):
        return self.invoice_set.aggregate(total=Sum('total_amount'))['total'] or 0

class Invoice(models.Model):
    INVOICE_STATUS = [
        ('BORRADOR', 'Borrador'),
        ('EMITIDA', 'Emitida'),
        ('PAGADA', 'Pagada'),
        ('ANULADA', 'Anulada')
    ]

    company = models.ForeignKey(
        'marketplace.Company',
        on_delete=models.CASCADE,
        related_name='invoices'
    )
    customer = models.ForeignKey(
        CustomerUser,
        on_delete=models.PROTECT,
        related_name='invoices'
    )
    invoice_number = models.CharField(max_length=50, unique=True)
    internal_id = models.CharField(
        max_length=20,
        unique=True,
        null=True,
        blank=True
    )
    issue_date = models.DateTimeField(default=now)
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
        self.total = self.subtotal
        self.save()

    def send_invoice_email(self):
        """Envía el email de la factura al cliente y al admin."""
        context = {
            'invoice': self,
            'items': self.invoice_items.all(),
            'customer': self.customer
        }
        
        # Renderizar el HTML
        html_content = render_to_string('invoices/invoice_email.html', context)
        
        # Crear el email
        subject = f'Factura #{self.invoice_number}'
        from_email = settings.DEFAULT_FROM_EMAIL
        to_emails = [self.customer.email, settings.ADMIN_EMAIL]
        
        msg = EmailMultiAlternatives(
            subject,
            'Su factura está adjunta',
            from_email,
            to_emails
        )
        msg.attach_alternative(html_content, "text/html")
        
        # Generar y adjuntar PDF
        from .views import InvoiceViewSet
        pdf = InvoiceViewSet.generate_pdf_file(self)
        msg.attach(f'invoice_{self.invoice_number}.pdf', pdf.getvalue(), 'application/pdf')
        
        msg.send()

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
        return f"Factura {self.invoice_number} - {self.customer.get_full_name()}"

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