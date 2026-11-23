from django.test import TestCase
from django.contrib.sessions.models import Session
from rest_framework.test import APIClient
from apps.common.test_revenue_api import RevenueControlTests
from apps.auditlog.models import AuditEvent
from .models import User
from .lifecycle import guard_change
from rest_framework.exceptions import ValidationError
from django.db import transaction

class AccountLifecycleTests(TestCase):
    @classmethod
    def setUpTestData(cls):RevenueControlTests.setUpTestData.__func__(cls)
    def setUp(self):
        self.client=APIClient();self.client.force_login(self.admin)
        self.staff=APIClient();self.cashier.set_password('Synthetic-Lifecycle-Test-29!');self.cashier.save();self.staff.force_login(self.cashier)
    def endpoint(self,action=''):return f'/api/v1/users/{self.cashier.pk}/'+(action+'/' if action else '')
    def test_ban_blocks_login_and_revokes_sessions_unban_does_not_revive_sessions(self):
        key=self.staff.session.session_key
        result=self.client.post(self.endpoint('ban'),{},format='json');self.assertEqual(result.status_code,200,result.data)
        self.cashier.refresh_from_db();self.assertFalse(self.cashier.is_active);self.assertIsNotNone(self.cashier.banned_at)
        self.assertFalse(Session.objects.filter(session_key=key).exists())
        self.assertFalse(self.staff.get('/api/v1/session/').data['authenticated'])
        self.assertFalse(self.staff.login(username=self.cashier.username,password='Synthetic-Lifecycle-Test-29!'))
        self.assertEqual(self.client.patch(self.endpoint(),{'is_active':True},format='json').status_code,400)
        self.assertEqual(self.client.post(self.endpoint('unban'),{},format='json').status_code,200)
        self.assertFalse(self.staff.get('/api/v1/session/').data['authenticated'])
        self.assertTrue(self.staff.login(username=self.cashier.username,password='Synthetic-Lifecycle-Test-29!'))
        self.assertTrue(AuditEvent.objects.filter(action='user.banned',object_id=str(self.cashier.pk)).exists())
    def test_delete_hides_account_preserves_payments_and_cannot_reactivate(self):
        result=self.client.delete(self.endpoint());self.assertEqual(result.status_code,204,result.data)
        self.cashier.refresh_from_db();self.assertIsNotNone(self.cashier.deleted_at);self.assertFalse(self.cashier.is_active)
        self.invoice.refresh_from_db();self.payment.refresh_from_db();self.receipt.refresh_from_db()
        self.assertEqual(self.invoice.created_by_id,self.cashier.pk);self.assertEqual(self.payment.initiated_by_id,self.cashier.pk)
        self.assertEqual(self.client.get(self.endpoint()).status_code,404)
        self.assertEqual(self.client.post(self.endpoint('unban'),{},format='json').status_code,404)
        self.assertFalse(self.staff.get('/api/v1/session/').data['authenticated'])
        self.assertTrue(AuditEvent.objects.filter(action='user.deleted',object_id=str(self.cashier.pk)).exists())
    def test_nonadmins_cannot_manage_accounts(self):
        for method,path in [('post',self.endpoint('ban')),('post',self.endpoint('unban')),('delete',self.endpoint()),('patch',self.endpoint())]:
            result=getattr(self.staff,method)(path,{'page_access':[]},format='json');self.assertEqual(result.status_code,403)
    def test_self_actions_and_last_active_admin_are_protected(self):
        for action in ['ban','']:
            path=f'/api/v1/users/{self.admin.pk}/'+(action+'/' if action else '')
            result=self.client.post(path,{},format='json') if action else self.client.delete(path)
            self.assertEqual(result.status_code,400)
        inactive_admin=User.objects.create_user(username='inactive-admin',role='super_admin',is_active=False)
        with transaction.atomic():
            with self.assertRaises(ValidationError):guard_change(inactive_admin,self.admin,active=False)
    def test_restriction_revokes_sessions_and_is_enforced_after_signin(self):
        key=self.staff.session.session_key
        result=self.client.patch(self.endpoint(),{'page_access':['dashboard-record-payment']},format='json')
        self.assertEqual(result.status_code,200,result.data);self.assertFalse(Session.objects.filter(session_key=key).exists())
        self.assertTrue(self.staff.login(username=self.cashier.username,password='Synthetic-Lifecycle-Test-29!'))
        self.assertEqual(self.staff.get('/api/v1/session/?page=dashboard-record-payment').status_code,200)
        self.assertEqual(self.staff.get('/api/v1/session/?page=reports').status_code,403)
        self.assertEqual(self.staff.get('/api/v1/audit-logs/').status_code,403)
