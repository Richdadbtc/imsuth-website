"""Deterministic, non-billable catalogue planning and transactional import."""
import csv
import hashlib
import io
import json
import re
import unicodedata
from difflib import SequenceMatcher
from pathlib import Path
from django.conf import settings
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction, IntegrityError
from apps.common.models import Sequence
from apps.auditlog.models import AuditEvent
from .models import Department, DepartmentCategory, Service

COLUMNS=('kind','code','name','department_code','parent_code')
CONFIRM='IMPORT INACTIVE CATALOGUE'
MASTER=Path(__file__).parent/'data'/'hospital_catalogue.json'
MAX_ROWS=500


def authorized(actor):
    if not actor or not actor.is_authenticated or not actor.is_active or actor.role!='super_admin':
        raise PermissionDenied('An active authenticated Super Administrator is required.')


def normalized(value):
    return ' '.join(unicodedata.normalize('NFKC',value).casefold().replace('&',' and ').split())


def key(row):
    return 'department:'+row['code'] if row['kind']=='department' else 'category:'+row['department_code']+':'+row['code']


def validate_entries(entries):
    if not isinstance(entries,list) or not 1<=len(entries)<=MAX_ROWS:raise ValidationError('Supply 1–500 catalogue entries.')
    seen=set();names=set();departments={r.get('code') for r in entries if isinstance(r,dict) and r.get('kind')=='department'}
    for row in entries:
        if not isinstance(row,dict) or set(row)!=set(COLUMNS) or any(not isinstance(v,str) for v in row.values()):raise ValidationError('Only kind, code, name, department_code and parent_code are accepted.')
        if row['kind'] not in {'department','category'}:raise ValidationError('Kind must be department or category.')
        if not re.fullmatch(r'[A-Z][A-Z0-9-]{0,23}' if row['kind']=='department' else r'[A-Z][A-Z0-9-]{0,31}',row['code']):raise ValidationError('Use stable uppercase alphanumeric/hyphen codes within model limits.')
        limit=120 if row['kind']=='department' else 80
        if not row['name'].strip() or row['name']!=row['name'].strip() or len(row['name'])>limit:raise ValidationError('Names must be nonempty, trimmed, and within model limits.')
        if any(v.lstrip().startswith(('=','+','-','@')) or any(ord(c)<32 for c in v) for v in row.values()):raise ValidationError('Spreadsheet formulas and control characters are not allowed.')
        if row['kind']=='department' and (row['department_code'] or row['parent_code']):raise ValidationError('Departments cannot specify a parent or department_code.')
        if row['kind']=='category' and not re.fullmatch(r'[A-Z][A-Z0-9-]{0,23}',row['department_code']):raise ValidationError('Each category requires a department_code.')
        if row['parent_code'] and not re.fullmatch(r'[A-Z][A-Z0-9-]{0,31}',row['parent_code']):raise ValidationError('Invalid parent category code.')
        identity=(row['kind'],row['department_code'],normalized(row['name']))
        if key(row) in seen or identity in names:raise ValidationError('The proposal contains duplicate codes or names in the same scope.')
        seen.add(key(row));names.add(identity)
    # Resolve submitted hierarchy only; database references are checked by plan().
    categories={(r['department_code'],r['code']):r for r in entries if r['kind']=='category'}
    for row in categories.values():
        visited=set();cursor=row
        while cursor and cursor['parent_code']:
            identity=(cursor['department_code'],cursor['code'])
            if identity in visited or len(visited)>=8:raise ValidationError('Category hierarchy contains a cycle or exceeds eight levels.')
            visited.add(identity);cursor=categories.get((row['department_code'],cursor['parent_code']))
    return entries


def proposal(csv_text=None):
    if csv_text is None:
        data=json.loads(MASTER.read_text());entries=data['entries'];version=data['version']
    else:
        if not isinstance(csv_text,str) or len(csv_text.encode('utf-8'))>512*1024:raise ValidationError('Use a UTF-8 CSV of at most 512KB.')
        reader=csv.DictReader(io.StringIO(csv_text.lstrip('\ufeff')))
        if reader.fieldnames is None or len(reader.fieldnames)!=len(COLUMNS) or set(reader.fieldnames)!=set(COLUMNS):raise ValidationError('CSV headers must be: '+', '.join(COLUMNS))
        entries=[]
        for row in reader:
            entries.append(row)
            if len(entries)>MAX_ROWS:raise ValidationError('CSV cannot exceed 500 rows.')
        version='validated-csv-v1'
    return {'version':version,'entries':validate_entries(entries)}


