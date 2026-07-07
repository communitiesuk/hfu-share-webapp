from django.test import TestCase

from ontology.models import MvAccommodationRequest
from webapp.constants import (
    GREEN,
    GREY,
    LIGHT_BLUE,
    ORANGE,
    PINK,
    PURPLE,
    RED,
    TURQUOISE,
    YELLOW,
    status_to_tag_colour,
)
from webapp.templatetags.safeguarding_checks_extras import (
    safeguarding_check_status_to_tag_colour,
    safeguarding_check_status_to_tag_text,
)


class StatusToTagColourTest(TestCase):
    def assert_status_to_tag_colour(self, status_type: str, value: str, expected: str):
        self.assertEqual(status_to_tag_colour(status_type, value), expected)

    def test_no_status_to_tag_colour(self):
        self.assert_status_to_tag_colour("visa_status", None, GREY)
        self.assert_status_to_tag_colour("accommodation_checks_status", None, GREY)
        self.assert_status_to_tag_colour("accommodation_request_status", None, GREY)
        self.assert_status_to_tag_colour("sponsor_withdrawn", None, RED)
        self.assert_status_to_tag_colour("test", None, None)

    def test_status_to_tag_colour(self):
        self.assert_status_to_tag_colour("visa_status", "Arrived", GREEN)
        self.assert_status_to_tag_colour("visa_status", "Issued", TURQUOISE)
        self.assert_status_to_tag_colour("visa_status", "Confirmed", LIGHT_BLUE)
        self.assert_status_to_tag_colour("visa_status", "Flow Visa Pending", PURPLE)
        self.assert_status_to_tag_colour("visa_status", "Pending", YELLOW)
        self.assert_status_to_tag_colour("visa_status", "Refused", RED)
        self.assert_status_to_tag_colour("visa_status", "Withdrawn", GREY)
        self.assert_status_to_tag_colour("visa_status", "Lapsed", ORANGE)
        self.assert_status_to_tag_colour("visa_status", "Missing Application", PINK)
        self.assert_status_to_tag_colour("visa_status", "Some issued", GREY)

        self.assert_status_to_tag_colour(
            "accommodation_checks_status",
            MvAccommodationRequest.ChecksStatus.CHECKS_REQUIRED,
            YELLOW,
        )
        self.assert_status_to_tag_colour(
            "accommodation_checks_status",
            MvAccommodationRequest.ChecksStatus.PRE_ARRIVAL_CHECKS_COMPLETE,
            PINK,
        )
        self.assert_status_to_tag_colour(
            "accommodation_checks_status",
            MvAccommodationRequest.ChecksStatus.CHECKS_COMPLETED,
            GREEN,
        )
        self.assert_status_to_tag_colour(
            "accommodation_checks_status",
            MvAccommodationRequest.ChecksStatus.CHECKS_PARTIALLY_COMPLETED,
            LIGHT_BLUE,
        )
        self.assert_status_to_tag_colour(
            "accommodation_checks_status",
            MvAccommodationRequest.ChecksStatus.SOME_CHECKS_FAILED,
            RED,
        )
        self.assert_status_to_tag_colour(
            "accommodation_checks_status",
            MvAccommodationRequest.ChecksStatus.CLOSED_DUPLICATE,
            ORANGE,
        )
        self.assert_status_to_tag_colour(
            "accommodation_checks_status",
            MvAccommodationRequest.ChecksStatus.CLOSED_LEFT_PROGRAMME,
            ORANGE,
        )
        self.assert_status_to_tag_colour(
            "accommodation_checks_status",
            MvAccommodationRequest.ChecksStatus.CLOSED_EMPTY,
            ORANGE,
        )
        self.assert_status_to_tag_colour(
            "accommodation_checks_status",
            MvAccommodationRequest.ChecksStatus.REMATCH_REQUIRED,
            YELLOW,
        )
        self.assert_status_to_tag_colour(
            "accommodation_checks_status",
            MvAccommodationRequest.ChecksStatus.IN_TEMPORARY_ACCOMMODATION,
            GREY,
        )
        self.assert_status_to_tag_colour(
            "accommodation_checks_status",
            MvAccommodationRequest.ChecksStatus.CANCELLED,
            GREY,
        )

        self.assert_status_to_tag_colour(
            "accommodation_request_status",
            MvAccommodationRequest.Status.ACCOMMODATION_ASSIGNED,
            GREEN,
        )
        self.assert_status_to_tag_colour(
            "accommodation_request_status",
            MvAccommodationRequest.Status.MISSING_ACCOMMODATION,
            ORANGE,
        )
        self.assert_status_to_tag_colour(
            "accommodation_request_status",
            MvAccommodationRequest.Status.ARRIVAL_CONFIRMED,
            YELLOW,
        )


class SafeguardingTemplateTagTest(TestCase):
    def test_safeguarding_check_templatetag_colour_handles_sentence_case_value(self):
        self.assertEqual(safeguarding_check_status_to_tag_colour("Passed"), GREEN)

    def test_safeguarding_check_templatetag_colour_handles_all_caps_value(self):
        self.assertEqual(safeguarding_check_status_to_tag_colour("PASSED"), GREEN)

    def test_safeguarding_check_templatetag_colour_converts_space_to_underscore(self):
        self.assertEqual(
            safeguarding_check_status_to_tag_colour("IN PROGRESS"), LIGHT_BLUE
        )

    def test_safeguarding_check_templatetag_colour_handles_existing_underscore(self):
        self.assertEqual(
            safeguarding_check_status_to_tag_colour("IN_PROGRESS"), LIGHT_BLUE
        )

    def test_safeguarding_check_templatetag_colour_handles_no_longer_required_case(
        self,
    ):
        self.assertEqual(
            safeguarding_check_status_to_tag_colour("No longer required"), GREY
        )

    def test_safeguarding_check_templatetag_colour_handles_unexpected_value(self):
        self.assertEqual(
            safeguarding_check_status_to_tag_colour("unexpected value"), GREY
        )

    def test_safeguarding_check_templatetag_label_handles_sentence_case_value(self):
        self.assertEqual(
            safeguarding_check_status_to_tag_text("Passed"), "Checks complete: Passed"
        )

    def test_safeguarding_check_templatetag_label_handles_all_caps_value(self):
        self.assertEqual(
            safeguarding_check_status_to_tag_text("PASSED"), "Checks complete: Passed"
        )

    def test_safeguarding_check_templatetag_label_converts_space_to_underscore(self):
        self.assertEqual(
            safeguarding_check_status_to_tag_text("IN PROGRESS"), "Checks in progress"
        )

    def test_safeguarding_check_templatetag_label_handles_existing_underscore(self):
        self.assertEqual(
            safeguarding_check_status_to_tag_text("IN_PROGRESS"), "Checks in progress"
        )

    def test_safeguarding_check_templatetag_label_handles_no_longer_required_case(self):
        self.assertEqual(
            safeguarding_check_status_to_tag_text("No longer required"),
            "Checks complete: No longer needed",
        )

    def test_safeguarding_check_templatetag_label_handles_unexpected_value(self):
        self.assertEqual(
            safeguarding_check_status_to_tag_text("unexpected value"),
            "Check status unavailable",
        )
