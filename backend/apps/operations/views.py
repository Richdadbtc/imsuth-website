import csv

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.exceptions import PermissionDenied, ValidationError
from django.db.models import Count, Sum
from django.db.models.functions import TruncDate, TruncMonth, TruncWeek
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.utils import timezone
from django.utils.dateparse import parse_date
from django.views import View
from django.views.generic import DetailView, FormView, ListView, TemplateView

from apps.accounts.models import User
from apps.billing.models import Invoice
from apps.catalogue.models import TariffVersion
from apps.payments.models import Payment
from apps.registry.models import Patient
from apps.auditlog.models import AuditEvent
from .forms import ApprovalDecisionForm, FinancialRequestForm, ReconciliationImportForm
from .models import ApprovalRequest, NotificationRecipient, ReconciliationBatch, Refund, Reversal, Settlement
from .services import decide_approval, import_reconciliation_csv, request_refund, request_reversal


class FinanceAccessMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        return self.request.user.has_paypoint_role(User.Role.FINANCE, User.Role.AUDITOR, User.Role.MANAGEMENT)


class ManagementDashboardView(FinanceAccessMixin, TemplateView):
    template_name = "operations/management_dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        today = timezone.localdate()
        confirmed = Payment.objects.filter(status=Payment.Status.CONFIRMED)
        date_from = parse_date(self.request.GET.get("from", ""))
        date_to = parse_date(self.request.GET.get("to", ""))
        if date_from:
            confirmed = confirmed.filter(confirmed_at__date__gte=date_from)
        if date_to:
            confirmed = confirmed.filter(confirmed_at__date__lte=date_to)
        week_start = today - timezone.timedelta(days=today.weekday())
        month_total = confirmed.filter(
            confirmed_at__year=today.year,
            confirmed_at__month=today.month,
        ).aggregate(total=Sum("amount"))["total"] or 0
        department_total = confirmed.aggregate(total=Sum("amount"))["total"] or 0
        department_rows = list(
            confirmed.values("invoice__department__name")
            .annotate(total=Sum("amount"), count=Count("id"))
            .order_by("-total")
        )
        for row in department_rows:
            row["percentage"] = round((row["total"] / department_total) * 100) if department_total else 0

        daily_revenue = []
        for offset in range(6, -1, -1):
            day = today - timezone.timedelta(days=offset)
            total = confirmed.filter(confirmed_at__date=day).aggregate(total=Sum("amount"))["total"] or 0
            daily_revenue.append({"date": day, "total": total})
        chart_max = max((row["total"] for row in daily_revenue), default=0) or 1
        for row in daily_revenue:
            row["percentage"] = round((row["total"] / chart_max) * 100)

        channel_keys = [value for value, _label in Payment.Channel.choices]
        channel_labels = dict(Payment.Channel.choices)

        def month_start(months_ago):
            month_index = today.year * 12 + today.month - 1 - months_ago
            return today.replace(year=month_index // 12, month=month_index % 12 + 1, day=1)

        daily_periods = [today - timezone.timedelta(days=offset) for offset in range(6, -1, -1)]
        weekly_periods = [week_start - timezone.timedelta(weeks=offset) for offset in range(5, -1, -1)]
        monthly_periods = [month_start(offset) for offset in range(5, -1, -1)]

        def build_series(periods, truncation, label_format):
            grouped = confirmed.filter(confirmed_at__date__gte=periods[0]).annotate(
                period=truncation("confirmed_at")
            ).values("period", "channel").annotate(total=Sum("amount"))
            totals = {}
            for row in grouped:
                period = row["period"]
                if hasattr(period, "date"):
                    period = period.date()
                totals[(period, row["channel"])] = float(row["total"])
            return [{
                "label": period.strftime(label_format),
                "channels": {channel: totals.get((period, channel), 0) for channel in channel_keys},
            } for period in periods]

        revenue_series = {
            "channels": [{"key": key, "label": channel_labels[key]} for key in channel_keys],
            "daily": build_series(daily_periods, TruncDate, "%d %b"),
            "weekly": build_series(weekly_periods, TruncWeek, "%d %b"),
            "monthly": build_series(monthly_periods, TruncMonth, "%b %Y"),
        }

        context.update({
            "today_total": confirmed.filter(confirmed_at__date=today).aggregate(total=Sum("amount"))["total"] or 0,
            "week_total": confirmed.filter(confirmed_at__date__gte=week_start).aggregate(total=Sum("amount"))["total"] or 0,
            "month_total": month_total,
            "transaction_count": confirmed.count(),
            "pending_invoices": Invoice.objects.filter(status__in=(Invoice.Status.ISSUED, Invoice.Status.PARTIALLY_PAID)).count(),
            "payment_reviews": Payment.objects.filter(status__in=(Payment.Status.AWAITING_OFFLINE_VERIFICATION, Payment.Status.REVIEW_REQUIRED)).count(),
            "pending_approvals": ApprovalRequest.objects.filter(status=ApprovalRequest.Status.PENDING).count(),
            "tariff_reviews": TariffVersion.objects.filter(is_approved=False).count(),
            "unmatched": ReconciliationBatch.objects.filter(status=ReconciliationBatch.Status.REVIEW_REQUIRED).count(),
            "refunds_pending": Refund.objects.filter(status=Refund.Status.APPROVED_PENDING_EXECUTION).count(),
            "reversals_pending": Reversal.objects.filter(status=Reversal.Status.APPROVED_PENDING_EXECUTION).count(),
            "by_channel": confirmed.values("channel").annotate(total=Sum("amount"), count=Count("id")).order_by("channel"),
            "by_department": department_rows,
            "department_total": department_total,
            "daily_revenue": daily_revenue,
            "revenue_series": revenue_series,
            "today": today,
            "new_patients_today": Patient.objects.filter(created_at__date=today).count(),
            "invoices_today": Invoice.objects.filter(created_at__date=today).count(),
            "verified_payments_today": Payment.objects.filter(status=Payment.Status.CONFIRMED, confirmed_at__date=today).count(),
            "notifications": NotificationRecipient.objects.filter(user=self.request.user).select_related("notification").order_by("-notification__created_at")[:10],
            "recent_transactions": confirmed.select_related("invoice__patient", "invoice__department")[:8],
            "date_from": date_from,
            "date_to": date_to,
        })
        return context


class ReconciliationListView(FinanceAccessMixin, ListView):
    model = ReconciliationBatch
    template_name = "operations/reconciliation_list.html"
    context_object_name = "batches"
    paginate_by = 25


class ReconciliationDetailView(FinanceAccessMixin, DetailView):
    model = ReconciliationBatch
    template_name = "operations/reconciliation_detail.html"
    context_object_name = "batch"

    def get_queryset(self):
        return super().get_queryset().select_related("imported_by").prefetch_related("items", "items__payment")


class ReconciliationImportView(FinanceAccessMixin, FormView):
    template_name = "operations/reconciliation_import.html"
    form_class = ReconciliationImportForm

    def form_valid(self, form):
        try:
            batch = import_reconciliation_csv(content=form.cleaned_data["csv_file"].read(), source=form.cleaned_data["source"], imported_by=self.request.user)
        except (ValidationError, UnicodeDecodeError) as exc:
            form.add_error("csv_file", exc)
            return self.form_invalid(form)
        messages.success(self.request, "Reconciliation batch imported and matched.")
        return redirect("reconciliation-detail", pk=batch.pk)


class RevenueExportView(FinanceAccessMixin, View):
    def get(self, request):
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="imsuth-revenue-export.csv"'
        writer = csv.writer(response)
        writer.writerow(("payment_reference", "invoice", "department", "channel", "amount", "currency", "confirmed_at"))
        for payment in Payment.objects.filter(status=Payment.Status.CONFIRMED).select_related("invoice__department").iterator():
            writer.writerow((payment.reference, payment.invoice.invoice_number, payment.invoice.department.name, payment.channel, payment.amount, payment.currency, payment.confirmed_at.isoformat()))
        return response


class FinanceWorkspaceView(FinanceAccessMixin, TemplateView):
    template_name = "operations/finance_workspace.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            "approvals": ApprovalRequest.objects.select_related("requested_by")[:12],
            "refunds": Refund.objects.select_related("payment", "requested_by")[:10],
            "reversals": Reversal.objects.select_related("payment", "requested_by")[:10],
            "settlements": Settlement.objects.all().order_by("-settlement_date")[:10],
        })
        return context


