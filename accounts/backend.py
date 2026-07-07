from django.contrib.auth.backends import ModelBackend

from .authentication import Authentication


class EntraBackend(ModelBackend):
    def authenticate(self, request, token=None, *args, **kwargs):
        if not token:
            return None

        user = Authentication(request).authenticate(token)
        # Return only if `is_active`
        if self.user_can_authenticate(user):
            return user

        return None
