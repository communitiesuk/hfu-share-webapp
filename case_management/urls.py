from debug_toolbar.toolbar import debug_toolbar_urls
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from django.views.generic import TemplateView

from webapp.admin import AuditlogAdminStatsView

# Extra views added to the Django admin.
_EXTRA_ADMIN_URLS = [
    path(
        "auditlog/statistics/",
        admin.site.admin_view(AuditlogAdminStatsView.as_view()),
        name="auditlog-stats",
    ),
]

_admin_urls, _, _admin_namespace = admin.site.urls

urlpatterns = (
    [
        path("", TemplateView.as_view(template_name="base.html"), name="home"),
        path(
            "admin/",
            include((_EXTRA_ADMIN_URLS + list(_admin_urls), _admin_namespace)),
        ),
        path("", include("webapp.urls")),
        path(
            "user-management/",
            include("user_management.urls", namespace="user_management"),
        ),
        path(
            "accommodations/",
            include("accommodations.urls", namespace="accommodations"),
        ),
        path(
            "accommodation-requests/",
            include("accommodation_requests.urls", namespace="accommodation_requests"),
        ),
        path("guests/", include("guests.urls", namespace="guests")),
        path("safeguarding/", include("safeguarding.urls", namespace="safeguarding")),
        path("sponsors/", include("sponsors.urls", namespace="sponsors")),
        path("uams/", include("uams.urls", namespace="uams")),
        path(
            "visa-applications/",
            include("visa_applications.urls", namespace="visa_applications"),
        ),
        path("", include("accounts.urls", namespace="accounts")),
        path("downloads/", include("downloads.urls")),
        path(
            "reassignment-requests/",
            include("reassignment_requests.urls", namespace="reassignment_requests"),
        ),
        path(
            "review-potential-duplicate-records-manual/",
            include("deduplication.urls", namespace="deduplication"),
        ),
        path(
            "unassigned-accommodation-requests/",
            include(
                "unassigned_accommodation_requests.urls",
                namespace="unassigned_accommodation_requests",
            ),
        ),
    ]
    + debug_toolbar_urls()
    + static("assets/", document_root="static/gds/assets")
)
