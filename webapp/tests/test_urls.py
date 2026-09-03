from django.contrib.staticfiles.storage import staticfiles_storage

from test_utils.base import BaseTestCase


class FaviconAuthBypassTest(BaseTestCase):
    def test_favicon_bypasses_auth_middleware(self):
        """
        Ensure unauthenticated requests to /favicon.ico route directly to
        static files and do not trigger the MSAL authentication flow.
        """

        response = self.client.get("/favicon.ico")

        self.assertEqual(response.status_code, 302)

        # redirect should be to static asset, not login endpoint or anywhere else
        expected_static_url = staticfiles_storage.url("gds/assets/images/favicon.ico")
        self.assertEqual(response.url, expected_static_url)

        # auth flow puts some stuff into the session
        self.assertNotIn("auth_flow", self.client.session)
