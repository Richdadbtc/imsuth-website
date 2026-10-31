from django.contrib.auth.signals import user_logged_in, user_logged_out, user_login_failed
from django.dispatch import receiver

from .models import AuditEvent


@receiver(user_logged_in)
def record_login(sender, request, user, **kwargs):
    AuditEvent.record("authentication.login", actor=user, request=request)


@receiver(user_logged_out)
def record_logout(sender, request, user, **kwargs):
    AuditEvent.record("authentication.logout", actor=user, request=request)


@receiver(user_login_failed)
def record_login_failed(sender, credentials, request, **kwargs):
    AuditEvent.record("authentication.login_failed", request=request, metadata={"username": credentials.get("username", "")[:150]})


class AuthenticationAuditMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)
