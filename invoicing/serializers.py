from rest_framework import serializers
from .models import Invoice, InvoiceItem, TaxItem
from marketplace.models import Company, Product  # Cambié company por marketplace

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
        fields = ['id', 'product', 'product_id', 'quantity', 'unit_price', 'total']
        read_only_fields = ['total']

    def validate(self, data):
        # Validación adicional para cantidad y precio
        if data.get('quantity', 0) <= 0:
            raise serializers.ValidationError("La cantidad debe ser mayor a cero")
        if data.get('unit_price', 0) <= 0:
            raise serializers.ValidationError("El precio unitario debe ser mayor a cero")
        return data

class TaxItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = TaxItem
        fields = ['tax_type', 'percentage', 'amount']

    def validate(self, data):
        # Validación de porcentaje de impuesto
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

    class Meta:
        model = Invoice
        fields = [
            'id', 'company_id', 'invoice_number', 'customer_name', 
            'customer_email', 'customer_identification_type', 
            'customer_identification_number', 'status', 
            'subtotal', 'total', 'invoice_items', 'taxes'
        ]
        read_only_fields = ['subtotal', 'total', 'invoice_number']

    def validate_invoice_items(self, value):
        # Validación de que haya al menos un item en la factura
        if not value:
            raise serializers.ValidationError("Debe haber al menos un item en la factura")
        return value

    def validate(self, data):
        # Validaciones adicionales globales
        if not data.get('invoice_items'):
            raise serializers.ValidationError("La factura debe contener al menos un item")
        
        # Validar email
        if not data.get('customer_email'):
            raise serializers.ValidationError("El correo electrónico es obligatorio")
        
        return data

    def create(self, validated_data):
        invoice_items_data = validated_data.pop('invoice_items')
        taxes_data = validated_data.pop('taxes', [])

        # Crear factura
        invoice = Invoice.objects.create(**validated_data)

        # Crear items de factura
        for item_data in invoice_items_data:
            product = item_data.pop('product')
            InvoiceItem.objects.create(
                invoice=invoice, 
                product=product, 
                **item_data
            )

        # Crear impuestos
        for tax_data in taxes_data:
            TaxItem.objects.create(invoice=invoice, **tax_data)

        # Recalcular totales
        invoice.calculate_totals()

        return invoice

    def update(self, instance, validated_data):
        # Manejar actualización de factura
        invoice_items_data = validated_data.pop('invoice_items', None)
        taxes_data = validated_data.pop('taxes', None)

        # Actualizar campos de la factura
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        # Eliminar items existentes y crear nuevos
        if invoice_items_data is not None:
            instance.invoice_items.all().delete()
            for item_data in invoice_items_data:
                product = item_data.pop('product')
                InvoiceItem.objects.create(
                    invoice=instance, 
                    product=product, 
                    **item_data
                )

        # Actualizar impuestos
        if taxes_data is not None:
            instance.taxes.all().delete()
            for tax_data in taxes_data:
                TaxItem.objects.create(invoice=instance, **tax_data)

        # Guardar y recalcular
        instance.save()
        instance.calculate_totals()

        return instance