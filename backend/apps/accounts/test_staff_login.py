from django.test import TestCase
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
User=get_user_model()

class StaffLoginTests(TestCase):
    def setUp(self):
        self.admin=User.objects.create_user(username='login-admin',role='super_admin',is_superuser=True)
        self.client=APIClient();self.client.force_authenticate(self.admin)
    def create_staff(self,password):
        return self.client.post('/api/v1/users/',{'username':'PriscaEzeTest','role':'cashier','password':password,'is_active':True},format='json')
    def signin(self,username,password):
        client=APIClient()
        return client.post('/api/v1/session/login/',{'username':username,'password':password},format='json')
    def test_created_user_can_login_with_exact_password_and_capitalization_difference(self):
        password='  Synthetic-Staff-Login-2030!  '
        result=self.create_staff(password);self.assertEqual(result.status_code,201,result.data)
        user=User.objects.get(pk=result.data['id'])
        self.assertTrue(user.check_password(password))
        self.assertFalse(user.check_password(password.strip()))
        self.assertNotIn('password',result.data)
        self.assertTrue(result.data['has_usable_password'])
        self.assertEqual(self.signin('PRISCAEZETEST',password).status_code,200)
        self.assertEqual(self.signin('PriscaEzeTest',password).status_code,200)
        self.assertEqual(self.signin('PRISCAEZETEST',password.strip()).status_code,400)
    def test_missing_password_does_not_create_an_unusable_account(self):
        result=self.client.post('/api/v1/users/',{'username':'NoPasswordTest','role':'cashier'},format='json')
        self.assertEqual(result.status_code,400,result.data)
        self.assertFalse(User.objects.filter(username='NoPasswordTest').exists())
    def test_reset_existing_password_makes_the_account_usable(self):
        user=User.objects.create_user(username='OldUnusableTest',role='cashier')
        user.set_unusable_password();user.save()
        password='Synthetic-New-Login-2030!'
        result=self.client.patch(f'/api/v1/users/{user.pk}/',{'password':password},format='json')
        self.assertEqual(result.status_code,200,result.data)
        self.assertTrue(result.data['has_usable_password'])
        self.assertEqual(self.signin(user.username,password).status_code,200)
    def test_inactive_wrong_password_and_ambiguous_case_stay_denied(self):
        password='Synthetic-New-Login-2030!'
        User.objects.create_user(username='CaseUserTest',password=password,role='cashier')
        User.objects.create_user(username='caseusertest',password=password,role='cashier')
        self.assertEqual(self.signin('CASEUSERTEST',password).status_code,400)
        self.assertEqual(self.signin('CaseUserTest',password).status_code,200)
        user=User.objects.get(username='CaseUserTest');user.is_active=False;user.save()
        self.assertEqual(self.signin(user.username,password).status_code,400)
        self.assertEqual(self.signin('caseusertest','Wrong-Synthetic-Password').status_code,400)
