"""Atomic point-of-collection capture. A supplied reference never confirms payment."""
import hashlib
import json
from decimal import Decimal
from datetime import timedelta
from django.db import transaction, IntegrityError
from django.core.exceptions import ValidationError as DjangoValidationError
from django.utils import timezone
from rest_framework import serializers, permissions
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView
from apps.registry.models import Patient
from apps.catalogue.models import Department, Service
from apps.billing.models import Invoice
from apps.billing.serializers import InvoiceSerializer
from apps.payments.models import Payment, Receipt
from apps.payments.serializers import PaymentSerializer
from apps.auditlog.models import AuditEvent
from .models import CashPoint, CashOrder, RecordedPayment, Alert
from .revenue_api import scoped


class CaptureInput(serializers.Serializer):
    patient = serializers.UUIDField()
    department = serializers.UUIDField()
    service = serializers.UUIDField()
    cash_point = serializers.UUIDField()
    cash_order = serializers.UUIDField(required=False, allow_null=True, default=None)
    quantity = serializers.IntegerField(min_value=1, max_value=100, default=1)
    amount = serializers.DecimalField(max_digits=19, decimal_places=2, min_value=Decimal('0.01'))
    override_reason = serializers.CharField(max_length=500, allow_blank=True, default='')
    channel = serializers.ChoiceField(choices=Payment.Channel.choices)
    submitted_reference = serializers.CharField(max_length=120)
    reported_paid_at = serializers.DateTimeField()
    remarks = serializers.CharField(max_length=500, allow_blank=True, default='')
    idempotency_key = serializers.UUIDField()

    def validate_reported_paid_at(self,value):
        if value > timezone.now()+timedelta(minutes=1): raise ValidationError('Payment time cannot be in the future.')
        return value


def capture_payload(context):
    return {'payment':PaymentSerializer(context.payment).data,'invoice':InvoiceSerializer(context.payment.invoice).data,'price_changed':context.entered_total!=context.approved_total,'receipt_issued':hasattr(context.payment,'receipt')}


