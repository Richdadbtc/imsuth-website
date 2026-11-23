"""Account removal preserves the attribution of historical hospital transactions."""
from django.contrib.sessions.models import Session
from django.utils import timezone
from rest_framework.exceptions import ValidationError
from .models import User


def lock_administrators():
    # Serialize lifecycle/role changes to prevent two requests removing the last admin.
    return list(User.objects.select_for_update().filter(role='super_admin').order_by('pk'))


def guard_change(actor,target,*,role=None,active=None):
    admins=lock_administrators()
    User.objects.select_for_update().get(pk=target.pk)
    target.refresh_from_db()
    if target.deleted_at:raise ValidationError('Deleted accounts cannot be changed.')
    loses_admin=target.role=='super_admin' and (role not in (None,'super_admin') or active is False)
    if target.pk==actor.pk and (active is False or role not in (None,target.role)):
        raise ValidationError('You cannot ban, delete or demote your own account.')
    if loses_admin and not any(u.pk!=target.pk and u.is_active and not u.deleted_at for u in admins):
        raise ValidationError('At least one active administrator must remain.')


def revoke_sessions(user):
    for session in Session.objects.filter(expire_date__gt=timezone.now()).iterator():
        if str(session.get_decoded().get('_auth_user_id',''))==str(user.pk):
            session.delete()
