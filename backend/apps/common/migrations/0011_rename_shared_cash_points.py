"""Rename existing shared points in place, retaining all transaction links."""
from django.db import migrations

RENAMES=(('Main cash-point 1','OPD CASH POINT'),('Main cash-point 2','GOPD CASH POINT'))

def rename_points(apps,schema_editor):
    Point=apps.get_model('common','CashPoint')
    Event=apps.get_model('auditlog','AuditEvent')
    database=schema_editor.connection.alias
    changes=[]
    for old,new in RENAMES:
        sources=list(Point.objects.using(database).filter(name__iexact=old))
        targets=list(Point.objects.using(database).filter(name__iexact=new))
        if len(sources)>1 or len(targets)>1 or sources and targets:
            raise RuntimeError('Conflicting cash-point names found. Review existing points before renaming; no records will be merged.')
        if sources:changes.append((sources[0],new))
    for point,new in changes:
        old=point.name
        Point.objects.using(database).filter(pk=point.pk).update(name=new)
        Event.objects.using(database).create(action='cash_point.renamed',object_type='common.CashPoint',object_id=str(point.pk),reason='Hospital requested updated cash-point names.',metadata={'before':old,'after':new,'source':'common.0011'})

class Migration(migrations.Migration):
    dependencies=[('common','0010_recordedpayment_base_total_and_more')]
    operations=[migrations.RunPython(rename_points,migrations.RunPython.noop)]
