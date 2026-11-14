from django.test import SimpleTestCase, TestCase
from django.core.exceptions import ValidationError
from .slip_reference import validate_slip_reference

VALID='09FG2611042341124813CY0W7'
class SlipReferenceTests(SimpleTestCase):
    def test_accepts_printed_reference_and_wrapped_lowercase(self):
        for channel in ['bank_transfer']:
            self.assertEqual(validate_slip_reference(VALID,channel),VALID)
            self.assertEqual(validate_slip_reference('09fg2611042341124813\ncy0w7',channel),VALID)
    def test_rejects_other_formats_and_invalid_calendar_values(self):
        for value in ['123456789012','ABC123',VALID+'0',VALID[:-1],VALID.replace('09FG','09XX'),'09FG2613322341124813CY0W7','09FG2611042541124813CY0W7']:
            for channel in ['bank_transfer']:
                with self.assertRaises(ValidationError):validate_slip_reference(value,channel)
    def test_card_reference_is_twelve_digits_and_not_transfer_or_auth_code(self):
        self.assertEqual(validate_slip_reference('631313012611','pos'),'631313012611')
        self.assertEqual(validate_slip_reference(' 631313 012611 ','pos'),'631313012611')
        for value in [VALID,'012611','611231','63131301261','6313130126111','63131301261A']:
            with self.assertRaises(ValidationError):validate_slip_reference(value,'pos')

    def test_other_channels_keep_their_own_reference_format(self):
        self.assertEqual(validate_slip_reference('CASH-001','cash'),'CASH-001')

class ReceiptSlipGateTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        from apps.common.test_revenue_api import RevenueControlTests
        RevenueControlTests.setUpTestData.__func__(cls)
    def test_print_refuses_invalid_slip_but_keeps_valid_confirmed_receipt(self):
        from rest_framework.test import APIClient
        client=APIClient();client.force_authenticate(self.admin)
        self.receipt.payment.channel='pos';self.receipt.payment.submitted_reference='invalid';self.receipt.payment.save()
        path=f'/api/v1/receipts/{self.receipt.pk}/print/'
        self.assertEqual(client.get(path).status_code,400)
        self.receipt.payment.submitted_reference='631313012611';self.receipt.payment.save()
        self.assertEqual(client.get(path).status_code,200)
