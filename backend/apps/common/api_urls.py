from rest_framework.routers import DefaultRouter

from .api import RevenueDepartmentViewSet as DepartmentViewSet, RevenuePatientViewSet as PatientViewSet, RevenueServiceViewSet as ServiceViewSet, TariffVersionViewSet
from apps.billing.api import InvoiceViewSet
from apps.payments.api import PaymentViewSet, ReceiptViewSet, TestWebhookView
from apps.operations.api import ApprovalRequestViewSet, ReconciliationBatchViewSet
from django.urls import path
from .api_views import DashboardSummaryView, SessionLoginView, SessionLogoutView, SessionView

from .ui_api import (StaffViewSet, RoleViewSet, ConfigurationViewSet, TicketViewSet, AttachmentView,
    MyProfileView, PasswordChangeView, RefundViewSet, ReversalViewSet, SettlementViewSet,
    AuditViewSet, ReprintViewSet, ReceiptVerificationView, NotificationViewSet, InboxViewSet,
    CapabilitiesView, DiscrepancyViewSet, TariffManagementViewSet, ProfilePhotoView, IntegrationActionView, HelpResourcesView, DeactivateAccountView, ReportCatalogueView)
from .reports_api import ReportView

from .revenue_api import (AlertViewSet, CashPointViewSet, CashOrderViewSet, DepartmentDeskViewSet,
    RevenueDashboardView, UsersViewSet, AuditLogsViewSet, TariffProposalViewSet)

router = DefaultRouter()
router.register("alerts", AlertViewSet)
router.register("cash-points", CashPointViewSet)
router.register("cash-orders", CashOrderViewSet)
router.register("department-desk", DepartmentDeskViewSet, basename="department-desk")
router.register("users", UsersViewSet, basename="revenue-user")
router.register("audit-logs", AuditLogsViewSet, basename="revenue-audit-log")
router.register("tariff-proposals", TariffProposalViewSet)
router.register("patients", PatientViewSet)
router.register("departments", DepartmentViewSet)
router.register("services", ServiceViewSet)
router.register("tariffs", TariffManagementViewSet)
router.register("invoices", InvoiceViewSet)
router.register("payments", PaymentViewSet)
router.register("receipts", ReceiptViewSet)
router.register("approvals", ApprovalRequestViewSet)
router.register("reconciliation-batches", ReconciliationBatchViewSet)

from .recovery import RecoveryRequestView, RecoveryVerifyView, RecoveryCompleteView

router.register("staff", StaffViewSet)
router.register("roles", RoleViewSet)
router.register("settings", ConfigurationViewSet)
router.register("support-tickets", TicketViewSet, basename="support-ticket")
router.register("refunds", RefundViewSet)
router.register("reversals", ReversalViewSet)
router.register("settlements", SettlementViewSet)
router.register("audit-events", AuditViewSet)
router.register("receipt-reprints", ReprintViewSet)
router.register("notifications", NotificationViewSet)
router.register("inbox", InboxViewSet, basename="inbox")
router.register("discrepancies", DiscrepancyViewSet)

from .record_payment import RecordPaymentView
from apps.catalogue.catalogue_api import CatalogueSetupView

app_name = "api"
urlpatterns = [
    path("catalogue-setup/", CatalogueSetupView.as_view()),
    path("catalogue-setup/<slug:operation>/", CatalogueSetupView.as_view()),
    path("record-payment/", RecordPaymentView.as_view()),
    path("dashboard/<slug:metric>/", RevenueDashboardView.as_view()),
    path("help/", HelpResourcesView.as_view()),
    path("profile/deactivate/", DeactivateAccountView.as_view()),
    path("reports/", ReportCatalogueView.as_view()),
    path("profile/photo/", ProfilePhotoView.as_view()),
    path("integrations/<slug:operation>/", IntegrationActionView.as_view()),
    path("capabilities/", CapabilitiesView.as_view()),
    path("profile/", MyProfileView.as_view()),
    path("profile/password/", PasswordChangeView.as_view()),
    path("attachments/<uuid:pk>/", AttachmentView.as_view()),
    path("receipts/verify/", ReceiptVerificationView.as_view()),
    path("reports/<slug:report>/", ReportView.as_view()),
    path("session/recovery/request/", RecoveryRequestView.as_view()),
    path("session/recovery/verify/", RecoveryVerifyView.as_view()),
    path("session/recovery/complete/", RecoveryCompleteView.as_view()),
    path("session/", SessionView.as_view(), name="session"),
    path("session/login/", SessionLoginView.as_view(), name="session-login"),
    path("session/logout/", SessionLogoutView.as_view(), name="session-logout"),
    path("dashboard/", DashboardSummaryView.as_view(), name="dashboard-summary"),
    path("payments/test-webhook/", TestWebhookView.as_view(), name="test-payment-webhook"),
] + router.urls
