"""Optional scheduled detector; it records exceptions without changing financial state."""
from celery import shared_task
from .models import Alert


@shared_task
def detect_reconciliation_alerts(min_age_hours=0):
    from apps.operations.models import ReconciliationItem
    # Only linked payments have a proven department; unlinked rows are finance-only.
    from datetime import timedelta
    from django.utils import timezone
    created=0
    rows=ReconciliationItem.objects.exclude(status__in=['matched','resolved'])
    if min_age_hours: rows=rows.filter(transaction_date__lt=timezone.now()-timedelta(hours=min_age_hours))
    for item in rows.select_related('payment__invoice').iterator(chunk_size=200):
        _,new=Alert.objects.get_or_create(alert_type='reconciliation_discrepancy',related_type='operations.ReconciliationItem',related_id=str(item.pk),defaults={'department_id':item.payment.invoice.department_id if item.payment_id else None,'severity':'high','description':'An imported statement row requires reconciliation review.'})
        created+=int(new)
    return created
