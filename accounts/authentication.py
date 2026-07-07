import datetime
from http import HTTPStatus
from typing import Optional
from urllib import parse

import msal
import requests
from django.conf import settings
from django.contrib.auth.models import AbstractBaseUser, AnonymousUser
from django.http import HttpRequest

from .exceptions import EntraAuthException, FlowError, TokenError
from .models import User


class Authentication:
    """
    Class to interface with `msal` package and execute authentication process.
    """

    def __init__(self, request: HttpRequest):
        self.request = request
        self.graph_user_endpoint = settings.ENTRA_AUTH.get(
            "GRAPH_USER_ENDPOINT", "https://graph.microsoft.com/v1.0/me"
        )
        self.auth_flow_session_key = "auth_flow"
        self._cache = msal.SerializableTokenCache()
        self._msal_app = None

        # Eagerly load the claims from the session
        self.claims = self.request.session.get("id_token_claims", {})

    def get_auth_uri(self, state: Optional[str] = None) -> str:
        redirect_uri = self._get_redirect_uri()
        flow = self.msal_app.initiate_auth_code_flow(
            scopes=settings.ENTRA_AUTH["SCOPES"],
            redirect_uri=redirect_uri,
            state=state,
        )
        self.request.session[self.auth_flow_session_key] = flow
        return flow["auth_uri"]

    def get_token_from_flow(self):
        flow = self.request.session.pop(self.auth_flow_session_key, {})
        if not flow:
            raise FlowError("Flow cannot be extracted from session")

        token = self.msal_app.acquire_token_by_auth_code_flow(
            auth_code_flow=flow, auth_response=self.request.GET
        )
        if "error" in token:
            raise TokenError(token["error"], token["error_description"])
        self._save_cache()
        self.request.session["id_token_claims"] = token["id_token_claims"]
        return token

    def get_token_from_cache(self, username: Optional[str] = None):
        accounts = self.msal_app.get_accounts(username)
        if not accounts:
            return None

        # Will return `None` if CCA cannot retrieve or generate new token
        token_result = self.msal_app.acquire_token_silent(
            scopes=settings.ENTRA_AUTH["SCOPES"], account=accounts[0]
        )
        self._save_cache()

        # `acquire_token_silent` doesn't always return ID token/ID token claims
        # https://github.com/AzureAD/microsoft-authentication-library-for-python/issues/139
        if token_result and token_result.get("id_token_claims"):
            self.request.session["id_token_claims"] = token_result["id_token_claims"]
        return token_result

    def authenticate(self, token: dict):
        user_profile = {}
        if fields := settings.ENTRA_AUTH.get("EXTRA_FIELDS"):
            user_profile = self._get_user_profile(token["access_token"], fields=fields)
        else:
            user_profile = self._get_user_profile(token["access_token"])

        # https://learn.microsoft.com/en-us/entra/external-id/customers/concept-user-attributes
        # https://learn.microsoft.com/en-us/entra/identity-platform/id-token-claims-reference
        attributes = {**user_profile, **token.get("id_token_claims", {})}

        if not self._is_tenant_allowed(attributes):
            return AnonymousUser()

        try:
            user = User.objects.get(
                entra_tid=attributes["tid"], entra_oid=attributes["oid"]
            )
            self._update_user(user, **attributes)
        except User.DoesNotExist:
            # Password is set to a weird value here
            user = User.objects.create_user(**self._user_mapping(**attributes))
            user.save()

        return user

    def get_logout_uri(self) -> str:
        authority = settings.ENTRA_AUTH["AUTHORITY"]
        _query_params = {
            "post_logout_redirect_uri": settings.ENTRA_AUTH.get("LOGOUT_URI"),
            "logout_hint": self.claims.get("login_hint"),
        }
        query_params = {k: v for k, v in _query_params.items() if v}
        return f"{authority}/oauth2/v2.0/logout?{parse.urlencode(query_params)}"

    @property
    def user_is_authenticated(self) -> bool:
        if not self.request.user.is_authenticated:
            return False

        # Exception to support super users on the admin panel (having no claims)
        if isinstance(self.request.user, User) and self.request.user.is_superuser:
            return True

        # Check the ID token is still valid in the first instance
        now = datetime.datetime.now(datetime.timezone.utc).timestamp()
        if now < self.claims.get("exp", 0):
            return True

        # Otherwise try refresh the token
        return self.get_token_from_cache(self.request.user.get_username()) is not None

    @property
    def msal_app(self):
        if self._msal_app is None:
            self._msal_app = msal.ConfidentialClientApplication(
                client_id=settings.ENTRA_AUTH["CLIENT_ID"],
                client_credential=settings.ENTRA_AUTH["CLIENT_SECRET"],
                authority=settings.ENTRA_AUTH["AUTHORITY"],
                token_cache=self.cache,
            )
        return self._msal_app

    @property
    def cache(self):
        if self.request.session.get("token_cache"):  # pragma: no branch
            self._cache.deserialize(self.request.session["token_cache"])
        return self._cache

    def _get_user_profile(self, token: str, fields: Optional[dict] = None):
        params = {"$select": ",".join(fields)} if fields else None
        response = requests.get(
            self.graph_user_endpoint,
            headers={"Authorization": f"Bearer {token}"},
            params=params,
            timeout=10,
        )
        if response.ok:
            return response.json()

        if response.status_code == HTTPStatus.UNAUTHORIZED:
            error = response.json()["error"]
            raise TokenError(message=error["code"], description=error["message"])

        raise EntraAuthException("An error occurred while contacting the graph API")

    def _update_user(self, user: AbstractBaseUser, **fields):
        for field, value in self._user_mapping(**fields).items():
            setattr(user, field, value)
        user.save()

    def _user_mapping(self, **attributes):
        return {
            "first_name": attributes["givenName"],
            "last_name": attributes["surname"],
            "email": attributes["mail"],
            "username": attributes["preferred_username"],
            "entra_oid": attributes["oid"],
            "entra_tid": attributes["tid"],
        }

    def _save_cache(self):
        if self.cache.has_state_changed:
            self.request.session["token_cache"] = self.cache.serialize()

    def _get_redirect_uri(self) -> str:
        redirect_uri = settings.ENTRA_AUTH["REDIRECT_URI"]
        if not isinstance(redirect_uri, str):
            # Resolve the URI when it's a reverse_lazy callable
            redirect_uri = str(redirect_uri)
        if not redirect_uri.startswith("http"):
            redirect_uri = self.request.build_absolute_uri(redirect_uri)
        return redirect_uri

    def _is_tenant_allowed(self, attributes) -> bool:
        return attributes["tid"] in settings.ENTRA_AUTH.get("ALLOWED_TENANTS", [])
