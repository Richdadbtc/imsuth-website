from django.core.exceptions import ValidationError as DjangoValidationError, PermissionDenied as DjangoPermissionDenied
from django.http import HttpResponse
from rest_framework import permissions, serializers
from rest_framework.exceptions import ValidationError, PermissionDenied
from rest_framework.response import Response
from rest_framework.views import APIView
from apps.auditlog.models import AuditEvent
from apps.operations.models import ApprovalRequest
from .catalogue_setup import proposal,plan,apply,csv_export,CONFIRM
from .catalogue_approvals import request_activation,decide_activation


class CatalogueSetupPermission(permissions.BasePermission):
    def has_permission(self,request,view):
        return request.user.is_authenticated and request.user.is_active and request.user.role=='super_admin'


def invoke(function,*args,**kwargs):
    try:return function(*args,**kwargs)
    except DjangoPermissionDenied as error:raise PermissionDenied(str(error)) from error
    except DjangoValidationError as error:raise ValidationError(error.messages) from error


class CatalogueSetupView(APIView):
    permission_classes=[CatalogueSetupPermission]

    def get(self,request,operation='preview'):
        if operation=='preview':return Response(invoke(plan,invoke(proposal)))
        if operation=='csv':
            response=HttpResponse(csv_export(proposal()),content_type='text/csv; charset=utf-8');response['Content-Disposition']='attachment; filename="hospital-catalogue-template.csv"';return response
        if operation=='history':
            approvals=list(ApprovalRequest.objects.filter(request_type='catalogue_activation').select_related('requested_by').order_by('-created_at')[:200])
            return Response({'events':list(AuditEvent.objects.filter(action__startswith='catalogue.').values('id','occurred_at','actor_id','action','object_type','object_id','reason','metadata')[:50]),'approvals':[{'id':str(a.pk),'target':a.object_type+':'+a.object_id,'requested_by':a.requested_by_id,'requester':a.requested_by.username,'reason':a.reason,'status':a.status,'created_at':a.created_at,'can_decide':a.status=='pending' and a.requested_by_id!=request.user.pk} for a in approvals]})
        raise ValidationError('Unknown catalogue operation.')

    def post(self,request,operation='preview'):
        allowed={'preview':{'csv','selected'},'import':{'csv','selected','reason','plan_token','confirmation'},'request-activation':{'targets','reason'},'decide':{'approvals','approved','reason'}}
        if operation not in allowed or not isinstance(request.data,dict) or set(request.data)-allowed[operation]:raise ValidationError('Unsupported catalogue operation or fields. Prices and staff changes are never accepted.')
        if operation in {'preview','import'}:
            data=invoke(proposal,request.data.get('csv'))
            selected=request.data.get('selected')
            if selected is not None:selected=serializers.ListField(child=serializers.CharField(max_length=120),max_length=500).run_validation(selected)
            if operation=='preview':return Response(invoke(plan,data,selected))
            if request.data.get('confirmation')!=CONFIRM:raise ValidationError('Confirm that this import creates inactive placeholders only.')
            token=serializers.RegexField(r'^[a-f0-9]{64}$').run_validation(request.data.get('plan_token'))
            reason=serializers.CharField(min_length=5,max_length=255).run_validation(request.data.get('reason'))
            return Response(invoke(apply,data,selected,request.user,reason,plan_token=token,confirmation=CONFIRM),status=201)
        reason=serializers.CharField(min_length=5,max_length=255).run_validation(request.data.get('reason'))
        if operation=='request-activation':
            targets=serializers.ListField(child=serializers.CharField(max_length=80),min_length=1,max_length=200).run_validation(request.data.get('targets'))
            return Response({'approvals':invoke(request_activation,targets,request.user,reason)},status=201)
        identities=serializers.ListField(child=serializers.UUIDField(),min_length=1,max_length=200).run_validation(request.data.get('approvals'))
        approved=serializers.BooleanField().run_validation(request.data.get('approved'))
        return Response({'decisions':[{'id':d.pk,'approved':d.approved} for d in invoke(decide_activation,identities,request.user,approved,reason)]})
