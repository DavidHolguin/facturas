from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from .models import Invoice
from .serializers import InvoiceSerializer
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from django.http import HttpResponse
import io

class InvoiceViewSet(viewsets.ModelViewSet):
    queryset = Invoice.objects.all()
    serializer_class = InvoiceSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """Filtrar facturas por empresa del usuario"""
        return Invoice.objects.filter(company__user=self.request.user)

    @action(detail=True, methods=['GET'])
    def generate_pdf(self, request, pk=None):
        """Genera PDF de la factura"""
        invoice = get_object_or_404(Invoice, pk=pk)
        
        # Crear PDF
        buffer = io.BytesIO()
        p = canvas.Canvas(buffer, pagesize=letter)
        
        # Encabezado de la factura
        p.setFont("Helvetica-Bold", 16)
        p.drawString(100, 750, f"Factura No. {invoice.invoice_number}")
        
        # Información de la empresa
        p.setFont("Helvetica", 12)
        p.drawString(100, 700, invoice.company.name)
        p.drawString(100, 680, invoice.company.address)
        
        # Información del cliente
        p.drawString(100, 640, f"Cliente: {invoice.customer_name}")
        p.drawString(100, 620, f"Identificación: {invoice.customer_identification_number}")
        
        # Detalles de los productos
        p.setFont("Helvetica-Bold", 12)
        p.drawString(100, 580, "Productos")
        
        y = 560
        for item in invoice.invoice_items.all():
            p.setFont("Helvetica", 10)
            p.drawString(100, y, item.product.name)
            p.drawString(300, y, f"{item.quantity} x ${item.unit_price}")
            p.drawString(450, y, f"${item.total}")
            y -= 20
        
        # Totales
        p.setFont("Helvetica-Bold", 12)
        p.drawString(350, y-20, "Subtotal:")
        p.drawString(450, y-20, f"${invoice.subtotal}")
        
        # Impuestos
        for tax in invoice.taxes.all():
            y -= 20
            p.setFont("Helvetica", 10)
            p.drawString(350, y, f"{tax.tax_type} ({tax.percentage}%):")
            p.drawString(450, y, f"${tax.amount}")
        
        p.setFont("Helvetica-Bold", 12)
        p.drawString(350, y-40, "Total:")
        p.drawString(450, y-40, f"${invoice.total}")
        
        p.showPage()
        p.save()
        
        buffer.seek(0)
        response = HttpResponse(buffer, content_type='application/pdf')
        response['Content-Disposition'] = f'filename="factura_{invoice.invoice_number}.pdf"'
        return response