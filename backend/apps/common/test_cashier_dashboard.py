from decimal import Decimal
from django.test import TestCase
from django.utils import timezone
from datetime import timedelta
from rest_framework.test import APIClient
from apps.accounts.models import User
from apps.payments.models import Payment
from .test_revenue_api import RevenueControlTests


class CashierDashboardTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        RevenueControlTests.setUpTestData.__func__(cls)

    def setUp(self):
        self.client=APIClient();self.client.force_authenticate(self.cashier)

    def test_own_collections_are_visible_without_department_and_other_officers_are_excluded(self):
        self.cashier.department=None;self.cashier.save()
        self.invoice.department=self.other;self.invoice.save()
        Payment.objects.create(invoice=self.invoice,reference='DASH-PENDING',idempotency_key='DASH-PENDING',channel='bank_transfer',amount='25',status='awaiting_offline_verification',initiated_by=self.cashier)
        Payment.objects.create(invoice=self.invoice,reference='DASH-OTHER',idempotency_key='DASH-OTHER',channel='cash',amount='900',status='confirmed',confirmed_at=timezone.now(),initiated_by=self.finance)
        response=self.client.get('/api/v1/dashboard/cashier/?period=all')
        self.assertEqual(response.status_code,200,response.data)
        data=response.data
        self.assertEqual(data['scope'],'own_collections')
        self.assertEqual(data['confirmed_amount'],Decimal('100'))
        self.assertEqual(data['confirmed_transactions'],1)
        self.assertEqual(data['receipts_issued'],1)
        self.assertEqual(data['pending_amount'],Decimal('25'))
        self.assertEqual(data['pending_transactions'],1)
        self.assertEqual({row['reference'] for row in data['recent_transactions']},{'SYN-PAY','DASH-PENDING'})
        self.assertEqual(data['channels'],[{'channel':'cash','amount':Decimal('100'),'transactions':1}])
        self.cashier.department=self.dep;self.cashier.save()
        self.assertEqual(self.client.get('/api/v1/dashboard/cashier/?period=all').data['confirmed_amount'],Decimal('100'))

    def test_empty_cashier_and_role_access(self):
        new=User.objects.create_user(username='empty-cashier',role='cashier')
        self.client.force_authenticate(new)
        response=self.client.get('/api/v1/dashboard/cashier/')
        self.assertEqual(response.status_code,200)
        self.assertEqual(response.data['confirmed_amount'],0)
        self.assertEqual(response.data['recent_transactions'],[])
        self.client.force_authenticate(self.supervisor)
        self.assertEqual(self.client.get('/api/v1/dashboard/cashier/').status_code,403)
        self.client.force_authenticate(None)
        self.assertIn(self.client.get('/api/v1/dashboard/cashier/').status_code,[401,403])

    def test_period_uses_confirmation_date_for_collections(self):
        self.payment.confirmed_at=timezone.now()-timedelta(days=40);self.payment.save()
        self.assertEqual(self.client.get('/api/v1/dashboard/cashier/?period=30').data['confirmed_amount'],0)
        self.assertEqual(self.client.get('/api/v1/dashboard/cashier/?period=all').data['confirmed_amount'],Decimal('100'))
        self.assertEqual(self.client.get('/api/v1/dashboard/cashier/?period=invalid').status_code,400)
