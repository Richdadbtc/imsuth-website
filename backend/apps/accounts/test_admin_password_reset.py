from django.test import TestCase
from django.contrib.sessions.models import Session
from rest_framework.test import APIClient
from apps.common.test_revenue_api import RevenueControlTests
from apps.auditlog.models import AuditEvent

class AdminPasswordResetTests(TestCase):
    @classmethod
    def setUpTestData(cls):RevenueControlTests.setUpTestData.__func__(cls)
    def setUp(self):
        self.client=APIClient();self.client.force_login(self.admin)
        self.old='Previous-Synthetic-Pass-93!';self.new='Updated-Synthetic-Pass-76!'
        self.cashier.set_password(self.old);self.cashier.save()
        self.staff=APIClient();self.staff.force_login(self.cashier)
        self.url=f'/api/v1/users/{self.cashier.pk}/reset-password/'
    def test_reset_changes_password_revokes_sessions_and_audits_without_secret(self):
        session=self.staff.session.session_key
        response=self.client.post(self.url,{'new_password':self.new,'confirm_password':self.new},format='json')
        self.assertEqual(response.status_code,200,response.data)
        self.cashier.refresh_from_db();self.assertTrue(self.cashier.check_password(self.new));self.assertFalse(self.cashier.check_password(self.old))
        self.assertTrue(self.cashier.must_change_password)
        self.assertFalse(Session.objects.filter(session_key=session).exists())
        self.assertFalse(self.staff.get('/api/v1/session/').data['authenticated'])
        self.assertTrue(self.staff.login(username=self.cashier.username,password=self.new))
        event=AuditEvent.objects.get(action='user.password_reset',object_id=str(self.cashier.pk))
        self.assertEqual(event.actor_id,self.admin.pk)
        self.assertNotIn(self.new,str(response.data));self.assertNotIn(self.new,str(event.metadata))
    def test_invalid_or_mismatched_password_does_not_change_account(self):
        for data in [{'new_password':'short','confirm_password':'short'},{'new_password':self.new,'confirm_password':'different'},{'new_password':self.new},{}]:
            response=self.client.post(self.url,data,format='json');self.assertEqual(response.status_code,400,response.data)
            self.cashier.refresh_from_db();self.assertTrue(self.cashier.check_password(self.old))
        self.assertFalse(AuditEvent.objects.filter(action='user.password_reset').exists())
    def test_only_admin_can_reset_and_self_deleted_targets_are_rejected(self):
        payload={'new_password':self.new,'confirm_password':self.new}
        self.assertEqual(self.staff.post(self.url,payload,format='json').status_code,403)
        self.assertEqual(self.client.post(f'/api/v1/users/{self.admin.pk}/reset-password/',payload,format='json').status_code,400)
        from django.utils import timezone
        self.cashier.deleted_at=timezone.now();self.cashier.save()
        self.assertEqual(self.client.post(self.url,payload,format='json').status_code,404)
    def test_existing_password_edit_also_revokes_sessions(self):
        session=self.staff.session.session_key
        response=self.client.patch(f'/api/v1/users/{self.cashier.pk}/',{'password':self.new},format='json')
        self.assertEqual(response.status_code,200,response.data)
        self.assertFalse(Session.objects.filter(session_key=session).exists())
