from datetime import datetime
from decimal import Decimal
from zoneinfo import ZoneInfo
from django.test import TestCase
from rest_framework.test import APIClient
from apps.accounts.models import User
from apps.payments.models import Payment
from . import test_revenue_api

class StaffCollectionsTests(TestCase):
    @classmethod
    def setUpTestData(cls):test_revenue_api.RevenueControlTests.setUpTestData.__func__(cls)
    def setUp(self):
        self.client=APIClient();self.client.force_authenticate(self.admin)
        self.auditor=User.objects.create_user(username='SyntheticAuditor',role='auditor')
        self.second=User.objects.create_user(username='SyntheticCollector2',first_name='Second',last_name='Collector',role='cashier',department=self.other)
        self.zero=User.objects.create_user(username='SyntheticZero',role='cashier')
        self.start=datetime(2026,11,25,0,0,tzinfo=ZoneInfo('Africa/Lagos'));self.end=datetime(2026,11,26,23,59,59,tzinfo=ZoneInfo('Africa/Lagos'))
        Payment.objects.filter(pk=self.payment.pk).update(confirmed_at=self.start,amount='100.50')
        for ref,who,channel,amount,status,when in [('two',self.second,'pos','250.25','confirmed',self.end),('three',self.second,'bank_transfer','40','confirmed',self.start),('old',self.cashier,'cash','999','confirmed',datetime(2026,11,24,23,59,59,tzinfo=ZoneInfo('Africa/Lagos'))),('next',self.second,'cash','999','confirmed',datetime(2026,11,27,0,0,tzinfo=ZoneInfo('Africa/Lagos'))),('pending',self.second,'cash','999','pending',self.start),('refunded',self.second,'cash','999','refunded',self.start)]:
            Payment.objects.create(invoice=self.invoice,reference='SYN-'+ref,idempotency_key='staff-'+ref,initiated_by=who,channel=channel,amount=amount,status=status,confirmed_at=when)
        self.path='/api/v1/dashboard/collections-by-staff/?period=custom&date_from=2026-11-25&date_to=2026-11-26'
    def test_admin_and_auditor_see_all_collectors_exact_totals_and_inclusive_dates(self):
        for actor in [self.admin,self.auditor]:
            self.client.force_authenticate(actor);response=self.client.get(self.path)
            self.assertEqual(response.status_code,200,response.data);data=response.data
            self.assertEqual(data['amount'],Decimal('390.75'));self.assertEqual(data['transactions'],3)
            rows={r['id']:r for r in data['staff']}
            self.assertEqual(rows[self.cashier.pk]['channels']['cash'],Decimal('100.50'))
            self.assertEqual(rows[self.second.pk]['name'],'Second Collector')
            self.assertEqual(rows[self.second.pk]['amount'],Decimal('290.25'))
            self.assertEqual(rows[self.zero.pk]['amount'],0)
    def test_unauthorized_roles_and_bad_ranges_are_rejected(self):
        for actor in [self.cashier,self.finance,self.supervisor]:
            self.client.force_authenticate(actor);self.assertEqual(self.client.get(self.path).status_code,403)
        self.client.force_authenticate(None);self.assertIn(self.client.get(self.path).status_code,[401,403])
        self.client.force_authenticate(self.admin)
        self.assertEqual(self.client.get(self.path.replace('date_from=2026-11-25','date_from=2026-11-28')).status_code,400)
        self.assertEqual(self.client.get(self.path.replace('2026-11-25','invalid')).status_code,400)
