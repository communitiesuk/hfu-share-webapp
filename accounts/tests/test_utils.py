from django.test import TestCase

from accounts.utils import EntraStateSerializer


class EntraStateSerializerTest(TestCase):
    def test_deserialize_success(self):
        self.assertEqual(
            EntraStateSerializer.deserialize(self, '{"test_key": "test_value"}'),
            {"test_key": "test_value"},
        )

    def test_deserialize_error(self):
        self.assertEqual(EntraStateSerializer.deserialize(self, '{"test_key"}'), {})