def csv_export(data):
    output=io.StringIO(newline='');writer=csv.DictWriter(output,fieldnames=COLUMNS);writer.writeheader();writer.writerows(data['entries']);return output.getvalue()


def _match(row,records):
    code=[r for r in records if normalized(r['code'])==normalized(row['code'])]
    name=[r for r in records if normalized(r['name'])==normalized(row['name'])]
    if len(code)>1 or len(name)>1:return None,'conflict','Multiple existing records share a normalized code or name.'
    if code and (normalized(code[0]['name'])!=normalized(row['name']) or (name and code[0]['id']!=name[0]['id'])):
        return None,'conflict','Existing code belongs to a different name; explicit reconciliation is required.'
    if name:return name[0],'existing','Existing identity retained, including its current code and status.'
    if code:return code[0],'existing','Existing identity retained.'
    proposed=normalized(row['name'])
    possible=[r for r in records if SequenceMatcher(None,proposed,normalized(r['name'])).ratio()>=.88 or (min(len(proposed),len(normalized(r['name'])))>=6 and (proposed in normalized(r['name']) or normalized(r['name']) in proposed))]
    if possible:return None,'conflict','Possible name duplicate: '+', '.join(r['code']+' / '+r['name'] for r in possible[:5])
    return None,'new','Will be created inactive; no service or tariff will be created.'


def snapshot():
    departments=list(Department.objects.order_by('pk').values('id','code','name','is_active'))
    categories=list(DepartmentCategory.objects.order_by('pk').values('id','department_id','code','name','parent_id','is_active'))
    legacy=list(Service.objects.exclude(category='').order_by('department_id','category').values('department_id','category').distinct())
    return departments,categories,legacy


def plan(data,selected=None):
    entries=validate_entries(data['entries']);all_keys={key(r) for r in entries}
    if selected is not None and (not isinstance(selected,list) or len(selected)>MAX_ROWS or any(not isinstance(v,str) or v not in all_keys for v in selected) or len(set(selected))!=len(selected)):raise ValidationError('Select unique entry keys from this proposal.')
    chosen=all_keys if selected is None else set(selected)
    departments,categories,legacy=snapshot();rows=[];mapping={}
    # Fixture order does not control matching or creation.
    for row in sorted((r for r in entries if r['kind']=='department'),key=key):
        existing,status,note=_match(row,departments)
        result={**row,'key':key(row),'status':status,'note':note,'id':str(existing['id']) if existing else None,'actual_code':existing['code'] if existing else row['code'],'is_active':existing['is_active'] if existing else False}
        mapping[row['code']]=result;rows.append(result)
    pending=[r for r in entries if r['kind']=='category'];category_map={}
    while pending:
        progress=False
        for row in pending[:]:
            parent_key=(row['department_code'],row['parent_code'])
            parent_proposed=any(r['kind']=='category' and r['department_code']==row['department_code'] and r['code']==row['parent_code'] for r in entries)
            if row['parent_code'] and parent_proposed and parent_key not in category_map:continue
            department=mapping.get(row['department_code'])
            if department is None:
                candidate={'code':row['department_code'],'name':''}
                candidates=[d for d in departments if normalized(d['code'])==normalized(row['department_code'])]
                department={'id':str(candidates[0]['id']),'status':'existing','key':None} if len(candidates)==1 else None
            records=[r for r in categories if department and str(r['department_id'])==department['id']]
            existing,status,note=_match(row,records)
            parent=category_map.get(parent_key)
            if row['parent_code'] and not parent_proposed:
                candidates=[r for r in records if normalized(r['code'])==normalized(row['parent_code'])]
                parent={'id':str(candidates[0]['id']),'status':'existing','key':None} if len(candidates)==1 else None
            if not department or department['status']=='conflict':status='conflict';note='Department is missing or conflicting.'
            elif row['parent_code'] and (not parent or parent['status']=='conflict'):status='conflict';note='Parent category is missing or conflicting.'
            elif existing and ((parent and parent['status']=='new') or str(existing['parent_id'] or '')!=str((parent or {}).get('id') or '')):status='conflict';note='Existing category has a different parent; it will not be reparented.'
            dependencies=[item['key'] for item in [department,parent] if item and item.get('key') and item['status']=='new']
            result={**row,'key':key(row),'status':status,'note':note,'id':str(existing['id']) if existing else None,'actual_code':existing['code'] if existing else row['code'],'is_active':existing['is_active'] if existing else False,'dependencies':dependencies,'department_id':department['id'] if department else None,'parent_id':parent['id'] if parent else None}
            category_map[(row['department_code'],row['code'])]=result;rows.append(result);pending.remove(row);progress=True
        if not progress:raise ValidationError('Category hierarchy cannot be resolved.')
    for row in rows:
        if row['key'] in chosen and row['status']!='conflict' and any(dependency not in chosen for dependency in row.get('dependencies',[])):
            row['status']='conflict';row['note']='Select the missing new parent/department as well.'
        row['comparison_status']=row['status'];row['selected']=row['key'] in chosen
        if not row['selected']:row['status']='skipped'
    digest=hashlib.sha256(json.dumps({'proposal':data,'snapshot':[departments,categories,legacy]},sort_keys=True,default=str).encode()).hexdigest()
    duplicates=[]
    for label,records in [('department',departments),('category',categories)]:
        for field in ['code','name']:
            groups={}
            for record in records:groups.setdefault((str(record.get('department_id','')),normalized(record[field])),[]).append(record)
            duplicates.extend({'kind':label,'field':field,'records':values} for values in groups.values() if len(values)>1)
    return {'version':data['version'],'plan_token':digest,'rows':rows,'summary':{status:sum(r['status']==status for r in rows) for status in ['new','existing','conflict','skipped']},'existing_counts':{'departments':len(departments),'categories':len(categories)},'existing_duplicates':duplicates,'legacy_service_categories':legacy,'notice':'Proposed, unverified, inactive placeholders only. Existing records and financial history are unchanged.'}


