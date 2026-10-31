from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers
from django.db import IntegrityError

from apps.catalogue.models import Service
from .models import Invoice, InvoiceItem


class InvoiceItemRequestSerializer(serializers.Serializer):
    service = serializers.PrimaryKeyRelatedField(queryset=Service.objects.filter(is_active=True))
    quantity = serializers.IntegerField(min_value=1, max_value=100, default=1)


class InvoiceItemSerializer(serializers.ModelSerializer):
    line_total = serializers.DecimalField(max_digits=19, decimal_places=2, read_only=True)

    class Meta:
        model = InvoiceItem
        fields = ("id", "service", "service_code", "description", "quantity", "unit_amount", "line_total", "currency")


class InvoiceSerializer(serializers.ModelSerializer):
    items = InvoiceItemRequestSerializer(many=True, write_only=True, min_length=1, max_length=100)
    line_items = InvoiceItemSerializer(source="items", many=True, read_only=True)
    outstanding_balance = serializers.DecimalField(max_digits=19, decimal_places=2, read_only=True)

    class Meta:
        extra_kwargs = {'idempotency_key': {'validators': []}}
        model = Invoice
        fields = ("id", "invoice_number", "payment_reference", "patient", "department", "status", "total_amount", "amount_paid", "outstanding_balance", "currency", "idempotency_key", "issued_at", "items", "line_items")
        read_only_fields = ("id", "invoice_number", "payment_reference", "status", "total_amount", "amount_paid", "currency", "issued_at")

    def create(self, validated_data):
        from apps.common.revenue_api import scoped
        from apps.catalogue.models import Department
        if not scoped(Department.objects.filter(pk=validated_data['department'].pk),self.context['request'].user,'pk').exists():
            raise serializers.ValidationError('Department is outside your access scope.')
        from apps.common.api import RevenuePatientViewSet
        view=RevenuePatientViewSet();view.request=self.context['request']
        if not view.get_queryset().filter(pk=validated_data['patient'].pk).exists():
            raise serializers.ValidationError('Patient is outside your access scope.')
        if not validated_data['department'].is_active:
            raise serializers.ValidationError('Department is inactive.')
        items = validated_data.pop("items")
        try:
            return Invoice.create_from_items(item_requests=items, created_by=self.context["request"].user, **validated_data)
        except IntegrityError as exc:
            raise serializers.ValidationError("Conflicting concurrent invoice request; retry with the same idempotency key.") from exc
        except DjangoValidationError as exc:
            raise serializers.ValidationError(exc.messages) from exc
