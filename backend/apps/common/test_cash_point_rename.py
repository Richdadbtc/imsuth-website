import importlib
from types import SimpleNamespace
from django.test import TestCase
from django.apps import apps
from django.db import connection
from django.contrib.auth import get_user_model
from .models import CashPoint,CashOrder
from apps.auditlog.models import AuditEvent

class CashPointRenameTests(TestCase):
    def test_rename_preserves_identity_settings_and_cash_orders(self):
        point=CashPoint.objects.get(name='OPD CASH POINT')
        CashPoint.objects.filter(pk=point.pk).update(name='Main cash-point 1')
        officer=get_user_model().objects.create_user(username='rename-test',role='cashier')
        order=CashOrder.objects.create(cash_point=point,requested_by=officer,amount='100',purpose='Rename test',idempotency_key='rename-test')
        migration=importlib.import_module('apps.common.migrations.0011_rename_shared_cash_points')
        migration.rename_points(apps,SimpleNamespace(connection=connection))
        point.refresh_from_db();order.refresh_from_db()
        self.assertEqual(point.name,'OPD CASH POINT')
        self.assertEqual(order.cash_point_id,point.pk)
        self.assertIsNone(point.daily_limit);self.assertIsNone(point.department_id)
        self.assertTrue(AuditEvent.objects.filter(action='cash_point.renamed',object_id=str(point.pk)).exists())
        self.assertEqual(CashPoint.objects.filter(name='A&E Cash-point').count(),1)
    def test_collision_does_not_merge_or_rename_another_point(self):
        old=CashPoint.objects.create(name='Main cash-point 1',location='Test')
        migration=importlib.import_module('apps.common.migrations.0011_rename_shared_cash_points')
        with self.assertRaises(RuntimeError):
            migration.rename_points(apps,SimpleNamespace(connection=connection))
        old.refresh_from_db();self.assertEqual(old.name,'Main cash-point 1')
        self.assertTrue(CashPoint.objects.filter(name='OPD CASH POINT').exists())
