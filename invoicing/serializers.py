# serializers.py
from rest_framework import serializers
from .models import Invoice, InvoiceItem, TaxItem
from marketplace.models import Company, Product

class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ['id', 'name', 'price']

class InvoiceItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)
    product_id = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.all(),
        source='product',
        write_only=True
    )

    class Meta:
        model = InvoiceItem
        fields = ['id', 'product', 'product_id', 'quantity', 'unit_price', 'total', 'description']
        read_only_fields = ['total']

    def validate(self, data):
        if data.get('quantity', 0) <= 0:
            raise serializers.ValidationError("La cantidad debe ser mayor a cero")
        if data.get('unit_price', 0) <= 0:
            raise serializers.ValidationError("El precio unitario debe ser mayor a cero")
        return data

class TaxItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = TaxItem
        fields = ['id', 'tax_type', 'percentage', 'amount']
        read_only_fields = ['amount']

    def validate(self, data):
        if data.get('percentage', 0) < 0 or data.get('percentage', 0) > 100:
            raise serializers.ValidationError("El porcentaje de impuesto debe estar entre 0 y 100")
        return data

class InvoiceSerializer(serializers.ModelSerializer):
    invoice_items = InvoiceItemSerializer(many=True)
    taxes = TaxItemSerializer(many=True, required=False)
    company_id = serializers.PrimaryKeyRelatedField(
        queryset=Company.objects.all(),
        source='company',
        write_only=True
    )
    company_name = serializers.CharField(source='company.name', read_only=True)

    class Meta:
        model = Invoice
        fields = [
            'id', 'internal_id', 'company_id', 'company_name', 'invoice_number',
            'customer_name', 'customer_email', 'customer_identification_type',
            'customer_identification_number', 'status', 'subtotal', 'total',
            'invoice_items', 'taxes', 'issue_date', 'due_date', 'notes',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['subtotal', 'total', 'invoice_number', 'internal_id']

    def validate(self, data):
        if not data.get('invoice_items'):
            raise serializers.ValidationError("La factura debe contener al menos un item")
        if not data.get('customer_email'):
            raise serializers.ValidationError("El correo electrónico es obligatorio")
        return data

    def create(self, validated_data):
        invoice_items_data = validated_data.pop('invoice_items')
        taxes_data = validated_data.pop('taxes', [])

        # Generar ID interno
        company = validated_data['company']
        internal_id = Invoice.generate_internal_id(company.id)
        validated_data['internal_id'] = internal_id

        invoice = Invoice.objects.create(**validated_data)

        for item_data in invoice_items_data:
            product = item_data.pop('product')
            InvoiceItem.objects.create(invoice=invoice, product=product, **item_data)

        for tax_data in taxes_data:
            TaxItem.objects.create(invoice=invoice, **tax_data)

        invoice.calculate_totals()
        return invoice

    def update(self, instance, validated_data):
        invoice_items_data = validated_data.pop('invoice_items', None)
        taxes_data = validated_data.pop('taxes', None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        if invoice_items_data is not None:
            instance.invoice_items.all().delete()
            for item_data in invoice_items_data:
                product = item_data.pop('product')
                InvoiceItem.objects.create(invoice=instance, product=product, **item_data)

        if taxes_data is not None:
            instance.taxes.all().delete()
            for tax_data in taxes_data:
                TaxItem.objects.create(invoice=instance, **tax_data)

        instance.save()
        instance.calculate_totals()
        return instance