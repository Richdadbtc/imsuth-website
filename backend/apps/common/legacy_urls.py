"""Bookmarks for retired server-rendered UI; never process legacy financial forms."""
from django.urls import path
from django.http import HttpResponseRedirect, JsonResponse
from django.contrib.auth.views import redirect_to_login

FINANCE={'finance','management','auditor'}
REGISTRY={'front_desk','finance','department_supervisor'}
ALL={'super_admin','finance','management','auditor','front_desk','cashier','department_supervisor'}
# name, historical path, current fragment (None = retired object-specific screen), roles
DESTINATIONS=[
 ('login','login/','',None),('password_reset','password-reset/','forgot-password',None),
 ('dashboard','','dashboard',ALL),('management-dashboard','management/','dashboard-overview-preview',FINANCE),
 ('patient-list','patients/','patient-directory',REGISTRY),('patient-create','patients/new/','patient-registration',REGISTRY),
 ('patient-detail','patients/<uuid:pk>/',None,REGISTRY),('patient-edit','patients/<uuid:pk>/edit/',None,REGISTRY),
 ('invoice-list','invoices/','billing',ALL),('invoice-create','invoices/new/','billing-create',{'front_desk','cashier','finance'}),
 ('invoice-detail','invoices/<uuid:pk>/',None,ALL),('invoice-print','invoices/<uuid:pk>/print/',None,ALL),
 ('invoice-pay','invoices/<uuid:pk>/pay/',None,{'cashier','finance'}),('billing-correction','invoices/<uuid:pk>/correct/',None,{'front_desk','cashier','finance'}),
 ('payment-detail','payments/<uuid:pk>/',None,ALL),('receipt-print','receipts/<uuid:pk>/print/',None,ALL),
 ('department-list','departments/','admin-departments',ALL),('department-detail','departments/<uuid:pk>/',None,ALL),
 ('department-create','departments/new/','admin-departments',{'super_admin','finance'}),
 ('service-list','services/','admin-services',ALL),('service-detail','services/<uuid:pk>/',None,ALL),
 ('service-create','services/new/','admin-services',{'super_admin','finance'}),
 ('tariff-list','tariffs/','admin-tariffs',ALL),('tariff-create','tariffs/new/','admin-services',{'super_admin','finance'}),
 ('profile','profile/','profile',ALL),('password_change','password-change/','change-password',ALL),
 ('staff-list','staff/','users-audit',{'super_admin'}),('finance-workspace','finance/','finance',FINANCE),('audit-log','audit/','admin-audit',FINANCE),
 ('notification-list','notifications/','notifications',ALL),('notification-detail','notifications/<int:pk>/',None,ALL),
 ('notification-read','notifications/<int:pk>/read/',None,ALL),('reconciliation-import','reconciliation/import/','finance-reconciliation',FINANCE),
 ('reconciliation-detail','reconciliation/<uuid:pk>/',None,FINANCE),
]


def bookmark(fragment,roles):
    def view(request,**kwargs):
        if roles is not None:
            if not request.user.is_authenticated:return redirect_to_login(request.get_full_path(),login_url='/login/')
            if request.user.role not in roles:return JsonResponse({'detail':'Access restricted.'},status=403)
        if request.method not in {'GET','HEAD'} or fragment is None:
            return JsonResponse({'detail':'This server-rendered form/detail route was retired. Use the authenticated Revenue Control interface and API.','replacement':'/paypoint/'},status=410)
        return HttpResponseRedirect('/paypoint/'+('#'+fragment if fragment else ''))
    return view

urlpatterns=[path(route,bookmark(fragment,roles),name=name) for name,route,fragment,roles in DESTINATIONS]
