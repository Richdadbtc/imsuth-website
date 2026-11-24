from decimal import Decimal
from datetime import timedelta
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
        self.data={'patient':str(self.patient.pk),'department':str(self.dep.pk),'sub_head':'rf','service':str(self.service.pk),'cash_point':str(self.point.pk),'quantity':1,'amount':'100.00','channel':'cash','cash_receiver':'Nwaele Juliet','submitted_reference':'','reported_paid_at':timezone.now().isoformat(),'idempotency_key':str(uuid4())}

    def post(self):return self.client.post('/api/v1/record-payment/',self.data,format='json')

    def test_sub_head_choices_are_required_validated_and_saved(self):
        from apps.auditlog.models import AuditEvent
        self.assertEqual(self.client.get('/api/v1/record-payment/').data['sub_heads'],[
            {'value':'overhead','label':'Over-head'},{'value':'rf','label':'R/F'},{'value':'drf','label':'DRF'}])
        self.data.pop('sub_head')
        self.assertEqual(self.post().status_code,400)
        self.data['sub_head']='other';self.assertEqual(self.post().status_code,400)
        self.assertFalse(RecordedPayment.objects.exists())
        self.point.daily_limit=None;self.point.save()
        for value,label in [('overhead','Over-head'),('rf','R/F'),('drf','DRF')]:
            self.data.update(sub_head=value,idempotency_key=str(uuid4()))
            self.data.update(overhead_items=[{'code':'card','quantity':1}] if value=='overhead' else [],drf_items=[{'code':'pharmacy_001','quantity':1,'unit_amount':'100'}] if value=='drf' else [],service=None if value in {'overhead','drf'} else str(self.service.pk),amount='1000' if value=='overhead' else '100')
            response=self.post();self.assertEqual(response.status_code,201,response.data)
            self.assertEqual(response.data['sub_head'],value)
            self.assertEqual(response.data['sub_head_label'],label)
            recorded=RecordedPayment.objects.get(payment_id=response.data['payment']['id'])
            self.assertEqual(recorded.sub_head,value)
            event=AuditEvent.objects.filter(action='payment.recorded_at_point',object_id=str(recorded.payment_id)).first()
            self.assertEqual(event.metadata['sub_head'],value)

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
        names={'OPD CASH POINT','GOPD CASH POINT','A&E Cash-point'}
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

    def test_cashier_without_department_collects_for_any_active_department_at_shared_point(self):
        from apps.common.models import CashPoint
        from apps.catalogue.models import Department
        from apps.accounts.models import User
        self.cashier.department=None;self.cashier.save()
        inactive=Department.objects.create(code='CLOSED',name='Inactive synthetic',is_active=False)
        choices=self.client.get('/api/v1/record-payment/').data['departments']
        self.assertIn(str(self.other.pk),{str(row['id']) for row in choices})
        self.assertNotIn(str(inactive.pk),{str(row['id']) for row in choices})
        self.data.update(cash_point=str(CashPoint.objects.get(name='OPD CASH POINT').pk),
            department=str(self.other.pk),patient=None,patient_name='Synthetic walk-in',
            service=None,service_description='Synthetic manual service',base_amount='100',payment_received=True)
        result=self.post();self.assertEqual(result.status_code,201,result.data)
        receipt=RecordedPayment.objects.get().payment.receipt
        self.assertEqual(self.client.get(f'/api/v1/receipts/{receipt.pk}/print/').status_code,200)
        self.assertIn(str(receipt.pk),{row['id'] for row in self.client.get('/api/v1/record-payment/').data['receipts']})
        other_cashier=User.objects.create_user(username='other-point-officer',role='cashier')
        self.client.force_authenticate(other_cashier)
        self.assertEqual(self.client.get(f'/api/v1/receipts/{receipt.pk}/print/').status_code,404)
        self.client.force_authenticate(self.cashier)
        self.data['department']=str(inactive.pk);self.data['idempotency_key']=str(uuid4())
        self.assertEqual(self.post().status_code,400)

    def test_shared_cash_orders_are_unlimited_but_private_to_requester(self):
        from apps.common.models import CashPoint
        shared=CashPoint.objects.get(name='OPD CASH POINT')
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
                self.data.update(service_description='Entered consultation',patient_type=category,base_amount='3000.00',amount=net,cash_receiver='',channel='pos',idempotency_key=str(uuid4()),submitted_reference={'regular':'631313012611','nhis':'631313012612','imshia':'631313012613'}[category])
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
        self.data.update(patient_type='nhis',base_amount='50000',amount='90',cash_receiver='',channel='pos',submitted_reference='631313012611')
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
        self.data.update(cash_receiver='',channel='bank_transfer',submitted_reference='09fg2611042341124813 cy0w7')
        result=self.post();self.assertEqual(result.status_code,201,result.data)
        self.assertEqual(RecordedPayment.objects.get().payment.submitted_reference,'09FG/CY0W7')
        self.assertFalse(result.data['receipt_issued'])

    def test_compact_transfer_reference_and_legacy_duplicate_protection(self):
        self.data.update(cash_receiver='',channel='bank_transfer',submitted_reference='09fgcy0w7')
        result=self.post();self.assertEqual(result.status_code,201,result.data)
        payment=RecordedPayment.objects.get().payment
        self.assertEqual(payment.submitted_reference,'09FG/CY0W7')
        self.data['idempotency_key']=str(uuid4())
        self.assertEqual(self.post().status_code,400)
        payment.submitted_reference='09FG2611042341124813CY0W7';payment.save()
        self.assertEqual(self.post().status_code,400)

    def test_payment_setup_includes_active_department_services_with_current_approved_prices(self):
        from apps.catalogue.models import Service, TariffVersion
        self.cashier.department=None;self.cashier.save()
        unpriced=Service.objects.create(code='UNPRICED',name='Unpriced service',department=self.other)
        inactive=Service.objects.create(code='INACTIVE',name='Inactive service',department=self.other,is_active=False)
        TariffVersion.objects.create(service=self.service,amount='200',is_approved=True,effective_from=timezone.now()+timedelta(days=1))
        rows=self.client.get('/api/v1/record-payment/').data['services']
        services={str(row['id']):row for row in rows}
        self.assertEqual(services[str(self.service.pk)]['amount'],Decimal('100'))
        self.assertEqual(str(services[str(self.service.pk)]['department_id']),str(self.dep.pk))
        self.assertIsNone(services[str(unpriced.pk)]['amount'])
        self.assertNotIn(str(inactive.pk),services)

    def test_cash_receiver_uses_signed_in_name_and_ignores_submitted_names(self):
        self.cashier.first_name='Sabina';self.cashier.last_name='Mbenaso';self.cashier.save()
        setup=self.client.get('/api/v1/record-payment/').data
        self.assertTrue(setup['cash_receiver_automatic'])
        self.assertEqual(setup['cash_receiver'],'Sabina Mbenaso')
        for submitted in [None,'','Another officer']:
            self.data['idempotency_key']=str(uuid4())
            if submitted is None:self.data.pop('cash_receiver',None)
            else:self.data['cash_receiver']=submitted
            response=self.post();self.assertEqual(response.status_code,201,response.data)
            payment=Payment.objects.get(pk=response.data['payment']['id'])
            self.assertEqual(payment.cash_receiver,'Sabina Mbenaso')
            self.assertEqual(payment.initiated_by_id,self.cashier.pk)
        self.cashier.first_name='Renamed';self.cashier.save()
        payment.refresh_from_db();self.assertEqual(payment.cash_receiver,'Sabina Mbenaso')

    def test_cash_receiver_falls_back_to_username_and_preserves_full_length(self):
        self.data.pop('cash_receiver',None)
        response=self.post();self.assertEqual(response.status_code,201,response.data)
        self.assertEqual(response.data['payment']['cash_receiver'],self.cashier.username)
        self.cashier.first_name='A'*150;self.cashier.last_name='B'*150;self.cashier.save()
        self.data['idempotency_key']=str(uuid4())
        response=self.post();self.assertEqual(response.status_code,201,response.data)
        self.assertEqual(response.data['payment']['cash_receiver'],self.cashier.get_full_name())

    def test_walk_in_capture_keeps_name_without_registering_patient(self):
        from apps.registry.models import Patient
        before=Patient.objects.count()
        self.data.pop('patient');self.data['patient_name']='Walk-in Example'
        result=self.post();self.assertEqual(result.status_code,201,result.data)
        context=RecordedPayment.objects.select_related('payment__invoice').get()
        invoice=context.payment.invoice
        self.assertIsNone(invoice.patient_id)
        self.assertEqual(invoice.patient_name,'Walk-in Example')
        self.assertEqual(result.data['payment']['patient_name'],'Walk-in Example')
        self.assertEqual(Patient.objects.count(),before)
        self.assertEqual(self.post().data['payment']['id'],result.data['payment']['id'])
        self.data['patient_name']='Different name'
        self.assertEqual(self.post().status_code,400)
        payment=context.payment;payment.status='confirmed';payment.save()
        receipt=Receipt.objects.create(receipt_number='WALK-IN-TEST',payment=payment,invoice=invoice,amount=payment.amount,currency='NGN')
        self.assertContains(self.client.get(f'/api/v1/receipts/{receipt.pk}/print/'),'Walk-in Example')
        latest=self.client.get('/api/v1/record-payment/').data['receipts']
        self.assertEqual(next(r for r in latest if r['id']==str(receipt.pk))['patient_name'],'Walk-in Example')
        self.client.force_authenticate(self.finance)
        listing=self.client.get('/api/v1/department-desk/receipts/?department='+str(self.dep.pk))
        self.assertEqual(listing.status_code,200,listing.data)
        self.assertIn('Walk-in Example',[r['patient_name'] for r in listing.data['results']])

    def test_walk_in_capture_requires_name_and_preserves_registered_patient_scope(self):
        self.data.pop('patient');self.data['patient_name']='   '
        before=Invoice.objects.count()
        self.assertEqual(self.post().status_code,400)
        self.assertEqual(Invoice.objects.count(),before)
        self.data.update(patient=str(uuid4()),patient_name='Cannot override invalid patient')
        self.assertEqual(self.post().status_code,400)

    def test_staff_received_confirmation_issues_one_paid_printable_receipt(self):
        from apps.auditlog.models import AuditEvent
        for channel,reference in [('cash',''),('pos','631313012611'),('bank_transfer','09FG2611042341124813CY0W7')]:
            with self.subTest(channel=channel):
                self.data.pop('patient',None)
                self.data.update(patient_name='Receipt Example',channel=channel,submitted_reference=reference,cash_receiver='Nwaele Juliet' if channel=='cash' else '',payment_received=True,idempotency_key=str(uuid4()))
                before=Receipt.objects.count()
                result=self.post();self.assertEqual(result.status_code,201,result.data)
                self.assertTrue(result.data['receipt_issued'])
                self.assertTrue(result.data['payment']['receipt_number'].startswith('IMSUTH-RCT-'))
                self.assertEqual(result.data['payment']['status'],'confirmed')
                self.assertEqual(Decimal(result.data['invoice']['amount_paid']),Decimal('100'))
                payment=Payment.objects.get(pk=result.data['payment']['id'])
                self.assertEqual(payment.invoice.status,'paid')
                self.assertEqual(payment.invoice.outstanding_balance,Decimal('0'))
                self.assertContains(self.client.get(f'/api/v1/receipts/{payment.receipt.pk}/print/'),'Receipt Example')
                self.assertEqual(self.post().status_code,200)
                self.assertEqual(Receipt.objects.count(),before+1)
                self.assertTrue(AuditEvent.objects.filter(action='payment.staff_received_confirmed',actor=self.cashier).exists())

    def test_online_cannot_use_staff_received_confirmation(self):
        self.data.update(channel='online',cash_receiver='',submitted_reference='online-example',payment_received=True)
        self.assertEqual(self.post().status_code,400)

    def test_overview_includes_cash_without_standing_order(self):
        self.data.update(payment_received=True)
        result=self.post();self.assertEqual(result.status_code,201,result.data)
        self.client.force_authenticate(self.finance)
        coverage=self.client.get('/api/v1/dashboard/overview-coverage/?period=all').data
        self.assertEqual(coverage['cash_received']['amount'],Decimal('200'))
        self.assertEqual(coverage['cash_received']['transactions'],2)
        self.assertEqual(coverage['cash_under_orders']['amount'],0)
        channels=self.client.get('/api/v1/dashboard/collections-by-channel/?period=all').data
        self.assertEqual(next(r for r in channels if r['channel']=='cash')['amount'],Decimal('200'))
        self.assertTrue(any(r['channel']=='cash' for r in coverage['daily_channels']))
        payment=Payment.objects.get(pk=result.data['payment']['id']);payment.status='reversed';payment.save()
        self.assertEqual(self.client.get('/api/v1/dashboard/overview-coverage/?period=all').data['cash_received']['amount'],Decimal('100'))
