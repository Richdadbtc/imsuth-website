from rest_framework.permissions import BasePermission, SAFE_METHODS

from apps.accounts.models import User


class RegistryPermission(BasePermission):
    read_roles = set(User.Role.values)
    write_roles = {User.Role.FRONT_DESK, User.Role.FINANCE, User.Role.DEPARTMENT_SUPERVISOR}

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        roles = self.read_roles if request.method in SAFE_METHODS else self.write_roles
        return request.user.role in roles


class CataloguePermission(BasePermission):
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        if request.method in SAFE_METHODS:
            return True
        return request.user.role in {User.Role.FINANCE, User.Role.SUPER_ADMIN}
