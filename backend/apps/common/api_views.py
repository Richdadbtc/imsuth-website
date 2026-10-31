from django.contrib.auth import authenticate, login, logout
from django.db.models import Sum
from django.middleware.csrf import get_token
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect, ensure_csrf_cookie
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.models import User
from apps.auditlog.models import AuditEvent
from apps.billing.models import Invoice
from apps.operations.models import ApprovalRequest, NotificationRecipient, ReconciliationBatch
from apps.payments.models import Payment
from apps.registry.models import Patient


def user_payload(user):
    return {
        "id": user.pk,
        "username": user.username,
        "full_name": user.get_full_name() or user.username,
        "role": user.role,
        "role_label": user.get_role_display(),
        "employee_id": user.employee_id,
        "email": user.email,
        "department": user.department_id,
        "is_active": user.is_active,
        "last_login": user.last_login,
        "date_joined": user.date_joined,
        "permissions": {
            "patients": user.role in {User.Role.FRONT_DESK, User.Role.SUPER_ADMIN, User.Role.DEPARTMENT_SUPERVISOR, User.Role.CASHIER, User.Role.FINANCE},
            "billing": bool(user.role),
            "payments": user.role in {User.Role.CASHIER, User.Role.FINANCE, User.Role.AUDITOR, User.Role.MANAGEMENT, User.Role.SUPER_ADMIN},
            "finance": user.role in {User.Role.FINANCE, User.Role.AUDITOR, User.Role.MANAGEMENT, User.Role.SUPER_ADMIN},
            "administration": user.role == User.Role.SUPER_ADMIN,
            "reports": user.role in {User.Role.FINANCE, User.Role.AUDITOR, User.Role.MANAGEMENT, User.Role.SUPER_ADMIN},
        },
    }


@method_decorator(ensure_csrf_cookie, name="dispatch")
class SessionView(APIView):
    permission_classes = (permissions.AllowAny,)

    def get(self, request):
        payload = {"authenticated": request.user.is_authenticated, "csrf_token": get_token(request)}
        if request.user.is_authenticated:
            payload["user"] = user_payload(request.user)
        return Response(payload)


@method_decorator(csrf_protect, name="dispatch")
class SessionLoginView(APIView):
    permission_classes = (permissions.AllowAny,)

    def post(self, request):
        username = str(request.data.get("username", "")).strip()
        password = str(request.data.get("password", ""))
        user = authenticate(request, username=username, password=password)
        if user is None or not user.is_active:
            return Response({"detail": "The username or password was not recognised."}, status=status.HTTP_400_BAD_REQUEST)
        from rest_framework import serializers
        remembered=serializers.BooleanField().run_validation(request.data.get('remember_me',False))
        login(request, user)
        request.session.set_expiry(8*60*60 if remembered else 0)
        AuditEvent.record("account.login", actor=user, obj=user, request=request)
        return Response({"authenticated": True, "user": user_payload(user)})


class SessionLogoutView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request):
        AuditEvent.record("account.logout", actor=request.user, request=request)
        logout(request)
        return Response(status=status.HTTP_204_NO_CONTENT)


class DashboardSummaryView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request):
        today = timezone.localdate()
        week_start = today - timezone.timedelta(days=today.weekday())
        from .revenue_api import scoped
        confirmed = scoped(Payment.objects.filter(status=Payment.Status.CONFIRMED),request.user,'invoice__department_id')
        recent = confirmed.select_related("invoice__patient", "invoice__department").order_by("-confirmed_at")[:8]
        return Response({
            "metrics": {
                "today_revenue": confirmed.filter(confirmed_at__date=today).aggregate(total=Sum("amount"))["total"] or 0,
                "week_revenue": confirmed.filter(confirmed_at__date__gte=week_start).aggregate(total=Sum("amount"))["total"] or 0,
                "month_revenue": confirmed.filter(confirmed_at__year=today.year, confirmed_at__month=today.month).aggregate(total=Sum("amount"))["total"] or 0,
                "transactions": confirmed.count(),
                "outstanding_invoices": scoped(Invoice.objects.filter(status__in=(Invoice.Status.ISSUED, Invoice.Status.PARTIALLY_PAID)),request.user).count(),
                "patients_today": Patient.objects.filter(created_at__date=today,registered_by=request.user).count() if request.user.role not in {'super_admin','finance','management','auditor'} else Patient.objects.filter(created_at__date=today).count(),
                "invoices_today": scoped(Invoice.objects.filter(created_at__date=today),request.user).count(),
                "pending_approvals": ApprovalRequest.objects.filter(status=ApprovalRequest.Status.PENDING).count() if request.user.role in {'super_admin','finance','management','auditor'} else 0,
                "reconciliation_reviews": ReconciliationBatch.objects.filter(status=ReconciliationBatch.Status.REVIEW_REQUIRED).count() if request.user.role in {'super_admin','finance','management','auditor'} else 0,
                "unread_notifications": NotificationRecipient.objects.filter(user=request.user, read_at__isnull=True).count(),
            },
            "recent_transactions": [{
                "id": payment.pk,
                "reference": payment.reference,
                "patient": payment.invoice.patient.patient_id,
                "department": payment.invoice.department.name,
                "amount": payment.amount,
                "currency": payment.currency,
                "channel": payment.get_channel_display(),
                "status": payment.status,
                "confirmed_at": payment.confirmed_at,
            } for payment in recent],
        })

from drf_spectacular.utils import extend_schema_view, extend_schema, OpenApiTypes
for _view, _method in ((SessionView,'get'),(SessionLoginView,'post'),(SessionLogoutView,'post'),(DashboardSummaryView,'get')):
    extend_schema_view(**{_method:extend_schema(request=OpenApiTypes.OBJECT if _method=='post' else None,responses=OpenApiTypes.OBJECT)})(_view)
