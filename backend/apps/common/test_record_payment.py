from decimal import Decimal
from uuid import uuid4
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient
from apps.billing.models import Invoice
from apps.payments.models import Payment, Receipt
from .models import RecordedPayment, CashOrder, Alert
from .test_revenue_api import RevenueControlTests


class RecordPaymentTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        RevenueControlTests.setUpTestData.__func__(cls)

    def setUp(self):
        self.client=APIClient();self.client.force_authenticate(self.cashier)
        self.data={'patient':str(self.patient.pk),'department':str(self.dep.pk),'service':str(self.service.pk),'cash_point':str(self.point.pk),'quantity':1,'amount':'100.00','channel':'cash','cash_receiver':'Nwaele Juliet','submitted_reference':'','reported_paid_at':timezone.now().isoformat(),'idempotency_key':str(uuid4())}

    def post(self):return self.client.post('/api/v1/record-payment/',self.data,format='json')

    def test_atomic_capture_retry_and_no_receipt_before_verification(self):
        result=self.post();self.assertEqual(result.status_code,201,result.data)
        self.assertFalse(result.data['receipt_issued']);self.assertEqual(result.data['payment']['status'],'awaiting_offline_verification')
        self.assertEqual(self.post().data['payment']['id'],result.data['payment']['id'])
        self.assertEqual(RecordedPayment.objects.count(),1);self.assertEqual(Receipt.objects.count(),1)
        self.data['amount']='90.00';self.data['override_reason']='Synthetic override'
        self.assertEqual(self.post().status_code,400)

    def test_price_change_requires_reason_and_creates_audited_flag(self):
        before=Invoice.objects.count();self.data['amount']='90.00'
        self.assertEqual(self.post().status_code,400);self.assertEqual(Invoice.objects.count(),before)
        self.data['override_reason']='Synthetic approved concession'
        result=self.post();self.assertEqual(result.status_code,201,result.data)
        context=RecordedPayment.objects.get();self.assertEqual(context.approved_total,Decimal('100'))
        self.assertEqual(context.payment.invoice.total_amount,Decimal('90'));self.assertEqual(context.payment.amount,Decimal('90'))
        self.assertTrue(Alert.objects.filter(alert_type='service_price_change',related_id=str(context.payment_id)).exists())

    def test_cash_order_must_match_point_be_approved_and_have_capacity(self):
        order=CashOrder.objects.create(cash_point=self.point,requested_by=self.cashier,amount='50',purpose='Synthetic',idempotency_key='synthetic-capture-order',status='approved')
        self.data['cash_order']=str(order.pk);self.assertEqual(self.post().status_code,400)
        self.assertFalse(RecordedPayment.objects.exists())
        order.amount='150';order.save()
        self.assertEqual(self.post().status_code,201)
        self.data['idempotency_key']=str(uuid4());self.data['submitted_reference']='SYN-CAPTURE-002'
        self.assertEqual(self.post().status_code,400)
        self.data['cash_receiver']='';self.data['channel']='pos';self.assertEqual(self.post().status_code,400)

    def test_permissions_scope_and_cash_daily_limit(self):
        self.client.force_authenticate(self.supervisor);self.assertEqual(self.post().status_code,403)
        self.client.force_authenticate(self.cashier)
        self.data['department']=str(self.other.pk);self.assertEqual(self.post().status_code,400)
        self.data['department']=str(self.dep.pk);self.point.daily_limit='50';self.point.save()
        self.assertEqual(self.post().status_code,400);self.assertFalse(RecordedPayment.objects.exists())

    def test_latest_receipts_show_service_status_and_print_identifier(self):
        result=self.client.get('/api/v1/record-payment/');self.assertEqual(result.status_code,200)
        row=result.data['receipts'][0];self.assertEqual(row['receipt_number'],'SYN-RECEIPT');self.assertEqual(row['service_status'],'Not yet used')
        self.assertEqual(row['id'],str(self.receipt.pk))
        self.client.force_authenticate(None);self.assertIn(self.client.get('/api/v1/record-payment/').status_code,[401,403])

    def test_department_desk_selection_reuse_and_persisted_delivery(self):
        self.client.force_authenticate(self.finance)
        wrong='?department='+str(self.other.pk)
        path='/api/v1/department-desk/receipts/'+self.receipt.receipt_number
        self.assertEqual(self.client.get('/api/v1/department-desk/receipts/'+wrong).data['count'],0)
        self.assertEqual(self.client.post(path+'/verify/'+wrong,{},format='json').status_code,404)
        self.client.force_authenticate(self.supervisor)
        query='?department='+str(self.dep.pk)
        checked=self.client.post(path+'/verify/'+query,{},format='json')
        self.assertEqual(checked.status_code,200);self.assertTrue(checked.data['can_deliver'])
        delivery='/api/v1/department-desk/service-items/'+str(self.invoice.items.get().pk)+'/deliver/'+query
        self.assertEqual(self.client.post(delivery,{'receipt':str(self.receipt.pk),'notes':'Synthetic delivery'},format='json').status_code,201)
        self.assertEqual(self.client.post(delivery,{'receipt':str(self.receipt.pk),'notes':'Duplicate delivery'},format='json').status_code,400)
        row=self.client.get('/api/v1/department-desk/receipts/'+query).data['results'][0]
        self.assertEqual(row['service_status'],'Service delivered');self.assertTrue(row['items'][0]['delivered'])

    def test_department_desk_blocks_disputed_invoices_before_delivery(self):
        Payment.objects.create(invoice=self.invoice,reference='SYN-DISPUTED',idempotency_key='SYN-DISPUTED',channel='cash',amount='10',status='refund_pending',initiated_by=self.cashier)
        self.client.force_authenticate(self.supervisor)
        path='/api/v1/department-desk/receipts/'+self.receipt.receipt_number+'/verify/'
        row=self.client.post(path,{},format='json').data
        self.assertFalse(row['eligible_for_delivery']);self.assertFalse(row['can_deliver'])

    def test_overview_cash_under_orders_excludes_unverified_and_unlinked_cash(self):
        order=CashOrder.objects.create(cash_point=self.point,requested_by=self.cashier,amount='150',purpose='Synthetic',idempotency_key='synthetic-overview-capture-order',status='approved')
        self.data['cash_order']=str(order.pk)
        result=self.post();self.assertEqual(result.status_code,201,result.data)
        response=self.client.get('/api/v1/dashboard/overview-coverage/').data
        self.assertEqual(response['cash_under_orders']['amount'],0)
        payment=Payment.objects.get(pk=result.data['payment']['id']);payment.status='confirmed';payment.confirmed_at=timezone.now();payment.save()
        response=self.client.get('/api/v1/dashboard/overview-coverage/').data
        self.assertEqual(response['cash_under_orders']['amount'],Decimal('100'))
        self.assertFalse(response['insurance']['configured']);self.assertIsNone(response['insurance']['nhis'])

    def test_shared_unlimited_points_are_available_without_expanding_patient_scope(self):
        from apps.common.models import CashPoint
        names={'Main cash-point 1','Main cash-point 2','A&E Cash-point'}
        points=CashPoint.objects.filter(name__in=names)
        self.assertEqual(points.count(),3)
        self.assertTrue(all(p.department_id is None and p.daily_limit is None for p in points))
        shared=points.first();self.data['cash_point']=str(shared.pk)
        listing=self.client.get('/api/v1/record-payment/');self.assertEqual(listing.status_code,200)
        self.assertTrue(names.issubset({p['name'] for p in listing.data['cash_points']}))
        result=self.post();self.assertEqual(result.status_code,201,result.data)
        context=RecordedPayment.objects.get();self.assertEqual(context.created_by_id,self.cashier.pk)
        self.data['idempotency_key']=str(uuid4());self.data['submitted_reference']='SYN-SHARED-OTHER';self.data['department']=str(self.other.pk)
        self.assertEqual(self.post().status_code,400)

    def test_shared_cash_orders_are_unlimited_but_private_to_requester(self):
        from apps.common.models import CashPoint
        shared=CashPoint.objects.get(name='Main cash-point 1')
        order=CashOrder.objects.create(cash_point=shared,requested_by=self.cashier,amount='5000000',purpose='Synthetic shared order',idempotency_key='synthetic-unlimited-order',status='approved')
        visible=self.client.get('/api/v1/record-payment/').data['cash_orders']
        self.assertIn(str(order.pk),[o['id'] for o in visible])
        self.client.force_authenticate(self.supervisor)
        self.assertNotIn(str(order.pk),[o['id'] for o in self.client.get('/api/v1/record-payment/').data['cash_orders']])
        self.client.force_authenticate(self.finance)
        response=self.client.post('/api/v1/cash-points/',{'name':'Synthetic unlimited point','location':'Test location','department':None,'assigned_officer':None,'daily_limit':None},format='json')
        self.assertEqual(response.status_code,201,response.data);self.assertIsNone(response.data['daily_limit'])

    def test_manual_service_and_patient_discounts_are_server_calculated(self):
        from apps.catalogue.models import Service, TariffVersion
        service_count=Service.objects.count();tariff_count=TariffVersion.objects.count()
        for category,net in [('regular','3000.00'),('nhis','2700.00'),('imshia','2700.00')]:
            with self.subTest(category=category):
                self.data.pop('service',None)
                self.data.update(service_description='Entered consultation',patient_type=category,base_amount='3000.00',amount=net,cash_receiver='',channel='pos',idempotency_key=str(uuid4()),submitted_reference='09FG2611111259590001'+{'regular':'ABCDE','nhis':'ABCDF','imshia':'ABCDG'}[category])
                response=self.post();self.assertEqual(response.status_code,201,response.data)
                context=RecordedPayment.objects.get(payment_id=response.data['payment']['id']);item=context.payment.invoice.items.get()
                self.assertEqual(str(context.payment.amount),net);self.assertEqual(context.patient_type,category)
                self.assertTrue(item.is_manual);self.assertIsNone(item.service_id);self.assertIsNone(item.tariff_version_id)
                self.assertEqual(item.description,'Entered consultation');self.assertEqual(context.base_total,Decimal('3000'))
                self.assertEqual(context.discount_total,Decimal('3000')-Decimal(net))
                self.assertFalse(response.data['receipt_issued'])
                self.assertEqual(self.post().status_code,200)
        self.assertEqual(Service.objects.count(),service_count);self.assertEqual(TariffVersion.objects.count(),tariff_count)

    def test_manual_discount_tampering_and_invalid_types_roll_back(self):
        before=Invoice.objects.count();self.data.pop('service')
        self.data.update(service_description='Entered service',base_amount='100',amount='50',patient_type='nhis',cash_receiver='',channel='pos')
        self.assertEqual(self.post().status_code,400)
        self.data.update(amount='90',patient_type='unapproved')
        self.assertEqual(self.post().status_code,400)
        self.data.update(patient_type='regular',service_description='')
        self.assertEqual(self.post().status_code,400)
        self.assertEqual(Invoice.objects.count(),before)

    def test_catalogue_service_uses_tariff_for_discount_not_submitted_base(self):
        self.data.update(patient_type='nhis',base_amount='50000',amount='90',cash_receiver='',channel='pos',submitted_reference='09FG2611111259590001ABCDE')
        response=self.post();self.assertEqual(response.status_code,201,response.data)
        context=RecordedPayment.objects.get();self.assertEqual(context.base_total,Decimal('100'))
        self.assertEqual(context.discount_total,Decimal('10'));self.assertEqual(context.approved_total,Decimal('90'))
        self.assertFalse(Alert.objects.filter(alert_type='service_price_change').exists())

    def test_slip_format_is_required_before_any_invoice_or_receipt(self):
        before=Invoice.objects.count()
        for channel in ['pos','bank_transfer']:
            self.data.update(cash_receiver='',channel=channel,submitted_reference='123456',idempotency_key=str(uuid4()))
            response=self.post();self.assertEqual(response.status_code,400,response.data)
            self.assertEqual(Invoice.objects.count(),before)
        self.data.update(cash_receiver='',channel='pos',submitted_reference='09fg2611042341124813 cy0w7')
        result=self.post();self.assertEqual(result.status_code,201,result.data)
        self.assertEqual(RecordedPayment.objects.get().payment.submitted_reference,'09FG2611042341124813CY0W7')
        self.assertFalse(result.data['receipt_issued'])

    def test_cash_receiver_required_validated_and_reusable(self):
        choices=self.client.get('/api/v1/record-payment/').data['cash_receivers']
        self.assertEqual(list(choices),['Nwaele Juliet','Udegbe Egonna','Onuoha Lilian','Ibewuike Blessing'])
        for value in ['', 'Unlisted Person']:
            self.data['cash_receiver']=value
            response=self.post();self.assertEqual(response.status_code,400,response.data)
        for receiver in choices:
            self.data.update(cash_receiver=receiver,idempotency_key=str(uuid4()))
            response=self.post();self.assertEqual(response.status_code,201,response.data)
            self.assertEqual(response.data['payment']['cash_receiver'],receiver)
            payment=Payment.objects.get(pk=response.data['payment']['id'])
            self.assertEqual(payment.cash_receiver,receiver)
            self.assertEqual(payment.submitted_reference,'')
            self.assertEqual(payment.initiated_by_id,self.cashier.pk)
        self.data.update(idempotency_key=str(uuid4()))
        self.assertEqual(self.post().status_code,201)
