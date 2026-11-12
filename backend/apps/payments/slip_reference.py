"""Validation of the hospital's confirmed POS-slip TRANS REF format."""
import re
from datetime import datetime
from django.core.exceptions import ValidationError

SLIP_CHANNELS={'pos','bank_transfer'}
SLIP_PATTERN=r'09FG[0-9]{16}[A-Z0-9]{5}'
SLIP_HELP='Enter the complete 25-character TRANS REF from the POS slip: 09FG, 16 digits, then 5 letters/numbers.'

def validate_slip_reference(value,channel):
    if channel not in SLIP_CHANNELS:return value
    reference=re.sub(r'\s+','',value or '').upper()
    if not re.fullmatch(SLIP_PATTERN,reference):raise ValidationError(SLIP_HELP)
    try:datetime.strptime('20'+reference[4:16],'%Y%m%d%H%M%S')
    except ValueError as error:raise ValidationError('The TRANS REF contains an invalid transaction date or time.') from error
    return reference
