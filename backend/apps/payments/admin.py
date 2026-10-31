from django.contrib import admin
from apps.common.admin_utils import ReadOnlyAdmin
from .models import Payment, PaymentEvent, Receipt, ReceiptReprint

admin.site.register(Payment, ReadOnlyAdmin)
admin.site.register(PaymentEvent, ReadOnlyAdmin)
admin.site.register(Receipt, ReadOnlyAdmin)
admin.site.register(ReceiptReprint, ReadOnlyAdmin)
