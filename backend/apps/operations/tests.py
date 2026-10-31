import hashlib
import hmac
import json
from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied, ValidationError
from django.test import TestCase, override_settings
from django.utils import timezone

from apps.billing.models import Invoice
from apps.catalogue.models import Department, Service, TariffVersion
from apps.payments.models import Payment
from apps.payments.services import DeterministicTestAdapter, confirm_payment_event
from apps.registry.models import Patient
from .models import ApprovalRequest, ReconciliationBatch, ReconciliationItem, Refund
from .services import decide_approval, import_reconciliation_csv, request_refund


@override_settings(DEBUG=True, PAYMENT_TEST_MODE=True, TEST_WEBHOOK_SECRET="ops-secret")
class OperationsTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        User = get_user_model()
        cls.maker = User.objects.create_user(username="maker", password="long-test-password", role="finance")
        cls.approver = User.objects.create_user(username="approver", password="long-test-password", role="management")
        patient = Patient.objects.create(first_name="Synthetic", last_name="Operations", registered_by=cls.maker)
        department = Department.objects.create(code="OPS", name="Synthetic Operations")
        service = Service.objects.create(department=department, code="OPS-001", name="Synthetic Charge")
        TariffVersion.objects.create(service=service, amount=Decimal("3000.00"), effective_from=timezone.now() - timedelta(minutes=1), is_approved=True, approved_by=cls.maker, approval_reference="TEST")
        cls.invoice = Invoice.create_from_items(patient=patient, department=department, item_requests=[{"service": service}], created_by=cls.maker)

    def confirmed_payment(self, key="ops-payment"):
        payment = Payment.create_intent(invoice=self.invoice, channel=Payment.Channel.ONLINE, initiated_by=self.maker, idempotency_key=key, provider="deterministic-test")
        body = json.dumps({"event_id": f"evt-{key}", "payment_reference": payment.reference, "provider_reference": f"provider-{key}", "status": "successful", "amount": "3000.00", "currency": "NGN"}, separators=(",", ":")).encode()
        signature = hmac.new(b"ops-secret", body, hashlib.sha256).hexdigest()
        payment, _ = confirm_payment_event(adapter=DeterministicTestAdapter(), raw_body=body, signature=signature)
        return payment

    def test_maker_cannot_approve_own_refund(self):
        refund = request_refund(payment=self.confirmed_payment(), amount="1000.00", reason="Synthetic request", requested_by=self.maker)
        with self.assertRaises(PermissionDenied):
            decide_approval(approval=refund.approval, approver=self.maker, approved=True, reason="Not permitted")

    def test_approved_refund_remains_pending_external_execution(self):
        refund = request_refund(payment=self.confirmed_payment(), amount="1000.00", reason="Synthetic request", requested_by=self.maker)
        decide_approval(approval=refund.approval, approver=self.approver, approved=True, reason="Synthetic approval")
        refund.refresh_from_db()
        self.assertEqual(refund.status, Refund.Status.APPROVED_PENDING_EXECUTION)
        self.assertEqual(refund.approval.status, ApprovalRequest.Status.APPROVED)

    def test_reconciliation_exact_match(self):
        payment = self.confirmed_payment()
        content = f"reference,amount,currency,transaction_date\n{payment.provider_reference},3000.00,NGN,2026-10-10T12:00:00+01:00\n".encode()
        batch = import_reconciliation_csv(content=content, source="synthetic-bank", imported_by=self.maker)
        self.assertEqual(batch.status, ReconciliationBatch.Status.RECONCILED)
        self.assertEqual(batch.items.get().status, ReconciliationItem.Status.MATCHED)

    def test_reconciliation_amount_mismatch_requires_review(self):
        payment = self.confirmed_payment()
        content = f"reference,amount,currency,transaction_date\n{payment.provider_reference},2999.00,NGN,2026-10-10T12:00:00+01:00\n".encode()
        batch = import_reconciliation_csv(content=content, source="synthetic-bank", imported_by=self.maker)
        self.assertEqual(batch.status, ReconciliationBatch.Status.REVIEW_REQUIRED)
        self.assertEqual(batch.items.get().status, ReconciliationItem.Status.AMOUNT_MISMATCH)

    def test_duplicate_reconciliation_file_is_rejected(self):
        payment = self.confirmed_payment()
        content = f"reference,amount,currency,transaction_date\n{payment.provider_reference},3000.00,NGN,2026-10-10T12:00:00+01:00\n".encode()
        import_reconciliation_csv(content=content, source="synthetic-bank", imported_by=self.maker)
        with self.assertRaises(ValidationError):
            import_reconciliation_csv(content=content, source="synthetic-bank", imported_by=self.maker)
