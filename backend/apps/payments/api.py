import json

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from rest_framework import permissions, status, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema

from apps.accounts.models import User
from .models import Payment, Receipt
from .serializers import PaymentSerializer, ReceiptSerializer, TestWebhookResponseSerializer, TestWebhookSerializer
from .services import DeterministicTestAdapter, confirm_payment_event


class PaymentPermission(permissions.BasePermission):
    write_roles = {User.Role.CASHIER, User.Role.FINANCE}

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        return request.method in permissions.SAFE_METHODS or request.user.role in self.write_roles


class PaymentViewSet(viewsets.ModelViewSet):
    queryset = Payment.objects.select_related("invoice__patient", "invoice__department", "initiated_by", "receipt").prefetch_related("invoice__items").all()
    serializer_class = PaymentSerializer
    permission_classes = (PaymentPermission,)
    http_method_names = ("get", "post", "head", "options")
    @transaction.atomic
    def perform_create(self,serializer):
        from apps.auditlog.models import AuditEvent
        obj=serializer.save()
        AuditEvent.record("payment.intent_recorded",actor=self.request.user,obj=obj)

    def get_queryset(self):
        from apps.common.revenue_api import scoped
        return scoped(super().get_queryset(), self.request.user, 'invoice__department_id')
    search_fields = ("reference", "provider_reference", "invoice__invoice_number", "invoice__patient__patient_id")
    filterset_fields = {"status":["exact","in"],"channel":["exact"],"provider":["exact"],"currency":["exact"],"invoice":["exact"],"invoice__patient":["exact"]}


class ReceiptViewSet(viewsets.ReadOnlyModelViewSet):
    filterset_fields=('payment','invoice')
    queryset = Receipt.objects.select_related("payment", "invoice").all()
    serializer_class = ReceiptSerializer
    permission_classes = (permissions.IsAuthenticated,)
    def get_queryset(self):
        from apps.common.revenue_api import scoped
        return scoped(super().get_queryset(), self.request.user, 'invoice__department_id')
    search_fields = ("receipt_number", "payment__reference", "invoice__invoice_number")


class TestWebhookView(APIView):
    authentication_classes = ()
    permission_classes = (permissions.AllowAny,)

    @extend_schema(request=TestWebhookSerializer, responses={200: TestWebhookResponseSerializer})
    def post(self, request):
        raw_body = request.body
        signature = request.headers.get("X-Test-Signature", "")
        try:
            payment, processed = confirm_payment_event(adapter=DeterministicTestAdapter(), raw_body=raw_body, signature=signature)
        except (PermissionDenied, ValidationError, json.JSONDecodeError) as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response({"payment": payment.reference, "status": payment.status, "processed": processed})


from rest_framework.decorators import action
from rest_framework import serializers
from rest_framework.exceptions import ValidationError as APIValidationError


@action(detail=True, methods=['post'])
def retry(self, request, pk=None):
    payment = self.get_object()
    if payment.status not in {'failed', 'expired'}:
        raise APIValidationError('Only failed or expired payments may be retried.')
    key = serializers.CharField(max_length=100).run_validation(request.data.get('idempotency_key'))
    try:
        obj = Payment.create_intent(invoice=payment.invoice, channel=payment.channel, initiated_by=request.user, idempotency_key=key, provider=payment.provider)
    except ValidationError as error:
        raise APIValidationError(error.messages)
    return Response(self.get_serializer(obj).data, status=201)


@action(detail=True, methods=['post'])
def verify(self, request, pk=None):
    payment = self.get_object()
    if payment.status == Payment.Status.CONFIRMED:
        return Response(self.get_serializer(payment).data)
    return Response({'detail':'Authoritative provider verification is not configured. Payment has not been confirmed.','status':payment.status},status=503)


PaymentViewSet.retry = retry
PaymentViewSet.verify = verify

@action(detail=True, methods=['get'], url_path='verification-status')
def verification_status(self,request,pk=None):
    obj=self.get_object()
    return Response({'id':str(obj.pk),'status':obj.status,'confirmed_at':obj.confirmed_at})

PaymentViewSet.verification_status=verification_status

@action(detail=True,methods=['get'],url_path='print')
def print_receipt(self,request,pk=None):
    from django.http import HttpResponse
    from django.template.loader import render_to_string
    from apps.auditlog.models import AuditEvent
    obj=self.get_object()
    if obj.payment.status != Payment.Status.CONFIRMED:
        raise APIValidationError('The underlying payment is not currently confirmed.')
    from .slip_reference import validate_slip_reference
    try:validate_slip_reference(obj.payment.submitted_reference,obj.payment.channel)
    except ValidationError as error:raise APIValidationError(error.messages) from error
    AuditEvent.record('receipt.print_viewed',actor=request.user,obj=obj)
    paper=request.query_params.get('paper','a4')
    if paper not in {'a4','thermal'}:raise APIValidationError('Choose A4 or thermal paper.')
    from .receipt_assets import receipt_images
    html=render_to_string('paypoint/receipt.html',{'receipt':obj,'items':obj.invoice.items.all(),'thermal':paper=='thermal',**receipt_images(obj)})
    response=HttpResponse(html);response['Cache-Control']='private, no-store';return response

ReceiptViewSet.print_receipt=print_receipt
