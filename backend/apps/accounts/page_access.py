"""Page selections narrow role access; existing workflow permissions remain authoritative."""
import json
from pathlib import Path
from django.http import JsonResponse

PAGES=json.loads(Path(__file__).with_name('page_catalogue.json').read_text())
PERSONAL={'my-profile','change-password','help-support','help','notifications'}
ROLES={'super_admin','management','finance','auditor','department_supervisor','front_desk','cashier'}
FINANCE={'super_admin','finance','management','auditor'}
PATIENTS={'super_admin','finance','department_supervisor','front_desk','cashier'}
ALIASES={'department-management':'admin-departments','services-management':'admin-services','help':'help-support'}

def role_pages(role):
    allowed=set()
    section_roles={'dashboard':ROLES,'billing':ROLES,'patients':PATIENTS,'payments':FINANCE|{'cashier'},'finance':FINANCE,'reports':FINANCE,'administration':{'super_admin'}}
    for row in PAGES:
        section=row['section'];page=row['id']
        yes=role in section_roles.get(section,set())
        if page=='dashboard-record-payment':yes=role in {'super_admin','finance','cashier'}
        if page=='dashboard-front-desk':yes=role in {'super_admin','finance','front_desk'}
        if page=='dashboard-cashier':yes=role in {'super_admin','finance','cashier'}
        if page=='dashboard-finance':yes=role in FINANCE
        if page in {'admin-departments','admin-services'}:yes=role in ROLES
        if yes:allowed.add(page)
    return allowed

def allowed_pages(user):
    base=role_pages(user.role)
    if user.role!='super_admin' and user.page_access is not None:base &= set(user.page_access)
    return sorted(base|PERSONAL)

def can_access_page(user,page):
    return ALIASES.get(page,page) in allowed_pages(user)

# Read dependencies shared by multiple screens do not confer write access.
def resources(page):
    if page=='dashboard-record-payment':return {'record-payment','departments','services','tariffs','cash-points','cash-orders','payments','receipts'}, {'record-payment'}
    if page=='patients':return {'department-desk','departments','services','payments','receipts'}, {'department-desk'}
    if page.startswith('dashboard'):return {'dashboard','departments','payments','receipts','invoices','alerts','cash-orders','cash-points'}, set()
    if page in {'admin-departments','admin-services','billing-services','billing-tariffs','admin-tariffs'}:
        return {'departments','services','tariffs','tariff-proposals','payments','dashboard'}, {'departments','services','tariffs','tariff-proposals'}
    if page=='cash-points':return {'cash-points','cash-orders','departments','staff','users','payments'}, {'cash-points','cash-orders'}
    if page.startswith('patient-'):return {'patients','departments','invoices','payments'}, {'patients'}
    if page.startswith('billing'):return {'invoices','patients','departments','services','tariffs','payments'}, {'invoices'}
    if page.startswith('payments'):return {'payments','receipts','invoices','patients','receipt-reprints'}, {'payments','receipt-reprints','receipts'}
    if page=='alerts':return {'alerts','users','staff'}, {'alerts'}
    finance_writes={'finance-refunds':{'refunds'},'finance-reversals':{'reversals'},'finance-approvals':{'approvals'},'finance-settlements':{'settlements'},'finance-reconciliation':{'reconciliation-batches'},'finance-discrepancies':{'discrepancies'}}
    if page.startswith('reports') or page.startswith('finance'):return {'reports','payments','invoices','departments','settlements','reconciliation-batches','discrepancies','refunds','reversals','approvals','alerts','audit-events','audit-logs','staff','users','dashboard'}, finance_writes.get(page,set())
    if page in {'administration','admin-add-staff','users-audit'}:return {'staff','users','audit-logs','audit-events','departments'}, {'staff','users'}
    if page=='admin-roles':return {'roles'}, {'roles'}
    if page=='admin-catalogue-setup':return {'catalogue-setup','departments','services'}, {'catalogue-setup'}
    if page=='admin-settings':return {'settings','integrations'}, {'settings','integrations'}
    if page=='admin-notifications':return {'notifications'}, {'notifications'}
    if page=='admin-audit':return {'audit-events','audit-logs'}, set()
    return set(),set()

class PageAccessMiddleware:
    def __init__(self,get_response):self.get_response=get_response
    def __call__(self,request):
        user=getattr(request,'user',None)
        prefix=next((p for p in ['/api/v1/','/paypoint/api/v1/'] if request.path.startswith(p)),None)
        if prefix and user and user.is_authenticated and user.role!='super_admin' and user.page_access is not None:
            resource=request.path[len(prefix):].split('/')[0]
            personal={'session','profile','help','support-tickets','attachments','inbox','capabilities','notifications'}
            readable=set();writable=set()
            for page in allowed_pages(user):
                read,write=resources(page);readable|=read;writable|=write
            allowed=readable if request.method in {'GET','HEAD','OPTIONS'} else writable
            if resource not in personal and resource not in allowed:
                return JsonResponse({'detail':'Your administrator has not granted access to this area.','status':403},status=403)
        return self.get_response(request)
