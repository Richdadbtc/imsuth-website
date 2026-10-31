from django.contrib import admin
from apps.common.admin_utils import ReadOnlyAdmin
from .models import Patient, PatientRevision

admin.site.register(Patient, ReadOnlyAdmin)
admin.site.register(PatientRevision, ReadOnlyAdmin)
