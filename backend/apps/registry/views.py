from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.db.models import Count, Prefetch, Q, Sum
from django.contrib import messages
from django.urls import reverse
from django.utils import timezone
from django.views.generic import CreateView, DetailView, ListView, UpdateView

from apps.accounts.models import User
from apps.common.ui import RoleRequiredMixin

from .forms import PatientForm
from apps.billing.models import Invoice
from apps.catalogue.models import Department
from apps.payments.models import Payment

from .models import Patient, PatientRevision, normalize_phone


class PatientListView(RoleRequiredMixin, ListView):
    allowed_roles = (User.Role.SUPER_ADMIN, User.Role.FRONT_DESK)
    model = Patient
    template_name = "registry/patient_list.html"
    context_object_name = "patients"
    paginate_by = 25

    def get_queryset(self):
        queryset = super().get_queryset()
        query = self.request.GET.get("q", "").strip()
        status = self.request.GET.get("status", "").strip()
        department = self.request.GET.get("department", "").strip()
        if query:
            phone_digits = normalize_phone(query)
            filters = (
                Q(patient_id__icontains=query)
                | Q(first_name__icontains=query)
                | Q(middle_name__icontains=query)
                | Q(last_name__icontains=query)
                | Q(normalized_phone__icontains=query)
            )
            if phone_digits:
                filters |= Q(normalized_phone__icontains=phone_digits)
            queryset = queryset.filter(filters)
        if status in Patient.Status.values:
            queryset = queryset.filter(status=status)
        if department:
            # A patient is linked to a department only through issued invoices.
            queryset = queryset.filter(invoices__department_id=department).distinct()
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        today = timezone.localdate()
        registry = Patient.objects.all()
        context.update({
            "total_patients": registry.count(),
            "new_this_month": registry.filter(created_at__year=today.year, created_at__month=today.month).count(),
            "active_patients": registry.filter(status=Patient.Status.ACTIVE).count(),
            "pending_records": registry.filter(status=Patient.Status.DUPLICATE_REVIEW).count(),
            "patient_statuses": Patient.Status.choices,
            "departments": Department.objects.filter(is_active=True).order_by("name"),
        })
        return context


class PatientCreateView(RoleRequiredMixin, CreateView):
    allowed_roles = (User.Role.SUPER_ADMIN, User.Role.FRONT_DESK)
    model = Patient
    form_class = PatientForm
    template_name = "registry/patient_form.html"

    def form_valid(self, form):
        form.instance.registered_by = self.request.user
        response = super().form_valid(form)
        duplicates = self.object.potential_duplicates().count()
        if duplicates:
            messages.warning(self.request, f"Patient registered. {duplicates} possible duplicate record(s) require review.")
        else:
            messages.success(self.request, "Patient registered successfully. Continue to billing when ready.")
        return response

    def get_success_url(self):
        return reverse("patient-detail", kwargs={"pk": self.object.pk})


class PatientDetailView(RoleRequiredMixin, DetailView):
    allowed_roles = (User.Role.SUPER_ADMIN, User.Role.FRONT_DESK)
    model = Patient
    template_name = "registry/patient_detail.html"
    context_object_name = "patient"

    def get_queryset(self):
        payment_queryset = Payment.objects.select_related("receipt").order_by("-created_at")
        invoice_queryset = Invoice.objects.select_related("department").prefetch_related(Prefetch("payments", queryset=payment_queryset))
        return super().get_queryset().select_related("registered_by").prefetch_related(Prefetch("invoices", queryset=invoice_queryset))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        invoices = list(self.object.invoices.all())
        payments = [payment for invoice in invoices for payment in invoice.payments.all()]
        context.update({
            "invoices": invoices,
            "payments": sorted(payments, key=lambda item: item.created_at, reverse=True),
            "invoice_total": len(invoices),
            "payment_total": len(payments),
        })
        return context


class PatientUpdateView(RoleRequiredMixin, UpdateView):
    allowed_roles = (User.Role.SUPER_ADMIN, User.Role.FRONT_DESK)
    model = Patient
    form_class = PatientForm
    template_name = "registry/patient_form.html"

    def get_form_kwargs(self):
        # Capture the persisted values before the ModelForm mutates the instance
        # during validation, so the audit revision reflects the true before/after.
        kwargs = super().get_form_kwargs()
        self.original_values = {
            name: str(getattr(self.object, name) or "")
            for name in PatientForm.Meta.fields
        }
        return kwargs

    def form_valid(self, form):
        before = getattr(self, "original_values", {})
        with transaction.atomic():
            response = super().form_valid(form)
            after = {name: str(getattr(self.object, name) or "") for name in form.fields}
            changed = {name: value for name, value in after.items() if value != before.get(name)}
            if changed:
                PatientRevision.objects.create(
                    patient=self.object,
                    changed_by=self.request.user,
                    reason="Authorised demographic update",
                    before={name: before.get(name, "") for name in changed},
                    after=changed,
                )
        messages.success(self.request, "Patient details updated and recorded in the audit history.")
        return response

    def get_success_url(self):
        return reverse("patient-detail", kwargs={"pk": self.object.pk})
