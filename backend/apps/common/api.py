from rest_framework import viewsets

from apps.catalogue.models import Department, Service, TariffVersion
from apps.registry.models import Patient
from .permissions import CataloguePermission, RegistryPermission
from .serializers import DepartmentSerializer, PatientSerializer, ServiceSerializer, TariffVersionSerializer


class PatientViewSet(viewsets.ModelViewSet):
    queryset = Patient.objects.select_related("registered_by").all()
    serializer_class = PatientSerializer
    permission_classes = (RegistryPermission,)
    search_fields = ("patient_id", "first_name", "middle_name", "last_name", "normalized_phone")
    filterset_fields = ("status", "sex")


class DepartmentViewSet(viewsets.ModelViewSet):
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer
    permission_classes = (CataloguePermission,)
    search_fields = ("code", "name")
    filterset_fields = ("is_active",)


class ServiceViewSet(viewsets.ModelViewSet):
    queryset = Service.objects.select_related("department").all()
    serializer_class = ServiceSerializer
    permission_classes = (CataloguePermission,)
    search_fields = ("code", "name", "description")
    filterset_fields = ("department", "is_active")


class TariffVersionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = TariffVersion.objects.select_related("service", "approved_by").all()
    serializer_class = TariffVersionSerializer
    permission_classes = (CataloguePermission,)
    filterset_fields = ("service", "is_approved", "currency")

# Revenue Control actions reuse the original resource classes and serializers.
from django.db import transaction
from django.db.models import Q, Sum, Count, Avg, Max
from django.db.models.functions import Coalesce
from decimal import Decimal
from django.utils import timezone
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from apps.auditlog.models import AuditEvent
from .revenue_api import scoped, dated, date_range, require_writer, TariffProposalSerializer


class ScopedCatalogueMixin:
    http_method_names = ('get','post','patch','head','options')
    def get_queryset(self):
        return scoped(super().get_queryset(),self.request.user,'pk' if self.queryset.model is Department else 'department_id')
    @transaction.atomic
    def perform_create(self,serializer):
        obj=serializer.save();AuditEvent.record('catalogue.created',actor=self.request.user,obj=obj)
    @transaction.atomic
    def perform_update(self,serializer):
        obj=serializer.save();AuditEvent.record('catalogue.updated',actor=self.request.user,obj=obj)


class RevenuePatientViewSet(PatientViewSet):
    http_method_names=('get','post','patch','head','options')
    def get_queryset(self):
        if self.request.user.role in {'super_admin','finance','management','auditor'}: return super().get_queryset()
        qs=super().get_queryset()
        if not self.request.user.department_id: return qs.filter(registered_by=self.request.user)
        return qs.filter(Q(invoices__department_id=self.request.user.department_id)|Q(registered_by=self.request.user)).distinct()
    @transaction.atomic
    def perform_update(self,serializer):
        from apps.registry.models import PatientRevision
        from apps.registry.models import Patient
        original=Patient.objects.select_for_update().get(pk=serializer.instance.pk)
        keys=[key for key in serializer.validated_data if key not in {'status'}]
        before={key:str(getattr(original,key) or '') for key in keys}
        obj=serializer.save()
        after={key:str(getattr(obj,key) or '') for key in keys if str(getattr(obj,key) or '')!=before[key]}
        if after:
            PatientRevision.objects.create(patient=obj,changed_by=self.request.user,reason='Authorised demographic update',before={key:before[key] for key in after},after=after)
        AuditEvent.record('patient.updated',actor=self.request.user,obj=obj,metadata={'changed_fields':list(after)})
    @action(detail=False,url_path='search')
    def patient_search(self,request): return self.list(request)


