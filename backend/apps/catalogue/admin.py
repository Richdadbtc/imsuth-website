from django.contrib import admin
from apps.common.admin_utils import ReadOnlyAdmin
from .models import Department, Service, TariffVersion, DepartmentCategory

admin.site.register(Department, ReadOnlyAdmin)
admin.site.register(Service, ReadOnlyAdmin)
admin.site.register(TariffVersion, ReadOnlyAdmin)

admin.site.register(DepartmentCategory, ReadOnlyAdmin)
