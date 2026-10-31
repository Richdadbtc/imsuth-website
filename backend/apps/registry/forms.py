from django import forms

from .models import Patient


class PatientForm(forms.ModelForm):
    class Meta:
        model = Patient
        fields = ("first_name", "middle_name", "last_name", "date_of_birth", "approximate_age", "sex", "phone", "email", "address", "emergency_contact")
        widgets = {"date_of_birth": forms.DateInput(attrs={"type": "date"}), "address": forms.Textarea(attrs={"rows": 3})}

    def clean(self):
        cleaned = super().clean()
        if not cleaned.get("date_of_birth") and not cleaned.get("approximate_age"):
            self.add_error("approximate_age", "Provide either date of birth or an approximate age.")
        return cleaned