class ApprovalDecisionView(FinanceAccessMixin, FormView):
    template_name = "operations/approval_decision.html"
    form_class = ApprovalDecisionForm

    def dispatch(self, request, *args, **kwargs):
        self.approval = get_object_or_404(ApprovalRequest.objects.select_related("requested_by"), pk=kwargs["pk"])
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["approval"] = self.approval
        return context

    def form_valid(self, form):
        try:
            decide_approval(approval=self.approval, approver=self.request.user, approved=form.cleaned_data["decision"] == "approve", reason=form.cleaned_data["reason"])
        except (ValidationError, PermissionDenied) as exc:
            form.add_error(None, exc)
            return self.form_invalid(form)
        messages.success(self.request, "Approval decision recorded.")
        return redirect("finance-workspace")


class FinancialRequestView(FinanceAccessMixin, FormView):
    template_name = "operations/financial_request.html"
    form_class = FinancialRequestForm

    def dispatch(self, request, *args, **kwargs):
        self.payment = get_object_or_404(Payment.objects.select_related("invoice", "invoice__patient"), pk=kwargs["pk"])
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["payment"] = self.payment
        return context

    def form_valid(self, form):
        try:
            if form.cleaned_data["request_type"] == "refund":
                request_refund(payment=self.payment, amount=form.cleaned_data["amount"], reason=form.cleaned_data["reason"], requested_by=self.request.user)
            else:
                request_reversal(payment=self.payment, reason=form.cleaned_data["reason"], requested_by=self.request.user)
        except ValidationError as exc:
            form.add_error(None, exc)
            return self.form_invalid(form)
        messages.success(self.request, "Financial request submitted for independent approval.")
        return redirect("payment-detail", pk=self.payment.pk)


