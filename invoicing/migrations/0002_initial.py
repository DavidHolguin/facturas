# Generated by Django 5.1 on 2024-11-25 07:12

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('invoicing', '0001_initial'),
        ('marketplace', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='invoice',
            name='company',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='invoices', to='marketplace.company'),
        ),
        migrations.AddField(
            model_name='invoice',
            name='customer',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='invoices', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='invoiceitem',
            name='invoice',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='invoice_items', to='invoicing.invoice'),
        ),
        migrations.AddField(
            model_name='invoiceitem',
            name='product',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='marketplace.product'),
        ),
    ]
