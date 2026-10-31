"""Report APIs with one filter contract and decimal-safe, explicitly scoped totals."""
import csv
import io
from datetime import date, timedelta
from decimal import Decimal
from collections import defaultdict
from django.db.models import Sum, Count
from django.http import HttpResponse
from django.utils import timezone
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.exceptions import ValidationError
from rest_framework.pagination import PageNumberPagination
from apps.billing.models import Invoice
from apps.registry.models import Patient
from apps.payments.models import Payment
from apps.operations.models import Settlement, ReconciliationItem
from apps.auditlog.models import AuditEvent
from .ui_api import FinanceRead, AuditSerializer, SettlementSerializer
from apps.payments.serializers import PaymentSerializer
from apps.billing.serializers import InvoiceSerializer
from .serializers import PatientSerializer
from apps.operations.serializers import ReconciliationItemSerializer


class ReportView(APIView):
    permission_classes=[FinanceRead]
    def perform_content_negotiation(self, request, force=False):
        if request.query_params.get('format') == 'csv':
            from rest_framework.renderers import JSONRenderer
            return JSONRenderer(), 'application/json'
        return super().perform_content_negotiation(request, force)
    def get(self,request,report):
        aliases={'overview':'revenue','daily-collection':'collections','department-revenue':'departments','cashier-collection':'cashiers','payment-channel':'channels','outstanding-invoices':'outstanding','reconciliation-discrepancies':'reconciliation','system-activity':'activity','patient-registration':'patients','revenue-collections':'collections','finance-overview':'revenue','revenue-reports':'revenue'}
        report=aliases.get(report,report)
        try:
            end=date.fromisoformat(request.query_params.get('to',str(timezone.localdate())))
            start=date.fromisoformat(request.query_params.get('from',str(end.replace(day=1))))
        except ValueError:
            raise ValidationError('Dates must use YYYY-MM-DD.')
        if end<start or (end-start).days>365:
            raise ValidationError('Choose a date range of at most 366 days.')
        params=request.query_params
        def fk(value):
            import uuid
            try:
                return str(uuid.UUID(value))
            except (ValueError,TypeError,AttributeError):
                raise ValidationError('Invalid resource identifier.')
        summary={}
        groups=[]
        if report in {'revenue','collections','departments','cashiers','channels'}:
            qs=Payment.objects.select_related('invoice__department','invoice__patient','initiated_by','receipt').prefetch_related('invoice__items').filter(created_at__date__gte=start,created_at__date__lte=end,currency='NGN')
            if params.get('department'):qs=qs.filter(invoice__department_id=fk(params['department']))
            if params.get('channel'):qs=qs.filter(channel=params['channel'])
            if params.get('provider'):qs=qs.filter(provider=params['provider'])
            if params.get('status'):qs=qs.filter(status=params['status'])
            if params.get('cashier'):
                try:qs=qs.filter(initiated_by_id=int(params['cashier']))
                except ValueError:raise ValidationError('Invalid cashier identifier.')
            if params.get('service'):
                # Balance allocation is explicit; do not count full invoices as service revenue.
                raise ValidationError('Service allocation is available through invoice line items; this payment report does not accept a service filter.')
            total=qs.count();success=qs.filter(status='confirmed');failed=qs.filter(status__in=['failed','rejected','expired'])
            summary={'transactions':total,'collected':success.aggregate(amount=Sum('amount'))['amount'] or 0,'failed_amount':failed.aggregate(amount=Sum('amount'))['amount'] or 0,'successful_transactions':success.count(),'failed_transactions':failed.count(),'success_rate':str(round(Decimal(success.count())*100/total,2)) if total else '0','currency':'NGN','scope':'payments created in selected period'}
            key={'departments':'invoice__department__name','cashiers':'initiated_by__username','channels':'channel'}.get(report,'channel')
            groups=list(success.values(key).annotate(amount=Sum('amount'),transactions=Count('pk')).order_by('-amount'))
            serializer=PaymentSerializer
        elif report=='outstanding':
            qs=Invoice.objects.select_related('patient','department').prefetch_related('items').filter(issued_at__date__gte=start,issued_at__date__lte=end,status__in=['issued','partially_paid'],currency='NGN')
            if params.get('department'):qs=qs.filter(department_id=fk(params['department']))
            if params.get('status'):qs=qs.filter(status=params['status'])
            summary={'outstanding':sum((obj.outstanding_balance for obj in qs),Decimal('0')),'invoices':qs.count(),'patients':qs.values('patient').distinct().count(),'overdue':None,'note':'Due dates are not recorded. Age uses invoice issue date as of period end.'}
            aging=defaultdict(lambda:{'amount':Decimal('0'),'count':0})
            for obj in qs:
                age=(end-timezone.localtime(obj.issued_at).date()).days
                bucket='0-30' if age<=30 else '31-60' if age<=60 else '61-90' if age<=90 else '91-180' if age<=180 else '181+'
                aging[bucket]['amount']+=obj.outstanding_balance
                aging[bucket]['count']+=1
            groups=[{'age_group':k,**v} for k,v in aging.items()]
            serializer=InvoiceSerializer
        elif report=='settlements':
            qs=Settlement.objects.filter(settlement_date__gte=start,settlement_date__lte=end)
            if params.get('provider'):qs=qs.filter(provider=params['provider'])
            summary={'recorded_amount':qs.aggregate(amount=Sum('amount'))['amount'] or 0,'records':qs.count(),'note':'Recorded settlement amounts only. Collected, pending and failed batch totals are not recorded.'}
            groups=list(qs.values('provider','currency').annotate(amount=Sum('amount'),records=Count('pk')))
            serializer=SettlementSerializer
        elif report=='reconciliation':
            qs=ReconciliationItem.objects.select_related('payment','batch').filter(transaction_date__date__gte=start,transaction_date__date__lte=end,currency='NGN')
            if params.get('status'):qs=qs.filter(status=params['status'])
            if params.get('channel'):qs=qs.filter(payment__channel=params['channel'])
            if params.get('provider'):qs=qs.filter(payment__provider=params['provider'])
            summary={'bank_amount':qs.aggregate(amount=Sum('amount'))['amount'] or 0,'records':qs.count(),'matched':qs.filter(status__in=['matched','resolved']).count(),'discrepancies':qs.exclude(status__in=['matched','resolved']).count(),'scope':'imported statement rows; a payment may occur in multiple batches'}
            groups=list(qs.values('status').annotate(amount=Sum('amount'),records=Count('pk')))
            serializer=ReconciliationItemSerializer
        elif report in {'audit','activity'}:
            qs=AuditEvent.objects.select_related('actor').filter(occurred_at__date__gte=start,occurred_at__date__lte=end)
            if params.get('action'):qs=qs.filter(action=params['action'])
            if params.get('user'):
                try:qs=qs.filter(actor_id=int(params['user']))
                except ValueError:raise ValidationError('Invalid user identifier.')
            summary={'activities':qs.count(),'unique_users':qs.exclude(actor=None).values('actor').distinct().count(),'uptime':None,'note':'Uptime telemetry is not configured.'}
            groups=list(qs.values('action').annotate(count=Count('pk')).order_by('-count'))
            serializer=AuditSerializer
        elif report=='patients':
            qs=Patient.objects.filter(created_at__date__gte=start,created_at__date__lte=end)
            if params.get('sex'):qs=qs.filter(sex=params['sex'])
            if params.get('status'):qs=qs.filter(status=params['status'])
            summary={'registered_profiles':qs.count(),'average_daily':str(round(Decimal(qs.count())/((end-start).days+1),2)),'returning_visits':None,'note':'Patient profile creation is not a returning visit event.'}
            groups=list(qs.values('sex').annotate(count=Count('pk')))
            serializer=PatientSerializer
        else:
            raise ValidationError('Unknown report type.')
        qs=qs.order_by('pk')
        if params.get('format')=='csv' or params.get('export')=='csv':
            if qs.count()>10000:
                raise ValidationError('Limit exports to 10,000 rows by narrowing the date range.')
            rows=serializer(qs,many=True).data
            stream=io.StringIO();writer=csv.writer(stream)
            if rows:
                keys=list(rows[0]);writer.writerow(keys)
                def cell(value):
                    text=str(value if value is not None else '')
                    return "'"+text if text.lstrip().startswith(('=','+','-','@')) else text
                for row in rows:writer.writerow([cell(row.get(key)) for key in keys])
            response=HttpResponse('\ufeff'+stream.getvalue(),content_type='text/csv; charset=utf-8')
            response['Content-Disposition']=f'attachment; filename="{report}-{start}-{end}.csv"'
            response['Cache-Control']='no-store'
            return response
        paginator=PageNumberPagination();paginator.page_size=50
        result=paginator.paginate_queryset(qs,request)
        response=paginator.get_paginated_response(serializer(result,many=True).data)
        response.data.update({'report':report,'from':str(start),'to':str(end),'summary':summary,'groups':groups})
        response['Cache-Control']='no-store'
        return response

from drf_spectacular.utils import extend_schema_view, extend_schema, OpenApiTypes
extend_schema_view(get=extend_schema(operation_id="report_data", responses=OpenApiTypes.OBJECT))(ReportView)
