from ontology.utils import build_full_name
from test_utils.base import BaseSimpleTestCase


class TestBuildFullName(BaseSimpleTestCase):
    def test_returns_full_name_when_both_parts_are_there(self):
        assert build_full_name("Jane", "Doe") == "Jane Doe"

    def test_returns_first_name_when_only_first_name(self):
        assert build_full_name("Jane", None) == "Jane"

    def test_returns_family_name_when_only_family_name(self):
        assert build_full_name(None, "Doe") == "Doe"

    def test_returns_uknown_when_both_none(self):
        assert build_full_name(None, None) == "Unknown"

    def test_returns_uknown_when_both_empty(self):
        assert build_full_name("", "") == "Unknown"

    def test_returns_default_value_when_both_none_and_default_given(self):
        assert build_full_name(None, None, "Not known") == "Not known"

    def test_returns_none_when_both_none_and_default_given_is_none(self):
        assert build_full_name(None, None, None) is None
