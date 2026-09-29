from django.test import SimpleTestCase, TestCase

from .mixins import FakerMixin


class BaseTestCase(FakerMixin, TestCase):
    pass


class BaseSimpleTestCase(FakerMixin, SimpleTestCase):
    pass
