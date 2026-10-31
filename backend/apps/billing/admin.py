from django.contrib import admin
from apps.common.admin_utils import ReadOnlyAdmin
from .models import BillingCorrectionRequest, Invoice, InvoiceItem

admin.site.register(Invoice, ReadOnlyAdmin)
admin.site.register(InvoiceItem, ReadOnlyAdmin)
admin.site.register(BillingCorrectionRequest, ReadOnlyAdmin)
