from django.contrib import admin
from django.urls import include, path
from django.views.generic import TemplateView
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

from apps.common.views import HealthView

urlpatterns = [
    path("paypoint/index.html", TemplateView.as_view(template_name="paypoint/index.html")),
    path("paypoint/", TemplateView.as_view(template_name="paypoint/index.html"), name="revenue-control"),
    path("health/", HealthView.as_view(), name="health"),
    path("admin/", admin.site.urls),
    path("api/v1/", include(("apps.common.api_urls", "api"), namespace="api")),
    path("paypoint/api/v1/", include(("apps.common.api_urls", "api"), namespace="paypoint-api")),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="api-docs"),
]

from django.contrib.staticfiles.urls import staticfiles_urlpatterns
urlpatterns += staticfiles_urlpatterns()
urlpatterns += [path("", include("apps.common.legacy_urls"))]
