import hashlib
import hmac
import json
import uuid
from decimal import Decimal, InvalidOperation

from django.conf import settings
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import IntegrityError, transaction
from django.utils import timezone

from apps.auditlog.models import AuditEvent
from apps.billing.models import Invoice
from apps.common.models import Sequence
from .models import Payment, PaymentEvent, Receipt


class ProviderAdapter:
    name = "unconfigured"

    def verify_webhook(self, raw_body, signature):
        raise NotImplementedError

    def parse_event(self, payload):
        raise NotImplementedError


class DeterministicTestAdapter(ProviderAdapter):
    name = "deterministic-test"

    def __init__(self):
        if settings.ENVIRONMENT == "production" or not settings.PAYMENT_TEST_MODE or not settings.TEST_WEBHOOK_SECRET:
            raise PermissionDenied("Test payment adapter is disabled.")

    def verify_webhook(self, raw_body, signature):
        expected = hmac.new(settings.TEST_WEBHOOK_SECRET.encode(), raw_body, hashlib.sha256).hexdigest()
        return hmac.compare_digest(expected, signature or "")

    def parse_event(self, payload):
        required = {"event_id", "payment_reference", "provider_reference", "status", "amount", "currency"}
        if not required.issubset(payload):
            raise ValidationError("Incomplete provider event.")
        return payload


def confirm_payment_event(*, adapter, raw_body, signature):
    if not adapter.verify_webhook(raw_body, signature):
        raise PermissionDenied("Invalid webhook signature.")
    payload = adapter.parse_event(json.loads(raw_body))
    digest = hashlib.sha256(raw_body).hexdigest()
    with transaction.atomic():
        existing = PaymentEvent.objects.filter(provider=adapter.name, provider_event_id=payload["event_id"]).select_related("payment").first()
        if existing:
            return existing.payment, False
        payment = Payment.objects.select_for_update().select_related("invoice").get(reference=payload["payment_reference"])
        invoice = Invoice.objects.select_for_update().get(pk=payment.invoice_id)
        try:
            event = PaymentEvent.objects.create(
                id=uuid.uuid4(), payment=payment, provider=adapter.name,
                provider_event_id=payload["event_id"], event_type=f"payment.{payload['status']}",
                signature_verified=True, payload_digest=digest,
                metadata={"provider_reference": payload["provider_reference"]},
            )
        except IntegrityError:
            return payment, False
        try:
            provider_amount = Decimal(str(payload["amount"]))
        except InvalidOperation:
            provider_amount = None
        amount_matches = payment.amount == provider_amount
        currency_matches = payment.currency == payload["currency"]
        if payload["status"] != "successful" or not amount_matches or not currency_matches:
            payment.status = Payment.Status.REVIEW_REQUIRED if payload["status"] == "successful" else Payment.Status.FAILED
            payment.provider_reference = payload["provider_reference"]
            payment.save(update_fields=("status", "provider_reference", "updated_at"))
            return payment, True
        if payment.status == Payment.Status.CONFIRMED:
            return payment, False
        if payment.status != Payment.Status.PENDING:
            raise ValidationError("Payment is not eligible for electronic confirmation.")
        payment.status = Payment.Status.CONFIRMED
        payment.provider = adapter.name
        payment.provider_reference = payload["provider_reference"]
        payment.confirmed_at = timezone.now()
        payment.save(update_fields=("status", "provider", "provider_reference", "confirmed_at", "updated_at"))
        invoice.amount_paid += payment.amount
        invoice.status = Invoice.Status.PAID if invoice.amount_paid == invoice.total_amount else Invoice.Status.PARTIALLY_PAID
        invoice.save(update_fields=("amount_paid", "status", "updated_at"))
        year = timezone.localdate().year
        receipt_number = Sequence.next_value(f"receipt:{year}")
        receipt = Receipt.objects.create(
            payment=payment, invoice=invoice,
            receipt_number=f"RCT-{year}-{receipt_number:010d}",
            verification_token=hashlib.sha256(f"{uuid.uuid4()}:{payment.pk}".encode()).hexdigest(),
            amount=payment.amount, currency=payment.currency,
        )
        AuditEvent.record("payment.confirmed", actor=None, obj=payment, metadata={"receipt_id": str(receipt.pk), "provider": adapter.name})
        from apps.accounts.models import User
        from apps.operations.models import Notification, NotificationRecipient

        notification = Notification.objects.create(
            event_type="payment.confirmed",
            subject="Payment confirmed",
            body=f"Payment {payment.reference} for {payment.currency} {payment.amount} was confirmed.",
            channel=Notification.Channel.IN_APP,
            sensitive=False,
        )
        recipients = User.objects.filter(is_active=True, role__in=(User.Role.MANAGEMENT, User.Role.FINANCE))
        NotificationRecipient.objects.bulk_create([
            NotificationRecipient(notification=notification, user=user, status=NotificationRecipient.Status.SENT)
            for user in recipients
        ])
        return payment, True
