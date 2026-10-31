from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import connection
from django.http import JsonResponse
from django.views import View
from django.views.generic import TemplateView


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = "dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from apps.registry.models import Patient
        from apps.catalogue.models import Department, Service
        from apps.billing.models import Invoice
        from apps.payments.models import Payment
        from apps.operations.models import ApprovalRequest, ReconciliationBatch

        context.update({
            "patient_count": Patient.objects.filter(status=Patient.Status.ACTIVE).count(),
            "department_count": Department.objects.filter(is_active=True).count(),
            "service_count": Service.objects.filter(is_active=True).count(),
            "pending_invoice_count": Invoice.objects.filter(status__in=(Invoice.Status.ISSUED, Invoice.Status.PARTIALLY_PAID)).count(),
            "pending_payment_count": Payment.objects.filter(status__in=(Payment.Status.PENDING, Payment.Status.AWAITING_OFFLINE_VERIFICATION, Payment.Status.REVIEW_REQUIRED)).count(),
            "approval_count": ApprovalRequest.objects.filter(status=ApprovalRequest.Status.PENDING).count(),
            "discrepancy_count": ReconciliationBatch.objects.filter(status=ReconciliationBatch.Status.REVIEW_REQUIRED).count(),
            "recent_invoices": Invoice.objects.select_related("patient", "department")[:6],
        })
        return context


class HealthView(View):
    def get(self, request):
        from django.db import DatabaseError
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
        except DatabaseError:
            response = JsonResponse({"status": "unavailable"}, status=503)
        else:
            response = JsonResponse({"status": "ok", "service": "imsuth-paypoint"})
        response['Cache-Control'] = 'no-store'
        return response
