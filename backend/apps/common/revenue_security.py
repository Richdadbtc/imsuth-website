"""Body-free mutation logging and predictable validation envelopes."""
import logging
from rest_framework.views import exception_handler
logger=logging.getLogger('paypoint.requests')


def api_exception_handler(exc,context):
    response=exception_handler(exc,context)
    if response is not None and isinstance(response.data,dict):
        if 'detail' not in response.data:
            response.data={'detail':'Please check the submitted fields.','errors':response.data}
        response.data.setdefault('status',response.status_code)
    return response


class RevenueRequestLoggingMiddleware:
    def __init__(self,get_response):self.get_response=get_response
    def __call__(self,request):
        response=self.get_response(request)
        if '/api/v1/' in request.path:
            # Never log bodies, query strings, credentials, tokens, codes or patient data.
            logger.info('api_request method=%s route=%s status=%s actor=%s',request.method,getattr(request.resolver_match,'view_name','unresolved'),response.status_code,getattr(request.user,'pk',None))
            response['Cache-Control']='private, no-store'
        return response
