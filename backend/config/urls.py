"""Root URL routing for SlotChef API v1."""

from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

from config.views import HealthCheckView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/health", HealthCheckView.as_view(), name="health-check"),
    path("api/v1/schema/", SpectacularAPIView.as_view(), name="openapi-schema"),
    path(
        "api/v1/docs/",
        SpectacularSwaggerView.as_view(url_name="openapi-schema"),
        name="swagger-ui",
    ),
    # Domain URL modules (populated incrementally across Phases 4 and 6)
    path("api/v1/", include("apps.identity.urls")),
    path("api/v1/", include("apps.communities.urls")),
    path("api/v1/", include("apps.households.urls")),
    path("api/v1/", include("apps.cooks.urls")),
    path("api/v1/", include("apps.bookings.urls")),
    path("api/v1/", include("apps.scheduling.urls")),
    path("api/v1/", include("apps.visits.urls")),
    path("api/v1/", include("apps.finance.urls")),
    path("api/v1/", include("apps.audit.urls")),
]

