"""Add two shared points without renaming or merging existing collection points."""
from django.db import migrations

NAMES=('Main Cashpoint 1','Main Cashpoint 2')


def provision(apps,schema_editor):
    Point=apps.get_model('common','CashPoint')
    Event=apps.get_model('auditlog','AuditEvent')
    database=schema_editor.connection.alias
    planned=[]
    for name in NAMES:
        matches=list(Point.objects.using(database).filter(name__iexact=name))
        if len(matches)>1:
            raise RuntimeError('Resolve duplicate Main Cashpoint names before provisioning; no records will be merged.')
        planned.append((name,matches[0] if matches else None))
    for name,point in planned:
        previous={'name':point.name,'department':str(point.department_id) if point.department_id else None,'daily_limit':str(point.daily_limit) if point.daily_limit is not None else None,'is_active':point.is_active} if point else None
        if point and point.name==name and point.department_id is None and point.daily_limit is None and point.is_active:
            continue
        point=point or Point(location='Hospital-wide collection point')
        point.name=name;point.department_id=None;point.daily_limit=None;point.is_active=True
        point.save(using=database)
        Event.objects.using(database).create(action='cash_point.shared_provisioned',object_type='common.CashPoint',object_id=str(point.pk),reason='Hospital requested two additional shared cash points without daily collection limits.',metadata={'name':name,'previous':previous,'shared':True,'unlimited':True,'source':'common.0015'})


class Migration(migrations.Migration):
    dependencies=[('common','0014_recordedpayment_drf_breakdown')]
    operations=[migrations.RunPython(provision,migrations.RunPython.noop)]
