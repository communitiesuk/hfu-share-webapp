from unittest.mock import patch

from django.test import TestCase

from webapp.notify import send_email


class TestSendEmailWithoutApiKey(TestCase):
    @patch("webapp.notify.notify_client", None)
    def test_send_email_raises_when_notify_client_is_none(self):
        with self.assertRaises(RuntimeError) as error:
            send_email("test@example.com", "template-id", None)

        self.assertIn("NOTIFY_API_KEY is not set", str(error.exception))
