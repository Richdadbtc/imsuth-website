from django import forms


class ReconciliationImportForm(forms.Form):
    source = forms.CharField(max_length=64)
    csv_file = forms.FileField(help_text="CSV columns: reference, amount, currency, transaction_date")

    def clean_csv_file(self):
        upload = self.cleaned_data["csv_file"]
        if upload.size > 5 * 1024 * 1024:
            raise forms.ValidationError("The reconciliation file must not exceed 5 MB.")
        if not upload.name.lower().endswith(".csv"):
            raise forms.ValidationError("Upload a CSV file.")
        return upload


class ApprovalDecisionForm(forms.Form):
    decision = forms.ChoiceField(choices=(("approve", "Approve"), ("reject", "Reject")))
    reason = forms.CharField(widget=forms.Textarea(attrs={"rows": 3}), min_length=5)


class FinancialRequestForm(forms.Form):
    request_type = forms.ChoiceField(choices=(("refund", "Refund"), ("reversal", "Reversal")))
    amount = forms.DecimalField(min_value=0.01, required=False, decimal_places=2, max_digits=19)
    reason = forms.CharField(widget=forms.Textarea(attrs={"rows": 3}), min_length=10)

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("request_type") == "refund" and cleaned.get("amount") is None:
            self.add_error("amount", "Refund requests require an amount.")
        return cleaned
