"""Validation of the hospital's channel-specific card and transfer slip reference formats."""
import re
from datetime import datetime
from django.core.exceptions import ValidationError

SLIP_CHANNELS={'pos','bank_transfer'}
SLIP_PATTERN=r'09FG[0-9]{16}[A-Z0-9]{5}'
COMPACT_TRANSFER_PATTERN=r'[A-Z0-9]{4}/[A-Z0-9]{5}'
SLIP_HELP='Enter the first 4 and last 5 characters of the transfer reference, separated by / (example: 09FG/CY0W7).'

def validate_slip_reference(value,channel,*,compact=False):
    if channel not in SLIP_CHANNELS:return value
    reference=re.sub(r'\s+','',value or '').upper()
    if channel=='pos':
        if not re.fullmatch(r'[0-9]{12}',reference):raise ValidationError('Enter the 12-digit Reference Number printed on the card slip, not the STAN or Auth Code.')
        return reference
    if re.fullmatch(COMPACT_TRANSFER_PATTERN,reference):return reference
    if re.fullmatch(r'[A-Z0-9]{9}',reference):return reference[:4]+'/'+reference[4:]
    if not re.fullmatch(SLIP_PATTERN,reference):raise ValidationError(SLIP_HELP)
    try:datetime.strptime('20'+reference[4:16],'%Y%m%d%H%M%S')
    except ValueError as error:raise ValidationError('The TRANS REF contains an invalid transaction date or time.') from error
    return reference[:4]+'/'+reference[-5:] if compact else reference
