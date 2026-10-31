from django import forms

from .models import Department, Service, TariffVersion


class DepartmentForm(forms.ModelForm):
    def clean_is_active(self):
        from .catalogue_setup import imported_department
        value=self.cleaned_data.get("is_active")
        if value and not self.instance.is_active and imported_department(self.instance):
            raise forms.ValidationError("Imported placeholders require catalogue activation approval.")
        return value

    class Meta:
        model = Department
        fields = ("code", "name", "description", "is_active")


class ServiceForm(forms.ModelForm):
    class Meta:
        model = Service
        fields = ("department", "code", "name", "description", "is_active")


class TariffForm(forms.ModelForm):
    class Meta:
        model = TariffVersion
        fields = ("service", "amount", "currency", "effective_from", "effective_until", "approval_reference")
        widgets = {
            "effective_from": forms.DateTimeInput(attrs={"type": "datetime-local"}),
            "effective_until": forms.DateTimeInput(attrs={"type": "datetime-local"}),
        }

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("effective_until") and cleaned.get("effective_from") and cleaned["effective_until"] <= cleaned["effective_from"]:
            self.add_error("effective_until", "The end date must be after the effective date.")
        return cleaned
