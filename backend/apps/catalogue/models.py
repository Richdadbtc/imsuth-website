from django.conf import settings
from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models

from apps.common.models import TimeStampedModel


class Department(TimeStampedModel):
    code = models.CharField(max_length=24, unique=True)
    name = models.CharField(max_length=120, unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        ordering = ("name",)

    def __str__(self):
        return self.name


class Service(TimeStampedModel):
    department = models.ForeignKey(Department, on_delete=models.PROTECT, related_name="services")
    code = models.CharField(max_length=32, unique=True)
    name = models.CharField(max_length=160)
    category = models.CharField(max_length=80, blank=True)
    unit = models.CharField(max_length=80, blank=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        ordering = ("department__name", "name")
        constraints = [models.UniqueConstraint(fields=("department", "name"), name="unique_service_name_per_department")]

    def __str__(self):
        return f"{self.code} — {self.name}"


class TariffVersion(TimeStampedModel):
    service = models.ForeignKey(Service, on_delete=models.PROTECT, related_name="tariffs")
    amount = models.DecimalField(max_digits=19, decimal_places=2, validators=[MinValueValidator(Decimal("0.01"))])
    currency = models.CharField(max_length=3, default="NGN")
    effective_from = models.DateTimeField(db_index=True)
    effective_until = models.DateTimeField(null=True, blank=True, db_index=True)
    is_approved = models.BooleanField(default=False, db_index=True)
    approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.PROTECT, related_name="approved_tariffs")
    approval_reference = models.CharField(max_length=120, blank=True)
    proposed_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.PROTECT, related_name="proposed_tariffs")

    class Meta:
        ordering = ("-effective_from",)
        constraints = [
            models.CheckConstraint(condition=models.Q(amount__gt=0), name="tariff_amount_positive"),
            models.UniqueConstraint(fields=("service", "effective_from"), name="unique_service_tariff_effective_date"),
        ]

    def __str__(self):
        return f"{self.service.code}: {self.currency} {self.amount}"


class DepartmentCategory(TimeStampedModel):
    """Non-billable classification placeholder, separate from services and prices."""
    department = models.ForeignKey(Department, on_delete=models.PROTECT, related_name='catalogue_categories')
    code = models.CharField(max_length=32)
    name = models.CharField(max_length=80)
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.PROTECT, related_name='children')
    is_active = models.BooleanField(default=False, db_index=True)

    class Meta:
        ordering = ('department__name', 'name')
        constraints = [
            models.UniqueConstraint(fields=('department','code'),name='unique_category_code_per_department'),
            models.UniqueConstraint(fields=('department','name'),name='unique_category_name_per_department'),
        ]

    def __str__(self):
        return f'{self.department.code} / {self.name}'
