import uuid

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


def redact_metadata(value):
    sensitive=('password','secret','token','authorization','cookie','verification_code','otp','card_number','cvv')
    if isinstance(value,dict):
        return {key:('[redacted]' if any(term in str(key).lower() for term in sensitive) else redact_metadata(val)) for key,val in value.items()}
    if isinstance(value,list): return [redact_metadata(v) for v in value]
    return value


class AuditEvent(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    occurred_at = models.DateTimeField(auto_now_add=True, db_index=True)
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.PROTECT, related_name="audit_events")
    action = models.CharField(max_length=80, db_index=True)
    object_type = models.CharField(max_length=80, blank=True, db_index=True)
    object_id = models.CharField(max_length=80, blank=True)
    correlation_id = models.UUIDField(default=uuid.uuid4, db_index=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    reason = models.CharField(max_length=255, blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ("-occurred_at",)
        indexes = [models.Index(fields=("object_type", "object_id"))]

    def save(self, *args, **kwargs):
        if self.pk and AuditEvent.objects.filter(pk=self.pk).exists():
            raise ValidationError("Audit events are append-only.")
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError("Audit events cannot be deleted.")

    @classmethod
    def record(cls, action, *, actor=None, obj=None, request=None, reason="", metadata=None):
        return cls.objects.create(
            actor=actor if getattr(actor, "is_authenticated", False) else None,
            action=action,
            object_type=obj._meta.label if obj else "",
            object_id=str(obj.pk) if obj else "",
            ip_address=request.META.get("REMOTE_ADDR") if request else None,
            reason=reason,
            metadata=redact_metadata(metadata or {}),
        )
