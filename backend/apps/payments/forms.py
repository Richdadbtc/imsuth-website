from django import forms

from .models import Payment


class PaymentCreateForm(forms.Form):
    channel = forms.ChoiceField(choices=Payment.Channel.choices)
    confirmation = forms.BooleanField(label="I have confirmed the invoice and amount with the patient")
