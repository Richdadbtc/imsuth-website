from celery import shared_task
from django.core.mail import send_mail
from django.utils import timezone

from .models import NotificationRecipient


@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=True, max_retries=3)
def deliver_notification(self, recipient_id):
    recipient = NotificationRecipient.objects.select_related("notification", "user").get(pk=recipient_id)
    recipient.attempts += 1
    recipient.last_attempt_at = timezone.now()
    notification = recipient.notification
    if notification.channel == notification.Channel.IN_APP:
        recipient.status = NotificationRecipient.Status.SENT
        recipient.save(update_fields=("attempts", "last_attempt_at", "status"))
        return
    if notification.channel == notification.Channel.SMS:
        raise RuntimeError("SMS provider is not configured.")
    destination = recipient.destination or recipient.user.email
    if not destination:
        raise RuntimeError("Notification recipient has no approved email address.")
    send_mail(notification.subject, notification.body, None, [destination], fail_silently=False)
    recipient.status = NotificationRecipient.Status.SENT
    recipient.last_error = ""
    recipient.save(update_fields=("attempts", "last_attempt_at", "status", "last_error"))
