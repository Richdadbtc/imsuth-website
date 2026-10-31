import hashlib
import hmac
import json
import os
from datetime import timedelta
from decimal import Decimal

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from apps.accounts.models import User
from apps.billing.models import Invoice
from apps.catalogue.models import Department, Service, TariffVersion
from apps.operations.services import import_reconciliation_csv
from apps.payments.models import Payment
from apps.payments.services import DeterministicTestAdapter, confirm_payment_event
from apps.registry.models import Patient


class Command(BaseCommand):
    help = "Create visibly synthetic staging reviewers and one complete test workflow."

    def handle(self, *args, **options):
        if settings.ENVIRONMENT not in {"development", "staging"}:
            raise CommandError("Synthetic seeding is disabled outside development/staging.")
        if not settings.PAYMENT_TEST_MODE or not settings.TEST_WEBHOOK_SECRET:
            raise CommandError("The staging test adapter must be explicitly configured.")
        password = os.getenv("SYNTHETIC_SEED_PASSWORD", "")
        if len(password) < 12:
            raise CommandError("SYNTHETIC_SEED_PASSWORD must contain at least 12 characters.")

        users = {}
        for role in User.Role.values:
            user, _ = User.objects.get_or_create(
                username=f"synthetic-{role}",
                defaults={
                    "role": role,
                    "first_name": "Synthetic",
                    "last_name": User.Role(role).label,
                    "email": f"{role}@reviewer.example.invalid",
                    "is_staff": role == User.Role.SUPER_ADMIN,
                },
            )
            user.role = role
            user.set_password(password)
            user.save(update_fields=("role", "password"))
            users[role] = user

        department, _ = Department.objects.get_or_create(code="STAGE-UAT", defaults={"name": "Synthetic Staging Department"})
        service, _ = Service.objects.get_or_create(department=department, code="STAGE-UAT-001", defaults={"name": "Synthetic Staging Service"})
        tariff = TariffVersion.objects.filter(service=service, is_approved=True).order_by("-effective_from").first()
        if tariff is None:
            tariff = TariffVersion.objects.create(
                service=service,
                amount=Decimal("8250.00"),
                effective_from=timezone.now() - timedelta(minutes=1),
                is_approved=True,
                approved_by=users[User.Role.FINANCE],
                approval_reference="SYNTHETIC-STAGING-ONLY",
            )

        patient, _ = Patient.objects.get_or_create(
            first_name="Synthetic",
            last_name="Staging Patient",
            defaults={"registered_by": users[User.Role.FRONT_DESK], "email": "patient@review.example.invalid"},
        )
        invoice = Invoice.create_from_items(
            patient=patient,
            department=department,
            item_requests=[{"service": service, "quantity": 1}],
            created_by=users[User.Role.FRONT_DESK],
            idempotency_key="synthetic-staging-invoice-v1",
        )
        payment = Payment.create_intent(
            invoice=invoice,
            channel=Payment.Channel.ONLINE,
            initiated_by=users[User.Role.CASHIER],
            idempotency_key="synthetic-staging-payment-v1",
            provider="deterministic-test",
        )
        if payment.status == Payment.Status.PENDING:
            payload = json.dumps({
                "event_id": "synthetic-staging-event-v1",
                "payment_reference": payment.reference,
                "provider_reference": "synthetic-provider-reference-v1",
                "status": "successful",
                "amount": str(payment.amount),
                "currency": payment.currency,
            }, separators=(",", ":")).encode()
            signature = hmac.new(settings.TEST_WEBHOOK_SECRET.encode(), payload, hashlib.sha256).hexdigest()
            payment, _ = confirm_payment_event(adapter=DeterministicTestAdapter(), raw_body=payload, signature=signature)

        statement = f"reference,amount,currency,transaction_date\n{payment.provider_reference},{payment.amount},{payment.currency},{timezone.now().isoformat()}\n".encode()
        try:
            batch = import_reconciliation_csv(content=statement, source="synthetic-staging-bank", imported_by=users[User.Role.FINANCE])
        except Exception as exc:
            if "already imported" not in str(exc):
                raise
            batch = None

        self.stdout.write(self.style.SUCCESS(
            f"Synthetic staging workflow ready: patient={patient.patient_id}, invoice={invoice.invoice_number}, payment={payment.reference}, reconciliation={'existing' if batch is None else batch.status}."
        ))
