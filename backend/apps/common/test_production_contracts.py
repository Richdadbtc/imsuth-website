"""Deployment safety and full registered API namespace contracts."""
from pathlib import Path
from django.test import SimpleTestCase, TestCase, override_settings
from django.urls import resolve
from rest_framework.test import APIClient
from .api_urls import router
from .checks import deployment_configuration


class DeploymentChecks(SimpleTestCase):
    @override_settings(ENVIRONMENT='production', DEBUG=True, SECRET_KEY='unsafe-local',
        ALLOWED_HOSTS=['*'], CSRF_TRUSTED_ORIGINS=[], SESSION_COOKIE_SECURE=False,
        CSRF_COOKIE_SECURE=False, SECURE_SSL_REDIRECT=False, CELERY_TASK_ALWAYS_EAGER=True,
        PAYMENT_TEST_MODE=True, PASSWORD_RECOVERY_URL='http://foreign.invalid/?token=bad')
    def test_production_rejects_unsafe_defaults(self):
        ids={e.id for e in deployment_configuration(None)}
        self.assertTrue({'paypoint.E001','paypoint.E002','paypoint.E004','paypoint.E005','paypoint.E006','paypoint.E007','paypoint.E008','paypoint.E009','paypoint.E010'} <= ids)

    @override_settings(ENVIRONMENT='production', DEBUG=False, SECRET_KEY='x'*64,
        DATABASES={'default':{'ENGINE':'django.db.backends.postgresql'}},
        ALLOWED_HOSTS=['paypoint.imsuth.org'], CSRF_TRUSTED_ORIGINS=['https://paypoint.imsuth.org'],
        SESSION_COOKIE_SECURE=True, CSRF_COOKIE_SECURE=True, SECURE_SSL_REDIRECT=True,
        CELERY_TASK_ALWAYS_EAGER=False, PAYMENT_TEST_MODE=False, PASSWORD_RECOVERY_URL='')
    def test_explicit_safe_configuration_passes(self):
        self.assertEqual(deployment_configuration(None),[])

    def test_static_configuration_is_external_and_secret_files_excluded_from_image(self):
        base=Path(__file__).resolve().parent
        shell=(base/'templates/paypoint/index.html').read_text()
        self.assertNotIn('<script>window.PAYPOINT_CONFIG',shell)
        self.assertIn('static/paypoint/config.js',shell)
        backend=Path(__file__).resolve().parents[2]
        self.assertIn('deployment/secrets/',(backend/'.dockerignore').read_text())
        for stage in ('staging','production'):
            compose=(backend/f'deployment/compose.{stage}.yaml').read_text()
            self.assertIn('proxy-headers.conf:/etc/nginx/paypoint-proxy-headers.conf:ro',compose)
            self.assertIn('internal: true',compose)
            self.assertNotIn('0.0.0.0:',compose)


class ApiNamespaceContracts(TestCase):
    def test_every_registered_collection_is_available_and_private_in_both_namespaces(self):
        api=APIClient()
        for prefix,viewset,basename in router.registry:
            # Generic action-only viewsets intentionally have no collection route.
            if not hasattr(viewset, 'list'):
                continue
            for root in ('/api/v1/','/paypoint/api/v1/'):
                with self.subTest(root=root,prefix=prefix):
                    match=resolve(f'{root}{prefix}/')
                    self.assertIs(match.func.cls,viewset)
                    response=api.get(f'{root}{prefix}/')
                    self.assertIn(response.status_code,(401,403,405),response.content[:300])

    def test_all_router_actions_resolve_identically_in_both_namespaces(self):
        # Validate actual router routes rather than maintaining a second endpoint list.
        for route in router.urls:
            if route.name.endswith('-format-suffix') or not hasattr(route.callback,'actions'):
                continue
            pattern=str(route.pattern)
            if '(?P<format>' in pattern:
                continue
            import re
            relative=pattern.removeprefix('^').removesuffix('$')
            relative=re.sub(r'\(\?P<[^>]+>[^)]+\)', '00000000-0000-0000-0000-000000000001',relative)
            for root in ('/api/v1/','/paypoint/api/v1/'):
                with self.subTest(route=route.name,root=root):
                    resolved=resolve(root+relative)
                    self.assertEqual(resolved.func.actions,route.callback.actions)

    @classmethod
    def setUpTestData(cls):
        from .test_revenue_api import RevenueControlTests
        RevenueControlTests.setUpTestData.__func__(cls)

    def test_authenticated_collections_respond_without_missing_or_broken_routes(self):
        api=APIClient()
        for user in (self.admin,self.finance,self.cashier,self.supervisor):
            api.force_authenticate(user)
            for prefix,viewset,basename in router.registry:
                if not hasattr(viewset,'list'):
                    continue
                with self.subTest(role=user.role,collection=prefix):
                    response=api.get(f'/paypoint/api/v1/{prefix}/')
                    self.assertIn(response.status_code,(200,403),response.content[:300])

    def test_dashboard_and_report_contracts_return_live_results(self):
        api=APIClient();api.force_authenticate(self.finance)
        metrics=('summary','collections-by-channel','collections-by-department','payment-status','trends','alerts-summary','recent-transactions')
        for metric in metrics:
            with self.subTest(metric=metric):
                self.assertEqual(api.get(f'/paypoint/api/v1/dashboard/{metric}/').status_code,200)
        reports=('revenue','collections','departments','cashiers','channels','outstanding','settlements','reconciliation','audit','activity','patients')
        for report in reports:
            with self.subTest(report=report):
                response=api.get(f'/paypoint/api/v1/reports/{report}/')
                self.assertEqual(response.status_code,200,response.content[:300])

class HealthContract(TestCase):
    def test_database_outage_is_sanitized_and_not_cached(self):
        from unittest.mock import patch
        from django.db import DatabaseError
        with patch('apps.common.views.connection.cursor',side_effect=DatabaseError('sensitive connection information')):
            response=self.client.get('/health/')
        self.assertEqual(response.status_code,503)
        self.assertEqual(response.json(),{'status':'unavailable'})
        self.assertEqual(response['Cache-Control'],'no-store')
