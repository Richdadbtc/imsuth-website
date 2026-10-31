"""Fail-closed deployment checks; development remains usable without secrets."""
from urllib.parse import urlsplit
from django.conf import settings
from django.core.checks import Error, Tags, register


@register(Tags.security, deploy=True)
def deployment_configuration(app_configs, **kwargs):
    if settings.ENVIRONMENT not in {'staging', 'production'}:
        return []
    errors = []
    def require(condition, code, message):
        if not condition:
            errors.append(Error(message, id=f'paypoint.E{code}'))
    require(not settings.DEBUG, '001', 'DEBUG must be disabled for staging/production.')
    secret = settings.SECRET_KEY
    require(len(secret) >= 50 and not any(marker in secret.lower() for marker in ('unsafe-', 'replace-', 'change-me')), '002', 'Use a strong, unique Django secret from the approved secret store.')
    require(settings.DATABASES['default']['ENGINE'] == 'django.db.backends.postgresql', '003', 'Staging/production requires PostgreSQL; SQLite is for development only.')
    require(bool(settings.ALLOWED_HOSTS) and '*' not in settings.ALLOWED_HOSTS and not set(settings.ALLOWED_HOSTS) & {'localhost', '127.0.0.1', 'testserver'}, '004', 'Configure explicit deployment hostnames without development or wildcard hosts.')
    origins = settings.CSRF_TRUSTED_ORIGINS
    require(bool(origins) and all(urlsplit(origin).scheme == 'https' and urlsplit(origin).netloc and '*' not in origin for origin in origins), '005', 'Configure explicit HTTPS CSRF trusted origins.')
    require(settings.SESSION_COOKIE_SECURE and settings.CSRF_COOKIE_SECURE and settings.SECURE_SSL_REDIRECT, '006', 'Secure cookies and HTTPS redirection are required.')
    require(not settings.CELERY_TASK_ALWAYS_EAGER, '007', 'Use a real Celery worker in staging/production.')
    if settings.ENVIRONMENT == 'production':
        require(not settings.PAYMENT_TEST_MODE, '008', 'Payment test mode must be disabled in production.')
    recovery = settings.PASSWORD_RECOVERY_URL
    if recovery:
        parsed = urlsplit(recovery)
        require(parsed.scheme == 'https' and parsed.hostname in settings.ALLOWED_HOSTS and not parsed.query and not parsed.fragment and not parsed.username, '009', 'Recovery URL must use an approved HTTPS application hostname without credentials, query or fragment.')
        require(settings.EMAIL_BACKEND == 'django.core.mail.backends.smtp.EmailBackend' and bool(settings.EMAIL_HOST), '010', 'Enabled recovery requires a configured production SMTP delivery backend.')
    return errors
