from django.contrib import admin
from django.core.exceptions import PermissionDenied
from .models import CashApprovalLimit


@admin.register(CashApprovalLimit)
class CashApprovalLimitAdmin(admin.ModelAdmin):
    list_display=('role','amount','policy_reference','approved_by','updated_at')
    readonly_fields=('approved_by','created_at','updated_at')
    def has_add_permission(self,request):
        return super().has_add_permission(request) and request.user.role in {'management','super_admin'}
    def has_change_permission(self,request,obj=None):
        return super().has_change_permission(request,obj) and request.user.role in {'management','super_admin'}
    def has_delete_permission(self,request,obj=None):return False
    def save_model(self,request,obj,form,change):
        if request.user.role not in {'management','super_admin'}:raise PermissionDenied()
        from apps.accounts.models import User
        from apps.auditlog.models import AuditEvent
        from django.db import transaction
        if obj.role not in {User.Role.FINANCE,User.Role.MANAGEMENT,User.Role.SUPER_ADMIN}:
            raise PermissionDenied('Only financial approver roles may receive a limit.')
        with transaction.atomic():
            obj.approved_by=request.user
            super().save_model(request,obj,form,change)
            AuditEvent.record('cash_approval_policy.configured',actor=request.user,obj=obj,metadata={'role':obj.role,'amount':str(obj.amount)})
