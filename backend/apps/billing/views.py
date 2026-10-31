from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.shortcuts import redirect
from django.urls import reverse
from django.views.generic import CreateView, DetailView, FormView, ListView

from apps.accounts.models import User
from apps.common.ui import RoleRequiredMixin

from apps.auditlog.models import AuditEvent
from .forms import BillingCorrectionForm, InvoiceCreateForm
from .models import BillingCorrectionRequest, Invoice


class InvoiceListView(RoleRequiredMixin, ListView):
    allowed_roles = (User.Role.SUPER_ADMIN, User.Role.FRONT_DESK, User.Role.CASHIER, User.Role.FINANCE, User.Role.AUDITOR, User.Role.MANAGEMENT, User.Role.DEPARTMENT_SUPERVISOR)
    model = Invoice
    template_name = "billing/invoice_list.html"
    context_object_name = "invoices"
    paginate_by = 25

    def get_queryset(self):
        queryset = super().get_queryset().select_related("patient", "department")
        if self.request.user.role == User.Role.DEPARTMENT_SUPERVISOR:
            queryset = queryset.filter(department=self.request.user.department)
        query = self.request.GET.get("q", "").strip()
        if query:
            queryset = queryset.filter(Q(invoice_number__icontains=query) | Q(payment_reference__icontains=query) | Q(patient__patient_id__icontains=query) | Q(patient__last_name__icontains=query))
        return queryset


class InvoiceCreateView(RoleRequiredMixin, FormView):
    allowed_roles = (User.Role.SUPER_ADMIN, User.Role.FRONT_DESK, User.Role.CASHIER, User.Role.FINANCE)
    template_name = "billing/invoice_form.html"
    form_class = InvoiceCreateForm

    def get_initial(self):
        initial = super().get_initial()
        if self.request.GET.get("patient"):
            initial["patient"] = self.request.GET["patient"]
        return initial

    def form_valid(self, form):
        try:
            item_requests = [{"service": form.cleaned_data["service"], "quantity": form.cleaned_data["quantity"]}]
            item_requests.extend(form.cleaned_data.get("validated_line_items", []))
            invoice = Invoice.create_from_items(
                patient=form.cleaned_data["patient"], department=form.cleaned_data["department"],
                item_requests=item_requests,
                created_by=self.request.user,
            )
        except ValidationError as exc:
            form.add_error(None, exc)
            return self.form_invalid(form)
        messages.success(self.request, f"Invoice {invoice.invoice_number} generated from the approved tariff.")
        return redirect("invoice-detail", pk=invoice.pk)


class InvoiceDetailView(RoleRequiredMixin, DetailView):
    allowed_roles = (User.Role.SUPER_ADMIN, User.Role.FRONT_DESK, User.Role.CASHIER, User.Role.FINANCE, User.Role.AUDITOR, User.Role.MANAGEMENT, User.Role.DEPARTMENT_SUPERVISOR)
    model = Invoice
    template_name = "billing/invoice_detail.html"
    context_object_name = "invoice"

    def get_queryset(self):
        queryset = super().get_queryset().select_related("patient", "department", "created_by").prefetch_related("items", "payments")
        if self.request.user.role == User.Role.DEPARTMENT_SUPERVISOR:
            queryset = queryset.filter(department=self.request.user.department)
        return queryset


class InvoicePrintView(InvoiceDetailView):
    template_name = "billing/invoice_print.html"


class BillingCorrectionCreateView(RoleRequiredMixin, CreateView):
    allowed_roles = (User.Role.SUPER_ADMIN, User.Role.FRONT_DESK, User.Role.CASHIER, User.Role.FINANCE)
    model = BillingCorrectionRequest
    form_class = BillingCorrectionForm
    template_name = "billing/correction_form.html"

    def dispatch(self, request, *args, **kwargs):
        self.invoice = Invoice.objects.filter(pk=kwargs["pk"]).first()
        if self.invoice is None:
            from django.http import Http404
            raise Http404
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["invoice"] = self.invoice
        return context

    def form_valid(self, form):
        form.instance.invoice = self.invoice
        form.instance.requested_by = self.request.user
        response = super().form_valid(form)
        AuditEvent.record("billing.correction_requested", actor=self.request.user, obj=self.object, request=self.request, reason=self.object.reason)
        messages.success(self.request, "Billing correction request submitted for review.")
        return response

    def get_success_url(self):
        return reverse("invoice-detail", kwargs={"pk": self.invoice.pk})
