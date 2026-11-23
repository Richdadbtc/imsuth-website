import importlib
from types import SimpleNamespace
from django.test import TestCase
from django.apps import apps
from django.db import connection
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from apps.auditlog.models import AuditEvent
from .models import CashPoint

class MainCashpointTests(TestCase):
    def test_five_shared_points_available_to_cashier_and_rerun_is_idempotent(self):
        names={'OPD CASH POINT','GOPD CASH POINT','A&E Cash-point','Main Cashpoint 1','Main Cashpoint 2'}
        points={point.name:point.pk for point in CashPoint.objects.all()}
        self.assertEqual(set(points),names)
        self.assertFalse(CashPoint.objects.exclude(department__isnull=True,daily_limit__isnull=True,is_active=True).exists())
        officer=get_user_model().objects.create_user(username='additional-point-cashier',role='cashier')
        client=APIClient();client.force_authenticate(officer)
        result=client.get('/api/v1/record-payment/')
        self.assertEqual(result.status_code,200,result.data)
        self.assertEqual({row['name'] for row in result.data['cash_points']},names)
        migration=importlib.import_module('apps.common.migrations.0015_add_main_cashpoints')
        count=AuditEvent.objects.count();migration.provision(apps,SimpleNamespace(connection=connection))
        self.assertEqual({point.name:point.pk for point in CashPoint.objects.all()},points)
        self.assertEqual(AuditEvent.objects.count(),count)
    def test_matching_existing_point_is_reused_and_reactivated(self):
        point=CashPoint.objects.get(name='Main Cashpoint 1')
        CashPoint.objects.filter(pk=point.pk).update(name='main cashpoint 1',is_active=False,daily_limit='100')
        migration=importlib.import_module('apps.common.migrations.0015_add_main_cashpoints')
        migration.provision(apps,SimpleNamespace(connection=connection))
        point.refresh_from_db()
        self.assertEqual(point.name,'Main Cashpoint 1');self.assertTrue(point.is_active);self.assertIsNone(point.daily_limit)
        self.assertEqual(CashPoint.objects.count(),5)
