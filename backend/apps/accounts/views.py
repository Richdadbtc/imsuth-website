from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView, PasswordChangeView
from django.urls import reverse_lazy
from django.views.generic import CreateView, DetailView, ListView, UpdateView

from apps.auditlog.models import AuditEvent
from apps.common.ui import RoleRequiredMixin

from .forms import ProfileForm, StaffCreateForm, StaffUpdateForm
from .models import User


class StaffLoginView(LoginView):
    template_name = "registration/login.html"

    def form_valid(self, form):
        response = super().form_valid(form)
        if self.request.POST.get("remember_me"):
            self.request.session.set_expiry(60 * 60 * 8)
        else:
            self.request.session.set_expiry(0)
        return response


class ProfileView(LoginRequiredMixin, UpdateView):
    form_class = ProfileForm
    template_name = "accounts/profile.html"
    success_url = reverse_lazy("profile")

    def get_object(self, queryset=None):
        return self.request.user

    def form_valid(self, form):
        messages.success(self.request, "Your profile was updated.")
        AuditEvent.record("account.profile_updated", actor=self.request.user, obj=self.request.user, request=self.request)
        return super().form_valid(form)


class SecurePasswordChangeView(LoginRequiredMixin, PasswordChangeView):
    template_name = "registration/password_change_form.html"
    success_url = reverse_lazy("profile")

    def form_valid(self, form):
        response = super().form_valid(form)
        self.request.user.must_change_password = False
        self.request.user.save(update_fields=("must_change_password",))
        AuditEvent.record("account.password_changed", actor=self.request.user, obj=self.request.user, request=self.request)
        messages.success(self.request, "Your password was changed securely.")
        return response


class StaffListView(RoleRequiredMixin, ListView):
    allowed_roles = (User.Role.SUPER_ADMIN,)
    model = User
    template_name = "accounts/staff_list.html"
    context_object_name = "staff"
    paginate_by = 25

    def get_queryset(self):
        queryset = super().get_queryset().select_related("department").order_by("last_name", "first_name", "username")
        query = self.request.GET.get("q", "").strip()
        if query:
            from django.db.models import Q
            queryset = queryset.filter(Q(username__icontains=query) | Q(employee_id__icontains=query) | Q(first_name__icontains=query) | Q(last_name__icontains=query))
        return queryset


class StaffCreateView(RoleRequiredMixin, CreateView):
    allowed_roles = (User.Role.SUPER_ADMIN,)
    form_class = StaffCreateForm
    template_name = "accounts/staff_form.html"
    success_url = reverse_lazy("staff-list")

    def form_valid(self, form):
        response = super().form_valid(form)
        AuditEvent.record("staff.created", actor=self.request.user, obj=self.object, request=self.request, metadata={"role": self.object.role})
        messages.success(self.request, "Staff account created. The user must change the temporary password.")
        return response


class StaffDetailView(RoleRequiredMixin, DetailView):
    allowed_roles = (User.Role.SUPER_ADMIN,)
    model = User
    template_name = "accounts/staff_detail.html"
    context_object_name = "staff_member"


class StaffUpdateView(RoleRequiredMixin, UpdateView):
    allowed_roles = (User.Role.SUPER_ADMIN,)
    model = User
    form_class = StaffUpdateForm
    template_name = "accounts/staff_form.html"

    def get_success_url(self):
        return reverse_lazy("staff-detail", kwargs={"pk": self.object.pk})

    def form_valid(self, form):
        if self.object.pk == self.request.user.pk and not form.cleaned_data.get("is_active"):
            form.add_error("is_active", "You cannot deactivate your own account.")
            return self.form_invalid(form)
        response = super().form_valid(form)
        AuditEvent.record("staff.updated", actor=self.request.user, obj=self.object, request=self.request, metadata={"role": self.object.role, "active": self.object.is_active})
        messages.success(self.request, "Staff access updated.")
        return response
