def notification_summary(request):
    if not request.user.is_authenticated:
        return {"unread_notification_count": 0}
    from .models import NotificationRecipient
    return {"unread_notification_count": NotificationRecipient.objects.filter(user=request.user, read_at__isnull=True).count()}
