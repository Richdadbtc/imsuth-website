from rest_framework import serializers

from apps.catalogue.models import Department, Service, TariffVersion
from apps.registry.models import Patient


class PatientSerializer(serializers.ModelSerializer):
    duplicate_warning = serializers.SerializerMethodField()

    class Meta:
        model = Patient
        fields = ("id", "patient_id", "first_name", "middle_name", "last_name", "date_of_birth", "approximate_age", "sex", "phone", "email", "address", "emergency_contact", "status", "created_at", "duplicate_warning")
        read_only_fields = ("id", "patient_id", "created_at", "duplicate_warning")

    def get_duplicate_warning(self, obj) -> bool:
        return obj.potential_duplicates().exists()

    def create(self, validated_data):
        validated_data["registered_by"] = self.context["request"].user
        return super().create(validated_data)


class DepartmentSerializer(serializers.ModelSerializer):
    def validate(self,data):
        from apps.catalogue.catalogue_setup import imported_department
        if self.instance and not self.instance.is_active and data.get("is_active") is True and imported_department(self.instance):
            raise serializers.ValidationError("Imported placeholders require catalogue activation approval.")
        return data

    class Meta:
        model = Department
        fields = "__all__"
        read_only_fields = ("id", "created_at", "updated_at")


class ServiceSerializer(serializers.ModelSerializer):
    def validate(self,data):
        from apps.catalogue.models import DepartmentCategory
        from apps.catalogue.catalogue_setup import normalized
        department=data.get('department',getattr(self.instance,'department',None))
        active=data.get('is_active',getattr(self.instance,'is_active',True))
        changes_catalogue=not self.instance or any(k in data for k in ['department','category','is_active'])
        if active and changes_catalogue and department:
            if not department.is_active:raise serializers.ValidationError('Services in inactive departments must remain inactive.')
            category=data.get('category',getattr(self.instance,'category',''))
            candidates=[c for c in DepartmentCategory.objects.filter(department=department) if normalized(c.name)==normalized(category)]
            if candidates and not any(c.is_active for c in candidates):raise serializers.ValidationError('This placeholder category requires activation approval before use on active services.')
        return data

    class Meta:
        model = Service
        fields = "__all__"
        read_only_fields = ("id", "created_at", "updated_at")


class TariffVersionSerializer(serializers.ModelSerializer):
    class Meta:
        model = TariffVersion
        fields = "__all__"
        read_only_fields = ("id", "approved_by", "proposed_by", "is_approved", "created_at", "updated_at")
