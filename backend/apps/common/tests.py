from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from apps.auditlog.models import AuditEvent
from apps.catalogue.models import Department, Service, TariffVersion
from apps.registry.models import Patient


class FoundationModelTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username="frontdesk", password="a-secure-test-password", role="front_desk")

    def test_patient_ids_are_unique_and_sequential(self):
        first = Patient.objects.create(first_name="Test", last_name="One", registered_by=self.user)
        second = Patient.objects.create(first_name="Test", last_name="Two", registered_by=self.user)
        self.assertNotEqual(first.patient_id, second.patient_id)
        self.assertRegex(first.patient_id, r"^IMSUTH-\d{4}-\d{6}$")

    def test_duplicate_candidates_match_normalized_phone(self):
        first = Patient.objects.create(first_name="Synthetic", last_name="Person", phone="0803 000 0000", registered_by=self.user)
        second = Patient.objects.create(first_name="Different", last_name="Test", phone="+234 803 000 0000", registered_by=self.user)
        self.assertIn(first, second.potential_duplicates())

    def test_tariff_versions_preserve_history(self):
        department = Department.objects.create(code="TEST", name="Synthetic Department")
        service = Service.objects.create(department=department, code="TEST-001", name="Synthetic Service")
        old = TariffVersion.objects.create(service=service, amount=Decimal("100.00"), effective_from=timezone.now() - timedelta(days=1))
        new = TariffVersion.objects.create(service=service, amount=Decimal("150.00"), effective_from=timezone.now())
        self.assertEqual(old.amount, Decimal("100.00"))
        self.assertEqual(new.amount, Decimal("150.00"))

    def test_audit_event_is_append_only(self):
        event = AuditEvent.record("test.created", actor=self.user)
        event.action = "test.changed"
        with self.assertRaises(ValidationError):
            event.save()
        with self.assertRaises(ValidationError):
            event.delete()


class FoundationApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.frontdesk = get_user_model().objects.create_user(username="fd", password="test-password-long", role="front_desk")
        self.auditor = get_user_model().objects.create_user(username="audit", password="test-password-long", role="auditor")

    def test_anonymous_access_is_denied(self):
        response = self.client.get("/api/v1/patients/")
        self.assertIn(response.status_code, (401, 403))

    def test_front_desk_can_register_synthetic_patient(self):
        self.client.force_authenticate(self.frontdesk)
        response = self.client.post("/api/v1/patients/", {"first_name": "Test", "last_name": "Patient", "phone": "08030000001"})
        self.assertEqual(response.status_code, 201)
        self.assertTrue(response.data["patient_id"].startswith("IMSUTH-"))

    def test_auditor_cannot_register_patient(self):
        self.client.force_authenticate(self.auditor)
        response = self.client.post("/api/v1/patients/", {"first_name": "Test", "last_name": "Denied"})
        self.assertEqual(response.status_code, 403)
