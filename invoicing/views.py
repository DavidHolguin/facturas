from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db.models import Sum, Count, F, Q
from django.utils import timezone
from django.http import HttpResponse
from datetime import datetime, timedelta
from .models import CustomerUser, Invoice, InvoiceItem
from .serializers import CustomerUserSerializer, CustomerLookupSerializer, InvoiceSerializer, InvoiceItemSerializer
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib import colors
import io
import logging

from rest_framework.views import APIView
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate
from .serializers import LoginSerializer

class LoginView(APIView):
    permission_classes = []  # Permite acceso sin autenticación
    
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user = authenticate(
            email=serializer.validated_data['email'],
            password=serializer.validated_data['password']
        )
        
        if not user:
            return Response(
                {'error': 'Credenciales inválidas'},
                status=status.HTTP_401_UNAUTHORIZED
            )
            
        token, _ = Token.objects.get_or_create(user=user)
        
        return Response({
            'token': token.key,
            'user': CustomerUserSerializer(user).data
        })

logger = logging.getLogger(__name__)

class CustomerUserViewSet(viewsets.ModelViewSet):
    queryset = CustomerUser.objects.all()
    serializer_class = CustomerUserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return CustomerUser.objects.filter(company__user=self.request.user)

    @action(detail=False, methods=['POST'])
    def lookup(self, request):
        """Búsqueda de clientes por diferentes campos"""
        try:
            serializer = CustomerLookupSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            search_term = serializer.validated_data['search_term']
            
            customers = CustomerUser.objects.filter(
                Q(email__icontains=search_term) |
                Q(identification_number__icontains=search_term) |
                Q(phone_number__icontains=search_term) |
                Q(first_name__icontains=search_term) |
                Q(last_name__icontains=search_term)
            )[:5]
            
            return Response(CustomerUserSerializer(customers, many=True).data)
        except Exception as e:
            logger.error(f"Error in customer lookup: {str(e)}")
            return Response(
                {"error": "Error en la búsqueda de clientes"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

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
        customer_id = self.request.query_params.get('customer_id', None)

        if status:
            queryset = queryset.filter(status=status)
        if date_from:
            queryset = queryset.filter(issue_date__gte=date_from)
        if date_to:
            queryset = queryset.filter(issue_date__lte=date_to)
        if company_id:
            queryset = queryset.filter(company_id=company_id)
        if customer_id:
            queryset = queryset.filter(customer_id=customer_id)

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
            request.data['internal_id'] = Invoice.generate_internal_id(company_id)

            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)
            
            # Crear los items de la factura
            items_data = request.data.get('items', [])
            for item_data in items_data:
                item_data['invoice'] = serializer.instance.id
                item_serializer = InvoiceItemSerializer(data=item_data)
                item_serializer.is_valid(raise_exception=True)
                item_serializer.save()

            # Recalcular totales
            serializer.instance.calculate_totals()
            
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
            today = timezone.now()
            month_start = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            
            total_invoices = Invoice.objects.filter(company_id=company_id).count()
            total_amount = Invoice.objects.filter(company_id=company_id).aggregate(
                total=Sum('total')
            )['total'] or 0
            
            monthly_stats = Invoice.objects.filter(
                company_id=company_id,
                created_at__gte=month_start
            ).aggregate(
                count=Count('id'),
                total=Sum('total')
            )

            # Facturas por vencer
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
                .values('customer__first_name', 'customer__last_name')\
                .annotate(
                    total_invoices=Count('id'),
                    total_amount=Sum('total')
                )\
                .order_by('-total_amount')[:5]

            response_data = {
                'total_invoices': total_invoices,
                'total_amount': total_amount,
                'monthly_invoices': monthly_stats['count'] or 0,
                'monthly_amount': monthly_stats['total'] or 0,
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
            .values(
                'id', 'invoice_number', 'customer__first_name',
                'customer__last_name', 'total', 'status', 'updated_at'
            )
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
            
            # Enviar email si la factura pasa a estado EMITIDA
            if new_status == 'EMITIDA':
                invoice.send_invoice_email()
            
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
            buffer = self.generate_pdf_file(invoice)
            
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

    @staticmethod
    def generate_pdf_file(invoice):
        """Genera un archivo PDF de la factura"""
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
        elements.append(Paragraph(f"Cliente: {invoice.customer.get_full_name()}", styles['Normal']))
        elements.append(Paragraph(f"Email: {invoice.customer.email}", styles['Normal']))
        
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
        return buffer

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

class InvoiceItemViewSet(viewsets.ModelViewSet):
    serializer_class = InvoiceItemSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return InvoiceItem.objects.filter(
            invoice__company__user=self.request.user
        )

    def create(self, request, *args, **kwargs):
        try:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)
            
            # Recalcular totales de la factura
            invoice = serializer.instance.invoice
            invoice.calculate_totals()
            
            headers = self.get_success_headers(serializer.data)
            return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
        except Exception as e:
            logger.error(f"Error creating invoice item: {str(e)}")
            return Response(
                {"error": "Error al crear el ítem de la factura"},
                status=status.HTTP_400_BAD_REQUEST
            )

    def update(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            serializer = self.get_serializer(instance, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            self.perform_update(serializer)
            
            # Recalcular totales de la factura
            invoice = serializer.instance.invoice
            invoice.calculate_totals()
            
            return Response(serializer.data)
        except Exception as e:
            logger.error(f"Error updating invoice item: {str(e)}")
            return Response(
                {"error": "Error al actualizar el ítem de la factura"},
                status=status.HTTP_400_BAD_REQUEST
            )

    def destroy(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            invoice = instance.invoice
            self.perform_destroy(instance)
            
            # Recalcular totales de la factura
            invoice.calculate_totals()
            
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            logger.error(f"Error deleting invoice item: {str(e)}")
            return Response(
                {"error": "Error al eliminar el ítem de la factura"},
                status=status.HTTP_400_BAD_REQUEST
            )