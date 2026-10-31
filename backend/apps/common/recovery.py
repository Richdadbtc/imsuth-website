import hashlib
import secrets
from datetime import timedelta
from urllib.parse import urlsplit

from django.conf import settings
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.debug import sensitive_post_parameters, sensitive_variables
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.models import RecoveryChallenge, RecoveryRateLimit, User

GENERIC = 'If an eligible account matches, recovery instructions will be sent to its registered email.'
INVALID = 'The recovery token is invalid or expired. Request a new recovery email.'


def digest(value):
    return hashlib.sha256(value.encode()).hexdigest()


@transaction.atomic
def limited(scope, value, limit):
    now = timezone.now()
    key = digest(scope + ':' + value)
    RecoveryRateLimit.objects.get_or_create(key=key, defaults={'started_at': now})
    entry = RecoveryRateLimit.objects.select_for_update().get(key=key)
    if now - entry.started_at >= timedelta(minutes=15):
        entry.started_at, entry.attempts = now, 0
    entry.attempts += 1
    entry.save(update_fields=['started_at', 'attempts'])
    return entry.attempts > limit


@method_decorator(csrf_protect, name='dispatch')
@method_decorator(sensitive_post_parameters(), name='dispatch')
class RecoveryRequestView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    @sensitive_variables()
    def post(self, request):
        identity = str(request.data.get('identity', '')).strip()[:254]
        ip = request.META.get('REMOTE_ADDR', '')
        ip_limited = limited('request-ip', ip, 10)
        identity_limited = limited('request-identity', identity.casefold(), 3)
        if not identity or ip_limited or identity_limited:
            return Response({'detail': GENERIC})
        # Never send reset secrets to console/file email backends or untrusted hosts.
        url = getattr(settings, 'PASSWORD_RECOVERY_URL', '')
        parsed = urlsplit(url)
        backend = settings.EMAIL_BACKEND
        if parsed.scheme != 'https' or not parsed.netloc or parsed.fragment or parsed.query or backend not in {
            'django.core.mail.backends.smtp.EmailBackend', 'django.core.mail.backends.locmem.EmailBackend'
        }:
            return Response({'detail': GENERIC})
        users = User.objects.filter(Q(username__iexact=identity) | Q(email__iexact=identity) | Q(employee_id__iexact=identity), is_active=True).exclude(email='')[:2]
        if len(users) != 1 or not users[0].has_usable_password():
            return Response({'detail': GENERIC})
        user = users[0]
        token = secrets.token_urlsafe(32)
        challenge = RecoveryChallenge.objects.create(user=user, digest=digest(token), expires_at=timezone.now() + timedelta(minutes=10))
        try:
            send_mail('IMSUTH PayPoint account recovery', f'Use this link within 10 minutes to reset your password:\n{url}#recover={token}\n\nThis link can be used once. If you did not request it, ignore this email.', settings.DEFAULT_FROM_EMAIL, [user.email], fail_silently=False)
        except Exception:
            challenge.delete()
        return Response({'detail': GENERIC})


@method_decorator(csrf_protect, name='dispatch')
@method_decorator(sensitive_post_parameters(), name='dispatch')
class RecoveryVerifyView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    @sensitive_variables()
    def post(self, request):
        if limited('verify-ip', request.META.get('REMOTE_ADDR', ''), 20):
            return Response({'detail': 'Too many attempts. Try again later.'}, status=429)
        token = str(request.data.get('token', ''))[:256]
        if not RecoveryChallenge.objects.filter(digest=digest(token), consumed=False, expires_at__gt=timezone.now(), user__is_active=True).exists():
            return Response({'detail': INVALID}, status=400)
        return Response({'detail': 'Identity verified. Set a new password.'})


class RecoveryCompleteView(RecoveryVerifyView):
    @sensitive_variables()
    def post(self, request):
        if limited('complete-ip', request.META.get('REMOTE_ADDR', ''), 20):
            return Response({'detail': 'Too many attempts. Try again later.'}, status=429)
        token, password = str(request.data.get('token', ''))[:256], str(request.data.get('password', ''))
        if len(password) > 4096:
            return Response({'detail': 'Password is too long.'}, status=400)
        with transaction.atomic():
            # User lock serializes consumption of all outstanding challenges for this user.
            challenge = RecoveryChallenge.objects.filter(digest=digest(token)).first()
            if not challenge:
                return Response({'detail': INVALID}, status=400)
            user = User.objects.select_for_update().get(pk=challenge.user_id)
            challenge.refresh_from_db()
            if challenge.consumed or challenge.expires_at <= timezone.now() or not user.is_active:
                return Response({'detail': INVALID}, status=400)
            try:
                validate_password(password, user)
            except ValidationError as error:
                return Response({'detail': ' '.join(error.messages)}, status=400)
            user.set_password(password)
            user.must_change_password = False
            user.save(update_fields=['password', 'must_change_password'])
            RecoveryChallenge.objects.filter(user=user, consumed=False).update(consumed=True)
        # Django invalidates existing authenticated sessions through the changed password hash.
        return Response({'detail': 'Password reset successful. Sign in again on all devices.'})

from drf_spectacular.utils import extend_schema_view, extend_schema, OpenApiTypes
for _view in (RecoveryRequestView, RecoveryVerifyView, RecoveryCompleteView):
    extend_schema_view(post=extend_schema(request=OpenApiTypes.OBJECT,responses=OpenApiTypes.OBJECT))(_view)
