import hashlib
import hmac
import json
from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase, override_settings
from django.utils import timezone

from apps.billing.models import Invoice
from apps.catalogue.models import Department, Service, TariffVersion
from apps.registry.models import Patient
from .models import Payment, PaymentEvent, Receipt
from .services import DeterministicTestAdapter, confirm_payment_event


@override_settings(DEBUG=True, PAYMENT_TEST_MODE=True, TEST_WEBHOOK_SECRET="test-webhook-secret")
class PaymentLifecycleTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create_user(username="payment-cashier", password="long-test-password", role="cashier")
        patient = Patient.objects.create(first_name="Synthetic", last_name="Payer", registered_by=cls.user)
        department = Department.objects.create(code="PAY", name="Synthetic Payments")
        service = Service.objects.create(department=department, code="PAY-001", name="Synthetic Bill")
        TariffVersion.objects.create(service=service, amount=Decimal("5000.00"), effective_from=timezone.now() - timedelta(minutes=1), is_approved=True, approved_by=cls.user, approval_reference="TEST")
        cls.invoice = Invoice.create_from_items(patient=patient, department=department, item_requests=[{"service": service}], created_by=cls.user)

    def create_payment(self, key="payment-test-1"):
        return Payment.create_intent(invoice=self.invoice, channel=Payment.Channel.ONLINE, initiated_by=self.user, idempotency_key=key, provider="deterministic-test")

    def event_body(self, payment, *, event_id="evt-1", amount="5000.00", status="successful"):
        return json.dumps({"event_id": event_id, "payment_reference": payment.reference, "provider_reference": f"provider-{event_id}", "status": status, "amount": amount, "currency": "NGN"}, separators=(",", ":")).encode()

    def sign(self, body):
        return hmac.new(b"test-webhook-secret", body, hashlib.sha256).hexdigest()

    def test_pending_payment_has_no_receipt(self):
        payment = self.create_payment()
        self.assertEqual(payment.status, Payment.Status.PENDING)
        self.assertFalse(Receipt.objects.filter(payment=payment).exists())

    def test_signed_confirmation_creates_one_receipt_and_pays_invoice(self):
        payment = self.create_payment()
        body = self.event_body(payment)
        confirmed, processed = confirm_payment_event(adapter=DeterministicTestAdapter(), raw_body=body, signature=self.sign(body))
        self.assertTrue(processed)
        self.assertEqual(confirmed.status, Payment.Status.CONFIRMED)
        self.assertEqual(Receipt.objects.filter(payment=payment).count(), 1)
        self.invoice.refresh_from_db()
        self.assertEqual(self.invoice.status, Invoice.Status.PAID)

    def test_duplicate_event_is_idempotent(self):
        payment = self.create_payment()
        body = self.event_body(payment)
        confirm_payment_event(adapter=DeterministicTestAdapter(), raw_body=body, signature=self.sign(body))
        _, processed = confirm_payment_event(adapter=DeterministicTestAdapter(), raw_body=body, signature=self.sign(body))
        self.assertFalse(processed)
        self.assertEqual(PaymentEvent.objects.count(), 1)
        self.assertEqual(Receipt.objects.count(), 1)

    def test_incorrect_amount_requires_review_and_no_receipt(self):
        payment = self.create_payment()
        body = self.event_body(payment, amount="4999.00")
        result, _ = confirm_payment_event(adapter=DeterministicTestAdapter(), raw_body=body, signature=self.sign(body))
        self.assertEqual(result.status, Payment.Status.REVIEW_REQUIRED)
        self.assertFalse(Receipt.objects.exists())

    def test_invalid_signature_is_rejected(self):
        payment = self.create_payment()
        with self.assertRaises(Exception):
            confirm_payment_event(adapter=DeterministicTestAdapter(), raw_body=self.event_body(payment), signature="invalid")

    def test_receipt_cannot_be_created_for_pending_payment(self):
        payment = self.create_payment()
        with self.assertRaises(ValidationError):
            Receipt.objects.create(payment=payment, invoice=self.invoice, receipt_number="RCT-TEST", verification_token="test-token", amount=payment.amount)
