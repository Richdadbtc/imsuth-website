"""Revenue Control API. No external payment or deposit execution is simulated."""
from datetime import timedelta
from decimal import Decimal
from django.db import transaction, IntegrityError
from django.db.models import Count, Sum, Q
from django.db.models.functions import TruncDate
from django.utils import timezone
from rest_framework import permissions, serializers, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView
from apps.accounts.models import User
from apps.auditlog.models import AuditEvent
from apps.billing.models import Invoice, InvoiceItem
from apps.catalogue.models import Department, Service, TariffVersion
from apps.payments.models import Payment, Receipt
from apps.payments.serializers import PaymentSerializer, ReceiptSerializer
from .models import Alert, CashPoint, CashOrder, CashApprovalLimit, ServiceDelivery, TariffProposal, CashCollectionEvidence
from .ui_api import StaffViewSet, StaffSerializer, AuditViewSet

GLOBAL_ROLES = {'super_admin', 'finance', 'management', 'auditor'}
WRITERS = {'super_admin', 'finance', 'management'}


def scoped(queryset, user, field='department_id'):
    if user.role in GLOBAL_ROLES:
        return queryset
    return queryset.filter(**{field: user.department_id}) if user.department_id else queryset.none()


def date_range(params):
    today = timezone.localdate()
    period = params.get('period', '30')
    if period not in {'today','yesterday','7','30','all','custom'}:
        raise ValidationError({'period':'Use today, yesterday, 7, 30, all or custom.'})
    start = today - timedelta(days=29)
    end = today
    if period == 'today': start = today
    if period == 'yesterday': start = end = today - timedelta(days=1)
    if period == '7': start = today - timedelta(days=6)
    if period == 'all': start = None
    for key in ('date_from','date_to'):
        if params.get(key):
            value = serializers.DateField().run_validation(params[key])
            if key == 'date_from': start = value
            else: end = value
    if start and start > end: raise ValidationError('Start date must not follow end date.')
    return start, end


def dated(qs, params, field='created_at'):
    start, end = date_range(params)
    qs = qs.filter(**{field+'__date__lte': end})
    return qs.filter(**{field+'__date__gte': start}) if start else qs


def require_writer(user):
    if user.role not in WRITERS: raise PermissionDenied('This role cannot perform this action.')


def note(data, key='notes'):
    return serializers.CharField(min_length=5, max_length=2000).run_validation(data.get(key))


