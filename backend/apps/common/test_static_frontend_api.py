import json

from django.test import Client, TestCase
from django.urls import reverse

from apps.accounts.models import User


class StaticFrontendSessionApiTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="static-ui-reviewer",
            password="safe-test-password",
            role=User.Role.MANAGEMENT,
            first_name="Static",
            last_name="Reviewer",
        )

    def test_session_login_dashboard_and_logout_use_json_and_csrf(self):
        client = Client(enforce_csrf_checks=True)
        session_response = client.get(reverse("api:session"))
        self.assertEqual(session_response.status_code, 200)
        self.assertFalse(session_response.json()["authenticated"])
        csrf_token = session_response.cookies["csrftoken"].value

        login_response = client.post(
            reverse("api:session-login"),
            data=json.dumps({"username": self.user.username, "password": "safe-test-password"}),
            content_type="application/json",
            HTTP_X_CSRFTOKEN=csrf_token,
        )
        self.assertEqual(login_response.status_code, 200)
        self.assertEqual(login_response.json()["user"]["role"], User.Role.MANAGEMENT)
        csrf_token = login_response.cookies["csrftoken"].value

        authenticated_session = client.get(reverse("api:session"))
        self.assertTrue(authenticated_session.json()["authenticated"])

        dashboard_response = client.get(reverse("api:dashboard-summary"))
        self.assertEqual(dashboard_response.status_code, 200)
        self.assertIn("metrics", dashboard_response.json())
        self.assertIn("recent_transactions", dashboard_response.json())

        logout_response = client.post(reverse("api:session-logout"), HTTP_X_CSRFTOKEN=csrf_token)
        self.assertEqual(logout_response.status_code, 204)

    def test_dashboard_rejects_anonymous_access(self):
        response = self.client.get(reverse("api:dashboard-summary"))
        self.assertIn(response.status_code, (401, 403))
