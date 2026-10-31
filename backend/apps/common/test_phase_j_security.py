"""Phase J bounded-query, isolation, CSRF and private evidence regressions."""
from django.test import TestCase
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIClient
from apps.payments.models import Payment
from apps.catalogue.models import Department
from . import test_revenue_api as fixtures

class PhaseJSecurityPerformance(TestCase):
    @classmethod
    def setUpTestData(cls):
        fixtures.RevenueControlTests.setUpTestData.__func__(cls)
        for n in range(35):
            Payment.objects.create(invoice=cls.invoice,reference=f'J-PAGE-{n:03}',idempotency_key=f'J-PAGE-{n}',channel='pos',amount='100',initiated_by=cls.cashier)
            Department.objects.create(code=f'JP{n}',name=f'Pagination {n:03}')
    def setUp(self):
        self.api=APIClient();self.api.force_authenticate(self.finance)
    def test_transaction_pages_have_bounded_queries_and_search(self):
        path='/api/v1/dashboard/recent-transactions/';counts=[]
        for size in (1,25):
            with CaptureQueriesContext(connection) as queries:
                response=self.api.get(path,{'page_size':size})
                self.assertEqual(response.status_code,200,response.data)
                self.assertEqual(len(response.data['results']),size)
            counts.append(len(queries))
        self.assertLessEqual(counts[1],counts[0]+1,counts)
        first=self.api.get(path,{'page_size':10}).data;second=self.api.get(path,{'page_size':10,'page':2}).data
        self.assertEqual(first['count'],36)
        self.assertTrue(set(x['id'] for x in first['results']).isdisjoint(x['id'] for x in second['results']))
        self.assertEqual(self.api.get(path,{'search':'J-PAGE-007'}).data['count'],1)
        self.assertEqual(self.api.get(path,{'search':'NOTFOUND'}).data['count'],0)
        self.assertEqual(self.api.get(path,{'status':'invented'}).status_code,400)
        self.assertEqual(self.api.get(path,{'search':'x'*161}).status_code,400)
    def test_department_paging_and_server_filter(self):
        result=self.api.get('/api/v1/departments/',{'page_size':10,'page':2,'ordering':'name'})
        self.assertEqual(result.status_code,200,result.data)
        self.assertEqual(result.data['count'],37);self.assertEqual(len(result.data['results']),10)
        self.assertEqual(self.api.get('/api/v1/departments/',{'search':'Pagination 007'}).data['count'],1)
        self.api.force_authenticate(self.supervisor)
        self.assertEqual(self.api.get('/api/v1/departments/').data['count'],1)
    def evidence_path(self):
        result=self.api.post(f'/api/v1/cash-points/{self.point.pk}/collections/',{'payment':str(self.payment.pk),'evidence_reference':'Synthetic attachment test'},format='json')
        self.assertEqual(result.status_code,201,result.data)
        return f"/api/v1/cash-points/{self.point.pk}/collections/{result.data['id']}/attachment/"
    def test_private_attachment_validation_download_and_immutability(self):
        path=self.evidence_path()
        self.assertEqual(self.api.post(path,{'file':SimpleUploadedFile('evil.html',b'<script>alert(1)</script>','text/html')}).status_code,400)
        self.assertEqual(self.api.post(path,{'file':SimpleUploadedFile('large.pdf',b'%PDF-'+b'x'*(2*1024*1024),'application/pdf')}).status_code,400)
        content=b'%PDF-1.4\nSynthetic test evidence only\n%%EOF'
        self.assertEqual(self.api.post(path,{'file':SimpleUploadedFile('synthetic.pdf',content,'application/pdf')}).status_code,201)
        download=self.api.get(path);self.assertEqual(download.content,content)
        self.assertEqual(download['X-Content-Type-Options'],'nosniff');self.assertIn('no-store',download['Cache-Control']);self.assertIn('attachment;',download['Content-Disposition'])
        self.assertEqual(self.api.post(path,{'file':SimpleUploadedFile('again.pdf',content)}).status_code,400)
        self.api.force_authenticate(self.cashier);self.assertEqual(self.api.get(path).status_code,403)
        self.api.force_authenticate(None);self.assertIn(self.api.get(path).status_code,(401,403))
    def test_session_mutations_require_csrf(self):
        client=APIClient(enforce_csrf_checks=True);client.force_login(self.finance)
        result=client.post('/api/v1/alerts/',{'alert_type':'unmatched_payment','description':'Synthetic'},format='json')
        self.assertEqual(result.status_code,403);self.assertIn('CSRF',str(result.data))
