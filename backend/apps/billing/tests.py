from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from apps.catalogue.models import Department, Service, TariffVersion
from apps.registry.models import Patient
from .models import Invoice


class BillingTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create_user(username="cashier", password="long-test-password", role="cashier")
        cls.patient = Patient.objects.create(first_name="Synthetic", last_name="Patient", registered_by=cls.user)
        cls.department = Department.objects.create(code="LAB", name="Synthetic Laboratory")
        cls.service = Service.objects.create(department=cls.department, code="LAB-TEST", name="Synthetic Test")

    def approve_tariff(self, amount="1250.00"):
        return TariffVersion.objects.create(service=self.service, amount=Decimal(amount), effective_from=timezone.now() - timedelta(minutes=1), is_approved=True, approved_by=self.user, approval_reference="TEST-ONLY")

    def test_invoice_requires_approved_current_tariff(self):
        with self.assertRaises(ValidationError):
            Invoice.create_from_items(patient=self.patient, department=self.department, item_requests=[{"service": self.service, "quantity": 1}], created_by=self.user)

    def test_invoice_calculates_server_side_and_snapshots_tariff(self):
        tariff = self.approve_tariff()
        invoice = Invoice.create_from_items(patient=self.patient, department=self.department, item_requests=[{"service": self.service, "quantity": 2}], created_by=self.user)
        self.assertEqual(invoice.total_amount, Decimal("2500.00"))
        item = invoice.items.get()
        self.assertEqual(item.unit_amount, Decimal("1250.00"))
        tariff.amount = Decimal("5000.00")
        tariff.save()
        item.refresh_from_db()
        self.assertEqual(item.unit_amount, Decimal("1250.00"))

    def test_idempotency_returns_existing_invoice(self):
        self.approve_tariff()
        kwargs = {"patient": self.patient, "department": self.department, "item_requests": [{"service": self.service}], "created_by": self.user, "idempotency_key": "synthetic-request-1"}
        first = Invoice.create_from_items(**kwargs)
        second = Invoice.create_from_items(**kwargs)
        self.assertEqual(first.pk, second.pk)
        self.assertEqual(Invoice.objects.count(), 1)

    def test_invoice_items_are_immutable(self):
        self.approve_tariff()
        invoice = Invoice.create_from_items(patient=self.patient, department=self.department, item_requests=[{"service": self.service}], created_by=self.user)
        item = invoice.items.get()
        item.quantity = 2
        with self.assertRaises(ValidationError):
            item.save()

    def test_auditor_cannot_create_invoice(self):
        self.approve_tariff()
        auditor = get_user_model().objects.create_user(username="billing-auditor", password="long-test-password", role="auditor")
        client = APIClient()
        client.force_authenticate(auditor)
        response = client.post("/api/v1/invoices/", {"patient": str(self.patient.pk), "department": str(self.department.pk), "items": [{"service": str(self.service.pk), "quantity": 1}]}, format="json")
        self.assertEqual(response.status_code, 403)
