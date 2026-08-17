from django.urls import path

from . import views

app_name = "webapp"
urlpatterns = [
    path(
        "accessibility-statement",
        views.AccessibilityStatementView.as_view(),
        name="accessibility-statement",
    ),
    path(
        "cookies",
        views.CookiesView.as_view(),
        name="cookies",
    ),
    path(
        "landing-page",
        views.LandingPageView.as_view(),
        name="landing-page",
    ),
    path("csp-report/", views.CSPReportView.as_view(), name="csp-report"),
    path("favicon.ico", views.favicon_redirect, name="favicon_redirect"),
]
