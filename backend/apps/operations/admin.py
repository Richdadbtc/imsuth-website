from django.contrib import admin
from apps.common.admin_utils import ReadOnlyAdmin
from .models import ApprovalDecision, ApprovalRequest, Notification, NotificationRecipient, ReconciliationBatch, ReconciliationItem, Refund, Reversal, Settlement

for model in (ApprovalDecision, ApprovalRequest, Notification, NotificationRecipient, ReconciliationBatch, ReconciliationItem, Refund, Reversal, Settlement):
    admin.site.register(model, ReadOnlyAdmin)
