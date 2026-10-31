from rest_framework import permissions, viewsets
from rest_framework.decorators import action
from django.db import transaction

from apps.accounts.models import User
from .models import Invoice
from .serializers import InvoiceSerializer


class InvoicePermission(permissions.BasePermission):
    write_roles = {User.Role.FRONT_DESK, User.Role.CASHIER, User.Role.FINANCE}

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        return request.method in permissions.SAFE_METHODS or request.user.role in self.write_roles


class InvoiceViewSet(viewsets.ModelViewSet):
    queryset = Invoice.objects.select_related("patient", "department", "created_by").prefetch_related("items").all()
    serializer_class = InvoiceSerializer
    permission_classes = (InvoicePermission,)
    http_method_names = ("get", "post", "head", "options")
    @transaction.atomic
    def perform_create(self,serializer):
        from apps.auditlog.models import AuditEvent
        obj=serializer.save()
        AuditEvent.record("invoice.created",actor=self.request.user,obj=obj)

    def get_queryset(self):
        from apps.common.revenue_api import scoped
        return scoped(super().get_queryset(), self.request.user)

    @action(detail=True,methods=['post'],url_path='corrections')
    @transaction.atomic
    def corrections(self,request,pk=None):
        from rest_framework import serializers
        from rest_framework.exceptions import ValidationError
        from rest_framework.response import Response
        from apps.auditlog.models import AuditEvent
        from .models import BillingCorrectionRequest
        invoice=self.get_object()
        reason=serializers.CharField(min_length=5,max_length=255).run_validation(request.data.get('reason'))
        change=request.data.get('requested_change')
        if not isinstance(change,dict) or not change:raise ValidationError({'requested_change':'A non-empty JSON object is required.'})
        obj=BillingCorrectionRequest.objects.create(invoice=invoice,requested_by=request.user,reason=reason,requested_change=change)
        AuditEvent.record('billing.correction_requested',actor=request.user,obj=obj)
        return Response({'id':str(obj.pk),'status':obj.status},status=201)

    @action(detail=True)
    def balance(self, request, pk=None):
        from rest_framework.response import Response
        obj = self.get_object()
        return Response({'invoice': str(obj.pk), 'total': obj.total_amount, 'paid': obj.amount_paid, 'balance': obj.outstanding_balance, 'currency': obj.currency})

    search_fields = ("invoice_number", "payment_reference", "patient__patient_id", "patient__first_name", "patient__last_name")
    filterset_fields = {"status":["exact","in"],"department":["exact"],"patient":["exact"],"currency":["exact"]}
