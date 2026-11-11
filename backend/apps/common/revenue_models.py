"""Operational records; existing invoices, payments and receipts remain authoritative."""
from django.conf import settings
from django.db import models
from .models import TimeStampedModel


class ServiceDelivery(TimeStampedModel):
    item = models.OneToOneField('billing.InvoiceItem', on_delete=models.PROTECT, related_name='delivery')
    receipt = models.ForeignKey('payments.Receipt', on_delete=models.PROTECT)
    delivered_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    notes = models.CharField(max_length=2000, blank=True)


class CashPoint(TimeStampedModel):
    name = models.CharField(max_length=120, unique=True)
    location = models.CharField(max_length=200)
    department = models.ForeignKey('catalogue.Department', on_delete=models.PROTECT, null=True, blank=True)
    assigned_officer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True)
    daily_limit = models.DecimalField(max_digits=19, decimal_places=2, null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ('name',)
        constraints = [models.CheckConstraint(condition=models.Q(daily_limit__isnull=True) | models.Q(daily_limit__gt=0), name='cash_point_limit_positive')]


class CashApprovalLimit(TimeStampedModel):
    role = models.CharField(max_length=32, unique=True)
    amount = models.DecimalField(max_digits=19, decimal_places=2)
    approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    policy_reference = models.CharField(max_length=160)

    class Meta:
        constraints = [models.CheckConstraint(condition=models.Q(amount__gt=0), name='cash_approval_limit_positive')]


class CashOrder(TimeStampedModel):
    cash_point = models.ForeignKey(CashPoint, on_delete=models.PROTECT, related_name='orders')
    amount = models.DecimalField(max_digits=19, decimal_places=2)
    purpose = models.CharField(max_length=200)
    description = models.CharField(max_length=2000, blank=True)
    requested_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='cash_requests')
    decided_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.PROTECT, related_name='cash_decisions')
    status = models.CharField(max_length=16, default='pending', choices=[('pending','Pending'),('approved','Approved'),('rejected','Rejected')])
    decided_at = models.DateTimeField(null=True)
    decision_notes = models.CharField(max_length=2000, blank=True)
    idempotency_key = models.CharField(max_length=100, unique=True)

    class Meta:
        ordering = ('-created_at',)
        constraints = [models.CheckConstraint(condition=models.Q(amount__gt=0), name='cash_order_positive')]


class Alert(TimeStampedModel):
    department = models.ForeignKey('catalogue.Department', null=True, on_delete=models.PROTECT)
    alert_type = models.CharField(max_length=80)
    severity = models.CharField(max_length=16, choices=[(s,s.title()) for s in ('critical','high','medium','low')])
    status = models.CharField(max_length=16, default='open', choices=[('open','Open'),('in_review','In Review'),('resolved','Resolved')])
    description = models.CharField(max_length=2000)
    related_type = models.CharField(max_length=80, blank=True)
    related_id = models.CharField(max_length=100, blank=True)
    assigned_to = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.PROTECT, related_name='revenue_alerts')
    resolved_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.PROTECT, related_name='resolved_revenue_alerts')
    resolved_at = models.DateTimeField(null=True)
    resolution_notes = models.CharField(max_length=2000, blank=True)

    class Meta:
        ordering = ('-created_at',)
        constraints = [models.UniqueConstraint(fields=('alert_type','related_type','related_id'),condition=~models.Q(related_id=''),name='unique_revenue_alert_entity')]


class TariffProposal(TimeStampedModel):
    service = models.ForeignKey('catalogue.Service', on_delete=models.PROTECT)
    amount = models.DecimalField(max_digits=19, decimal_places=2)
    effective_from = models.DateTimeField()
    reason = models.CharField(max_length=2000)
    requested_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='tariff_proposals')
    decided_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.PROTECT, related_name='tariff_proposal_decisions')
    status = models.CharField(max_length=16, default='pending', choices=[('pending','Pending'),('approved','Approved'),('rejected','Rejected')])
    decision_notes = models.CharField(max_length=2000, blank=True)
    tariff = models.OneToOneField('catalogue.TariffVersion', null=True, on_delete=models.PROTECT)

    class Meta:
        ordering = ('-created_at',)
        constraints = [models.CheckConstraint(condition=models.Q(amount__gt=0), name='tariff_proposal_positive')]


class CashCollectionEvidence(TimeStampedModel):
    cash_point = models.ForeignKey(CashPoint,on_delete=models.PROTECT,related_name='collection_evidence')
    payment = models.OneToOneField('payments.Payment',on_delete=models.PROTECT,related_name='cash_evidence')
    recorded_by = models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.PROTECT)
    evidence_reference = models.CharField(max_length=160)
    attachment = models.OneToOneField('common.PrivateAttachment',null=True,blank=True,on_delete=models.PROTECT)


class RecordedPayment(TimeStampedModel):
    """Immutable capture context for an invoice/payment created at a collection point."""
    idempotency_key = models.CharField(max_length=100, unique=True)
    fingerprint = models.CharField(max_length=64)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    cash_point = models.ForeignKey(CashPoint, on_delete=models.PROTECT)
    cash_order = models.ForeignKey(CashOrder, null=True, blank=True, on_delete=models.PROTECT)
    payment = models.OneToOneField('payments.Payment', on_delete=models.PROTECT, related_name='recorded_context')
    patient_type = models.CharField(max_length=16, default='regular', choices=[('regular','Regular'),('nhis','NHIS'),('imshia','IMSHIA')])
    base_total = models.DecimalField(max_digits=19, decimal_places=2, null=True, blank=True)
    discount_total = models.DecimalField(max_digits=19, decimal_places=2, default=0)
    approved_total = models.DecimalField(max_digits=19, decimal_places=2)
    entered_total = models.DecimalField(max_digits=19, decimal_places=2)
    override_reason = models.CharField(max_length=500, blank=True)
