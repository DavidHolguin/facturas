from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Invoice, InvoiceItem
from marketplace.models import Product, Company
from marketplace.serializers import ProductSerializer

CustomerUser = get_user_model()

class CustomerUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomerUser
        fields = ['id', 'email', 'first_name', 'last_name', 'identification_type',
                 'identification_number', 'phone_number']
        extra_kwargs = {
            'password': {'write_only': True},
            'email': {'required': True},
            'identification_number': {'required': True},
            'identification_type': {'required': True}
        }

    def create(self, validated_data):
        password = validated_data.pop('password', None)
        user = CustomerUser.objects.create(**validated_data)
        if password:
            user.set_password(password)
            user.save()
        return user

class CustomerLookupSerializer(serializers.Serializer):
    search_term = serializers.CharField()

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

class InvoiceSerializer(serializers.ModelSerializer):
    invoice_items = InvoiceItemSerializer(many=True)
    company_id = serializers.PrimaryKeyRelatedField(
        queryset=Company.objects.all(),
        source='company',
        write_only=True
    )
    company_name = serializers.CharField(source='company.name', read_only=True)
    customer_details = CustomerUserSerializer(source='customer', read_only=True)
    customer_id = serializers.PrimaryKeyRelatedField(
        queryset=CustomerUser.objects.all(),
        source='customer',
        write_only=True
    )

    class Meta:
        model = Invoice
        fields = [
            'id', 'internal_id', 'company_id', 'company_name', 'invoice_number',
            'customer_id', 'customer_details', 'status', 'subtotal', 'total',
            'invoice_items', 'issue_date', 'due_date', 'notes',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['subtotal', 'total', 'invoice_number', 'internal_id']

    def create(self, validated_data):
        invoice_items_data = validated_data.pop('invoice_items')

        # Generar ID interno
        company = validated_data['company']
        internal_id = Invoice.generate_internal_id(company.id)
        validated_data['internal_id'] = internal_id

        invoice = Invoice.objects.create(**validated_data)

        for item_data in invoice_items_data:
            product = item_data.pop('product')
            InvoiceItem.objects.create(invoice=invoice, product=product, **item_data)

        invoice.calculate_totals()
        invoice.send_invoice_email()
        return invoice
    
class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(style={'input_type': 'password'})