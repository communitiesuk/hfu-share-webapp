from django.test import TestCase, override_settings

from deduplication.models import (
    _db_values,
    _in_memory_values,
    log_dedup_event,
    log_dedup_persistence_check,
)
from ontology.tests.factories import MvAccommodationRequestFactory
from webapp.enhanced_sentry_logging import (
    _as_sentry_log_value,
    _values_match_or_both_empty,
)


class ValuesMatchOrBothEmptyTestCase(TestCase):
    def test_equal_values_match(self):
        self.assertTrue(_values_match_or_both_empty("x", "x"))
        self.assertTrue(_values_match_or_both_empty([1, 2], [1, 2]))
        self.assertTrue(_values_match_or_both_empty(0, 0))

    def test_none_and_empty_treated_as_equal(self):
        # An empty ArrayField can come back from the DB as either [] or None;
        # they should not be reported as a persistence mismatch.
        self.assertTrue(_values_match_or_both_empty(None, []))
        self.assertTrue(_values_match_or_both_empty([], None))
        self.assertTrue(_values_match_or_both_empty(None, None))
        self.assertTrue(_values_match_or_both_empty("", None))

    def test_different_values_do_not_match(self):
        self.assertFalse(_values_match_or_both_empty("x", "y"))
        self.assertFalse(_values_match_or_both_empty([1], [2]))
        self.assertFalse(_values_match_or_both_empty([1], [1, 2]))

    def test_falsy_non_empty_values_are_not_treated_as_empty(self):
        self.assertFalse(_values_match_or_both_empty(0, None))
        self.assertFalse(_values_match_or_both_empty(None, 0))
        self.assertFalse(_values_match_or_both_empty(False, None))
        self.assertFalse(_values_match_or_both_empty(None, False))
        self.assertFalse(_values_match_or_both_empty(0, []))


class AsSentryLogValueTestCase(TestCase):
    def test_primitives_pass_through(self):
        self.assertEqual(_as_sentry_log_value(True), True)
        self.assertEqual(_as_sentry_log_value(42), 42)
        self.assertEqual(_as_sentry_log_value(3.14), 3.14)

    def test_none_becomes_string_none(self):
        self.assertEqual(_as_sentry_log_value(None), "None")

    def test_collections_are_stringified(self):
        self.assertEqual(_as_sentry_log_value(["a", "b"]), "['a', 'b']")


@override_settings(ENHANCED_DEDUPLICATION_LOGGING=True)
class InMemoryValuesTestCase(TestCase):
    def test_copies_list_so_later_in_place_mutation_does_not_alter_it(
        self,
    ):
        ar = MvAccommodationRequestFactory(sponsor_id=["sponsor-1", "sponsor-2"])
        before = _in_memory_values(ar, "sponsor_id")
        ar.sponsor_id.remove("sponsor-1")
        self.assertEqual(before["sponsor_id"], ["sponsor-1", "sponsor-2"])
        self.assertEqual(ar.sponsor_id, ["sponsor-2"])

    def test_captures_non_list_values(self):
        ar = MvAccommodationRequestFactory(title="hello")
        before = _in_memory_values(ar, "title")
        ar.title = "changed"
        self.assertEqual(before["title"], "hello")


@override_settings(ENHANCED_DEDUPLICATION_LOGGING=False)
class HelpersAreNoOpWhenFlagIsOffTestCase(TestCase):
    # With ENHANCED_DEDUPLICATION_LOGGING=False
    # the helpers must not run any DB query or coercion.

    def test_in_memory_values_returns_empty_dict(self):
        ar = MvAccommodationRequestFactory(sponsor_id=["sponsor-1"])
        self.assertEqual(_in_memory_values(ar, "sponsor_id"), {})

    def test_db_values_returns_empty_dict(self):
        ar = MvAccommodationRequestFactory()
        self.assertEqual(_db_values(ar, "sponsor_id"), {})

    def test_log_helpers_do_not_raise(self):
        log_dedup_event("test.flag_off", group_id=1, sponsor_pk="sponsor-1")
        log_dedup_persistence_check(
            "test.flag_off",
            changes={"sponsor_id": (["sponsor-1"], ["sponsor-2"])},
            before={"sponsor_id": ["sponsor-1"]},
        )
