import logging

from django.conf import settings
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_not_required
from django.http import HttpRequest, HttpResponseForbidden, HttpResponseRedirect
from django.utils.http import url_has_allowed_host_and_scheme

from .authentication import Authentication
from .exceptions import FlowError
from .utils import EntraStateSerializer

serializer = EntraStateSerializer()
logger = logging.getLogger(__name__)


@login_not_required
def entra_login(request: HttpRequest):
    redirect_url = Authentication(request).get_auth_uri(
        state=serializer.serialize(next=request.GET.get("next"))
    )
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
        return HttpResponseForbidden(
            "Unable to complete authentication process. Please try to login again."
        )

    user = authenticate(request, token=token)
    if user:
        login(request, user)

        next_url = settings.LOGIN_REDIRECT_URL
        if state := request.GET.get("state"):
            candidate = serializer.deserialize(state).get("next")
            if candidate and url_has_allowed_host_and_scheme(
                candidate,
                allowed_hosts={request.get_host()},
                require_https=request.is_secure(),
            ):
                next_url = candidate

        return HttpResponseRedirect(next_url)

    return HttpResponseForbidden("You are not allowed to access this application.")