class RevenueDepartmentViewSet(ScopedCatalogueMixin,DepartmentViewSet):
    ordering_fields=('name','collection','transactions','pending')
    def get_queryset(self):
        start,end=date_range(self.request.query_params)
        period=Q(invoices__payments__currency='NGN',invoices__payments__created_at__date__lte=end)
        if start:period &= Q(invoices__payments__created_at__date__gte=start)
        return super().get_queryset().annotate(collection=Coalesce(Sum('invoices__payments__amount',filter=period & Q(invoices__payments__status='confirmed')),Decimal('0')),transactions=Count('invoices__payments',filter=period),pending=Coalesce(Sum('invoices__payments__amount',filter=period & Q(invoices__payments__status__in=['pending','awaiting_offline_verification','review_required'])),Decimal('0'))).order_by('name')
    @action(detail=False)
    def analytics(self,request):
        from apps.payments.models import Payment
        departments=self.filter_queryset(self.get_queryset());qs=dated(Payment.objects.filter(invoice__department__in=departments,currency='NGN'),request.query_params)
        confirmed=Q(status='confirmed');pending=Q(status__in=['pending','awaiting_offline_verification','review_required'])
        rows=list(qs.values('invoice__department_id','invoice__department__name').annotate(collected=Sum('amount',filter=confirmed),pending=Sum('amount',filter=pending),count=Count('pk'),success_count=Count('pk',filter=confirmed),average=Avg('amount',filter=confirmed),last=Max('created_at')).order_by('invoice__department_id'))
        return Response({'departments_with_collections':sum(1 for row in rows if (row['collected'] or 0)>0),'department_count':departments.count(),'active_departments':departments.filter(is_active=True).count(),'results':rows,'collected':qs.filter(confirmed).aggregate(n=Sum('amount'))['n'] or 0,'transactions':qs.count(),'scope':'NGN attempts created in period, current verification state'})
    @action(detail=True)
    def services(self,request,pk=None):
        department=self.get_object();qs=Service.objects.filter(department=department)
        return self.get_paginated_response(ServiceSerializer(self.paginate_queryset(qs),many=True).data)
    @action(detail=True)
    def staff(self,request,pk=None):
        from .ui_api import StaffSerializer
        require_writer(request.user)
        return self.get_paginated_response(StaffSerializer(self.paginate_queryset(self.get_object().staff.all().order_by('username')),many=True).data)
    def payment_rows(self):
        from apps.payments.models import Payment
        return dated(Payment.objects.filter(invoice__department=self.get_object(),currency='NGN'),self.request.query_params)
    @action(detail=True)
    def summary(self,request,pk=None):
        qs=self.payment_rows()
        return Response({'verified_transactions':qs.filter(status='confirmed').count(),'last_transaction':qs.order_by('-created_at').values_list('created_at',flat=True).first(),'verified':qs.filter(status='confirmed').aggregate(n=Sum('amount'))['n'] or 0,'pending':qs.filter(status__in=['pending','awaiting_offline_verification','review_required']).aggregate(n=Sum('amount'))['n'] or 0,'transactions':qs.count(),'currency':'NGN','date_basis':'payment creation date'})
    @action(detail=True)
    def transactions(self,request,pk=None):
        from apps.payments.serializers import PaymentSerializer
        qs=self.payment_rows().select_related('invoice__patient','invoice__department','initiated_by','receipt').prefetch_related('invoice__items')
        return self.get_paginated_response(PaymentSerializer(self.paginate_queryset(qs),many=True).data)
    @action(detail=True)
    def collections(self,request,pk=None): return self.summary(request,pk)
    @action(detail=True)
    def trends(self,request,pk=None):
        from django.db.models.functions import TruncDate
        return Response(list(self.payment_rows().filter(status='confirmed').annotate(day=TruncDate('created_at')).values('day').annotate(amount=Sum('amount')).order_by('day')))


class RevenueServiceViewSet(ScopedCatalogueMixin,ServiceViewSet):
    @action(detail=True)
    def tariff(self,request,pk=None):
        service=self.get_object();now=timezone.now()
        obj=service.tariffs.filter(is_approved=True,effective_from__lte=now).filter(Q(effective_until__isnull=True)|Q(effective_until__gt=now)).first()
        if not obj: return Response({'detail':'No approved effective tariff is configured.'},status=404)
        category=request.query_params.get('patient_category','self_pay')
        if category!='self_pay': raise ValidationError('Category-specific approved pricing is not configured. No assumed discount is applied.')
        return Response(TariffVersionSerializer(obj).data)
    @action(detail=True)
    def tariffs(self,request,pk=None):
        return self.get_paginated_response(TariffVersionSerializer(self.paginate_queryset(self.get_object().tariffs.all()),many=True).data)
    @action(detail=False,url_path='price-history')
    def price_history(self,request):
        qs=TariffVersion.objects.filter(service__in=self.get_queryset()).select_related('service','approved_by').order_by('-effective_from')
        return self.get_paginated_response(TariffVersionSerializer(self.paginate_queryset(qs),many=True).data)
    @action(detail=False)
    def categories(self,request):
        from apps.catalogue.models import DepartmentCategory
        from rest_framework import serializers
        categories=DepartmentCategory.objects.filter(is_active=True,department__is_active=True,department__in=scoped(Department.objects.all(),request.user,'pk'))
        if request.query_params.get('department'):categories=categories.filter(department_id=serializers.UUIDField().run_validation(request.query_params['department']))
        names=set(self.filter_queryset(self.get_queryset()).exclude(category='').values_list('category',flat=True))
        names.update(categories.values_list('name',flat=True))
        return Response({'results':sorted(names),'catalogue_categories':list(categories.values('id','code','name','department_id','parent_id'))})
    @action(detail=True,methods=['post'],url_path='tariff-proposals')
    @transaction.atomic
    def propose(self,request,pk=None):
        require_writer(request.user)
        data=TariffProposalSerializer(data={**request.data,'service':str(self.get_object().pk)})
        data.is_valid(raise_exception=True);obj=data.save(requested_by=request.user)
        AuditEvent.record('tariff_proposal.created',actor=request.user,obj=obj)
        return Response(data.data,status=201)
