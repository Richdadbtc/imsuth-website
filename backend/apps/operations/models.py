from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

from apps.common.models import TimeStampedModel


class ApprovalRequest(TimeStampedModel):
    class Type(models.TextChoices):
        CATALOGUE_ACTIVATION = "catalogue_activation", "Catalogue activation"
        REFUND = "refund", "Refund"
        REVERSAL = "reversal", "Reversal"
        INVOICE_VOID = "invoice_void", "Invoice void"
        MANUAL_MATCH = "manual_match", "Manual reconciliation match"

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"

    request_type = models.CharField(max_length=32, choices=Type.choices, db_index=True)
    requested_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="approval_requests")
    object_type = models.CharField(max_length=80)
    object_id = models.CharField(max_length=80)
    amount = models.DecimalField(max_digits=19, decimal_places=2, null=True, blank=True)
    reason = models.TextField()
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.PENDING, db_index=True)

    class Meta:
        ordering = ("-created_at",)


class ApprovalDecision(models.Model):
    request = models.ForeignKey(ApprovalRequest, on_delete=models.PROTECT, related_name="decisions")
    decided_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    approved = models.BooleanField()
    reason = models.TextField()
    decided_at = models.DateTimeField(auto_now_add=True)


class Refund(TimeStampedModel):
    class Status(models.TextChoices):
        REQUESTED = "requested", "Requested"
        APPROVED_PENDING_EXECUTION = "approved_pending_execution", "Approved — pending provider execution"
        REJECTED = "rejected", "Rejected"
        COMPLETED = "completed", "Completed"
        FAILED = "failed", "Failed"

    payment = models.ForeignKey("payments.Payment", on_delete=models.PROTECT, related_name="refunds")
    amount = models.DecimalField(max_digits=19, decimal_places=2)
    reason = models.TextField()
    requested_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="refunds_requested")
    approval = models.OneToOneField(ApprovalRequest, on_delete=models.PROTECT, related_name="refund")
    status = models.CharField(max_length=40, choices=Status.choices, default=Status.REQUESTED)
    provider_reference = models.CharField(max_length=120, blank=True)

    class Meta:
        constraints = [models.CheckConstraint(condition=models.Q(amount__gt=0), name="refund_amount_positive")]


class Reversal(TimeStampedModel):
    class Status(models.TextChoices):
        REQUESTED = "requested", "Requested"
        APPROVED_PENDING_EXECUTION = "approved_pending_execution", "Approved — pending execution"
        REJECTED = "rejected", "Rejected"
        COMPLETED = "completed", "Completed"

    payment = models.ForeignKey("payments.Payment", on_delete=models.PROTECT, related_name="reversals")
    reason = models.TextField()
    requested_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="reversals_requested")
    approval = models.OneToOneField(ApprovalRequest, on_delete=models.PROTECT, related_name="reversal")
    status = models.CharField(max_length=40, choices=Status.choices, default=Status.REQUESTED)


class Notification(TimeStampedModel):
    class Channel(models.TextChoices):
        IN_APP = "in_app", "In-app"
        EMAIL = "email", "Email"
        SMS = "sms", "SMS"

    event_type = models.CharField(max_length=80, db_index=True)
    subject = models.CharField(max_length=160)
    body = models.TextField()
    channel = models.CharField(max_length=16, choices=Channel.choices, default=Channel.IN_APP)
    sensitive = models.BooleanField(default=False)


class NotificationRecipient(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        SENT = "sent", "Sent"
        FAILED = "failed", "Failed"

    notification = models.ForeignKey(Notification, on_delete=models.PROTECT, related_name="recipients")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    destination = models.CharField(max_length=254, blank=True)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.PENDING)
    attempts = models.PositiveSmallIntegerField(default=0)
    last_attempt_at = models.DateTimeField(null=True, blank=True)
    last_error = models.CharField(max_length=255, blank=True)
    read_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=("notification", "user"), name="unique_notification_user")]


class Settlement(TimeStampedModel):
    provider = models.CharField(max_length=64)
    settlement_reference = models.CharField(max_length=120)
    settlement_date = models.DateField()
    amount = models.DecimalField(max_digits=19, decimal_places=2)
    currency = models.CharField(max_length=3, default="NGN")

    class Meta:
        constraints = [models.UniqueConstraint(fields=("provider", "settlement_reference"), name="unique_provider_settlement")]


class ReconciliationBatch(TimeStampedModel):
    class Status(models.TextChoices):
        IMPORTED = "imported", "Imported"
        REVIEW_REQUIRED = "review_required", "Review required"
        RECONCILED = "reconciled", "Reconciled"
        CLOSED = "closed", "Closed"

    source = models.CharField(max_length=64)
    period_start = models.DateField()
    period_end = models.DateField()
    file_digest = models.CharField(max_length=64, unique=True)
    status = models.CharField(max_length=24, choices=Status.choices, default=Status.IMPORTED)
    imported_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    total_amount = models.DecimalField(max_digits=19, decimal_places=2, default=Decimal("0.00"))


class ReconciliationItem(TimeStampedModel):
    class Status(models.TextChoices):
        MATCHED = "matched", "Matched"
        UNMATCHED = "unmatched", "Unmatched"
        AMOUNT_MISMATCH = "amount_mismatch", "Amount mismatch"
        MANUAL_REVIEW = "manual_review", "Manual review"
        RESOLVED = "resolved", "Resolved"

    batch = models.ForeignKey(ReconciliationBatch, on_delete=models.PROTECT, related_name="items")
    external_reference = models.CharField(max_length=160, db_index=True)
    amount = models.DecimalField(max_digits=19, decimal_places=2)
    currency = models.CharField(max_length=3, default="NGN")
    transaction_date = models.DateTimeField()
    payment = models.ForeignKey("payments.Payment", null=True, blank=True, on_delete=models.PROTECT, related_name="reconciliation_items")
    settlement = models.ForeignKey(Settlement, null=True, blank=True, on_delete=models.PROTECT, related_name="items")
    status = models.CharField(max_length=24, choices=Status.choices, default=Status.UNMATCHED, db_index=True)
    resolution_reason = models.TextField(blank=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=("batch", "external_reference"), name="unique_batch_external_reference")]
