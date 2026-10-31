import uuid

from django.db import models, transaction


class TimeStampedModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Sequence(models.Model):
    key = models.CharField(max_length=64, unique=True)
    value = models.PositiveBigIntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

    @classmethod
    def next_value(cls, key):
        with transaction.atomic():
            sequence, _ = cls.objects.select_for_update().get_or_create(key=key)
            sequence.value += 1
            sequence.save(update_fields=["value", "updated_at"])
            return sequence.value


class AccountProfile(TimeStampedModel):
    user = models.OneToOneField('accounts.User', on_delete=models.CASCADE, related_name='account_profile')
    phone = models.CharField(max_length=30, blank=True)
    address = models.CharField(max_length=300, blank=True)
    job_title = models.CharField(max_length=120, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=30, blank=True)
    qualification = models.CharField(max_length=150, blank=True)
    specialization = models.CharField(max_length=150, blank=True)
    license_number = models.CharField(max_length=100, blank=True)
    bio = models.CharField(max_length=500, blank=True)
    preferences = models.JSONField(default=dict)


class SystemConfiguration(TimeStampedModel):
    section = models.CharField(max_length=40, unique=True)
    values = models.JSONField(default=dict)
    updated_by = models.ForeignKey('accounts.User', null=True, on_delete=models.PROTECT)


class SupportTicket(TimeStampedModel):
    requested_by = models.ForeignKey('accounts.User', on_delete=models.PROTECT, related_name='support_tickets')
    subject = models.CharField(max_length=160)
    category = models.CharField(max_length=60)
    priority = models.CharField(max_length=10, choices=[('low','Low'),('normal','Normal'),('high','High')], default='normal')
    message = models.TextField(max_length=3000)
    status = models.CharField(max_length=20, choices=[('open','Open'),('in_progress','In progress'),('resolved','Resolved')], default='open')


class SupportReply(TimeStampedModel):
    ticket = models.ForeignKey(SupportTicket, on_delete=models.CASCADE, related_name='replies')
    author = models.ForeignKey('accounts.User', on_delete=models.PROTECT)
    message = models.TextField(max_length=3000)


class PrivateAttachment(TimeStampedModel):
    owner = models.ForeignKey('accounts.User', on_delete=models.PROTECT)
    ticket = models.ForeignKey(SupportTicket, null=True, on_delete=models.CASCADE, related_name='attachments')
    filename = models.CharField(max_length=180)
    content_type = models.CharField(max_length=40)
    content = models.BinaryField()

# Operational extensions reuse the existing financial ledger models.
from .revenue_models import Alert, CashPoint, CashOrder, CashApprovalLimit, ServiceDelivery, TariffProposal, CashCollectionEvidence, RecordedPayment  # noqa: E402,F401
