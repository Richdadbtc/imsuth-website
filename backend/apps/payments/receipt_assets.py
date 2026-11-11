"""Self-contained receipt images; QR contents contain no patient information."""
import base64
from functools import lru_cache
from io import BytesIO
from pathlib import Path
from django.conf import settings
import qrcode

@lru_cache(maxsize=1)
def logo_data_uri():
    asset=Path(__file__).parent.parent/'common/static/paypoint/imsuth-logo.png'
    return 'data:image/png;base64,'+base64.b64encode(asset.read_bytes()).decode('ascii')

def receipt_images(receipt):
    origin=getattr(settings,'PAYPOINT_PUBLIC_ORIGIN','https://www.imsuth.site').rstrip('/')
    url=f'{origin}/paypoint/api/v1/receipts/{receipt.pk}/print/'
    qr=qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_M,box_size=6,border=4)
    qr.add_data(url);qr.make(fit=True)
    stream=BytesIO();qr.make_image(fill_color='black',back_color='white').save(stream,format='PNG')
    return {'receipt_logo':logo_data_uri(),'receipt_qr':'data:image/png;base64,'+base64.b64encode(stream.getvalue()).decode('ascii'),'receipt_view_url':url}
