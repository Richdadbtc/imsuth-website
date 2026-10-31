from django import forms

from .models import User


class ProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ("first_name", "last_name", "email")


class StaffCreateForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput, min_length=12)

    class Meta:
        model = User
        fields = ("username", "employee_id", "first_name", "last_name", "email", "role", "department", "is_active")

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])
        user.must_change_password = True
        if commit:
            user.save()
        return user


class StaffUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ("employee_id", "first_name", "last_name", "email", "role", "department", "is_active")
