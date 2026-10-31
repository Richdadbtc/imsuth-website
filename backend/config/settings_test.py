from .settings import *  # noqa: F401,F403

PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]
STORAGES = {"staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"}}
CELERY_TASK_ALWAYS_EAGER = True
PAYMENT_TEST_MODE = True
TEST_WEBHOOK_SECRET = "test-suite-only-secret"
FORCE_SCRIPT_NAME = None
