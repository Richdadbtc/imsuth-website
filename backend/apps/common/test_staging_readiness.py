import hashlib
import hmac
import json
import threading
from datetime import timedelta
from decimal import Decimal
from unittest import skipUnless

from django.contrib.auth import get_user_model
from django.db import close_old_connections, connection, connections
from django.test import TestCase, TransactionTestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.billing.models import Invoice
from apps.catalogue.models import Department, Service, TariffVersion
from apps.operations.models import NotificationRecipient, ReconciliationBatch
from apps.operations.services import import_reconciliation_csv
from apps.payments.models import Payment, Receipt
from apps.registry.models import Patient


@override_settings(
    ENVIRONMENT="staging",
    DEBUG=False,
    PAYMENT_TEST_MODE=True,
    TEST_WEBHOOK_SECRET="staging-test-secret",
    SECURE_SSL_REDIRECT=False,
)
class SyntheticEndToEndWorkflowTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.front_desk = User.objects.create_user(username="uat-front", password="synthetic-password", role=User.Role.FRONT_DESK)
        cls.cashier = User.objects.create_user(username="uat-cashier", password="synthetic-password", role=User.Role.CASHIER)
        cls.finance = User.objects.create_user(username="uat-finance", password="synthetic-password", role=User.Role.FINANCE)
        cls.management = User.objects.create_user(username="uat-management", password="synthetic-password", role=User.Role.MANAGEMENT)
        cls.department = Department.objects.create(code="UAT", name="Synthetic UAT Department")
        for user in (cls.front_desk,cls.cashier):
            user.department=cls.department
            user.save(update_fields=["department"])
        cls.service = Service.objects.create(department=cls.department, code="UAT-001", name="Synthetic UAT Service")
        TariffVersion.objects.create(
            service=cls.service,
            amount=Decimal("7250.00"),
            effective_from=timezone.now() - timedelta(minutes=1),
            is_approved=True,
            approved_by=cls.finance,
            approval_reference="SYNTHETIC-UAT",
        )

    def test_complete_synthetic_revenue_workflow(self):
        api = APIClient()
        api.force_authenticate(self.front_desk)
        patient_response = api.post("/api/v1/patients/", {
            "first_name": "Synthetic",
            "last_name": "Reviewer",
            "phone": "08000000001",
        }, format="json")
        self.assertEqual(patient_response.status_code, 201)
        self.assertRegex(patient_response.data["patient_id"], r"^IMSUTH-\d{4}-\d{6}$")

        invoice_response = api.post("/api/v1/invoices/", {
            "patient": str(patient_response.data["id"]),
            "department": str(self.department.pk),
            "idempotency_key": "uat-invoice-001",
            "items": [{"service": str(self.service.pk), "quantity": 1}],
        }, format="json")
        self.assertEqual(invoice_response.status_code, 201)
        self.assertEqual(Decimal(invoice_response.data["total_amount"]), Decimal("7250.00"))

        api.force_authenticate(self.cashier)
        payment_response = api.post("/api/v1/payments/", {
            "invoice": str(invoice_response.data["id"]),
            "idempotency_key": "uat-payment-001",
            "channel": Payment.Channel.ONLINE,
        }, format="json")
        self.assertEqual(payment_response.status_code, 201)
        self.assertEqual(payment_response.data["status"], Payment.Status.PENDING)

        payload = json.dumps({
            "event_id": "uat-event-001",
            "payment_reference": payment_response.data["reference"],
            "provider_reference": "uat-provider-001",
            "status": "successful",
            "amount": "7250.00",
            "currency": "NGN",
        }, separators=(",", ":")).encode()
        signature = hmac.new(b"staging-test-secret", payload, hashlib.sha256).hexdigest()
        api.force_authenticate(user=None)
        webhook_response = api.post(
            "/api/v1/payments/test-webhook/",
            data=payload,
            content_type="application/json",
            HTTP_X_TEST_SIGNATURE=signature,
        )
        self.assertEqual(webhook_response.status_code, 200)
        self.assertTrue(webhook_response.data["processed"])

        payment = Payment.objects.get(reference=payment_response.data["reference"])
        self.assertEqual(payment.status, Payment.Status.CONFIRMED)
        receipt = Receipt.objects.get(payment=payment)
        self.assertEqual(receipt.amount, Decimal("7250.00"))
        self.assertTrue(NotificationRecipient.objects.filter(user=self.management, notification__event_type="payment.confirmed").exists())

        reviewer = self.client
        reviewer.force_login(self.management)
        dashboard = reviewer.get("/api/v1/dashboard/recent-transactions/")
        self.assertEqual(dashboard.status_code, 200)
        self.assertIn(payment.reference,str(dashboard.json()))
        receipt_page = reviewer.get(f"/api/v1/receipts/{receipt.pk}/print/")
        self.assertEqual(receipt_page.status_code, 200)
        self.assertContains(receipt_page, receipt.receipt_number)

        statement = f"reference,amount,currency,transaction_date\n{payment.provider_reference},7250.00,NGN,2026-10-11T09:30:00+01:00\n".encode()
        batch = import_reconciliation_csv(content=statement, source="synthetic-uat-bank", imported_by=self.finance)
        self.assertEqual(batch.status, ReconciliationBatch.Status.RECONCILED)
        self.assertEqual(batch.items.get().payment_id, payment.id)


class SevenRolePermissionTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.users = {
            role: User.objects.create_user(
                username=f"role-{role}", password="synthetic-password", role=role,
                is_staff=role == User.Role.SUPER_ADMIN,
                is_superuser=role == User.Role.SUPER_ADMIN,
            )
            for role in User.Role.values
        }
        cls.department = Department.objects.create(code="ROLE", name="Role Test Department")
        cls.patient = Patient.objects.create(first_name="Role", last_name="Test", registered_by=cls.users[User.Role.FRONT_DESK])

    def test_patient_registration_role_matrix(self):
        allowed = {User.Role.FRONT_DESK, User.Role.FINANCE, User.Role.DEPARTMENT_SUPERVISOR}
        for role, user in self.users.items():
            with self.subTest(role=role):
                client = APIClient()
                client.force_authenticate(user)
                response = client.post("/api/v1/patients/", {"first_name": "Synthetic", "last_name": role}, format="json")
                self.assertEqual(response.status_code, 201 if role in allowed else 403)

    def test_invoice_creation_role_matrix(self):
        allowed = {User.Role.FRONT_DESK, User.Role.CASHIER, User.Role.FINANCE}
        for role, user in self.users.items():
            with self.subTest(role=role):
                client = APIClient()
                client.force_authenticate(user)
                response = client.post("/api/v1/invoices/", {"patient": str(self.patient.pk), "department": str(self.department.pk), "idempotency_key": f"role-{role}", "items": []}, format="json")
                self.assertNotEqual(response.status_code, 403) if role in allowed else self.assertEqual(response.status_code, 403)

    def test_financial_dashboard_role_matrix(self):
        allowed = {User.Role.FINANCE, User.Role.AUDITOR, User.Role.MANAGEMENT}
        for role, user in self.users.items():
            with self.subTest(role=role):
                self.client.force_login(user)
                response = self.client.get(reverse("management-dashboard"))
                self.assertEqual(response.status_code, 302 if role in allowed else 403)
                self.client.logout()

    def test_django_superuser_does_not_bypass_financial_api_role(self):
        super_admin = self.users[User.Role.SUPER_ADMIN]
        client = APIClient()
        client.force_authenticate(super_admin)
        response = client.post("/api/v1/payments/", {"invoice": "00000000-0000-0000-0000-000000000000", "idempotency_key": "forbidden", "channel": Payment.Channel.ONLINE}, format="json")
        self.assertEqual(response.status_code, 403)


@skipUnless(connection.vendor == "postgresql", "PostgreSQL concurrency test")
class PostgreSQLPaymentConcurrencyTests(TransactionTestCase):
    reset_sequences = True

    def setUp(self):
        self.user = get_user_model().objects.create_user(username="concurrency-cashier", password="synthetic-password", role=User.Role.CASHIER)
        patient = Patient.objects.create(first_name="Concurrent", last_name="Synthetic", registered_by=self.user)
        department = Department.objects.create(code="CONC", name="Concurrency Test")
        service = Service.objects.create(department=department, code="CONC-001", name="Concurrent Service")
        TariffVersion.objects.create(service=service, amount=Decimal("4000.00"), effective_from=timezone.now() - timedelta(minutes=1), is_approved=True, approved_by=self.user, approval_reference="SYNTHETIC")
        self.invoice = Invoice.create_from_items(patient=patient, department=department, item_requests=[{"service": service}], created_by=self.user)

    def test_concurrent_idempotent_payment_intents_create_one_record(self):
        barrier = threading.Barrier(2)
        results = []
        errors = []

        def create_intent():
            close_old_connections()
            try:
                barrier.wait(timeout=5)
                invoice = Invoice.objects.get(pk=self.invoice.pk)
                user = User.objects.get(pk=self.user.pk)
                payment = Payment.create_intent(invoice=invoice, channel=Payment.Channel.ONLINE, initiated_by=user, idempotency_key="concurrent-intent")
                results.append(payment.pk)
            except Exception as exc:  # captured for assertion in the main test thread
                errors.append(exc)
            finally:
                connections.close_all()

        threads = [threading.Thread(target=create_intent) for _ in range(2)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(timeout=10)
        connections.close_all()

        self.assertEqual(errors, [])
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0], results[1])
        self.assertEqual(Payment.objects.filter(idempotency_key="concurrent-intent").count(), 1)
