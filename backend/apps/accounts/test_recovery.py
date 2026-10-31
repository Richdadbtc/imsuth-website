from datetime import timedelta
from django.test import TestCase, override_settings, Client
from django.core import mail
from django.utils import timezone
from apps.accounts.models import User, RecoveryChallenge
from apps.common.recovery import digest


@override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend', PASSWORD_RECOVERY_URL='https://hospital.example/paypoint/')
class RecoveryTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='staff', email='staff@example.invalid', password='Old-Long-Pass-2030')
        self.base = '/api/v1/session/recovery/'

    def post(self, action, data):
        return self.client.post(self.base + action + '/', data, content_type='application/json')

    def token(self):
        self.post('request', {'identity': 'staff'})
        return mail.outbox[-1].body.split('#recover=')[1].split()[0]

    def test_generic_and_single_use(self):
        unknown = self.post('request', {'identity': 'unknown'}).json()
        token = self.token()
        self.assertEqual(unknown, self.post('request', {'identity': 'staff@example.invalid'}).json())
        self.assertTrue(RecoveryChallenge.objects.filter(digest=digest(token)).exists())
        self.assertEqual(self.post('verify', {'token': token}).status_code, 200)
        self.assertEqual(self.post('complete', {'token': token, 'password': 'Fresh-Strong-Pass-2041!'}).status_code, 200)
        self.assertEqual(self.post('complete', {'token': token, 'password': 'Another-Strong-Pass-2041!'}).status_code, 400)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('Fresh-Strong-Pass-2041!'))
        self.assertFalse(RecoveryChallenge.objects.filter(user=self.user, consumed=False).exists())

    def test_expired_and_weak(self):
        token = self.token()
        self.assertEqual(self.post('complete', {'token': token, 'password': '123'}).status_code, 400)
        RecoveryChallenge.objects.update(expires_at=timezone.now()-timedelta(seconds=1))
        self.assertEqual(self.post('verify', {'token': token}).status_code, 400)
        self.assertEqual(self.post('complete', {'token': token, 'password': 'Fresh-Strong-Pass-2041!'}).status_code, 400)

    def test_request_rate_limit(self):
        for _ in range(5):
            self.post('request', {'identity': 'staff'})
        self.assertEqual(len(mail.outbox), 3)
        for _ in range(21):
            response = self.post('verify', {'token': 'invalid'})
        self.assertEqual(response.status_code, 429)

    def test_sessions_invalidated(self):
        other = Client()
        other.force_login(self.user)
        token = self.token()
        self.post('complete', {'token': token, 'password': 'Fresh-Strong-Pass-2041!'})
        response = other.get('/api/v1/session/')
        self.assertFalse(response.json()['authenticated'])

    @override_settings(EMAIL_BACKEND='django.core.mail.backends.console.EmailBackend')
    def test_console_does_not_expose_tokens(self):
        self.post('request', {'identity': 'staff'})
        self.assertEqual(RecoveryChallenge.objects.count(), 0)

    def test_csrf(self):
        client = Client(enforce_csrf_checks=True)
        self.assertEqual(client.post(self.base+'request/', {'identity':'staff'}).status_code,403)
