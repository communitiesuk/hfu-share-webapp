from django.contrib.auth import views as auth_views
from django.urls import path

from case_management import settings

from .forms import GdsAuthForm
from .views import entra_callback, entra_login, entra_logout

app_name = "accounts"

if settings.ENTRA_ID_ENABLED:
    urlpatterns = [
        path("login", entra_login, name="login"),
        path("logout", entra_logout, name="logout"),
        path("auth_callback", entra_callback, name="callback"),
    ]

else:
    urlpatterns = [
        path(
            "accounts/login/",
            auth_views.LoginView.as_view(
                template_name="accounts/login.html", form_class=GdsAuthForm
            ),
            name="login",
        ),
        path(
            "accounts/logout/",
            auth_views.LogoutView.as_view(next_page="accounts:login"),
            name="logout",
        ),
    ]
