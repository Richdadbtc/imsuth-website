from decimal import Decimal
from datetime import timedelta
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient
from apps.accounts.models import User
from apps.payments.models import Payment
from .models import RecordedPayment
from . import test_revenue_api

class OverviewSubheadTests(TestCase):
    @classmethod
    def setUpTestData(cls):test_revenue_api.RevenueControlTests.setUpTestData.__func__(cls)
    def setUp(self):
        self.client=APIClient();self.client.force_authenticate(self.admin)
        self.today=timezone.localdate()
        for head,amount in [('overhead','10.50'),('rf','20.25'),('drf','30.75'),('deposit','40')]:
            payment=Payment.objects.create(invoice=self.invoice,reference='SYN-head-'+head,idempotency_key='head-'+head,initiated_by=self.cashier,channel='cash',status='confirmed',confirmed_at=timezone.now(),amount=amount)
            RecordedPayment.objects.create(payment=payment,cash_point=self.point,created_by=self.cashier,idempotency_key='context-'+head,fingerprint='synthetic',sub_head=head,approved_total=amount,entered_total=amount)
        Payment.objects.create(invoice=self.invoice,reference='SYN-head-pending',idempotency_key='head-pending',initiated_by=self.cashier,channel='cash',status='pending',amount='999')
    def test_admin_and_auditor_totals_use_paid_amounts_and_reconcile_to_summary(self):
        auditor=User.objects.create_user(username='SyntheticHeadAuditor',role='auditor')
        for actor in [self.admin,auditor]:
            self.client.force_authenticate(actor)
            response=self.client.get('/api/v1/dashboard/summary/?period=today');self.assertEqual(response.status_code,200,response.data)
            data=response.data;rows={row['value']:row for row in data['sub_head_totals']}
            self.assertEqual([rows[key]['amount'] for key in ['overhead','rf','drf','deposit']],[Decimal('10.50'),Decimal('20.25'),Decimal('30.75'),Decimal('40')])
            self.assertEqual(sum(row['amount'] for row in rows.values())+data['unclassified']['amount'],data['verified_collections'])
            self.assertEqual(data['unclassified']['amount'],Decimal('100'))
    def test_calendar_filters_and_department_scope_apply_to_subheads(self):
        old=timezone.now()-timedelta(days=2)
        Payment.objects.filter(recorded_context__sub_head='drf').update(confirmed_at=old)
        path=f'/api/v1/dashboard/summary/?period=custom&date_from={self.today}&date_to={self.today}'
        rows={row['value']:row for row in self.client.get(path).data['sub_head_totals']}
        self.assertEqual(rows['drf']['amount'],0);self.assertEqual(rows['drf']['transactions'],0)
        self.client.force_authenticate(self.supervisor)
        RecordedPayment.objects.filter(sub_head='deposit').update(sub_head='')
        self.assertEqual(len(self.client.get(path).data['sub_head_totals']),4)
        self.supervisor.department=self.other;self.supervisor.save()
        self.assertTrue(all(row['amount']==0 for row in self.client.get(path).data['sub_head_totals']))
