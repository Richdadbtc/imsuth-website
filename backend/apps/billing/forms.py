from django import forms
from django.db.models import Q
from django.utils import timezone

from apps.catalogue.models import Department, Service, TariffVersion
from apps.registry.models import Patient
from .models import BillingCorrectionRequest


class InvoiceCreateForm(forms.Form):
    patient = forms.ModelChoiceField(queryset=Patient.objects.none())
    department = forms.ModelChoiceField(queryset=Department.objects.none())
    service = forms.ModelChoiceField(queryset=Service.objects.none())
    quantity = forms.IntegerField(min_value=1, max_value=100, initial=1)
    line_items = forms.JSONField(required=False, widget=forms.HiddenInput)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["patient"].queryset = Patient.objects.filter(status=Patient.Status.ACTIVE)
        self.fields["department"].queryset = Department.objects.filter(is_active=True)
        self.fields["service"].queryset = Service.objects.filter(is_active=True).select_related("department")

    def clean(self):
        cleaned = super().clean()
        department, service = cleaned.get("department"), cleaned.get("service")
        if department and service and service.department_id != department.id:
            self.add_error("service", "Choose a service from the selected department.")
        if service:
            now = timezone.now()
            tariff = TariffVersion.objects.filter(service=service, is_approved=True, effective_from__lte=now).filter(
                Q(effective_until__isnull=True) | Q(effective_until__gt=now)
            ).order_by("-effective_from").first()
            if tariff is None:
                self.add_error("service", "This service has no approved current tariff.")
            else:
                cleaned["tariff"] = tariff
        line_items = cleaned.get("line_items") or []
        validated_items = []
        for index, item in enumerate(line_items):
            try:
                item_service = Service.objects.get(pk=item.get("service"), is_active=True)
                item_quantity = int(item.get("quantity", 1))
            except (Service.DoesNotExist, TypeError, ValueError):
                raise forms.ValidationError(f"Line {index + 2} contains an invalid service or quantity.")
            if item_quantity < 1 or item_quantity > 100:
                raise forms.ValidationError(f"Line {index + 2} quantity must be between 1 and 100.")
            if department and item_service.department_id != department.id:
                raise forms.ValidationError(f"Line {index + 2} is not in the selected department.")
            now = timezone.now()
            tariff = TariffVersion.objects.filter(service=item_service, is_approved=True, effective_from__lte=now).filter(Q(effective_until__isnull=True) | Q(effective_until__gt=now)).order_by("-effective_from").first()
            if tariff is None:
                raise forms.ValidationError(f"{item_service.name} has no approved current tariff.")
            validated_items.append({"service": item_service, "quantity": item_quantity})
        cleaned["validated_line_items"] = validated_items
        return cleaned


class BillingCorrectionForm(forms.ModelForm):
    class Meta:
        model = BillingCorrectionRequest
        fields = ("reason", "requested_change")
        widgets = {
            "reason": forms.Textarea(attrs={"rows": 4}),
            "requested_change": forms.Textarea(attrs={"rows": 5, "placeholder": '{"requested_action": "void", "details": "..."}'}),
        }

    def clean_requested_change(self):
        value = self.cleaned_data["requested_change"]
        if not isinstance(value, dict) or not value:
            raise forms.ValidationError("Describe the requested correction as a JSON object.")
        return value
