from django.contrib import messages
from django.urls import reverse_lazy
from django.views.generic import CreateView, DetailView, ListView, UpdateView

from apps.accounts.models import User
from apps.auditlog.models import AuditEvent
from apps.common.ui import RoleRequiredMixin

from .forms import DepartmentForm, ServiceForm, TariffForm
from .models import Department, Service, TariffVersion

CATALOGUE_ROLES = (User.Role.SUPER_ADMIN, User.Role.FINANCE, User.Role.AUDITOR, User.Role.MANAGEMENT, User.Role.DEPARTMENT_SUPERVISOR, User.Role.FRONT_DESK, User.Role.CASHIER)


class DepartmentListView(RoleRequiredMixin, ListView):
    allowed_roles = CATALOGUE_ROLES
    model = Department
    template_name = "catalogue/department_list.html"
    context_object_name = "departments"


class DepartmentDetailView(RoleRequiredMixin, DetailView):
    allowed_roles = CATALOGUE_ROLES
    model = Department
    template_name = "catalogue/department_detail.html"
    context_object_name = "department"

    def get_queryset(self):
        return super().get_queryset().prefetch_related("services")


class DepartmentCreateView(RoleRequiredMixin, CreateView):
    allowed_roles = (User.Role.SUPER_ADMIN,)
    model = Department
    form_class = DepartmentForm
    template_name = "catalogue/catalogue_form.html"
    success_url = reverse_lazy("department-list")

    def form_valid(self, form):
        response = super().form_valid(form)
        AuditEvent.record("catalogue.department_created", actor=self.request.user, obj=self.object, request=self.request)
        messages.success(self.request, "Department created.")
        return response


class ServiceListView(RoleRequiredMixin, ListView):
    allowed_roles = CATALOGUE_ROLES
    model = Service
    template_name = "catalogue/service_list.html"
    context_object_name = "services"
    paginate_by = 25

    def get_queryset(self):
        queryset = super().get_queryset().select_related("department")
        department = self.request.GET.get("department")
        if department:
            queryset = queryset.filter(department_id=department)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["departments"] = Department.objects.filter(is_active=True)
        return context


class ServiceDetailView(RoleRequiredMixin, DetailView):
    allowed_roles = CATALOGUE_ROLES
    model = Service
    template_name = "catalogue/service_detail.html"
    context_object_name = "service"

    def get_queryset(self):
        return super().get_queryset().select_related("department").prefetch_related("tariffs")


class ServiceCreateView(RoleRequiredMixin, CreateView):
    allowed_roles = (User.Role.SUPER_ADMIN,)
    model = Service
    form_class = ServiceForm
    template_name = "catalogue/catalogue_form.html"
    success_url = reverse_lazy("service-list")

    def form_valid(self, form):
        response = super().form_valid(form)
        AuditEvent.record("catalogue.service_created", actor=self.request.user, obj=self.object, request=self.request)
        messages.success(self.request, "Service created.")
        return response


class TariffListView(RoleRequiredMixin, ListView):
    allowed_roles = CATALOGUE_ROLES
    model = TariffVersion
    template_name = "catalogue/tariff_list.html"
    context_object_name = "tariffs"
    paginate_by = 25

    def get_queryset(self):
        return super().get_queryset().select_related("service", "service__department", "approved_by")


class TariffCreateView(RoleRequiredMixin, CreateView):
    allowed_roles = (User.Role.SUPER_ADMIN, User.Role.FINANCE)
    model = TariffVersion
    form_class = TariffForm
    template_name = "catalogue/catalogue_form.html"
    success_url = reverse_lazy("tariff-list")

    def get_initial(self):
        initial = super().get_initial()
        if self.request.GET.get("service"):
            initial["service"] = self.request.GET["service"]
        return initial

    def form_valid(self, form):
        form.instance.is_approved = True
        form.instance.approved_by = self.request.user
        response = super().form_valid(form)
        AuditEvent.record("catalogue.tariff_created", actor=self.request.user, obj=self.object, request=self.request, metadata={"amount": str(self.object.amount)})
        messages.success(self.request, "Approved tariff version created. Historical versions remain unchanged.")
        return response
