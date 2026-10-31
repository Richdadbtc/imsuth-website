from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import Http404
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404, redirect
from django.views.generic import DetailView, FormView, ListView, TemplateView

from apps.accounts.models import User
from apps.billing.models import Invoice
from apps.common.ui import RoleRequiredMixin

from .forms import PaymentCreateForm
from .models import Payment, Receipt, ReceiptReprint


class TransactionListView(RoleRequiredMixin, ListView):
    allowed_roles = (User.Role.CASHIER, User.Role.FINANCE, User.Role.AUDITOR, User.Role.MANAGEMENT)
    model = Payment
    template_name = "payments/transaction_list.html"
    context_object_name = "payments"
    paginate_by = 25
    queryset = Payment.objects.select_related("invoice", "invoice__patient")

    def get_queryset(self):
        queryset = super().get_queryset()
        query = self.request.GET.get("q", "").strip()
        status = self.request.GET.get("status", "").strip()
        if query:
            from django.db.models import Q
            queryset = queryset.filter(Q(reference__icontains=query) | Q(provider_reference__icontains=query) | Q(invoice__invoice_number__icontains=query) | Q(invoice__patient__patient_id__icontains=query))
        if status:
            queryset = queryset.filter(status=status)
        return queryset


class InvoicePaymentView(RoleRequiredMixin, FormView):
    allowed_roles = (User.Role.CASHIER, User.Role.FINANCE)
    template_name = "payments/payment_form.html"
    form_class = PaymentCreateForm

    def dispatch(self, request, *args, **kwargs):
        self.invoice = get_object_or_404(Invoice.objects.select_related("patient", "department").prefetch_related("items"), pk=kwargs["pk"])
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["invoice"] = self.invoice
        return context

    def form_valid(self, form):
        try:
            payment = Payment.create_intent(invoice=self.invoice, channel=form.cleaned_data["channel"], initiated_by=self.request.user, idempotency_key=f"ui:{self.request.user.pk}:{self.invoice.pk}:{self.invoice.updated_at.isoformat()}")
        except ValidationError as exc:
            form.add_error(None, exc)
            return self.form_invalid(form)
        messages.success(self.request, "Payment initiated. Electronic payments remain pending until provider verification succeeds.")
        return redirect("payment-detail", pk=payment.pk)


class PaymentDetailView(RoleRequiredMixin, DetailView):
    allowed_roles = (User.Role.CASHIER, User.Role.FINANCE, User.Role.AUDITOR, User.Role.MANAGEMENT)
    model = Payment
    template_name = "payments/payment_detail.html"
    context_object_name = "payment"

    def get_queryset(self):
        return super().get_queryset().select_related("invoice__patient", "invoice__department").prefetch_related("events")


class ReceiptPrintView(RoleRequiredMixin, DetailView):
    allowed_roles = (User.Role.CASHIER, User.Role.FINANCE, User.Role.AUDITOR, User.Role.MANAGEMENT)
    model = Receipt
    template_name = "payments/receipt_print.html"

    def get(self, request, *args, **kwargs):
        response = super().get(request, *args, **kwargs)
        if request.GET.get("reprint") == "1":
            reason = request.GET.get("reason", "Staff-requested reprint")[:255]
            ReceiptReprint.objects.create(receipt=self.object, printed_by=request.user, reason=reason, format=request.GET.get("format", "a4"))
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["print_format"] = "thermal" if self.request.GET.get("format") == "thermal" else "a4"
        return context


class ReceiptVerifyView(TemplateView):
    template_name = "payments/receipt_verify.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            context["receipt"] = Receipt.objects.select_related("payment").get(verification_token=kwargs["token"])
        except Receipt.DoesNotExist as exc:
            raise Http404("Receipt not found") from exc
        return context
