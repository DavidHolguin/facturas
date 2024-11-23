# views.py
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db.models import Sum, Count, F, Q
from django.utils import timezone
from django.http import HttpResponse
from datetime import datetime, timedelta
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
        queryset = Invoice.objects.filter(company__user=self.request.user)
        
        # Filtros adicionales
        status = self.request.query_params.get('status', None)
        date_from = self.request.query_params.get('date_from', None)
        date_to = self.request.query_params.get('date_to', None)
        company_id = self.request.query_params.get('company_id', None)

        if status:
            queryset = queryset.filter(status=status)
        if date_from:
            queryset = queryset.filter(issue_date__gte=date_from)
        if date_to:
            queryset = queryset.filter(issue_date__lte=date_to)
        if company_id:
            queryset = queryset.filter(company_id=company_id)

        return queryset

    def create(self, request, *args, **kwargs):
        try:
            # Generar número de factura único
            company_id = request.data.get('company_id')
            last_invoice = Invoice.objects.filter(company_id=company_id).order_by('-id').first()

            if last_invoice:
                last_number = int(last_invoice.invoice_number.split('-')[-1])
                new_number = f"{timezone.now().year}-{last_number + 1:04d}"
            else:
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
    def dashboard(self, request):
        """Dashboard completo para la empresa"""
        try:
            company_id = request.query_params.get('company_id')
            if not company_id:
                return Response(
                    {"error": "Se requiere company_id"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Estadísticas generales
            stats = Invoice.get_company_statistics(company_id)
            
            # Facturas por vencer
            today = timezone.now()
            upcoming_due = Invoice.objects.filter(
                company_id=company_id,
                status='EMITIDA',
                due_date__gte=today,
                due_date__lte=today + timedelta(days=7)
            ).count()

            # Facturas vencidas
            overdue = Invoice.objects.filter(
                company_id=company_id,
                status='EMITIDA',
                due_date__lt=today
            ).count()

            # Top clientes
            top_customers = Invoice.objects.filter(company_id=company_id)\
                .values('customer_name')\
                .annotate(
                    total_invoices=Count('id'),
                    total_amount=Sum('total')
                )\
                .order_by('-total_amount')[:5]

            response_data = {
                **stats,
                'upcoming_due': upcoming_due,
                'overdue': overdue,
                'top_customers': top_customers,
                'recent_activity': self.get_recent_activity(company_id)
            }

            return Response(response_data)
        except Exception as e:
            logger.error(f"Error getting dashboard data: {str(e)}")
            return Response(
                {"error": "Error al obtener datos del dashboard"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def get_recent_activity(self, company_id):
        """Obtiene la actividad reciente de facturación"""
        recent = Invoice.objects.filter(company_id=company_id)\
            .order_by('-updated_at')[:10]\
            .values('id', 'invoice_number', 'customer_name', 'total', 
                   'status', 'updated_at')
        return recent

    @action(detail=True, methods=['POST'])
    def change_status(self, request, pk=None):
        """Cambia el estado de una factura"""
        try:
            invoice = self.get_object()
            new_status = request.data.get('status')
            
            if new_status not in dict(Invoice.INVOICE_STATUS):
                return Response(
                    {"error": "Estado no válido"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Validaciones específicas por estado
            if new_status == 'PAGADA' and invoice.status != 'EMITIDA':
                return Response(
                    {"error": "Solo se pueden marcar como pagadas las facturas emitidas"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            if new_status == 'ANULADA' and invoice.status == 'PAGADA':
                return Response(
                    {"error": "No se pueden anular facturas pagadas"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            invoice.status = new_status
            invoice.save()
            
            return Response(self.get_serializer(invoice).data)
        except Exception as e:
            logger.error(f"Error changing invoice status: {str(e)}")
            return Response(
                {"error": "Error al cambiar el estado de la factura"},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['GET'])
    def generate_pdf(self, request, pk=None):
        """Genera un PDF de la factura"""
        try:
            invoice = self.get_object()
            buffer = io.BytesIO()
            
            # Crear el documento PDF
            doc = SimpleDocTemplate(
                buffer,
                pagesize=letter,
                rightMargin=inch/2,
                leftMargin=inch/2,
                topMargin=inch/2,
                bottomMargin=inch/2
            )
            
            # Contenido del PDF
            elements = []
            styles = getSampleStyleSheet()
            
            # Encabezado
            elements.append(Paragraph(f"Factura #{invoice.invoice_number}", styles['Title']))
            elements.append(Paragraph(f"Fecha: {invoice.issue_date.strftime('%d/%m/%Y')}", styles['Normal']))
            elements.append(Paragraph(f"Cliente: {invoice.customer_name}", styles['Normal']))
            elements.append(Paragraph(f"Email: {invoice.customer_email}", styles['Normal']))
            
            # Tabla de items
            items_data = [['Producto', 'Cantidad', 'Precio Unitario', 'Total']]
            for item in invoice.invoice_items.all():
                items_data.append([
                    item.product.name,
                    str(item.quantity),
                    f"${item.unit_price:,.2f}",
                    f"${item.total:,.2f}"
                ])
            
            # Estilo de la tabla
            table = Table(items_data)
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 14),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 12),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            elements.append(table)
            
            # Totales
            elements.append(Paragraph(f"Subtotal: ${invoice.subtotal:,.2f}", styles['Normal']))
            for tax in invoice.taxes.all():
                elements.append(Paragraph(
                    f"{tax.get_tax_type_display()}: ${tax.amount:,.2f}",
                    styles['Normal']
                ))
            elements.append(Paragraph(f"Total: ${invoice.total:,.2f}", styles['Normal']))
            
            # Generar PDF
            doc.build(elements)
            
            # Preparar la respuesta
            buffer.seek(0)
            response = HttpResponse(buffer, content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="invoice_{invoice.invoice_number}.pdf"'
            
            return response
        except Exception as e:
            logger.error(f"Error generating PDF: {str(e)}")
            return Response(
                {"error": "Error al generar el PDF"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['GET'])
    def summary(self, request):
        """Obtiene un resumen de facturación por período"""
        try:
            company_id = request.query_params.get('company_id')
            period = request.query_params.get('period', 'month')  # month, quarter, year
            
            if not company_id:
                return Response(
                    {"error": "Se requiere company_id"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            today = timezone.now()
            
            if period == 'month':
                start_date = today - timedelta(days=30)
                date_trunc = 'day'
            elif period == 'quarter':
                start_date = today - timedelta(days=90)
                date_trunc = 'week'
            else:  # year
                start_date = today - timedelta(days=365)
                date_trunc = 'month'
            
            summary = Invoice.objects.filter(
                company_id=company_id,
                created_at__gte=start_date
            ).values(
                'status'
            ).annotate(
                count=Count('id'),
                total_amount=Sum('total')
            )
            
            trends = Invoice.objects.filter(
                company_id=company_id,
                created_at__gte=start_date
            ).extra(
                select={'period': f"date_trunc('{date_trunc}', created_at)"}
            ).values(
                'period'
            ).annotate(
                count=Count('id'),
                total_amount=Sum('total')
            ).order_by('period')
            
            return Response({
                'summary': summary,
                'trends': trends
            })
        except Exception as e:
            logger.error(f"Error getting summary: {str(e)}")
            return Response(
                {"error": "Error al obtener el resumen"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )