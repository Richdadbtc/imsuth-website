import secrets
from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.utils import timezone

from apps.common.models import Sequence, TimeStampedModel


class Payment(TimeStampedModel):
    class Channel(models.TextChoices):
        BANK_TRANSFER = "bank_transfer", "Bank transfer"
        POS = "pos", "POS"
        CASH = "cash", "Cash"
        ONLINE = "online", "Online gateway"

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        AWAITING_OFFLINE_VERIFICATION = "awaiting_offline_verification", "Awaiting offline verification"
        CONFIRMED = "confirmed", "Confirmed"
        FAILED = "failed", "Failed"
        EXPIRED = "expired", "Expired"
        REVIEW_REQUIRED = "review_required", "Review required"
        REFUND_PENDING = "refund_pending", "Refund pending"
        REFUNDED = "refunded", "Refunded"
        REVERSAL_PENDING = "reversal_pending", "Reversal pending"
        REVERSED = "reversed", "Reversed"

    invoice = models.ForeignKey("billing.Invoice", on_delete=models.PROTECT, related_name="payments")
    reference = models.CharField(max_length=40, unique=True, editable=False, db_index=True)
    idempotency_key = models.CharField(max_length=100, unique=True)
    channel = models.CharField(max_length=32, choices=Channel.choices)
    provider = models.CharField(max_length=64, blank=True)
    provider_reference = models.CharField(max_length=120, blank=True, db_index=True)
    cash_receiver = models.CharField(max_length=100, blank=True)
    submitted_reference = models.CharField(max_length=120, blank=True)
    reported_paid_at = models.DateTimeField(null=True,blank=True)
    remarks = models.CharField(max_length=500,blank=True)
    amount = models.DecimalField(max_digits=19, decimal_places=2)
    currency = models.CharField(max_length=3, default="NGN")
    status = models.CharField(max_length=40, choices=Status.choices, default=Status.PENDING, db_index=True)
    initiated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="initiated_payments")
    confirmed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ("-created_at",)
        constraints = [models.CheckConstraint(condition=models.Q(amount__gt=0), name="payment_amount_positive")]

    @classmethod
    def create_intent(cls, *, invoice, channel, initiated_by, idempotency_key, provider=""):
        with transaction.atomic():
            existing = cls.objects.filter(idempotency_key=idempotency_key).first()
            if existing:
                return existing
            locked_invoice = invoice.__class__.objects.select_for_update().get(pk=invoice.pk)
            existing = cls.objects.filter(idempotency_key=idempotency_key).first()
            if existing:
                return existing
            if locked_invoice.status not in {locked_invoice.Status.ISSUED, locked_invoice.Status.PARTIALLY_PAID}:
                raise ValidationError("Invoice is not payable.")
            amount = locked_invoice.outstanding_balance
            if amount <= 0:
                raise ValidationError("Invoice has no outstanding balance.")
            year = timezone.localdate().year
            number = Sequence.next_value(f"payment:{year}")
            offline = channel in {cls.Channel.CASH, cls.Channel.POS}
            return cls.objects.create(
                invoice=locked_invoice,
                reference=f"PMT-{year}-{number:010d}",
                idempotency_key=idempotency_key,
                channel=channel,
                provider=provider,
                amount=amount,
                currency=locked_invoice.currency,
                status=cls.Status.AWAITING_OFFLINE_VERIFICATION if offline else cls.Status.PENDING,
                initiated_by=initiated_by,
            )

    def __str__(self):
        return self.reference


class PaymentEvent(models.Model):
    id = models.UUIDField(primary_key=True, editable=False)
    payment = models.ForeignKey(Payment, on_delete=models.PROTECT, related_name="events")
    provider = models.CharField(max_length=64)
    provider_event_id = models.CharField(max_length=160)
    event_type = models.CharField(max_length=80)
    received_at = models.DateTimeField(auto_now_add=True)
    signature_verified = models.BooleanField(default=False)
    payload_digest = models.CharField(max_length=64)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ("received_at",)
        constraints = [models.UniqueConstraint(fields=("provider", "provider_event_id"), name="unique_provider_event")]

    def save(self, *args, **kwargs):
        if self.pk and PaymentEvent.objects.filter(pk=self.pk).exists():
            raise ValidationError("Payment events are append-only.")
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError("Payment events cannot be deleted.")


class Receipt(TimeStampedModel):
    payment = models.OneToOneField(Payment, on_delete=models.PROTECT, related_name="receipt")
    invoice = models.ForeignKey("billing.Invoice", on_delete=models.PROTECT, related_name="receipts")
    receipt_number = models.CharField(max_length=32, unique=True, editable=False, db_index=True)
    verification_token = models.CharField(max_length=64, unique=True, editable=False, db_index=True)
    amount = models.DecimalField(max_digits=19, decimal_places=2)
    currency = models.CharField(max_length=3, default="NGN")
    issued_at = models.DateTimeField(default=timezone.now)

    def save(self, *args, **kwargs):
        if self.pk and Receipt.objects.filter(pk=self.pk).exists():
            raise ValidationError("Official receipts are immutable.")
        from .slip_reference import validate_slip_reference
        validate_slip_reference(self.payment.submitted_reference,self.payment.channel)
        if self.payment.status != Payment.Status.CONFIRMED:
            raise ValidationError("A receipt requires a confirmed payment.")
        return super().save(*args, **kwargs)


class ReceiptReprint(models.Model):
    receipt = models.ForeignKey(Receipt, on_delete=models.PROTECT, related_name="reprints")
    printed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    printed_at = models.DateTimeField(auto_now_add=True)
    reason = models.CharField(max_length=255)
    format = models.CharField(max_length=16, choices=(("a4", "A4"), ("thermal", "Thermal")), default="a4")
