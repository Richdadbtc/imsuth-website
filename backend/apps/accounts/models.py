from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    class Role(models.TextChoices):
        SUPER_ADMIN = "super_admin", "Super Administrator"
        MANAGEMENT = "management", "Hospital Management"
        FINANCE = "finance", "Accounts / Finance"
        AUDITOR = "auditor", "Auditor"
        DEPARTMENT_SUPERVISOR = "department_supervisor", "Department Supervisor"
        FRONT_DESK = "front_desk", "Front Desk Officer"
        CASHIER = "cashier", "Cashier / PayPoint Officer"

    banned_at = models.DateTimeField(null=True, blank=True)
    deleted_at = models.DateTimeField(null=True, blank=True)
    page_access = models.JSONField(null=True,blank=True,default=None)
    role = models.CharField(max_length=32, choices=Role.choices, blank=True)
    employee_id = models.CharField(max_length=32, unique=True, null=True, blank=True)
    department = models.ForeignKey("catalogue.Department", null=True, blank=True, on_delete=models.PROTECT, related_name="staff")
    paypoint_code = models.CharField(max_length=32, blank=True)
    must_change_password = models.BooleanField(default=True)

    def save(self,*args,**kwargs):
        if self.banned_at or self.deleted_at:
            self.is_active=False
            if kwargs.get('update_fields') is not None:kwargs['update_fields']=set(kwargs['update_fields'])|{'is_active'}
        return super().save(*args,**kwargs)

    def has_paypoint_role(self, *roles):
        return self.is_active and self.role in roles


class RecoveryChallenge(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    digest = models.CharField(max_length=64, unique=True)
    expires_at = models.DateTimeField()
    consumed = models.BooleanField(default=False)


class RecoveryRateLimit(models.Model):
    key = models.CharField(max_length=64, primary_key=True)
    started_at = models.DateTimeField()
    attempts = models.PositiveIntegerField(default=0)
