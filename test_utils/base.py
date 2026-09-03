from django.test import TestCase

from .faker import fake


class BaseTestCase(TestCase):
    def setUp(self):
        super().setUp()
        self._clear_faker_unique_cache()

    @staticmethod
    def _clear_faker_unique_cache():
        fake.unique.clear()
