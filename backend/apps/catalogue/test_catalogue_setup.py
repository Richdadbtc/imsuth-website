import io
import json
from django.test import TestCase, override_settings
from django.core.exceptions import ValidationError, PermissionDenied
from django.core.management import call_command
from rest_framework.test import APIClient
from apps.accounts.models import User
from apps.auditlog.models import AuditEvent
from apps.common.models import Sequence
from apps.operations.services import decide_approval
from apps.operations.models import ApprovalRequest
from .models import Department, DepartmentCategory, Service, TariffVersion
from .catalogue_setup import proposal, plan, apply, key, csv_export, CONFIRM
from .catalogue_approvals import request_activation, decide_activation


class CatalogueSetupTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.maker=User.objects.create_user(username='catalogue-maker',role='super_admin')
        cls.reviewer=User.objects.create_user(username='catalogue-reviewer',role='super_admin')
        cls.finance=User.objects.create_user(username='catalogue-finance',role='finance')

    def setUp(self):
        self.data=proposal(); self.keys=[key(r) for r in self.data['entries']]

    def load(self):
        return apply(self.data,self.keys,self.maker,'Verified proposal import')

    def test_master_is_nonbillable_and_idempotent(self):
        self.assertEqual(len(self.data['entries']),52)
        self.assertEqual(self.load()['created_count'],52)
        self.assertEqual(Department.objects.count(),40)
        self.assertEqual(DepartmentCategory.objects.count(),12)
        self.assertFalse(Department.objects.filter(is_active=True).exists())
        self.assertFalse(DepartmentCategory.objects.filter(is_active=True).exists())
        self.assertFalse(Service.objects.exists());self.assertFalse(TariffVersion.objects.exists())
        self.assertEqual(self.load()['created_count'],0)
        self.assertEqual(AuditEvent.objects.filter(action='catalogue.placeholder.imported').count(),52)

    def test_report_and_dry_run_are_read_only(self):
        before=AuditEvent.objects.count()
        for mode in ['--report','--dry-run']:
            output=io.StringIO();call_command('seed_hospital_catalogue',mode,stdout=output)
            self.assertTrue(json.loads(output.getvalue())['read_only'])
        self.assertFalse(Department.objects.exists());self.assertEqual(AuditEvent.objects.count(),before);self.assertFalse(Sequence.objects.exists())

    def test_existing_identity_code_and_status_are_preserved(self):
        dep=Department.objects.create(code='OLD-RAD',name='Radiology & Imaging',is_active=True)
        self.assertEqual(self.load()['created_count'],51)
        dep.refresh_from_db();self.assertEqual(dep.code,'OLD-RAD');self.assertTrue(dep.is_active)
        self.assertEqual(dep.catalogue_categories.count(),3)

    def test_conflict_rolls_back_entire_import(self):
        before=AuditEvent.objects.count()
        Department.objects.create(code='RAD',name='Unrelated department')
        with self.assertRaises(ValidationError):self.load()
        self.assertEqual(Department.objects.count(),1);self.assertFalse(DepartmentCategory.objects.exists());self.assertEqual(AuditEvent.objects.count(),before)

    def test_normalized_database_duplicates_block_import(self):
        Department.objects.create(code='FIRST',name='Existing name')
        Department.objects.create(code='SECOND',name='EXISTING NAME')
        self.assertTrue(plan(self.data)['existing_duplicates'])
        with self.assertRaises(ValidationError):self.load()

    def test_child_requires_selected_parent_and_department(self):
        with self.assertRaises(ValidationError):apply(self.data,['category:RAD:XRAY'],self.maker,'Selective import')
        result=apply(self.data,['department:RAD','category:RAD:IMAGING','category:RAD:XRAY'],self.maker,'Selective import')
        self.assertEqual(result['created_count'],3)
        self.assertEqual(DepartmentCategory.objects.get(code='XRAY').parent.code,'IMAGING')

    def test_stale_plan_cannot_be_applied(self):
        token=plan(self.data)['plan_token'];Department.objects.create(code='ZZZ',name='Unrelated existing unit')
        with self.assertRaises(ValidationError):apply(self.data,self.keys,self.maker,'Verified proposal import',plan_token=token)
        self.assertEqual(Department.objects.count(),1)

    @override_settings(ENVIRONMENT='production')
    def test_production_requires_confirmation_and_token(self):
        with self.assertRaises(ValidationError):self.load()
        with self.assertRaises(ValidationError):apply(self.data,self.keys,self.maker,'Verified proposal import',confirmation=CONFIRM)
        result=apply(self.data,self.keys,self.maker,'Verified proposal import',confirmation=CONFIRM,plan_token=plan(self.data)['plan_token'])
        self.assertEqual(result['created_count'],52)

    def test_csv_roundtrip_rejects_financial_and_privilege_columns(self):
        self.assertEqual(proposal(csv_export(self.data))['entries'],self.data['entries'])
        for text in ['kind,code,name,department_code,parent_code,amount\ndepartment,ZZZ,Unit,,,100', 'kind,code,name,department_code,parent_code\ndepartment,ZZZ,=SUM(A1),,']:
            with self.assertRaises(ValidationError):proposal(text)

    def test_cycle_duplicate_and_oversized_csv_rejected(self):
        for text in ['kind,code,name,department_code,parent_code\ncategory,R,Root,RAD,R',csv_export(self.data)+csv_export(self.data).split('\n')[1]+'\n','x'*524289]:
            with self.assertRaises(ValidationError):proposal(text)

    def test_only_active_superadministrator_can_import(self):
        with self.assertRaises(PermissionDenied):apply(self.data,self.keys,self.finance,'Verified proposal import')
        self.maker.is_active=False;self.maker.save()
        with self.assertRaises(PermissionDenied):self.load()

    def test_activation_requires_independent_review_and_orders_dependencies(self):
        self.load();dep=Department.objects.get(code='RAD');cats=list(dep.catalogue_categories.all())
        ids=request_activation(['category:'+str(c.pk) for c in cats]+['department:'+str(dep.pk)],self.maker,'Hospital approval requested')
        with self.assertRaises(PermissionDenied):decide_activation(ids,self.maker,True,'Hospital approval reviewed')
        self.assertEqual(decide_activation(ids,self.reviewer,True,'Hospital approval reviewed').__len__(),4)
        dep.refresh_from_db();self.assertTrue(dep.is_active);self.assertEqual(dep.catalogue_categories.filter(is_active=True).count(),3)
        self.assertFalse(Service.objects.exists());self.assertFalse(TariffVersion.objects.exists())

    def test_category_cannot_activate_under_inactive_department(self):
        self.load();cat=DepartmentCategory.objects.filter(parent=None).first()
        ids=request_activation(['category:'+str(cat.pk)],self.maker,'Hospital approval requested')
        with self.assertRaises(ValidationError):decide_activation(ids,self.reviewer,True,'Hospital approval reviewed')
        cat.refresh_from_db();self.assertFalse(cat.is_active)
        self.assertEqual(ApprovalRequest.objects.get(pk=ids[0]).status,'pending')

    def test_finance_cannot_bypass_catalogue_review_via_generic_approval(self):
        self.load();dep=Department.objects.first()
        ids=request_activation(['department:'+str(dep.pk)],self.maker,'Hospital approval requested')
        approval=ApprovalRequest.objects.get(pk=ids[0])
        with self.assertRaises(PermissionDenied):decide_approval(approval=approval,approver=self.finance,approved=True,reason='Hospital approval reviewed')

    def test_rejected_request_keeps_placeholder_inactive(self):
        self.load();dep=Department.objects.first();target=['department:'+str(dep.pk)]
        ids=request_activation(target,self.maker,'Hospital approval requested')
        self.assertEqual(request_activation(target,self.maker,'Hospital approval requested'),ids)
        decide_activation(ids,self.reviewer,False,'Awaiting hospital verification')
        dep.refresh_from_db();self.assertFalse(dep.is_active)

    def test_api_permissions_preview_import_and_activation_guard(self):
        client=APIClient();path='/api/v1/catalogue-setup/'
        self.assertIn(client.get(path).status_code,[401,403])
        client.force_authenticate(self.finance);self.assertEqual(client.get(path).status_code,403)
        client.force_authenticate(self.maker);preview=client.get(path);self.assertEqual(preview.status_code,200)
        payload={'selected':self.keys,'reason':'Verified proposal import','plan_token':preview.data['plan_token']}
        self.assertEqual(client.post(path+'import/',payload,format='json').status_code,400)
        payload['confirmation']=CONFIRM;result=client.post(path+'import/',payload,format='json');self.assertEqual(result.status_code,201,result.data)
        from apps.common.serializers import DepartmentSerializer
        dep=Department.objects.first();serializer=DepartmentSerializer(dep,data={'is_active':True},partial=True)
        self.assertFalse(serializer.is_valid())
        self.assertEqual(client.get(path+'history/').status_code,200)
