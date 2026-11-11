from django.utils import timezone

from ontology.models.DevCheckV2 import DevCheckV2
from ontology.models.MvInteraction import MvInteraction
from test_utils.base import BaseSimpleTestCase
from webapp.templatetags.timeline_extras import (
    ENHANCED_DBS_DISCLOSURE_NOTE,
    format_interaction_content,
)


class FormatInteractionContentTagTests(BaseSimpleTestCase):
    def test_generated_enhanced_dbs_note_flows_through_filter_with_disclosure(self):
        check = DevCheckV2(
            check_status=DevCheckV2.CheckStatus.PASSED,
            check_subtype=DevCheckV2.SponsorDBSPassedType.ENHANCED_DBS,
        )
        note = check.determine_interaction_notes(
            MvInteraction.InteractionContact.DBS_AND_SPONSOR_SUITABLE_CHECK,
            timezone.now(),
        )

        result = format_interaction_content(note)

        self.assertIn(ENHANCED_DBS_DISCLOSURE_NOTE, result)
        self.assertIn(f"{note}<br>{ENHANCED_DBS_DISCLOSURE_NOTE}", result)

    def test_generated_basic_dbs_note_does_not_get_disclosure(self):
        check = DevCheckV2(
            check_status=DevCheckV2.CheckStatus.PASSED,
            check_subtype=DevCheckV2.SponsorDBSPassedType.BASIC_DBS,
        )
        note = check.determine_interaction_notes(
            MvInteraction.InteractionContact.DBS_AND_SPONSOR_SUITABLE_CHECK,
            timezone.now(),
        )

        result = format_interaction_content(note)

        self.assertNotIn(ENHANCED_DBS_DISCLOSURE_NOTE, result)

    def test_enhanced_dbs_check_appends_disclosure_scotland_note_on_new_line(self):
        test_interaction_notes = "Enhanced DBS check: passed on 1 January 2024"

        result = format_interaction_content(test_interaction_notes)

        self.assertIn(ENHANCED_DBS_DISCLOSURE_NOTE, result)
        self.assertIn(
            f"Enhanced DBS check: passed on 1 January 2024<br>"
            f"{ENHANCED_DBS_DISCLOSURE_NOTE}",
            result,
        )

    def test_enhanced_dbs_check_failed_note_does_not_get_disclosure_note(self):
        test_interaction_notes = (
            "Sponsor suitable check failed on 1 January 2024. "
            "Reason: Enhanced DBS check not completed."
        )

        result = format_interaction_content(test_interaction_notes)

        self.assertNotIn(ENHANCED_DBS_DISCLOSURE_NOTE, result)
        self.assertNotIn("<br>", result)

    def test_basic_dbs_check_does_not_get_disclosure_note(self):
        test_interaction_notes = "Basic DBS check: passed on 1 January 2024"

        result = format_interaction_content(test_interaction_notes)

        self.assertNotIn(ENHANCED_DBS_DISCLOSURE_NOTE, result)
        self.assertNotIn("<br>", result)
        self.assertEqual(result, test_interaction_notes)

    def test_non_dbs_note_does_not_get_disclosure_note(self):
        test_interaction_notes = (
            "Reassignment request for "
            "[names_list]firstname1 lastname1 and firstname2 lastname2."
            "[names_list_end]"
            "from old_ltla to new_ltla."
        )

        result = format_interaction_content(test_interaction_notes)

        self.assertNotIn(ENHANCED_DBS_DISCLOSURE_NOTE, result)

    def test_interaction_content_tag_renders_names_as_list_for_reassignment_request(
        self,
    ):
        test_interaction_notes = (
            "Reassignment request for "
            "[names_list]firstname1 lastname1 and firstname2 lastname2."
            "[names_list_end]"
            "from old_ltla to new_ltla."
        )

        result = format_interaction_content(test_interaction_notes)

        expected = (
            "Reassignment request for "
            "<ul class='govuk-list govuk-list--bullet'>"
            "<li>firstname1 lastname1</li>"
            "<li>firstname2 lastname2</li>"
            "</ul>"
            "from old_ltla to new_ltla."
        )

        self.assertHTMLEqual(result, expected)

    def test_interaction_content_tag_renders_names_as_list_for_reassignment_rejected(
        self,
    ):
        test_interaction_notes = (
            "new_ltla rejected the reassignment request "
            "from old_ltla for "
            "[names_list]"
            "firstname1 lastname1 and firstname2 lastname2."
            "[names_list_end]"
            "Reason for rejecting: not in new_ltla"
        )

        result = format_interaction_content(test_interaction_notes)

        expected = (
            "new_ltla rejected the reassignment request "
            "from old_ltla for "
            "<ul class='govuk-list govuk-list--bullet'>"
            "<li>firstname1 lastname1</li>"
            "<li>firstname2 lastname2</li>"
            "</ul>"
            "Reason for rejecting: not in new_ltla"
        )

        self.assertHTMLEqual(result, expected)

    def test_interaction_content_tag_renders_names_as_list_for_reassignment_accepted(
        self,
    ):
        test_interaction_notes = (
            "new_ltla accepted the reassignment request "
            "from old_ltla for "
            "[names_list]"
            "firstname1 lastname1 and firstname2 lastname2."
            "[names_list_end]"
            "Reason for accepting: in new_ltla"
        )

        result = format_interaction_content(test_interaction_notes)

        expected = (
            "new_ltla accepted the reassignment request "
            "from old_ltla for "
            "<ul class='govuk-list govuk-list--bullet'>"
            "<li>firstname1 lastname1</li>"
            "<li>firstname2 lastname2</li>"
            "</ul>"
            "Reason for accepting: in new_ltla"
        )

        self.assertHTMLEqual(result, expected)

    def test_interaction_content_tag_names_as_list_for_any_amount_of_names(self):
        test_interaction_notes = (
            "new_ltla accepted the reassignment request from "
            "old_ltla for [names_list]firstname1 lastname1, "
            "firstname2 lastname2 and firstname3 lastname3."
            "[names_list_end] Reason for accepting: in new_ltla"
        )

        result = format_interaction_content(test_interaction_notes)

        expected = (
            "new_ltla accepted the reassignment request "
            "from old_ltla for "
            "<ul class='govuk-list govuk-list--bullet'>"
            "<li>firstname1 lastname1</li>"
            "<li>firstname2 lastname2</li>"
            "<li>firstname3 lastname3</li>"
            "</ul>"
            " Reason for accepting: in new_ltla"
        )

        self.assertHTMLEqual(result, expected)

    def test_interaction_content_tag_ignores_transforming_single_name(self):
        test_interaction_notes = (
            "new_ltla accepted the reassignment request "
            "from old_ltla for "
            "[names_list]"
            "firstname1 lastname1."
            "[names_list_end] "
            "Reason for accepting: not in new_ltla"
        )

        result = format_interaction_content(test_interaction_notes)

        expected = (
            "new_ltla accepted the reassignment request "
            "from old_ltla for "
            "firstname1 lastname1. "
            "Reason for accepting: not in new_ltla"
        )

        self.assertHTMLEqual(result, expected)

    def test_interaction_content_tag_ignores_html_in_reason_comment(self):
        test_interaction_notes = (
            "new_ltla accepted the reassignment request "
            "from old_ltla for "
            "[names_list]"
            "firstname1 lastname1 and firstname2 lastname2."
            "[names_list_end] "
            "Reason for accepting: "
            "<img src='www.image.com'>"
            "<p>p tag content</p>"
        )

        result = format_interaction_content(test_interaction_notes)

        expected = (
            "new_ltla accepted the reassignment request "
            "from old_ltla for "
            "<ul class='govuk-list govuk-list--bullet'>"
            "<li>firstname1 lastname1</li>"
            "<li>firstname2 lastname2</li>"
            "</ul> "
            "Reason for accepting: p tag content"
        )

        self.assertHTMLEqual(result, expected)

    def test_interaction_content_tag_ignores_non_flagged_lists(self):
        test_interaction_notes = (
            "new_ltla accepted the reassignment request "
            "from old_ltla for "
            "[names_list]"
            "firstname1 lastname1."
            "[names_list_end] "
            "Reason for accepting: firstname1 lastname1 "
            "and firstname2 lastname2"
        )

        result = format_interaction_content(test_interaction_notes)

        expected = (
            "new_ltla accepted the reassignment request "
            "from old_ltla for "
            "firstname1 lastname1. "
            "Reason for accepting: firstname1 lastname1 "
            "and firstname2 lastname2"
        )

        self.assertHTMLEqual(result, expected)

    def test_interaction_content_tag_ignores_flagged_lists_in_reason_comment(self):
        test_interaction_notes = (
            "new_ltla accepted the reassignment request "
            "from old_ltla for "
            "[names_list]"
            "firstname1 lastname1."
            "[names_list_end] "
            "Reason for accepting: [names_list]firstname1 "
            "lastname1 and firstname2 lastname2[names_list_end]"
        )

        result = format_interaction_content(test_interaction_notes)

        expected = (
            "new_ltla accepted the reassignment request "
            "from old_ltla for "
            "firstname1 lastname1. "
            "Reason for accepting: firstname1 lastname1 "
            "and firstname2 lastname2"
        )

        self.assertHTMLEqual(result, expected)
