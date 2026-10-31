"""Catalogue-only activation using existing append-only approval records."""
from django.core.exceptions import ValidationError, PermissionDenied
from django.db import transaction
from apps.common.models import Sequence
from apps.auditlog.models import AuditEvent
from apps.operations.models import ApprovalRequest, ApprovalDecision
from .models import Department, DepartmentCategory
from .catalogue_setup import authorized

MODELS={'department':Department,'category':DepartmentCategory}


def reason_valid(reason):
    if not isinstance(reason,str) or not 5<=len(reason.strip())<=255:raise ValidationError('Supply a review reason of 5–255 characters.')


@transaction.atomic
def request_activation(targets,actor,reason):
    authorized(actor);reason_valid(reason)
    if not isinstance(targets,list) or not 1<=len(targets)<=200 or any(not isinstance(v,str) for v in targets) or len(set(targets))!=len(targets):raise ValidationError('Select 1–200 unique inactive catalogue entries.')
    Sequence.objects.select_for_update().get_or_create(key='hospital-catalogue-import')
    results=[]
    for target in targets:
        if not isinstance(target,str):raise ValidationError('Invalid activation target.')
        kind,separator,identity=target.partition(':');model=MODELS.get(kind)
        if not separator or not model:raise ValidationError('Activation targets must be department or category IDs.')
        try:obj=model.objects.select_for_update().get(pk=identity)
        except (model.DoesNotExist,ValueError,ValidationError) as error:raise ValidationError('Catalogue entry does not exist.') from error
        if obj.is_active:raise ValidationError('An entry is already active. Refresh the preview.')
        approval=ApprovalRequest.objects.filter(request_type='catalogue_activation',object_type=obj._meta.label,object_id=str(obj.pk),status='pending').first()
        if not approval:
            approval=ApprovalRequest.objects.create(request_type='catalogue_activation',requested_by=actor,object_type=obj._meta.label,object_id=str(obj.pk),reason=reason)
            AuditEvent.record('catalogue.activation.requested',actor=actor,obj=approval,reason=reason,metadata={'target':target,'name':obj.name})
        results.append(str(approval.pk))
    return results


def depth(approval):
    if approval.object_type==Department._meta.label:return 0
    if approval.object_type!=DepartmentCategory._meta.label:raise ValidationError('Approval is not a catalogue activation.')
    try:item=DepartmentCategory.objects.get(pk=approval.object_id)
    except DepartmentCategory.DoesNotExist as error:raise ValidationError('Catalogue entry no longer exists.') from error
    count=1;seen=set()
    while item.parent_id:
        if item.pk in seen or count>=8:raise ValidationError('Invalid category hierarchy.')
        seen.add(item.pk);count+=1;item=item.parent
    return count


@transaction.atomic
def decide_activation(identities,actor,approved,reason):
    authorized(actor);reason_valid(reason)
    if not isinstance(approved,bool):raise ValidationError('A boolean approval decision is required.')
    if not isinstance(identities,list) or not 1<=len(identities)<=200 or len(set(identities))!=len(identities):raise ValidationError('Select 1–200 unique catalogue approvals.')
    Sequence.objects.select_for_update().get_or_create(key='hospital-catalogue-import')
    try:requests=list(ApprovalRequest.objects.select_for_update().filter(pk__in=identities,request_type='catalogue_activation'))
    except (ValueError,ValidationError) as error:raise ValidationError('Invalid approval IDs.') from error
    if len(requests)!=len(identities):raise ValidationError('Only catalogue activation approvals may be decided here.')
    decisions=[]
    for approval in sorted(requests,key=depth):
        if approval.requested_by_id==actor.pk:raise PermissionDenied('The requester cannot approve or reject their own catalogue activation. A second authorized Super Administrator must review it.')
        if approval.status!='pending':raise ValidationError('An approval has already been decided. Refresh history.')
        model={m._meta.label:m for m in MODELS.values()}.get(approval.object_type)
        if not model:raise ValidationError('Invalid catalogue approval target.')
        try:obj=model.objects.select_for_update().get(pk=approval.object_id)
        except model.DoesNotExist as error:raise ValidationError('Catalogue entry no longer exists.') from error
        if approved:
            if obj.is_active:raise ValidationError('The entry is already active.')
            if isinstance(obj,DepartmentCategory) and (not obj.department.is_active or obj.parent_id and not obj.parent.is_active):raise ValidationError('Approve the department and parent categories first, or include their approvals in this batch.')
            obj.is_active=True;obj.save(update_fields=['is_active','updated_at'])
            AuditEvent.record('catalogue.activated',actor=actor,obj=obj,reason=reason,metadata={'approval':str(approval.pk)})
        approval.status='approved' if approved else 'rejected';approval.save(update_fields=['status','updated_at'])
        decision=ApprovalDecision.objects.create(request=approval,decided_by=actor,approved=approved,reason=reason)
        AuditEvent.record('catalogue.activation.decided',actor=actor,obj=approval,reason=reason,metadata={'approved':approved,'target':approval.object_type+':'+approval.object_id})
        decisions.append(decision)
    return decisions
