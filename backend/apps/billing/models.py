from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models, transaction
from django.utils import timezone

from apps.catalogue.models import TariffVersion
from apps.common.models import Sequence, TimeStampedModel


class Invoice(TimeStampedModel):
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        ISSUED = "issued", "Issued"
        PARTIALLY_PAID = "partially_paid", "Partially paid"
        PAID = "paid", "Paid"
        VOID_REQUESTED = "void_requested", "Void requested"
        VOIDED = "voided", "Voided"

    invoice_number = models.CharField(max_length=32, unique=True, editable=False, db_index=True)
    payment_reference = models.CharField(max_length=40, unique=True, editable=False, db_index=True)
    patient = models.ForeignKey("registry.Patient", on_delete=models.PROTECT, related_name="invoices")
    department = models.ForeignKey("catalogue.Department", on_delete=models.PROTECT, related_name="invoices")
    status = models.CharField(max_length=24, choices=Status.choices, default=Status.ISSUED, db_index=True)
    total_amount = models.DecimalField(max_digits=19, decimal_places=2, default=Decimal("0.00"))
    amount_paid = models.DecimalField(max_digits=19, decimal_places=2, default=Decimal("0.00"))
    currency = models.CharField(max_length=3, default="NGN")
    idempotency_key = models.CharField(max_length=80, unique=True, null=True, blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="created_invoices")
    issued_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ("-issued_at",)
        constraints = [
            models.CheckConstraint(condition=models.Q(total_amount__gte=0), name="invoice_total_nonnegative"),
            models.CheckConstraint(condition=models.Q(amount_paid__gte=0), name="invoice_paid_nonnegative"),
            models.CheckConstraint(condition=models.Q(amount_paid__lte=models.F("total_amount")), name="invoice_paid_not_over_total"),
        ]

    @property
    def outstanding_balance(self):
        return self.total_amount - self.amount_paid

    @classmethod
    def create_from_items(cls, *, patient, department, item_requests, created_by, idempotency_key=None, capture_total=None, capture_reason=""):
        if not department.is_active:
            raise ValidationError('Inactive departments cannot issue new invoices.')
        with transaction.atomic():
            if idempotency_key:
                existing = cls.objects.filter(idempotency_key=idempotency_key).first()
                if existing:
                    same_items = sorted((str(i.service_id), i.quantity) for i in existing.items.all()) == sorted((str(i['service'].pk), i.get('quantity',1)) for i in item_requests)
                    if existing.patient_id != patient.pk or existing.department_id != department.pk or existing.created_by_id != created_by.pk or not same_items or (capture_total is not None and existing.total_amount != capture_total):
                        raise ValidationError('Idempotency key belongs to a different invoice request.')
                    return existing
            year = timezone.localdate().year
            number = Sequence.next_value(f"invoice:{year}")
            reference_number = Sequence.next_value(f"payment-reference:{year}")
            if idempotency_key:
                existing = cls.objects.filter(idempotency_key=idempotency_key).first()
                if existing:
                    same_items = sorted((str(i.service_id), i.quantity) for i in existing.items.all()) == sorted((str(i['service'].pk), i.get('quantity',1)) for i in item_requests)
                    if existing.patient_id != patient.pk or existing.department_id != department.pk or existing.created_by_id != created_by.pk or not same_items or (capture_total is not None and existing.total_amount != capture_total):
                        raise ValidationError('Idempotency key belongs to a different invoice request.')
                    return existing
            invoice = cls.objects.create(
                invoice_number=f"INV-{year}-{number:08d}",
                payment_reference=f"PAY-{year}-{reference_number:010d}",
                patient=patient,
                department=department,
                created_by=created_by,
                idempotency_key=idempotency_key,
            )
            total = Decimal("0.00")
            now = timezone.now()
            for request in item_requests:
                service = request["service"]
                quantity = request.get("quantity", 1)
                if service.department_id != department.id or not service.is_active:
                    raise ValidationError("Service is not active for the selected department.")
                tariff = TariffVersion.objects.filter(
                    service=service,
                    is_approved=True,
                    effective_from__lte=now,
                ).filter(models.Q(effective_until__isnull=True) | models.Q(effective_until__gt=now)).order_by("-effective_from").first()
                if tariff is None:
                    raise ValidationError(f"No approved current tariff for {service.code}.")
                if invoice.items.exists() and invoice.items.first().currency != tariff.currency:
                    raise ValidationError('Invoice items must use one currency.')
                unit_amount=tariff.amount
                if capture_total is not None:
                    if len(item_requests)!=1 or capture_total<=0 or not capture_total.is_finite():
                        raise ValidationError('Captured pricing requires one service and a positive finite total.')
                    if capture_total!=tariff.amount*quantity:
                        if created_by.role not in {'cashier','finance','super_admin'} or len(capture_reason.strip())<5:
                            raise ValidationError('A collection officer and a reason of at least five characters are required for a price change.')
                        unit_amount=(capture_total/quantity).quantize(Decimal('0.01'))
                        if unit_amount*quantity!=capture_total or unit_amount<Decimal('0.01'):
                            raise ValidationError('The total must divide into a positive two-decimal unit price.')
                item = InvoiceItem.objects.create(
                    invoice=invoice,
                    service=service,
                    tariff_version=tariff,
                    service_code=service.code,
                    description=service.name,
                    quantity=quantity,
                    unit_amount=unit_amount,
                    currency=tariff.currency,
                )
                total += item.line_total
            if total <= 0:
                raise ValidationError("An invoice requires at least one priced item.")
            invoice.total_amount = total
            invoice.currency = invoice.items.first().currency
            invoice.save(update_fields=("total_amount", "currency", "updated_at"))
            return invoice

    def __str__(self):
        return self.invoice_number


class InvoiceItem(TimeStampedModel):
    is_manual = models.BooleanField(default=False)

    class Meta:
        constraints = [models.CheckConstraint(condition=(models.Q(is_manual=True, service__isnull=True, tariff_version__isnull=True) | models.Q(is_manual=False, service__isnull=False, tariff_version__isnull=False)), name="invoice_item_source_consistent")]

    invoice = models.ForeignKey(Invoice, on_delete=models.PROTECT, related_name="items")
    service = models.ForeignKey("catalogue.Service", on_delete=models.PROTECT, null=True, blank=True)
    tariff_version = models.ForeignKey("catalogue.TariffVersion", on_delete=models.PROTECT, null=True, blank=True)
    service_code = models.CharField(max_length=32)
    description = models.CharField(max_length=200)
    quantity = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)])
    unit_amount = models.DecimalField(max_digits=19, decimal_places=2, validators=[MinValueValidator(Decimal("0.01"))])
    currency = models.CharField(max_length=3, default="NGN")

    @property
    def line_total(self):
        return self.unit_amount * self.quantity

    def save(self, *args, **kwargs):
        if self.pk and InvoiceItem.objects.filter(pk=self.pk).exists():
            raise ValidationError("Issued invoice items are immutable.")
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError("Issued invoice items cannot be deleted.")


class BillingCorrectionRequest(TimeStampedModel):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"

    invoice = models.ForeignKey(Invoice, on_delete=models.PROTECT, related_name="correction_requests")
    requested_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="billing_corrections_requested")
    reason = models.TextField()
    requested_change = models.JSONField(default=dict)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.PENDING)
    decided_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.PROTECT, related_name="billing_corrections_decided")
    decision_reason = models.TextField(blank=True)