class RecordPaymentView(APIView):
    permission_classes=[permissions.IsAuthenticated]

    def get(self,request):
        points=scoped(CashPoint.objects.filter(is_active=True),request.user)
        orders=scoped(CashOrder.objects.filter(status='approved',cash_point__is_active=True),request.user,'cash_point__department_id')
        receipts=scoped(Receipt.objects.select_related('payment','invoice__patient','invoice__department').prefetch_related('invoice__items__delivery'),request.user,'invoice__department_id').order_by('-issued_at')[:10]
        latest=[]
        for receipt in receipts:
            items=list(receipt.invoice.items.all());used=sum(hasattr(item,'delivery') for item in items)
            latest.append({'id':str(receipt.pk),'receipt_number':receipt.receipt_number,'patient_name':str(receipt.invoice.patient),'service':', '.join(item.description for item in items),'department':receipt.invoice.department.name,'amount':receipt.amount,'payment_status':receipt.payment.status,'service_status':'Used' if items and used==len(items) else 'Partially used' if used else 'Not yet used','issued_at':receipt.issued_at})
        return Response({'cash_points':[{'id':str(p.pk),'name':p.name,'department':str(p.department_id)} for p in points],'cash_orders':[{'id':str(o.pk),'cash_point':str(o.cash_point_id),'amount':o.amount,'purpose':o.purpose} for o in orders],'receipts':latest,'can_record':request.user.role in {'super_admin','finance','cashier'}})

    def post(self,request):
        if request.user.role not in {'super_admin','finance','cashier'}: raise PermissionDenied('Only collection officers and finance administrators may record payments.')
        serializer=CaptureInput(data=request.data);serializer.is_valid(raise_exception=True);data=serializer.validated_data
        fingerprint=hashlib.sha256(json.dumps(data,sort_keys=True,default=str).encode()).hexdigest()
        try:
            with transaction.atomic():
                point=scoped(CashPoint.objects.select_for_update().filter(pk=data['cash_point'],is_active=True),request.user).first()
                if not point: raise ValidationError({'cash_point':'Select an active cash point within your access scope.'})
                if request.user.role=='cashier' and point.assigned_officer_id!=request.user.pk: raise PermissionDenied('This cash point is assigned to another officer.')
                old=RecordedPayment.objects.select_related('payment__invoice').filter(idempotency_key=str(data['idempotency_key'])).first()
                if old:
                    if old.created_by_id!=request.user.pk or old.fingerprint!=fingerprint: raise ValidationError('This request key belongs to a different submission.')
                    return Response(capture_payload(old))
                if Payment.objects.filter(channel=data['channel'],submitted_reference=data['submitted_reference']).exists():raise ValidationError({'submitted_reference':'This payment reference has already been recorded. Check the existing transaction.'})
                department=scoped(Department.objects.filter(pk=data['department'],is_active=True),request.user,'pk').first()
                if not department: raise ValidationError({'department':'Select an active permitted department.'})
                from .api import RevenuePatientViewSet
                patient_view=RevenuePatientViewSet();patient_view.request=request
                patients=patient_view.get_queryset().filter(status='active')
                patient=patients.filter(pk=data['patient']).first()
                if not patient:raise ValidationError({'patient':'Select an active patient within your access scope.'})
                service=Service.objects.filter(pk=data['service'],department=department,is_active=True).first()
                if not service:raise ValidationError({'service':'Select an active service in this department.'})
                order=None
                if data['cash_order']:
                    if data['channel']!='cash':raise ValidationError({'cash_order':'Standing orders may be linked only to cash payments.'})
                    order=CashOrder.objects.select_for_update().filter(pk=data['cash_order'],cash_point=point,status='approved').first()
                    if not order:raise ValidationError({'cash_order':'Select an approved order for this cash point.'})
                invoice=Invoice.create_from_items(patient=patient,department=department,item_requests=[{'service':service,'quantity':data['quantity']}],created_by=request.user,idempotency_key='record:'+str(data['idempotency_key']),capture_total=data['amount'],capture_reason=data['override_reason'])
                if invoice.currency!='NGN':raise ValidationError('This capture flow accepts NGN tariffs only.')
                item=invoice.items.select_related('tariff_version').get()
                approved=item.tariff_version.amount*item.quantity
                active=RecordedPayment.objects.exclude(payment__status__in=['failed','expired','refunded','reversed'])
                if order:
                    used=sum(active.filter(cash_order=order).values_list('entered_total',flat=True),Decimal('0'))
                    if used+data['amount']>order.amount:raise ValidationError({'cash_order':'The approved order amount has insufficient remaining capacity.'})
                if data['channel']=='cash':
                    used=sum(active.filter(cash_point=point,payment__channel='cash',created_at__date=timezone.localdate()).values_list('entered_total',flat=True),Decimal('0'))
                    if used+data['amount']>point.daily_limit:raise ValidationError({'cash_point':'This cash point daily collection limit would be exceeded.'})
                payment=Payment.create_intent(invoice=invoice,channel=data['channel'],initiated_by=request.user,idempotency_key='record:'+str(data['idempotency_key']))
                payment.submitted_reference=data['submitted_reference'];payment.reported_paid_at=data['reported_paid_at'];payment.remarks=data['remarks'];payment.save(update_fields=['submitted_reference','reported_paid_at','remarks','updated_at'])
                context=RecordedPayment.objects.create(idempotency_key=str(data['idempotency_key']),fingerprint=fingerprint,created_by=request.user,cash_point=point,cash_order=order,payment=payment,approved_total=approved,entered_total=data['amount'],override_reason=data['override_reason'])
                AuditEvent.record('payment.recorded_at_point',actor=request.user,obj=payment,request=request,metadata={'cash_point':str(point.pk),'cash_order':str(order.pk) if order else None,'approved_total':str(approved),'entered_total':str(data['amount']),'override_reason':data['override_reason']})
                if approved!=data['amount']:
                    Alert.objects.create(department=department,alert_type='service_price_change',severity='medium',description='Recorded payment differs from the approved tariff; review the recorded reason.',related_type='payments.Payment',related_id=str(payment.pk))
                return Response(capture_payload(context),status=201)
        except DjangoValidationError as error:raise ValidationError(error.messages) from error
        except IntegrityError as error:raise ValidationError('Concurrent capture conflict; retry the same request key.') from error