class RevenuePermission(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and bool(request.user.role) and (request.method in permissions.SAFE_METHODS or request.user.role in WRITERS)


class AlertSerializer(serializers.ModelSerializer):
    type = serializers.CharField(source='alert_type', read_only=True)
    assigned_name = serializers.CharField(source='assigned_to.get_full_name', default='', read_only=True)
    class Meta:
        model = Alert
        fields = ('id','department','alert_type','type','severity','status','description','related_type','related_id','assigned_to','assigned_name','resolved_by','resolved_at','resolution_notes','created_at')
        read_only_fields = fields


class AlertViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Alert.objects.select_related('assigned_to','resolved_by','department').all()
    serializer_class = AlertSerializer
    permission_classes = [RevenuePermission]
    filterset_fields = ('severity','status','alert_type','assigned_to','department')
    search_fields = ('alert_type','description','related_id')
    ordering_fields = ('created_at','severity','status')
    def get_queryset(self):
        return dated(scoped(super().get_queryset(), self.request.user), self.request.query_params)
    @action(detail=False)
    def assignees(self,request):
        require_writer(request.user)
        return Response([{'id':u.pk,'name':u.get_full_name() or u.username} for u in User.objects.filter(is_active=True,role__in=WRITERS).order_by('username')])
    @action(detail=False)
    def summary(self, request):
        qs=self.filter_queryset(self.get_queryset())
        return Response({'total':qs.count(),'critical':qs.filter(severity='critical').count(),'pending_review':qs.exclude(status='resolved').count(),'resolved':qs.filter(status='resolved').count()})
    @action(detail=False)
    def analytics(self, request):
        qs=self.filter_queryset(self.get_queryset())
        return Response({key:list(qs.values(key).annotate(count=Count('pk')).order_by(key)) for key in ('alert_type','severity','status')})
    @transaction.atomic
    def transition(self, request, operation):
        obj=Alert.objects.select_for_update().get(pk=self.get_object().pk)
        if obj.status == 'resolved': raise ValidationError('Resolved alerts cannot be changed.')
        if operation=='assign':
            uid=serializers.IntegerField(min_value=1).run_validation(request.data.get('assigned_to'))
            assignee=User.objects.filter(pk=uid,is_active=True,role__in=WRITERS).first()
            if not assignee: raise ValidationError('Select an active finance, management or administrator account.')
            obj.assigned_to=assignee
        elif operation=='start-review': obj.status='in_review'
        else:
            obj.resolution_notes=note(request.data)
            obj.resolved_at=timezone.now();obj.resolved_by=request.user;obj.status='resolved'
        obj.save()
        AuditEvent.record('alert.'+operation,actor=request.user,obj=obj,metadata={'status':obj.status,'assigned_to':obj.assigned_to_id})
        return Response(self.get_serializer(obj).data)
    @action(detail=True,methods=['post'])
    def assign(self,request,pk=None): return self.transition(request,'assign')
    @action(detail=True,methods=['post'],url_path='start-review')
    def start_review(self,request,pk=None): return self.transition(request,'start-review')
    @action(detail=True,methods=['post'])
    def resolve(self,request,pk=None): return self.transition(request,'resolve')


class CashPointSerializer(serializers.ModelSerializer):
    department_name=serializers.CharField(source="department.name",read_only=True)
    assigned_officer_name=serializers.SerializerMethodField()
    def get_assigned_officer_name(self,obj) -> str:return obj.assigned_officer.get_full_name() or obj.assigned_officer.username
    class Meta:
        model=CashPoint
        fields='__all__'
        read_only_fields=('id','created_at','updated_at')
    def validate_daily_limit(self,value):
        if value<=0: raise ValidationError('Limit must be positive.')
        return value
    def validate(self,data):
        user=data.get('assigned_officer',getattr(self.instance,'assigned_officer',None))
        department=data.get('department',getattr(self.instance,'department',None))
        if user and (not user.is_active or user.role not in {'cashier','finance'} or user.department_id!=department.pk):
            raise ValidationError('Assigned officer must be an active cashier/finance officer in this department.')
        return data


class CashPointViewSet(viewsets.ModelViewSet):
    queryset=CashPoint.objects.select_related('department','assigned_officer').all()
    serializer_class=CashPointSerializer
    permission_classes=[RevenuePermission]
    http_method_names=('get','post','patch','head','options')
    filterset_fields=('department','is_active','assigned_officer')
    search_fields=('name','location','department__name')
    def get_queryset(self): return scoped(super().get_queryset(),self.request.user)
    @action(detail=False)
    def officers(self,request):
        require_writer(request.user)
        return Response([{'id':u.pk,'name':u.get_full_name() or u.username,'department':str(u.department_id)} for u in User.objects.filter(is_active=True,role__in=['cashier','finance'],department__isnull=False).order_by('username')])
    @transaction.atomic
    def perform_create(self,serializer):
        require_writer(self.request.user);obj=serializer.save();AuditEvent.record('cash_point.created',actor=self.request.user,obj=obj)
    @transaction.atomic
    def perform_update(self,serializer):
        require_writer(self.request.user);obj=serializer.save();AuditEvent.record('cash_point.updated',actor=self.request.user,obj=obj)
    @action(detail=True)
    def summary(self,request,pk=None):
        point=self.get_object()
        rows=dated(Payment.objects.filter(Q(cash_evidence__cash_point=point)|Q(recorded_context__cash_point=point),status='confirmed',channel='cash',currency='NGN'),request.query_params,'confirmed_at')
        return Response({'cash_point':str(point.pk),'daily_limit':point.daily_limit,'collections':rows.aggregate(n=Sum('amount'))['n'] or 0,'transactions':rows.count(),'currency':'NGN','note':'Confirmed cash payments with explicit point evidence; not a bank deposit or settlement total.'})
    @action(detail=True,methods=['get','post'])
    @transaction.atomic
    def collections(self,request,pk=None):
        point=self.get_object()
        if request.method=='POST':
            require_writer(request.user)
            payment_id=serializers.UUIDField().run_validation(request.data.get('payment'))
            payment=Payment.objects.select_for_update().filter(pk=payment_id,invoice__department=point.department,channel='cash',status='confirmed').first()
            if not payment: raise ValidationError('Evidence requires a confirmed cash payment in this department.')
            reference=serializers.CharField(min_length=5,max_length=160).run_validation(request.data.get('evidence_reference'))
            old=CashCollectionEvidence.objects.filter(payment=payment).first()
            if old:
                if old.cash_point_id!=point.pk or old.evidence_reference!=reference: raise ValidationError('Payment evidence is already recorded.')
                return Response({'id':str(old.pk)})
            obj=CashCollectionEvidence.objects.create(cash_point=point,payment=payment,recorded_by=request.user,evidence_reference=reference)
            AuditEvent.record('cash_collection.evidence_recorded',actor=request.user,obj=obj)
            return Response({'id':str(obj.pk)},status=201)
        rows=dated(point.collection_evidence.select_related('payment'),request.query_params)
        page=self.paginate_queryset(rows.order_by('-created_at'))
        return self.get_paginated_response([{'id':str(r.pk),'payment':str(r.payment_id),'amount':r.payment.amount,'currency':r.payment.currency,'payment_status':r.payment.status,'evidence_reference':r.evidence_reference,'has_attachment':bool(r.attachment_id),'bank_settled':None,'note':'Bank settlement is not certified by this evidence.'} for r in page])

    @action(detail=True,methods=['get','post'],url_path=r'collections/(?P<evidence_id>[^/.]+)/attachment')
    @transaction.atomic
    def evidence_attachment(self,request,pk=None,evidence_id=None):
        from django.shortcuts import get_object_or_404
        from django.http import HttpResponse
        from .models import PrivateAttachment
        import io
        point=self.get_object();require_writer(request.user)
        evidence=get_object_or_404(CashCollectionEvidence.objects.select_for_update(),pk=serializers.UUIDField().run_validation(evidence_id),cash_point=point)
        if request.method=='GET':
            if not evidence.attachment_id:return Response({'detail':'No attachment.'},status=404)
            response=HttpResponse(bytes(evidence.attachment.content),content_type='application/octet-stream')
            response['Content-Disposition']='attachment; filename="cash-evidence"'
            response['X-Content-Type-Options']='nosniff';response['Cache-Control']='private, no-store'
            return response
        if evidence.attachment_id:raise ValidationError('Evidence attachments are immutable.')
        uploaded=request.FILES.get('file')
        if not uploaded or uploaded.size>2*1024*1024:raise ValidationError('Select a PDF, PNG or JPG up to 2MB.')
        data=uploaded.read()
        if data.startswith(b'%PDF-'):
            content_type='application/pdf'
        else:
            from PIL import Image,UnidentifiedImageError
            try:
                source=Image.open(io.BytesIO(data))
                if source.format not in {'PNG','JPEG'} or source.width*source.height>16000000:raise ValueError()
                source.load();out=io.BytesIO();source.convert('RGB').save(out,format='JPEG');data=out.getvalue();content_type='image/jpeg'
            except (UnidentifiedImageError,Image.DecompressionBombError,ValueError,OSError):raise ValidationError('Select a valid PDF, PNG or JPG.')
        attachment=PrivateAttachment.objects.create(owner=request.user,filename='cash-evidence',content_type=content_type,content=data)
        evidence.attachment=attachment;evidence.save(update_fields=['attachment','updated_at'])
        AuditEvent.record('cash_evidence.attached',actor=request.user,obj=evidence)
        return Response({'id':str(attachment.pk)},status=201)


class CashOrderSerializer(serializers.ModelSerializer):
    requested_by_name=serializers.SerializerMethodField()
    decided_by_name=serializers.SerializerMethodField()
    def get_requested_by_name(self,obj) -> str:return obj.requested_by.get_full_name() or obj.requested_by.username
    def get_decided_by_name(self,obj) -> str:return (obj.decided_by.get_full_name() or obj.decided_by.username) if obj.decided_by else ""
    class Meta:
        model=CashOrder
        fields='__all__'
        read_only_fields=('id','created_at','updated_at','requested_by','decided_by','status','decided_at','decision_notes')
        extra_kwargs={'idempotency_key':{'validators':[]}}
    def validate_amount(self,value):
        if value<=0: raise ValidationError('Amount must be positive.')
        return value


class CashOrderViewSet(viewsets.ReadOnlyModelViewSet):
    queryset=CashOrder.objects.select_related('cash_point','requested_by','decided_by').all()
    serializer_class=CashOrderSerializer
    permission_classes=[permissions.IsAuthenticated]
    filterset_fields=('cash_point','status','requested_by')
    search_fields=('purpose','cash_point__name')
    def get_queryset(self): return dated(scoped(super().get_queryset(),self.request.user,'cash_point__department_id'),self.request.query_params)
    @transaction.atomic
    def create(self,request):
        if request.user.role not in WRITERS|{'cashier'}: raise PermissionDenied()
        data=self.get_serializer(data=request.data);data.is_valid(raise_exception=True);v=data.validated_data
        point=CashPoint.objects.select_for_update().get(pk=v['cash_point'].pk)
        if not scoped(CashPoint.objects.filter(pk=point.pk),request.user).exists(): raise PermissionDenied()
        old=CashOrder.objects.filter(idempotency_key=v['idempotency_key']).first()
        if old:
            if old.requested_by_id!=request.user.pk or old.cash_point_id!=point.pk or old.amount!=v['amount'] or old.purpose!=v['purpose'] or old.description!=v.get('description',''): raise ValidationError('Idempotency key already belongs to another request.')
            return Response(self.get_serializer(old).data)
        if not point.is_active: raise ValidationError('Cash point is inactive.')
        reserved=point.orders.filter(created_at__date=timezone.localdate(),status__in=['pending','approved']).aggregate(n=Sum('amount'))['n'] or Decimal('0')
        if reserved+v['amount']>point.daily_limit: raise ValidationError('Cash point daily authorization limit exceeded.')
        try:
            obj=data.save(requested_by=request.user)
        except IntegrityError as exc:
            raise ValidationError('Concurrent idempotency conflict. Retry the same request key.') from exc
        AuditEvent.record('cash_order.requested',actor=request.user,obj=obj)
        return Response(self.get_serializer(obj).data,status=201)
    @action(detail=False,url_path='approval-limits')
    def approval_limits(self,request):
        return Response({'results':list(CashApprovalLimit.objects.values('role','amount','policy_reference')),'note':'Only configured, management-approved limits apply; no default approval limit.'})
    @transaction.atomic
    def decide(self,request,approved):
        require_writer(request.user)
        obj=CashOrder.objects.select_for_update().get(pk=self.get_object().pk)
        if obj.requested_by_id==request.user.pk: raise PermissionDenied('The requester cannot decide their own order.')
        if obj.status!='pending': raise ValidationError('Order already decided.')
        notes=note(request.data)
        if approved:
            limit=CashApprovalLimit.objects.select_for_update().filter(role=request.user.role,approved_by__is_active=True,approved_by__role__in=['management','super_admin']).first()
            if not obj.cash_point.is_active: raise ValidationError('Cannot approve an inactive cash point.')
            if not limit or obj.amount>limit.amount: raise PermissionDenied('No sufficient management-approved limit is configured.')
        obj.status='approved' if approved else 'rejected';obj.decision_notes=notes;obj.decided_by=request.user;obj.decided_at=timezone.now();obj.save()
        AuditEvent.record('cash_order.decided',actor=request.user,obj=obj,metadata={'status':obj.status})
        return Response(self.get_serializer(obj).data)
    @action(detail=True,methods=['post'])
    def approve(self,request,pk=None): return self.decide(request,True)
    @action(detail=True,methods=['post'])
    def reject(self,request,pk=None): return self.decide(request,False)


class DeliverySerializer(serializers.ModelSerializer):
    class Meta:
        model=ServiceDelivery
        fields=('id','item','receipt','delivered_by','notes','created_at')
        read_only_fields=fields


class DepartmentDeskViewSet(viewsets.GenericViewSet):
    permission_classes=[permissions.IsAuthenticated]
    serializer_class=ReceiptSerializer
    queryset=Receipt.objects.select_related('payment','invoice__patient','invoice__department').all()
    def get_queryset(self):
        rows=scoped(super().get_queryset(),self.request.user,'invoice__department_id')
        department=self.request.query_params.get('department')
        if department: rows=rows.filter(invoice__department_id=serializers.UUIDField().run_validation(department))
        return rows
    def receipt(self,reference):
        from django.shortcuts import get_object_or_404
        return get_object_or_404(self.get_queryset(),receipt_number=reference)
    def payload(self,obj):
        valid=obj.payment.status=='confirmed' and obj.invoice.status=='paid' and not obj.invoice.payments.filter(status__in=['refund_pending','refunded','reversal_pending','reversed']).exists()
        items=obj.invoice.items.select_related('delivery').all()
        return {**ReceiptSerializer(obj).data,'payment_status':obj.payment.status,'eligible_for_delivery':valid,'patient_id':obj.invoice.patient.patient_id,'patient_name':str(obj.invoice.patient),'department':str(obj.invoice.department_id),'department_name':obj.invoice.department.name,'issued_at':obj.issued_at,'channel':obj.payment.channel,'payment_reference':obj.payment.reference,'can_deliver':valid and self.request.user.role in {'department_supervisor','finance','super_admin'},'service_status':'Service delivered' if items and all(hasattr(i,'delivery') for i in items) else 'Partially delivered' if any(hasattr(i,'delivery') for i in items) else 'Not yet used','items':[{'id':str(i.pk),'service':i.description,'quantity':i.quantity,'unit_amount':i.unit_amount,'delivered':hasattr(i,'delivery')} for i in items]}
    @action(detail=False,url_path='receipts')
    def receipts(self,request):
        qs=dated(self.get_queryset(),request.query_params,'issued_at')
        if request.query_params.get('search'): qs=qs.filter(Q(receipt_number__icontains=request.query_params['search'])|Q(invoice__patient__patient_id__icontains=request.query_params['search'])|Q(invoice__patient__first_name__icontains=request.query_params['search'])|Q(invoice__patient__last_name__icontains=request.query_params['search']))
        result=self.paginate_queryset(qs.order_by('-issued_at'))
        return self.get_paginated_response([self.payload(r) for r in result])
    @action(detail=False,url_path=r'receipts/(?P<reference>[^/.]+)')
    def receipt_detail(self,request,reference=None): return Response(self.payload(self.receipt(reference)))
    @action(detail=False,methods=['post'],url_path=r'receipts/(?P<reference>[^/.]+)/verify')
    def verify_receipt(self,request,reference=None):
        receipt=self.receipt(reference);result=self.payload(receipt)
        AuditEvent.record('department_desk.receipt_checked',actor=request.user,obj=receipt)
        return Response(result)
    @action(detail=False,methods=['post'],url_path=r'service-items/(?P<item_id>[^/.]+)/deliver')
    @transaction.atomic
    def deliver(self,request,item_id=None):
        from django.shortcuts import get_object_or_404
        if request.user.role not in {'department_supervisor','finance','super_admin'}: raise PermissionDenied('Service delivery requires an authorised department supervisor or finance officer.')
        item=get_object_or_404(scoped(InvoiceItem.objects.select_related('invoice'),request.user,'invoice__department_id'),pk=serializers.UUIDField().run_validation(item_id))
        chosen=request.query_params.get('department')
        if chosen and str(serializers.UUIDField().run_validation(chosen))!=str(item.invoice.department_id):raise ValidationError('The service is outside the selected department.')
        invoice=Invoice.objects.select_for_update().get(pk=item.invoice_id)
        # Serialize against payment changes as well as other deliveries.
        payments=list(Payment.objects.select_for_update().filter(invoice=invoice))
        receipt=get_object_or_404(Receipt,pk=serializers.UUIDField().run_validation(request.data.get('receipt')),invoice=invoice,payment__status='confirmed')
        if invoice.status!='paid' or any(p.status in {'refund_pending','refunded','reversal_pending','reversed'} for p in payments): raise ValidationError('Only fully paid, verified and undisputed services may be delivered.')
        if ServiceDelivery.objects.filter(item=item).exists(): raise ValidationError('This service item has already been delivered.')
        notes=serializers.CharField(max_length=2000,allow_blank=True).run_validation(request.data.get('notes',''))
        obj=ServiceDelivery.objects.create(item=item,receipt=receipt,delivered_by=request.user,notes=notes)
        AuditEvent.record('service.delivered',actor=request.user,obj=obj,metadata={'item':str(item.pk)})
        return Response(DeliverySerializer(obj).data,status=201)
    @action(detail=False,url_path='services/pending')
    def pending(self,request):
        qs=scoped(InvoiceItem.objects.filter(invoice__status='paid',delivery__isnull=True),request.user,'invoice__department_id')
        result=self.paginate_queryset(qs.order_by('created_at'))
        return self.get_paginated_response([{'id':str(i.pk),'invoice':str(i.invoice_id),'description':i.description,'quantity':i.quantity} for i in result])
    @action(detail=False)
    def activity(self,request):
        qs=dated(scoped(ServiceDelivery.objects.all(),request.user,'item__invoice__department_id'),request.query_params)
        return self.get_paginated_response(DeliverySerializer(self.paginate_queryset(qs.order_by('-created_at')),many=True).data)
    @action(detail=False)
    def summary(self,request):
        qs=scoped(ServiceDelivery.objects.all(),request.user,'item__invoice__department_id')
        return Response({'delivered':dated(qs,request.query_params).count()})


class RevenueDashboardView(APIView):
    permission_classes=[permissions.IsAuthenticated]
    def get(self,request,metric='summary'):
        base=scoped(Payment.objects.select_related('invoice__patient','invoice__department','initiated_by','receipt').prefetch_related('invoice__items'),request.user,'invoice__department_id').filter(currency='NGN')
        # Confirmed collections use confirmation date. Attempts use creation date.
        attempts=dated(base,request.query_params)
        confirmed=dated(base.filter(status='confirmed'),request.query_params,'confirmed_at')
        pending=attempts.filter(status__in=['pending','awaiting_offline_verification','review_required'])
        if metric=='overview-coverage':
            from apps.operations.models import ReconciliationItem
            rows=dated(scoped(ReconciliationItem.objects.filter(currency='NGN'),request.user,'payment__invoice__department_id'),request.query_params,'transaction_date')
            unmatched=rows.exclude(status__in=['matched','resolved'])
            channels=list(confirmed.values('channel').annotate(amount=Sum('amount'),transactions=Count('pk')).order_by('-amount'))
            start,end=date_range(request.query_params)
            return Response({
                'period':{'start':start,'end':end},
                'cash_under_orders':{'amount':confirmed.filter(channel='cash',recorded_context__cash_order__isnull=False).aggregate(n=Sum('amount'))['n'] or 0,'transactions':confirmed.filter(channel='cash',recorded_context__cash_order__isnull=False).count()},
                'insurance':{'nhis':None,'imshia':None,'configured':False},
                'cash_orders':{'amount':dated(scoped(CashOrder.objects.filter(status='approved'),request.user,'cash_point__department_id'),request.query_params).aggregate(n=Sum('amount'))['n'] or 0,'count':dated(scoped(CashOrder.objects.filter(status='approved'),request.user,'cash_point__department_id'),request.query_params).count()},
                'channels':channels,
                'daily_channels':list(confirmed.annotate(day=TruncDate('confirmed_at')).values('day','channel').annotate(amount=Sum('amount'),transactions=Count('pk')).order_by('day','channel')),
                'reconciliation':{'total':rows.count(),'matched':rows.filter(status__in=['matched','resolved']).count(),'pending':rows.filter(status='manual_review').count(),'unmatched':rows.filter(status__in=['unmatched','amount_mismatch']).count(),'unmatched_amount':unmatched.aggregate(n=Sum('amount'))['n'] or 0,'aged_unmatched':unmatched.filter(transaction_date__lt=timezone.now()-timedelta(days=1)).count()},
                'note':'Collections include confirmed NGN payments only. Reconciliation counts imported statement rows by transaction date; resolved rows count as matched. Unlinked rows are visible only to global finance roles.'})
        if metric=='summary':
            return Response({'currency':'NGN','verified_collections':confirmed.aggregate(n=Sum('amount'))['n'] or 0,'transactions':attempts.count(),'verified_transactions':confirmed.count(),'pending_transactions':pending.count(),'pending_amount':pending.aggregate(n=Sum('amount'))['n'] or 0,'active_departments':scoped(Department.objects.filter(is_active=True),request.user,'pk').count(),'note':'Gross confirmed NGN receipts by confirmation date; pending/failed/refunded/reversed states excluded. Not bank-settled revenue.'})
        if metric in {'collections-by-channel','collections-by-department'}:
            key='channel' if metric.endswith('channel') else 'invoice__department__name'
            return Response(list(confirmed.values(key).annotate(amount=Sum('amount'),transactions=Count('pk')).order_by('-amount')))
        if metric=='payment-status': return Response(list(attempts.values('status').annotate(count=Count('pk'),amount=Sum('amount')).order_by('status')))
        if metric=='trends': return Response(list(confirmed.annotate(day=TruncDate('confirmed_at')).values('day').annotate(amount=Sum('amount'),transactions=Count('pk')).order_by('day')))
        if metric=='alerts-summary':
            alerts=dated(scoped(Alert.objects.all(),request.user),request.query_params)
            return Response({'open':alerts.filter(status='open').count(),'in_review':alerts.filter(status='in_review').count(),'resolved':alerts.filter(status='resolved').count()})
        if metric=='recent-transactions':
            from .pagination import RevenuePagination
            search=serializers.CharField(max_length=160,allow_blank=True).run_validation(request.query_params.get('search',''))
            if search:attempts=attempts.filter(Q(reference__icontains=search)|Q(invoice__patient__first_name__icontains=search)|Q(invoice__patient__last_name__icontains=search))
            if request.query_params.get('status'):
                state=serializers.ChoiceField(choices=Payment.Status.choices).run_validation(request.query_params['status']);attempts=attempts.filter(status=state)
            pager=RevenuePagination();items=pager.paginate_queryset(attempts.order_by('-created_at','pk'),request)
            return pager.get_paginated_response(PaymentSerializer(items,many=True).data)
        raise ValidationError('Unknown dashboard metric.')


class UsersViewSet(StaffViewSet):
    http_method_names=('get','post','patch','head','options')
    @transaction.atomic
    def perform_update(self,serializer):
        before=serializer.instance.role
        super().perform_update(serializer)
        if before!=serializer.instance.role:
            AuditEvent.record('user.role_changed',actor=self.request.user,obj=serializer.instance,metadata={'before':before,'after':serializer.instance.role})
    @action(detail=True,methods=['post'])
    def activate(self,request,pk=None):
        data=self.get_serializer(self.get_object(),data={'is_active':True},partial=True);data.is_valid(raise_exception=True);self.perform_update(data);return Response(data.data)
    @action(detail=True)
    def permissions(self,request,pk=None):
        user=self.get_object()
        return Response({'role':user.role,'permissions':sorted(user.get_all_permissions())})
    @action(detail=False)
    def role_choices(self,request): return Response([{'value':v,'label':n} for v,n in User.Role.choices])


class AuditLogsViewSet(AuditViewSet):
    def get_queryset(self): return dated(super().get_queryset(),self.request.query_params,'occurred_at')
    @action(detail=False)
    def summary(self,request):
        qs=self.filter_queryset(self.get_queryset())
        return Response({'total':qs.count(),'unique_users':qs.values('actor').distinct().count(),'actions':list(qs.values('action').annotate(count=Count('pk')).order_by('-count'))})


class TariffProposalSerializer(serializers.ModelSerializer):
    service_name=serializers.CharField(source="service.name",read_only=True)
    class Meta:
        model=TariffProposal
        fields='__all__'
        read_only_fields=('id','created_at','updated_at','requested_by','decided_by','status','decision_notes','tariff')
    def validate_amount(self,value):
        if value<=0: raise ValidationError('Tariff must be positive.')
        return value
    def validate_effective_from(self,value):
        if value<timezone.now(): raise ValidationError('New tariffs must take effect in the future.')
        return value


class TariffProposalViewSet(viewsets.ReadOnlyModelViewSet):
    queryset=TariffProposal.objects.select_related('service').all()
    serializer_class=TariffProposalSerializer
    permission_classes=[RevenuePermission]
    def get_queryset(self): return scoped(super().get_queryset(),self.request.user,'service__department_id')
    @transaction.atomic
    def decide(self,request,approved):
        require_writer(request.user)
        obj=TariffProposal.objects.select_for_update().get(pk=self.get_object().pk)
        if obj.requested_by_id==request.user.pk: raise PermissionDenied('Maker cannot decide their own tariff proposal.')
        if obj.status!='pending': raise ValidationError('Proposal already decided.')
        obj.decision_notes=note(request.data)
        if approved:
            Service.objects.select_for_update().get(pk=obj.service_id)
            if obj.effective_from<timezone.now(): raise ValidationError('Effective date has passed. Submit a new proposal.')
            if TariffVersion.objects.filter(service=obj.service,effective_from=obj.effective_from).exists(): raise ValidationError('A tariff version already exists for that effective date.')
            # Adjust only validity windows under the service lock; pricing snapshots never change.
            approved=TariffVersion.objects.filter(service=obj.service,is_approved=True,currency='NGN')
            following=approved.filter(effective_from__gt=obj.effective_from).order_by('effective_from').first()
            previous=approved.filter(effective_from__lt=obj.effective_from).filter(Q(effective_until__isnull=True)|Q(effective_until__gt=obj.effective_from))
            previous_ids=list(previous.values_list('pk',flat=True))
            previous.update(effective_until=obj.effective_from)
            obj.tariff=TariffVersion.objects.create(service=obj.service,amount=obj.amount,effective_from=obj.effective_from,effective_until=following.effective_from if following else None,is_approved=True,approved_by=request.user,approval_reference=str(obj.pk),proposed_by=obj.requested_by)
            AuditEvent.record('tariff.validity_scheduled',actor=request.user,obj=obj.tariff,metadata={'previous_versions':[str(pk) for pk in previous_ids]})
        obj.status='approved' if approved else 'rejected';obj.decided_by=request.user;obj.save()
        AuditEvent.record('tariff_proposal.decided',actor=request.user,obj=obj,metadata={'status':obj.status})
        return Response(self.get_serializer(obj).data)
    @action(detail=True,methods=['post'])
    def approve(self,request,pk=None): return self.decide(request,True)
    @action(detail=True,methods=['post'])
    def reject(self,request,pk=None): return self.decide(request,False)

# Dynamic aggregate payloads are explicitly documented as objects.
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiTypes
extend_schema_view(get=extend_schema(responses=OpenApiTypes.OBJECT))(RevenueDashboardView)

# Explicit path types and distinct operation identities for nested actions.
from drf_spectacular.utils import OpenApiParameter
extend_schema_view(
    evidence_attachment=extend_schema(parameters=[OpenApiParameter('evidence_id', OpenApiTypes.UUID, OpenApiParameter.PATH)]),
)(CashPointViewSet)
extend_schema_view(
    receipt_detail=extend_schema(operation_id='department_receipt_detail', parameters=[OpenApiParameter('reference', OpenApiTypes.STR, OpenApiParameter.PATH)]),
    verify_receipt=extend_schema(parameters=[OpenApiParameter('reference', OpenApiTypes.STR, OpenApiParameter.PATH)]),
    deliver=extend_schema(parameters=[OpenApiParameter('item_id', OpenApiTypes.UUID, OpenApiParameter.PATH)]),
)(DepartmentDeskViewSet)
extend_schema_view(get=extend_schema(operation_id='revenue_dashboard_metric', responses=OpenApiTypes.OBJECT))(RevenueDashboardView)
