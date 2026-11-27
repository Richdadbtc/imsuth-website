from decimal import Decimal
from uuid import uuid4
from . import test_drf
from django.test import TestCase
from .rf import CATALOGUE

class RFPaymentTests(TestCase):
    @classmethod
    def setUpTestData(cls):test_drf.DRFPaymentTests.setUpTestData.__func__(cls)
    def post(self):return self.client.post('/api/v1/record-payment/',self.data,format='json')
    def setUp(self):
        test_drf.DRFPaymentTests.setUp(self)
        self.data.pop('drf_items')
        self.data.update(sub_head='rf',rf_department='ophthalmology',rf_items=[{'code':'rf_02_001','quantity':2},{'code':'rf_02_002','quantity':1}],amount='23000')
    def test_complete_source_catalogue(self):
        catalogue=self.client.get('/api/v1/record-payment/').data['rf_catalogue']
        self.assertEqual(len(catalogue['departments']),9)
        self.assertEqual(len(catalogue['items']),271)
        self.assertEqual(sum(i['available'] for i in catalogue['items']),252)
    def test_multiple_items_discounts_receipt_and_idempotency(self):
        self.data.update(patient_type='nhis',amount='20700')
        response=self.post();self.assertEqual(response.status_code,201,response.data)
        from .models import RecordedPayment
        context=RecordedPayment.objects.get()
        self.assertEqual(context.rf_breakdown['department']['code'],'ophthalmology')
        self.assertEqual(context.rf_breakdown['net_total'],'20700.00')
        self.assertEqual(sum(i.line_total for i in context.payment.invoice.items.all()),Decimal('20700'))
        printed=self.client.get(f'/api/v1/receipts/{context.payment.receipt.pk}/print/')
        self.assertContains(printed,'Ophthalmology');self.assertContains(printed,'CVF')
        self.assertEqual(self.post().data['payment']['id'],response.data['payment']['id'])
    def test_reject_tampered_prices_mixed_heads_unknown_duplicate_and_wrong_amount(self):
        original=self.data.copy()
        for change in [dict(rf_department=''),dict(rf_department='microbiology'),dict(rf_items=[{'code':'rf_04_016'}]),dict(rf_items=[{'code':'rf_06_027','unit_amount':'1000'}]),dict(rf_items=[{'code':'rf_02_001','unit_amount':'1'}]),dict(sub_head='drf'),dict(amount='1'),dict(rf_items=[{'code':'rf_02_001'},{'code':'rf_02_001'}])]:
            self.data={**original,**change,'idempotency_key':str(uuid4())}
            response=self.post();self.assertEqual(response.status_code,400,response.data)
    def test_emergency_tiered_days(self):
        self.data.update(rf_department='accident_and_emergency',rf_items=[{'code':'rf_06_009','quantity':3},{'code':'rf_06_010','quantity':3}],amount='32000')
        response=self.post();self.assertEqual(response.status_code,201,response.data)

    def test_every_unconfirmed_entry_is_rejected_server_side(self):
        from rest_framework.exceptions import ValidationError
        from .rf import department_catalogue
        from .overhead import price_basket
        for item in CATALOGUE['items']:
            if item['available']:continue
            with self.subTest(code=item['code']),self.assertRaises(ValidationError):
                price_basket([{'code':item['code'],'quantity':1}],'regular',department_catalogue(item['department']))

    def test_nutrition_and_paediatric_prices_and_units(self):
        from .rf import department_catalogue
        from .overhead import price_basket
        nutrition=department_catalogue('nutrition_and_dietetics')
        paediatric=department_catalogue('paediatric_emergency')
        self.assertEqual(len(nutrition['items']),9)
        self.assertEqual(len(paediatric['items']),24)
        normal=nutrition['items'][0]
        self.assertEqual((normal['amount'],normal['unit']),('4000','day'))
        result=price_basket([{'code':normal['code'],'quantity':3}], 'regular',nutrition)
        self.assertEqual(result['net_total'],'12000.00')
        oxygen=paediatric['items'][9]
        self.assertEqual((oxygen['amount'],oxygen['unit']),('2500','hour'))
        result=price_basket([{'code':oxygen['code'],'quantity':2}], 'regular',paediatric)
        self.assertEqual(result['net_total'],'5000.00')
        drinks=nutrition['items'][8]
        self.assertEqual(drinks['kind'],'editable')
        result=price_basket([{'code':drinks['code'],'quantity':2,'unit_amount':Decimal('1800')}], 'regular',nutrition)
        self.assertEqual(result['net_total'],'3600.00')
        from rest_framework.exceptions import ValidationError
        with self.assertRaises(ValidationError):
            price_basket([{'code':drinks['code'],'quantity':1}], 'regular',nutrition)