class NotificationListView(LoginRequiredMixin, ListView):
    model = NotificationRecipient
    template_name = "operations/notification_list.html"
    context_object_name = "notifications"
    paginate_by = 25

    def get_queryset(self):
        return super().get_queryset().filter(user=self.request.user).select_related("notification").order_by("-notification__created_at")


class NotificationDetailView(LoginRequiredMixin, DetailView):
    model = NotificationRecipient
    template_name = "operations/notification_detail.html"
    context_object_name = "recipient"

    def get_queryset(self):
        return super().get_queryset().filter(user=self.request.user).select_related("notification")


class NotificationReadView(LoginRequiredMixin, View):
    def post(self, request, pk):
        recipient = get_object_or_404(NotificationRecipient, pk=pk, user=request.user)
        if recipient.read_at is None:
            recipient.read_at = timezone.now()
            recipient.save(update_fields=("read_at",))
        messages.success(request, "Notification marked as read.")
        return redirect("notification-detail", pk=recipient.pk)


class AuditLogView(FinanceAccessMixin, ListView):
    model = AuditEvent
    template_name = "operations/audit_log.html"
    context_object_name = "events"
    paginate_by = 50

    def get_queryset(self):
        queryset = super().get_queryset().select_related("actor")
        query = self.request.GET.get("q", "").strip()
        if query:
            queryset = queryset.filter(action__icontains=query)
        return queryset
