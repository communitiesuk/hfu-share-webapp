import logging

from django.conf import settings
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_not_required
from django.core.exceptions import PermissionDenied
from django.http import HttpRequest, HttpResponseRedirect
from django.utils.http import url_has_allowed_host_and_scheme

from .authentication import Authentication
from .exceptions import FlowError

LOGIN_REDIRECT_SESSION_KEY = "login_redirect_url"
logger = logging.getLogger(__name__)


def _get_safe_redirect_url(request: HttpRequest, candidate: str | None) -> str | None:
    if not candidate:
        return None

    if url_has_allowed_host_and_scheme(
        candidate,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        return candidate

    return None


@login_not_required
def entra_login(request: HttpRequest):
    next_url = request.GET.get("next")
    safe_next_url = _get_safe_redirect_url(request, next_url)
    if safe_next_url:
        request.session[LOGIN_REDIRECT_SESSION_KEY] = safe_next_url
    else:
        request.session.pop(LOGIN_REDIRECT_SESSION_KEY, None)

    redirect_url = Authentication(request).get_auth_uri()
    return HttpResponseRedirect(redirect_url)


@login_not_required
def entra_logout(request: HttpRequest):
    authentication = Authentication(request)

    logout(request)
    return HttpResponseRedirect(authentication.get_logout_uri())


@login_not_required
def entra_callback(request: HttpRequest):
    try:
        token = Authentication(request).get_token_from_flow()
    except FlowError as error:
        logger.error(error)
        request.session.flush()
        raise PermissionDenied(
            "Unable to complete the authentication process."
        ) from error

    user = authenticate(request, token=token)
    if user:
        login(request, user)

        next_url = request.session.pop(LOGIN_REDIRECT_SESSION_KEY, None)
        next_url = _get_safe_redirect_url(request, next_url)

        if not next_url:
            next_url = settings.LOGIN_REDIRECT_URL

        return HttpResponseRedirect(next_url)

    raise PermissionDenied("You are not allowed to access this application.")
