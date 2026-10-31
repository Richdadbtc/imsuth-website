import threading
from unittest import skipUnless
from django.db import connection, close_old_connections, connections
from django.test import TransactionTestCase
from rest_framework.test import APIClient
from . import test_revenue_api as fixtures
from .models import ServiceDelivery


@skipUnless(connection.vendor=='postgresql','PostgreSQL row-lock test')
class DeliveryConcurrencyTests(TransactionTestCase):
    def setUp(self):
        fixtures.RevenueControlTests.setUpTestData.__func__(self.__class__)
    def test_duplicate_delivery_requests_serialize(self):
        barrier=threading.Barrier(2);statuses=[];errors=[]
        def deliver():
            close_old_connections()
            try:
                client=APIClient();client.force_authenticate(self.supervisor)
                barrier.wait(timeout=5)
                result=client.post(f'/api/v1/department-desk/service-items/{self.invoice.items.get().pk}/deliver/',{'receipt':str(self.receipt.pk)},format='json')
                statuses.append(result.status_code)
            except Exception as exc:errors.append(exc)
            finally:connections.close_all()
        workers=[threading.Thread(target=deliver) for _ in range(2)]
        for worker in workers:worker.start()
        for worker in workers:worker.join(timeout=15)
        self.assertEqual(errors,[])
        self.assertEqual(sorted(statuses),[201,400])
        self.assertEqual(ServiceDelivery.objects.count(),1)

    def test_cash_orders_serialize_daily_limit_reservations(self):
        from .models import CashOrder
        barrier=threading.Barrier(2);statuses=[];errors=[]
        def request_order(index):
            close_old_connections()
            try:
                client=APIClient();client.force_authenticate(self.finance)
                barrier.wait(timeout=5)
                result=client.post('/api/v1/cash-orders/',{'cash_point':str(self.point.pk),'amount':'600','purpose':'Synthetic concurrent request','idempotency_key':f'synthetic-limit-{index}'},format='json')
                statuses.append(result.status_code)
            except Exception as exc:errors.append(exc)
            finally:connections.close_all()
        workers=[threading.Thread(target=request_order,args=(i,)) for i in range(2)]
        for worker in workers:worker.start()
        for worker in workers:worker.join(timeout=15)
        self.assertEqual(errors,[])
        self.assertEqual(sorted(statuses),[201,400])
        self.assertEqual(CashOrder.objects.count(),1)
