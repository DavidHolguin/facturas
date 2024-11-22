from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db.models import Sum, F
from django.utils import timezone

from .models import Invoice
from .serializers import InvoiceSerializer
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib import colors

import io
import logging

logger = logging.getLogger(__name__)

class InvoiceViewSet(viewsets.ModelViewSet):
    queryset = Invoice.objects.all()
    serializer_class = InvoiceSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """Filtrar facturas por empresa del usuario"""
        return Invoice.objects.filter(company__user=self.request.user)

    def create(self, request, *args, **kwargs):
        """Sobrescribir método de creación para manejar generación de número de factura"""
        try:
            # Generar número de factura único
            last_invoice = Invoice.objects.filter(
                company=request.data.get('company_id')
            ).order_by('-id').first()

            if last_invoice:
                # Incrementar el último número de factura
                last_number = int(last_invoice.invoice_number.split('-')[-1])
                new_number = f"{timezone.now().year}-{last_number + 1:04d}"
            else:
                # Primera factura para esta empresa
                new_number = f"{timezone.now().year}-0001"

            request.data['invoice_number'] = new_number

            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)
            headers = self.get_success_headers(serializer.data)
            return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
        
        except Exception as e:
            logger.error(f"Error creating invoice: {str(e)}")
            return Response(
                {"error": "No se pudo crear la factura"},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=False, methods=['GET'])
    def summary(self, request):
        """Resumen de facturas"""
        try:
            queryset = self.get_queryset()
            summary = {
                'total_invoices': queryset.count(),
                'total_amount': queryset.aggregate(total=Sum('total'))['total'] or 0,
                'invoices_by_status': queryset.values('status').annotate(count=Sum('id'))
            }
            return Response(summary)
        except Exception as e:
            logger.error(f"Error generating invoice summary: {str(e)}")
            return Response(
                {"error": "No se pudo generar el resumen"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['GET'])
    def generate_pdf(self, request, pk=None):
        """Genera PDF de la factura con mejor formato"""
        try:
            invoice = get_object_or_404(Invoice, pk=pk)
            
            # Crear PDF en memoria
            buffer = io.BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=letter)
            styles = getSampleStyleSheet()
            elements = []

            # Encabezado
            elements.append(Paragraph(f"Factura No. {invoice.invoice_number}", styles['Title']))
            elements.append(Paragraph(f"Fecha: {invoice.issue_date.strftime('%d/%m/%Y')}", styles['Normal']))
            
            # Información de la empresa
            company_data = [
                ["Empresa:", invoice.company.name],
                ["NIT:", invoice.company.nit],
                ["Dirección:", invoice.company.address]
            ]
            company_table = Table(company_data, colWidths=[100, 300])
            company_table.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (0,-1), colors.grey),
                ('TEXTCOLOR', (0,0), (0,-1), colors.whitesmoke),
                ('ALIGN', (0,0), (-1,-1), 'LEFT'),
                ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                ('FONTSIZE', (0,0), (-1,0), 12),
                ('BOTTOMPADDING', (0,0), (-1,-1), 12),
                ('BACKGROUND', (1,0), (-1,-1), colors.beige),
            ]))
            elements.append(company_table)

            # Información del cliente
            customer_data = [
                ["Cliente:", invoice.customer_name],
                ["Identificación:", f"{invoice.customer_identification_type} {invoice.customer_identification_number}"],
                ["Correo:", invoice.customer_email]
            ]
            customer_table = Table(customer_data, colWidths=[100, 300])
            customer_table.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (0,-1), colors.grey),
                ('TEXTCOLOR', (0,0), (0,-1), colors.whitesmoke),
                ('ALIGN', (0,0), (-1,-1), 'LEFT'),
                ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                ('FONTSIZE', (0,0), (-1,0), 12),
                ('BOTTOMPADDING', (0,0), (-1,-1), 12),
                ('BACKGROUND', (1,0), (-1,-1), colors.beige),
            ]))
            elements.append(customer_table)

            # Detalle de productos
            productos_data = [["Producto", "Cantidad", "Precio Unitario", "Total"]]
            for item in invoice.invoice_items.all():
                productos_data.append([
                    item.product.name, 
                    str(item.quantity), 
                    f"${item.unit_price:.2f}", 
                    f"${item.total:.2f}"
                ])
            
            productos_table = Table(productos_data, colWidths=[200, 100, 100, 100])
            productos_table.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.grey),
                ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
                ('ALIGN', (0,0), (-1,-1), 'CENTER'),
                ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                ('FONTSIZE', (0,0), (-1,0), 12),
                ('BOTTOMPADDING', (0,0), (-1,-1), 12),
                ('GRID', (0,0), (-1,-1), 1, colors.black)
            ]))
            elements.append(productos_table)

            # Totales
            totales_data = [
                ["Subtotal", f"${invoice.subtotal:.2f}"],
            ]
            
            for tax in invoice.taxes.all():
                totales_data.append([
                    f"{tax.tax_type} ({tax.percentage}%)", 
                    f"${tax.amount:.2f}"
                ])
            
            totales_data.append(["Total", f"${invoice.total:.2f}"])
            
            totales_table = Table(totales_data, colWidths=[300, 100])
            totales_table.setStyle(TableStyle([
                ('ALIGN', (0,0), (-1,-1), 'RIGHT'),
                ('FONTNAME', (0,-1), (-1,-1), 'Helvetica-Bold'),
                ('FONTSIZE', (0,-1), (-1,-1), 12),
            ]))
            elements.append(totales_table)

            # Construir PDF
            doc.build(elements)
            
            buffer.seek(0)
            response = HttpResponse(buffer, content_type='application/pdf')
            response['Content-Disposition'] = f'filename="factura_{invoice.invoice_number}.pdf"'
            return response

        except Exception as e:
            logger.error(f"Error generating invoice PDF: {str(e)}")
            return Response(
                {"error": "No se pudo generar el PDF"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['POST'])
    def change_status(self, request, pk=None):
        """Cambiar el estado de la factura"""
        invoice = get_object_or_404(Invoice, pk=pk)
        new_status = request.data.get('status')
        
        if new_status not in dict(Invoice.INVOICE_STATUS):
            return Response(
                {"error": "Estado de factura inválido"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        invoice.status = new_status
        invoice.save()
        
        serializer = self.get_serializer(invoice)
        return Response(serializer.data)