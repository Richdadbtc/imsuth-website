from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers
from django.db import IntegrityError, transaction

from .models import Payment, Receipt


class PaymentSerializer(serializers.ModelSerializer):
    receipt_number=serializers.CharField(source='receipt.receipt_number',read_only=True,default='')
    receipt_id=serializers.UUIDField(source='receipt.id',read_only=True,default=None)
    service_summary=serializers.SerializerMethodField()
    def get_service_summary(self,obj) -> str:
        return ', '.join(item.description for item in obj.invoice.items.all())

    collected_by_id = serializers.IntegerField(source="initiated_by_id", read_only=True)
    collected_by_name = serializers.CharField(source="initiated_by.get_full_name", read_only=True)
    patient_name = serializers.CharField(source="invoice.patient.__str__", read_only=True)
    department_id = serializers.UUIDField(source="invoice.department_id", read_only=True)
    department = serializers.CharField(source="invoice.department.name", read_only=True)
    invoice_number = serializers.CharField(source="invoice.invoice_number", read_only=True)
    class Meta:
        extra_kwargs = {'idempotency_key': {'validators': []}}
        model = Payment
        fields = ("id", "invoice", "reference", "idempotency_key", "channel", "provider", "provider_reference", "submitted_reference", "reported_paid_at", "remarks", "amount", "currency", "status", "created_at", "confirmed_at", "collected_by_id", "collected_by_name", "patient_name", "department_id", "department", "invoice_number", "receipt_number", "receipt_id", "service_summary")
        read_only_fields = ("id", "reference", "provider", "provider_reference", "amount", "currency", "status", "created_at", "confirmed_at")

    def validate(self,data):
        from .slip_reference import validate_slip_reference
        try:data['submitted_reference']=validate_slip_reference(data.get('submitted_reference',getattr(self.instance,'submitted_reference','')),data.get('channel',getattr(self.instance,'channel','')))
        except DjangoValidationError as error:raise serializers.ValidationError({'submitted_reference':error.messages}) from error
        return data

    def validate_reported_paid_at(self,value):
        from django.utils import timezone
        from datetime import timedelta
        if value and value>timezone.now()+timedelta(minutes=1):raise serializers.ValidationError("Reported payment time cannot be in the future.")
        return value

    @transaction.atomic
    def create(self, validated_data):
        submitted_reference=validated_data.pop("submitted_reference", "")
        reported_paid_at=validated_data.pop("reported_paid_at",None)
        remarks=validated_data.pop("remarks", "")
        from apps.common.revenue_api import scoped
        from apps.billing.models import Invoice
        if not scoped(Invoice.objects.filter(pk=validated_data['invoice'].pk),self.context['request'].user).exists():
            raise serializers.ValidationError('Invoice is outside your access scope.')
        existing = Payment.objects.filter(idempotency_key=validated_data.get("idempotency_key")).first()
        if existing and (existing.invoice_id != validated_data["invoice"].pk or existing.channel != validated_data["channel"] or existing.initiated_by_id != self.context["request"].user.pk or existing.submitted_reference != submitted_reference or existing.reported_paid_at!=reported_paid_at or existing.remarks!=remarks):
            raise serializers.ValidationError("Idempotency key belongs to a different payment request.")
        try:
            obj=Payment.create_intent(initiated_by=self.context["request"].user, **validated_data)
            if not existing:
                obj.submitted_reference=submitted_reference
                obj.reported_paid_at=reported_paid_at
                obj.remarks=remarks
                obj.save(update_fields=['submitted_reference','reported_paid_at','remarks','updated_at'])
            return obj
        except IntegrityError as exc:
            raise serializers.ValidationError("Conflicting concurrent payment request; retry with the same idempotency key.") from exc
        except DjangoValidationError as exc:
            raise serializers.ValidationError(exc.messages) from exc


class ReceiptSerializer(serializers.ModelSerializer):
    class Meta:
        model = Receipt
        fields = ("id", "receipt_number", "payment", "invoice", "amount", "currency", "issued_at")


class TestWebhookSerializer(serializers.Serializer):
    event_id = serializers.CharField(max_length=160)
    payment_reference = serializers.CharField(max_length=40)
    provider_reference = serializers.CharField(max_length=120)
    status = serializers.ChoiceField(choices=("successful", "failed"))
    amount = serializers.DecimalField(max_digits=19, decimal_places=2)
    currency = serializers.CharField(min_length=3, max_length=3)


class TestWebhookResponseSerializer(serializers.Serializer):
    payment = serializers.CharField()
    status = serializers.CharField()
    processed = serializers.BooleanField()