def imported_department(instance):
    return bool(instance.pk and AuditEvent.objects.filter(action='catalogue.placeholder.imported',object_type='catalogue.Department',object_id=str(instance.pk)).exists())


def apply(data,selected,actor,reason,plan_token=None,confirmation=''):
    authorized(actor)
    if len(reason.strip())<5 or len(reason)>255:raise ValidationError('Provide an import reason of 5–255 characters.')
    if settings.ENVIRONMENT=='production' and confirmation!=CONFIRM:raise ValidationError('Production import requires the explicit confirmation phrase: '+CONFIRM)
    if settings.ENVIRONMENT=='production' and not plan_token:raise ValidationError('Production import requires a current preview --plan-token.')
    if not selected:raise ValidationError('Select at least one placeholder to import.')
    try:
        with transaction.atomic():
            Sequence.objects.select_for_update().get_or_create(key='hospital-catalogue-import')
            report=plan(data,selected)
            if plan_token and report['plan_token']!=plan_token:raise ValidationError('Catalogue changed since preview. Preview again before importing.')
            if report['summary']['conflict'] or report['existing_duplicates']:raise ValidationError('Selected entries conflict. Nothing was imported; reconcile the preview first.')
            mapped={};created=[];run_id=report['plan_token']
            for row in report['rows']:
                if row['id']:mapped[row['key']]=row['id']
                if row['status']!='new':continue
                if row['kind']=='department':obj=Department.objects.create(code=row['code'],name=row['name'],is_active=False)
                else:
                    dep_id=mapped.get('department:'+row['department_code']) or row['department_id']
                    parent_id=mapped.get('category:'+row['department_code']+':'+row['parent_code']) or row['parent_id']
                    obj=DepartmentCategory.objects.create(department_id=dep_id,code=row['code'],name=row['name'],parent_id=parent_id,is_active=False)
                mapped[row['key']]=str(obj.pk);created.append({'key':row['key'],'id':str(obj.pk)})
                AuditEvent.record('catalogue.placeholder.imported',actor=actor,obj=obj,reason=reason,metadata={'version':data['version'],'proposal_key':row['key'],'run_id':run_id,'inactive':True})
            result={'version':data['version'],'created':created,'created_count':len(created),'existing_count':report['summary']['existing'],'skipped_count':report['summary']['skipped'],'inactive':True}
            AuditEvent.record('catalogue.import.completed',actor=actor,reason=reason,metadata={**result,'run_id':run_id})
            return result
    except IntegrityError as error:raise ValidationError('A concurrent catalogue conflict occurred. Nothing was imported; preview again.') from error
