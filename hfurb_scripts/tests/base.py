from django.test import tag

from accounts.tests.base import TestSessionTokenMixin
from test_utils.base import BaseTestCase


@tag("scripts")
class BaseScriptTestCase(BaseTestCase): ...


@tag("scripts")
class BaseScriptTestCaseWithSession(TestSessionTokenMixin, BaseTestCase): ...
