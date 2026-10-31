import re

from django.conf import settings
from django.db import models, transaction
from django.utils import timezone

from apps.common.models import Sequence, TimeStampedModel


def normalize_phone(value):
    digits = re.sub(r"\D", "", value or "")
    if digits.startswith("234"):
        digits = "0" + digits[3:]
    return digits


class Patient(TimeStampedModel):
    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        INACTIVE = "inactive", "Inactive"
        DECEASED = "deceased", "Deceased"
        DUPLICATE_REVIEW = "duplicate_review", "Duplicate review"

    class Sex(models.TextChoices):
        FEMALE = "female", "Female"
        MALE = "male", "Male"
        OTHER = "other", "Other / not specified"

    patient_id = models.CharField(max_length=32, unique=True, editable=False, db_index=True)
    first_name = models.CharField(max_length=80)
    middle_name = models.CharField(max_length=80, blank=True)
    last_name = models.CharField(max_length=80)
    date_of_birth = models.DateField(null=True, blank=True)
    approximate_age = models.PositiveSmallIntegerField(null=True, blank=True)
    sex = models.CharField(max_length=16, choices=Sex.choices, blank=True)
    phone = models.CharField(max_length=24, blank=True, db_index=True)
    normalized_phone = models.CharField(max_length=20, blank=True, editable=False, db_index=True)
    email = models.EmailField(blank=True)
    address = models.TextField(blank=True)
    emergency_contact = models.CharField(max_length=160, blank=True)
    status = models.CharField(max_length=24, choices=Status.choices, default=Status.ACTIVE, db_index=True)
    registered_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.PROTECT, related_name="registered_patients")

    class Meta:
        ordering = ("last_name", "first_name")
        indexes = [models.Index(fields=("last_name", "first_name", "date_of_birth"))]

    def save(self, *args, **kwargs):
        self.normalized_phone = normalize_phone(self.phone)
        if not self.patient_id:
            with transaction.atomic():
                year = timezone.localdate().year
                number = Sequence.next_value(f"patient:{year}")
                self.patient_id = f"IMSUTH-{year}-{number:06d}"
                return super().save(*args, **kwargs)
        return super().save(*args, **kwargs)

    @property
    def full_name(self):
        return " ".join(part for part in (self.first_name, self.middle_name, self.last_name) if part)

    @property
    def initials(self):
        return f"{self.first_name[:1]}{self.last_name[:1]}".upper()

    def potential_duplicates(self):
        candidates = Patient.objects.exclude(pk=self.pk)
        phone_match = models.Q()
        if self.normalized_phone:
            phone_match = models.Q(normalized_phone=self.normalized_phone)
        identity_match = models.Q(
            first_name__iexact=self.first_name,
            last_name__iexact=self.last_name,
            date_of_birth=self.date_of_birth,
        )
        return candidates.filter(phone_match | identity_match).distinct()

    def __str__(self):
        return f"{self.patient_id} — {self.last_name}, {self.first_name}"


class PatientRevision(TimeStampedModel):
    patient = models.ForeignKey(Patient, on_delete=models.PROTECT, related_name="revisions")
    changed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    reason = models.CharField(max_length=255)
    before = models.JSONField(default=dict)
    after = models.JSONField(default=dict)
