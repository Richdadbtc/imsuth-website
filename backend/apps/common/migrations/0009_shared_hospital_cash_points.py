"""Provision the three explicitly requested shared, unlimited collection points."""
from django.db import migrations


def provision(apps,schema_editor):
    Point=apps.get_model('common','CashPoint')
    Event=apps.get_model('auditlog','AuditEvent')
    database=schema_editor.connection.alias
    for name in ['Main cash-point 1','Main cash-point 2','A&E Cash-point']:
        matches=list(Point.objects.using(database).filter(name__iexact=name))
        if len(matches)>1:raise RuntimeError('Resolve duplicate cash-point names before provisioning shared points.')
        point=matches[0] if matches else Point(name=name,location='Hospital-wide collection point')
        previous={'department':str(point.department_id) if point.department_id else None,'daily_limit':str(point.daily_limit) if point.daily_limit is not None else None,'is_active':point.is_active}
        point.department_id=None;point.daily_limit=None;point.is_active=True
        point.save(using=database)
        Event.objects.using(database).create(action='cash_point.shared_provisioned',object_type='common.CashPoint',object_id=str(point.pk),reason='User requested three hospital-wide cash points without daily collection limits.',metadata={'name':name,'previous':previous,'shared':True,'unlimited':True,'source':'common.0009'})


class Migration(migrations.Migration):
    dependencies=[('common','0008_remove_cashpoint_cash_point_limit_positive_and_more'),('auditlog','0001_initial')]
    # Keep configured points and their payment references when rolling code back.
    operations=[migrations.RunPython(provision,migrations.RunPython.noop)]
