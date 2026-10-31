from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User


@admin.register(User)
class PayPointUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (("PayPoint access", {"fields": ("role", "employee_id", "department", "paypoint_code", "must_change_password")}),)
    list_display = ("username", "employee_id", "role", "department", "is_active")
    list_filter = ("role", "is_active")
