from rest_framework.decorators import action
from rest_framework import serializers
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied, ValidationError
from apps.common.ui_api import invoke
from .services import decide_approval, import_reconciliation_csv

from rest_framework import permissions, viewsets

from apps.accounts.models import User
from .models import ApprovalRequest, ReconciliationBatch
from .serializers import ApprovalRequestSerializer, ReconciliationBatchSerializer


class FinanceControlPermission(permissions.BasePermission):
    roles = {User.Role.FINANCE, User.Role.AUDITOR, User.Role.MANAGEMENT, User.Role.SUPER_ADMIN}

    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role in self.roles


class ApprovalRequestViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ApprovalRequest.objects.select_related("requested_by").all()
    serializer_class = ApprovalRequestSerializer
    permission_classes = (FinanceControlPermission,)
    filterset_fields = ("request_type", "status", "requested_by")

    @action(detail=True, methods=['post'])
    def decide(self, request, pk=None):
        approval = self.get_object()
        approved = serializers.BooleanField().run_validation(request.data.get('approved'))
        reason = serializers.CharField(min_length=5,max_length=255).run_validation(request.data.get('reason'))
        decision = invoke(decide_approval, approval=approval, approver=request.user, approved=approved, reason=reason)
        return Response({'id':decision.pk,'approved':decision.approved,'reason':decision.reason,'decided_at':decision.decided_at})


    @action(detail=True, methods=['get'])
    def history(self, request, pk=None):
        approval=self.get_object()
        return Response(list(approval.decisions.values('id','decided_by','approved','reason','decided_at')))


class ReconciliationBatchViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ReconciliationBatch.objects.select_related("imported_by").prefetch_related("items").order_by("-created_at")
    serializer_class = ReconciliationBatchSerializer
    permission_classes = (FinanceControlPermission,)
    filterset_fields = ("source", "status", "period_start", "period_end")

    @action(detail=False, methods=['post'], url_path='import')
    def import_statement(self, request):
        if request.user.role not in {'finance','super_admin'}:
            raise PermissionDenied('Only finance administrators may import statements.')
        uploaded=request.FILES.get('file')
        source=serializers.CharField(max_length=64).run_validation(request.data.get('source'))
        if not uploaded or uploaded.size>5*1024*1024:
            raise ValidationError('Select a statement CSV up to 5MB.')
        try:
            batch=invoke(import_reconciliation_csv,content=uploaded.read(),source=source,imported_by=request.user)
        except UnicodeDecodeError:
            raise ValidationError('Use a UTF-8 CSV file.')
        return Response(self.get_serializer(batch).data,status=201)
