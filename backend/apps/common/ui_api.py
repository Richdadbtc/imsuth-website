"""Authenticated APIs for staff-facing management screens. No provider execution is simulated."""
import csv
import io
from datetime import date
from decimal import Decimal

from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.models import Group, Permission
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError, PermissionDenied as DjangoPermissionDenied
from django.db import transaction
from django.db.models import Sum, Count, Q
from django.http import HttpResponse
from django.utils import timezone
from rest_framework import serializers, permissions, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError, PermissionDenied
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.models import User
from apps.auditlog.models import AuditEvent
from apps.billing.models import Invoice
from apps.payments.models import Payment, Receipt, ReceiptReprint
from apps.operations.models import ApprovalRequest, Refund, Reversal, Settlement, Notification, NotificationRecipient, ReconciliationBatch, ReconciliationItem
from apps.operations.services import request_refund, request_reversal, decide_approval, import_reconciliation_csv
from .models import AccountProfile, SystemConfiguration, SupportTicket, SupportReply, PrivateAttachment


class AdminOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == User.Role.SUPER_ADMIN


class FinanceRead(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role in {'super_admin','finance','management','auditor'} and (request.method in permissions.SAFE_METHODS or request.user.role in {'super_admin','finance','management'})


class LoggedViewSet(viewsets.ModelViewSet):
    @transaction.atomic
    def perform_create(self, serializer):
        obj = serializer.save()
        AuditEvent.record('api.created', actor=self.request.user, obj=obj, request=self.request)

    @transaction.atomic
    def perform_update(self, serializer):
        obj = serializer.save()
        AuditEvent.record('api.updated', actor=self.request.user, obj=obj, request=self.request)

    def destroy(self, request, *args, **kwargs):
        raise ValidationError('Historical records cannot be deleted. Use a status change instead.')


class StaffSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()
    password = serializers.CharField(write_only=True, required=False, max_length=4096)
    phone = serializers.CharField(source='account_profile.phone',required=False,allow_blank=True,max_length=30,default='')
    class Meta:
        model = User
        fields = ('id','username','employee_id','first_name','last_name','full_name','email','role','department','is_active','date_joined','last_login','must_change_password','password','phone')
        read_only_fields = ('id','date_joined','last_login','must_change_password')
    def get_full_name(self, obj) -> str:
        return obj.get_full_name() or obj.username
    def validate(self, data):
        if data.get('role') == 'super_admin' and not self.context['request'].user.is_superuser:
            raise ValidationError('Only a Django superuser may assign the system administrator role.')
        if self.instance and self.instance.pk == self.context['request'].user.pk and (data.get('is_active') is False or 'role' in data and data['role'] != self.instance.role):
            raise ValidationError('You cannot deactivate or change your own administrative role here.')
        if 'password' in data:
            try:
                validate_password(data['password'], self.instance or User(username=data.get('username',''), email=data.get('email','')))
            except DjangoValidationError as error:
                raise ValidationError({'password': error.messages})
        return data
    def create(self, data):
        password = data.pop('password', None)
        profile = data.pop('account_profile',{})
        user = User(**data)
        user.set_password(password) if password else user.set_unusable_password()
        user.save()
        if profile:AccountProfile.objects.update_or_create(user=user,defaults=profile)
        return user
    def update(self, instance, data):
        profile=data.pop('account_profile',None)
        password = data.pop('password', None)
        if password:
            instance.set_password(password)
            instance.must_change_password = True
        user=super().update(instance, data)
        if profile is not None:AccountProfile.objects.update_or_create(user=user,defaults=profile)
        return user


class StaffViewSet(LoggedViewSet):
    queryset = User.objects.select_related('account_profile').all().order_by('username')
    serializer_class = StaffSerializer
    permission_classes = [AdminOnly]
    search_fields = ('username','first_name','last_name','email','employee_id')
    filterset_fields = ('role','department','is_active')
    @action(detail=True, methods=['post'])
    def deactivate(self, request, pk=None):
        user = self.get_object()
        serializer = self.get_serializer(user, data={'is_active':False}, partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data)


class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = AccountProfile
        fields = ('phone','address','job_title','date_of_birth','gender','qualification','specialization','license_number','bio','preferences')
    def validate_date_of_birth(self, value):
        if value and value > timezone.localdate():
            raise ValidationError('Date of birth cannot be in the future.')
        return value
    def validate_preferences(self, value):
        allowed = {'payments','reports','system','security','email','sms','language','theme','date_format','time_format'}
        if not isinstance(value, dict) or set(value) - allowed:
            raise ValidationError('Unrecognised preference.')
        for key, val in value.items():
            if key in {'payments','reports','system','security','email','sms'} and not isinstance(val,bool):
                raise ValidationError('Notification preferences must be booleans.')
            if key in {'language','theme','date_format','time_format'} and (not isinstance(val,str) or len(val)>40):
                raise ValidationError('Invalid display preference.')
        return value


class MyProfileView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    def get(self, request):
        profile, _ = AccountProfile.objects.get_or_create(user=request.user)
        return Response({'user':StaffSerializer(request.user).data, 'profile':ProfileSerializer(profile).data, 'has_photo':PrivateAttachment.objects.filter(owner=request.user,ticket=None,filename='profile.jpg',content_type='image/jpeg').exists()})
    @transaction.atomic
    def patch(self, request):
        allowed = {'first_name','last_name','email','profile'}
        if set(request.data)-allowed:
            raise ValidationError('Only personal information may be changed here.')
        user = User.objects.select_for_update().get(pk=request.user.pk)
        data = {key:value for key,value in request.data.items() if key != 'profile'}
        serializer = StaffSerializer(user, data=data, partial=True, context={'request':request})
        serializer.is_valid(raise_exception=True)
        profile, _ = AccountProfile.objects.get_or_create(user=user)
        details = ProfileSerializer(profile, data=request.data.get('profile',{}), partial=True)
        details.is_valid(raise_exception=True)
        serializer.save()
        details.save()
        AuditEvent.record('account.profile_updated', actor=user, request=request)
        return self.get(request)


class PasswordChangeView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    def post(self, request):
        from .recovery import limited
        if limited('password-change',str(request.user.pk),5):
            return Response({'detail':'Too many attempts. Try again later.'},status=429)
        old, new = request.data.get('current_password',''), request.data.get('new_password','')
        if not isinstance(old,str) or not isinstance(new,str) or len(new)>4096 or not request.user.check_password(old):
            raise ValidationError('Current password was not recognised or password is invalid.')
        try:
            validate_password(new, request.user)
        except DjangoValidationError as error:
            raise ValidationError({'detail':' '.join(error.messages)})
        request.user.set_password(new)
        request.user.must_change_password = False
        request.user.save(update_fields=['password','must_change_password'])
        # All sessions, including the current one, become invalid on their next request.
        AuditEvent.record('account.password_changed', actor=request.user, request=request)
        return Response({'detail':'Password changed. Sign in again on all devices.'})


class RoleSerializer(serializers.ModelSerializer):
    staff_count = serializers.IntegerField(source='user_set.count', read_only=True)
    class Meta:
        model = Group
        fields = ('id','name','permissions','staff_count')
    def validate_permissions(self, values):
        if any(p.content_type.app_label in {'auth','accounts'} for p in values):
            raise ValidationError('Administrative Django permissions cannot be delegated through this screen.')
        return values


class RoleViewSet(LoggedViewSet):
    queryset = Group.objects.prefetch_related('permissions').all().order_by('name')
    serializer_class = RoleSerializer
    permission_classes = [AdminOnly]
    @action(detail=False,url_path='permission-choices')
    def permission_choices(self,request):
        return Response({'results':list(Permission.objects.exclude(content_type__app_label__in=['auth','accounts']).order_by('content_type__app_label','codename').values('id','name','codename'))})
    @action(detail=True, methods=['post'])
    def assign(self, request, pk=None):
        role = self.get_object()
        user_id = serializers.IntegerField(min_value=1).run_validation(request.data.get('user'))
        try:
            user = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            raise ValidationError('Staff member not found.')
        user.groups.add(role)
        AuditEvent.record('account.group_assigned', actor=request.user, obj=user, request=request)
        return Response({'detail':'Group assigned. Financial role restrictions remain enforced.'})


class ConfigurationSerializer(serializers.ModelSerializer):
    class Meta:
        model = SystemConfiguration
        fields = ('id','section','values','updated_at')
        read_only_fields = ('id','updated_at')
    def validate(self, data):
        schemas = {'hospital':{'name','address','phone','email','website','receipt_header','receipt_footer'}, 'receipt':{'header','footer','format','copies','show_logo','show_staff'}, 'preferences':{'currency','date_format','timezone','items_per_page','default_dashboard'}, 'notifications':{'sender_name'}}
        section = data.get('section', getattr(self.instance,'section',None))
        values = data.get('values',{})
        if section not in schemas or not isinstance(values,dict) or set(values)-schemas[section]:
            raise ValidationError('Unsupported configuration. Security, credentials and infrastructure settings are managed by deployment configuration.')
        for value in values.values():
            if not isinstance(value,(str,int,bool)) or isinstance(value,str) and len(value)>500:
                raise ValidationError('Invalid setting value.')
        return data


class ConfigurationViewSet(LoggedViewSet):
    queryset = SystemConfiguration.objects.all().order_by('section')
    serializer_class = ConfigurationSerializer
    permission_classes = [AdminOnly]
    lookup_field = 'section'
    def perform_create(self, serializer):
        obj = serializer.save(updated_by=self.request.user)
        AuditEvent.record('settings.updated', actor=self.request.user, obj=obj, request=self.request)
    perform_update = perform_create


class ReplySerializer(serializers.ModelSerializer):
    class Meta:
        model = SupportReply
        fields = ('id','author','message','created_at')
        read_only_fields = ('id','author','created_at')


class TicketSerializer(serializers.ModelSerializer):
    replies = ReplySerializer(many=True, read_only=True)
    attachments = serializers.SerializerMethodField()
    def get_attachments(self,obj) -> list[dict]:return list(obj.attachments.values('id','filename','content_type'))
    class Meta:
        model = SupportTicket
        fields = ('id','subject','category','priority','message','status','requested_by','created_at','updated_at','replies','attachments')
        read_only_fields = ('id','requested_by','created_at','updated_at','replies','attachments')
    def validate(self, data):
        if self.context['request'].user.role != 'super_admin' and data.get('status') not in (None,'open'):
            raise ValidationError('Only support administrators may change ticket status.')
        return data


class TicketViewSet(LoggedViewSet):
    serializer_class = TicketSerializer
    permission_classes = [permissions.IsAuthenticated]
    search_fields = ('subject','message')
    filterset_fields = ('status','priority','category')
    def get_queryset(self):
        if getattr(self,'swagger_fake_view',False):return SupportTicket.objects.none()
        qs = SupportTicket.objects.prefetch_related('replies').order_by('-created_at')
        return qs if self.request.user.role == 'super_admin' else qs.filter(requested_by=self.request.user)
    def perform_create(self, serializer):
        obj = serializer.save(requested_by=self.request.user)
        AuditEvent.record('support.created', actor=self.request.user, obj=obj, request=self.request)
    @action(detail=True, methods=['post'])
    def reply(self, request, pk=None):
        ticket = self.get_object()
        serializer = ReplySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(ticket=ticket, author=request.user)
        return Response(serializer.data, status=201)
    @action(detail=True, methods=['post'])
    def attachments(self, request, pk=None):
        ticket = self.get_object()
        uploaded = request.FILES.get('file')
        if not uploaded or uploaded.size>5*1024*1024:
            raise ValidationError('Select a PDF, PNG or JPG file up to 5MB.')
        content = uploaded.read()
        kind = 'image/png' if content.startswith(b'\x89PNG\r\n\x1a\n') else 'image/jpeg' if content.startswith(b'\xff\xd8\xff') else 'application/pdf' if content.startswith(b'%PDF-') else None
        if not kind:
            raise ValidationError('Unsupported file format.')
        attachment = PrivateAttachment.objects.create(owner=request.user, ticket=ticket, filename=uploaded.name[:180], content_type=kind, content=content)
        return Response({'id':attachment.pk,'filename':attachment.filename}, status=201)


class AttachmentView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    def get(self, request, pk):
        from django.shortcuts import get_object_or_404
        qs = PrivateAttachment.objects.all()
        if request.user.role != 'super_admin':
            qs = qs.filter(Q(owner=request.user)|Q(ticket__requested_by=request.user))
        obj = get_object_or_404(qs,pk=pk)
        response = HttpResponse(bytes(obj.content), content_type=obj.content_type)
        response['Content-Disposition'] = 'attachment; filename="attachment"'
        response['X-Content-Type-Options'] = 'nosniff'
        response['Cache-Control'] = 'no-store'
        return response


def invoke(function, **kwargs):
    try:
        return function(**kwargs)
    except DjangoValidationError as error:
        raise ValidationError(error.messages)
    except DjangoPermissionDenied as error:
        raise PermissionDenied(str(error))


class FinancialRequestSerializer(serializers.Serializer):
    payment = serializers.PrimaryKeyRelatedField(queryset=Payment.objects.all())
    amount = serializers.DecimalField(max_digits=19, decimal_places=2, min_value=Decimal('0.01'), required=False)
    reason = serializers.CharField(min_length=5, max_length=255)


class RefundSerializer(serializers.ModelSerializer):
    class Meta:
        model = Refund
        fields = '__all__'
        read_only_fields = tuple(field.name for field in Refund._meta.fields)


class RefundViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Refund.objects.select_related('payment','approval').all().order_by('-created_at')
    serializer_class = RefundSerializer
    permission_classes = [FinanceRead]
    filterset_fields = ('status','payment')
    def create(self, request):
        serializer = FinancialRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        if 'amount' not in data:
            raise ValidationError('Refund amount is required.')
        with transaction.atomic():
            payment = Payment.objects.select_for_update().get(pk=data['payment'].pk)
            committed = payment.refunds.exclude(status__in=['rejected','failed']).aggregate(amount=Sum('amount'))['amount'] or Decimal('0')
            if data['amount'] + committed > payment.amount:
                raise ValidationError('Pending and completed refunds exceed the original payment.')
            if payment.reversals.exclude(status='rejected').exists():
                raise ValidationError('This payment already has a reversal request.')
            obj = invoke(request_refund, payment=payment, amount=data['amount'], reason=data['reason'], requested_by=request.user)
        return Response(self.get_serializer(obj).data, status=201)


class ReversalSerializer(serializers.ModelSerializer):
    class Meta:
        model = Reversal
        fields = '__all__'
        read_only_fields = tuple(field.name for field in Reversal._meta.fields)


class ReversalViewSet(RefundViewSet):
    queryset = Reversal.objects.select_related('payment','approval').all().order_by('-created_at')
    serializer_class = ReversalSerializer
    def create(self, request):
        serializer = FinancialRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        with transaction.atomic():
            payment = Payment.objects.select_for_update().get(pk=data['payment'].pk)
            if payment.reversals.exclude(status='rejected').exists() or payment.refunds.exclude(status__in=['rejected','failed']).exists():
                raise ValidationError('A refund or reversal request already exists for this payment.')
            obj = invoke(request_reversal, payment=payment, reason=data['reason'], requested_by=request.user)
        return Response(self.get_serializer(obj).data, status=201)


class SettlementSerializer(serializers.ModelSerializer):
    settled_at = serializers.DateField(source='settlement_date', read_only=True)
    settlement_id = serializers.CharField(source='settlement_reference', read_only=True)
    class Meta:
        model = Settlement
        fields = ('id','provider','settlement_reference','settlement_id','settlement_date','settled_at','amount','currency','created_at')
        read_only_fields = fields


class SettlementViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Settlement.objects.all().order_by('-settlement_date')
    serializer_class = SettlementSerializer
    permission_classes = [FinanceRead]
    search_fields = ('provider','settlement_reference')
    filterset_fields = ('provider','currency','settlement_date')
    def create(self,request):
        class Input(serializers.ModelSerializer):
            amount=serializers.DecimalField(max_digits=19,decimal_places=2,min_value=Decimal('0.01'))
            currency=serializers.ChoiceField(choices=['NGN'],default='NGN')
            class Meta:
                model=Settlement
                fields=('provider','settlement_reference','settlement_date','amount','currency')
        serializer=Input(data=request.data)
        serializer.is_valid(raise_exception=True)
        obj=serializer.save()
        AuditEvent.record('settlement.recorded',actor=request.user,obj=obj,request=request)
        return Response(self.get_serializer(obj).data,status=201)


class AuditSerializer(serializers.ModelSerializer):
    created_at = serializers.DateTimeField(source='occurred_at', read_only=True)
    user = serializers.SerializerMethodField()
    role = serializers.CharField(source='actor.role', read_only=True, default='')
    module = serializers.SerializerMethodField()
    description = serializers.CharField(source='reason',read_only=True)
    reference = serializers.CharField(source='object_id',read_only=True)
    class Meta:
        model = AuditEvent
        fields = ('id','occurred_at','created_at','actor','user','role','action','module','object_type','reference','description','ip_address','correlation_id')
    def get_user(self,obj) -> str:
        return obj.actor.get_full_name() or obj.actor.username if obj.actor else 'System'
    def get_module(self,obj) -> str:
        return obj.object_type.split('.')[0] or obj.action.split('.')[0]


class AuditViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = AuditEvent.objects.select_related('actor').all()
    serializer_class = AuditSerializer
    permission_classes = [FinanceRead]
    search_fields = ('action','object_type','object_id','actor__username')
    filterset_fields = ('actor','action','object_type')


class ReprintSerializer(serializers.ModelSerializer):
    receipt_number = serializers.CharField(source='receipt.receipt_number',read_only=True)
    class Meta:
        model = ReceiptReprint
        fields = ('id','receipt','receipt_number','printed_by','printed_at','reason','format')
        read_only_fields = ('id','printed_by','printed_at','receipt_number')


class ReprintViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ReceiptReprint.objects.select_related('receipt','printed_by').order_by('-printed_at')
    serializer_class = ReprintSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ('receipt','printed_by','format')
    def get_queryset(self):
        from .revenue_api import scoped
        return scoped(super().get_queryset(),self.request.user,'receipt__invoice__department_id')
    def create(self, request):
        if request.user.role not in {'cashier','finance','super_admin'}:
            raise PermissionDenied('This role cannot reprint receipts.')
        serializer = ReprintSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        from .revenue_api import scoped
        if not scoped(Receipt.objects.filter(pk=serializer.validated_data['receipt'].pk),request.user,'invoice__department_id').exists():
            raise PermissionDenied('Receipt is outside your access scope.')
        if serializer.validated_data['receipt'].payment.status != Payment.Status.CONFIRMED:
            raise ValidationError('Only confirmed payment receipts can be reprinted.')
        obj = serializer.save(printed_by=request.user)
        AuditEvent.record('receipt.reprinted', actor=request.user, obj=obj, request=request, reason=obj.reason)
        return Response(serializer.data,status=201)


class ReceiptVerificationView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    def post(self, request):
        number = serializers.CharField(max_length=64).run_validation(request.data.get('receipt_number'))
        from .revenue_api import scoped
        obj = scoped(Receipt.objects.select_related('payment','invoice'),request.user,'invoice__department_id').filter(receipt_number=number).first()
        from apps.payments.serializers import ReceiptSerializer
        valid = bool(obj and obj.payment.status==Payment.Status.CONFIRMED)
        AuditEvent.record('receipt.verified',actor=request.user,obj=obj,request=request,metadata={'valid':valid})
        return Response({'valid':valid,'status':'valid' if valid else 'not_found_or_invalid','receipt':ReceiptSerializer(obj).data if obj else None})


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ('id','event_type','subject','body','channel','sensitive','created_at')
        read_only_fields = ('id','created_at')


class NotificationViewSet(LoggedViewSet):
    queryset = Notification.objects.all().order_by('-created_at')
    serializer_class = NotificationSerializer
    permission_classes = [AdminOnly]
    filterset_fields = ('channel','event_type')
    search_fields = ('subject',)
    @action(detail=True,methods=['post'])
    @transaction.atomic
    def enqueue(self,request,pk=None):
        obj = self.get_object()
        users = serializers.ListField(child=serializers.IntegerField(min_value=1), min_length=1,max_length=200).run_validation(request.data.get('users'))
        targets = list(User.objects.filter(pk__in=users,is_active=True))
        if len(targets)!=len(set(users)):
            raise ValidationError('One or more recipients are not active staff.')
        if obj.channel != 'in_app':
            return Response({'detail':'External delivery requires a configured notification dispatcher. No message sent.'},status=503)
        for user in targets:
            NotificationRecipient.objects.get_or_create(notification=obj,user=user,defaults={'status':'sent'})
        AuditEvent.record('notification.published',actor=request.user,obj=obj,request=request,metadata={'recipient_count':len(targets)})
        return Response({'detail':'Published in-app.', 'recipients':len(targets)})


class InboxSerializer(serializers.ModelSerializer):
    notification = NotificationSerializer(read_only=True)
    class Meta:
        model = NotificationRecipient
        fields = ('id','notification','status','read_at','last_attempt_at')


class InboxViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = InboxSerializer
    permission_classes = [permissions.IsAuthenticated]
    def get_queryset(self):
        if getattr(self,'swagger_fake_view',False):return NotificationRecipient.objects.none()
        return NotificationRecipient.objects.filter(user=self.request.user).select_related('notification').order_by('-notification__created_at')
    @action(detail=False,url_path='unread-count')
    def unread_count(self,request):return Response({'count':self.get_queryset().filter(read_at__isnull=True).count()})
    @action(detail=True,methods=['post'])
    def read(self,request,pk=None):
        obj=self.get_object()
        obj.read_at=timezone.now()
        obj.save(update_fields=['read_at'])
        return Response(self.get_serializer(obj).data)


class CapabilitiesView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    def get(self,request):
        return Response({'profile':True,'staff':True,'groups':True,'financial_roles':User.Role.choices,'support_tickets':True,'in_app_notifications':True,'receipt_reprints':True,'audit':True,'settlement_records':True,'provider_refund_execution':False,'provider_reversal_execution':False,'sms_delivery':False,'email_dispatch':False,'two_factor_setup':False,'backup_execution':False,'uptime_monitoring':False,'qr_login':False,'notes':'Financial roles remain authoritative; Django groups do not override financial workflow permissions.'})


class DiscrepancySerializer(serializers.ModelSerializer):
    class Meta:
        model = ReconciliationItem
        fields = '__all__'
        read_only_fields = tuple(field.name for field in ReconciliationItem._meta.fields)


class DiscrepancyViewSet(viewsets.ReadOnlyModelViewSet):
    queryset=ReconciliationItem.objects.exclude(status='matched').select_related('batch','payment').order_by('-transaction_date')
    serializer_class=DiscrepancySerializer
    permission_classes=[FinanceRead]
    filterset_fields=('status','batch','currency','payment')
    search_fields=('external_reference','resolution_reason')
    @action(detail=True,methods=['post'])
    def request_resolution(self,request,pk=None):
        obj=self.get_object()
        reason=serializers.CharField(min_length=5,max_length=255).run_validation(request.data.get('reason'))
        with transaction.atomic():
            item=ReconciliationItem.objects.select_for_update().get(pk=obj.pk)
            if item.status=='resolved':
                raise ValidationError('Already resolved.')
            if ApprovalRequest.objects.filter(object_type='operations.ReconciliationItem',object_id=str(item.pk),status='pending').exists():
                raise ValidationError('Resolution already awaits approval.')
            approval=ApprovalRequest.objects.create(request_type='manual_match',requested_by=request.user,object_type='operations.ReconciliationItem',object_id=str(item.pk),reason=reason)
        AuditEvent.record('reconciliation.resolution_requested',actor=request.user,obj=item,request=request,reason=reason)
        return Response({'approval':approval.pk,'status':'pending'},status=201)


class TariffWriteSerializer(serializers.ModelSerializer):
    class Meta:
        from apps.catalogue.models import TariffVersion
        model=TariffVersion
        fields='__all__'
        read_only_fields=('id','approved_by','proposed_by','is_approved','created_at','updated_at')
    def validate(self,data):
        start=data.get('effective_from',getattr(self.instance,'effective_from',None))
        end=data.get('effective_until',getattr(self.instance,'effective_until',None))
        if end and start and end<=start:
            raise ValidationError('Effective end must follow effective start.')
        if self.instance and self.instance.is_approved:
            raise ValidationError('Approved tariffs are immutable. Create a new version.')
        return data


class TariffAccess(permissions.BasePermission):
    def has_permission(self,request,view):
        return request.user.is_authenticated and bool(request.user.role) and (request.method in permissions.SAFE_METHODS or request.user.role in {'finance','management','super_admin'})


class TariffManagementViewSet(LoggedViewSet):
    from apps.catalogue.models import TariffVersion
    queryset=TariffVersion.objects.select_related('service','approved_by').all()
    serializer_class=TariffWriteSerializer
    permission_classes=[TariffAccess]
    def get_queryset(self):
        from .revenue_api import scoped
        return scoped(super().get_queryset(),self.request.user,'service__department_id')
    filterset_fields=('service','is_approved','currency')
    @transaction.atomic
    def perform_create(self,serializer):
        obj=serializer.save(proposed_by=self.request.user)
        AuditEvent.record('tariff.proposed',actor=self.request.user,obj=obj)
    @action(detail=True,methods=['post'])
    def approve(self,request,pk=None):
        if request.user.role not in {'finance','management','super_admin'}:
            raise PermissionDenied()
        obj=self.get_object()
        if obj.proposed_by_id is None or obj.proposed_by_id==request.user.pk:
            raise PermissionDenied('An independent approver and recorded proposer are required.')
        with transaction.atomic():
            from apps.catalogue.models import Service, TariffVersion
            Service.objects.select_for_update().get(pk=obj.service_id)
            obj.refresh_from_db()
            if obj.is_approved:
                raise ValidationError('Already approved.')
            overlap=TariffVersion.objects.filter(service=obj.service,currency=obj.currency,is_approved=True).exclude(pk=obj.pk).filter(Q(effective_until__isnull=True)|Q(effective_until__gt=obj.effective_from))
            if obj.effective_until:
                overlap=overlap.filter(effective_from__lt=obj.effective_until)
            if overlap.exists():
                raise ValidationError('This version overlaps an approved tariff. Set non-overlapping effective dates.')
            obj.is_approved=True
            obj.approved_by=request.user
            obj.save(update_fields=['is_approved','approved_by','updated_at'])
        AuditEvent.record('tariff.approved',actor=request.user,obj=obj,request=request)
        return Response(self.get_serializer(obj).data)


class ProfilePhotoView(APIView):
    permission_classes=[permissions.IsAuthenticated]
    def get(self,request):
        obj=PrivateAttachment.objects.filter(owner=request.user,ticket=None,filename='profile.jpg',content_type='image/jpeg').order_by('-created_at').first()
        if not obj:return Response({'detail':'No profile photo.'},status=404)
        response=HttpResponse(bytes(obj.content),content_type=obj.content_type)
        response['Cache-Control']='private, no-store'
        response['X-Content-Type-Options']='nosniff'
        return response
    def post(self,request):
        file=request.FILES.get('file')
        if not file or file.size>2*1024*1024:
            raise ValidationError('Choose a PNG or JPG up to 2MB.')
        content=file.read()
        # Decode with Pillow, reject malformed/decompression-bomb images, re-encode to strip metadata.
        from PIL import Image, UnidentifiedImageError
        import warnings
        try:
            with warnings.catch_warnings():
                warnings.simplefilter('error',Image.DecompressionBombWarning)
                image=Image.open(io.BytesIO(content))
                if image.format not in {'PNG','JPEG'}:raise ValueError()
                image.load()
                image.thumbnail((800,800))
                output=io.BytesIO();image.convert('RGB').save(output,format='JPEG')
                content=output.getvalue()
        except (UnidentifiedImageError, ValueError, OSError, Image.DecompressionBombError, Image.DecompressionBombWarning):
            raise ValidationError('Invalid image.')
        with transaction.atomic():
            PrivateAttachment.objects.filter(owner=request.user,ticket=None,filename='profile.jpg',content_type='image/jpeg').delete()
            PrivateAttachment.objects.create(owner=request.user,filename='profile.jpg',content_type='image/jpeg',content=content)
        return Response({'detail':'Profile photo updated.'},status=201)
    def delete(self,request):
        PrivateAttachment.objects.filter(owner=request.user,ticket=None,filename='profile.jpg',content_type='image/jpeg').delete()
        return Response(status=204)


class IntegrationActionView(APIView):
    permission_classes=[AdminOnly]
    def post(self,request,operation):
        messages={'two-factor':'Two-factor enrollment is not configured. Account security was not changed.','backup':'A backup runner is not configured. No backup was executed.','restore':'Restore operations require the deployment backup runner. No data was changed.','provider-settings':'Provider credentials are managed through deployment secrets. No credentials were changed.'}
        if operation not in messages:raise ValidationError('Unknown integration operation.')
        return Response({'detail':messages[operation],'configured':False},status=503)


class HelpResourcesView(APIView):
    permission_classes=[permissions.IsAuthenticated]
    def get(self,request):
        return Response({'categories':['Getting Started','Patient Management','Billing','Payments','Reports','Administration','Troubleshooting'],'support_contacts':[],'ticket_submission':True,'live_chat':False,'video_tutorials':[],'note':'Support contacts must be configured by the hospital; illustrative contacts are not published.'})


class DeactivateAccountView(APIView):
    permission_classes=[permissions.IsAuthenticated]
    def post(self,request):
        from .recovery import limited
        if limited('account-deactivation',str(request.user.pk),5):
            return Response({'detail':'Too many attempts. Try again later.'},status=429)
        password=request.data.get('password','')
        if not isinstance(password,str) or not request.user.check_password(password):
            raise ValidationError('Current password was not recognised.')
        with transaction.atomic():
            user=User.objects.select_for_update().get(pk=request.user.pk)
            if user.role=='super_admin':
                raise ValidationError('Administrative accounts must be deactivated by another administrator.')
            user.is_active=False
            user.save(update_fields=['is_active'])
            AuditEvent.record('account.deactivated',actor=user,request=request)
        from django.contrib.auth import logout
        logout(request)
        return Response({'detail':'Account deactivated. Historical records have been preserved.'})


class ReportCatalogueView(APIView):
    permission_classes=[FinanceRead]
    def get(self,request):
        names={'revenue':'Revenue Reports','daily-collection':'Daily Collection Report','department-revenue':'Department Revenue Report','cashier-collection':'Cashier Collection Report','payment-channel':'Payment Channel Report','outstanding-invoices':'Outstanding Invoices Report','settlements':'Settlement Report','reconciliation':'Reconciliation Report','audit':'Audit Trail Report','patient-registration':'Patient Registration Report','system-activity':'System Activity Report'}
        return Response({'reports':[{'id':key,'name':name,'path':f'reports/{key}/','formats':['json','csv']} for key,name in names.items()]})

# Dynamic report/configuration payloads are documented as objects; exact contracts
# and supported keys are in UI_API.md. Never omit these paths from OpenAPI.
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiTypes
for _view, _methods in (
    (MyProfileView, ('get','patch')), (PasswordChangeView, ('post',)),
    (AttachmentView, ('get',)), (ProfilePhotoView, ('get','post','delete')),
    (ReceiptVerificationView, ('post',)), (CapabilitiesView, ('get',)),
    (HelpResourcesView, ('get',)), (IntegrationActionView, ('post',)),
    (DeactivateAccountView, ('post',)), (ReportCatalogueView, ('get',)),
):
    extend_schema_view(**{method:extend_schema(request=OpenApiTypes.OBJECT if method in {'post','patch'} else None, responses=OpenApiTypes.OBJECT) for method in _methods})(_view)
RefundViewSet.create=extend_schema(request=FinancialRequestSerializer,responses=RefundSerializer)(RefundViewSet.create)
ReversalViewSet.create=extend_schema(request=FinancialRequestSerializer,responses=ReversalSerializer)(ReversalViewSet.create)
