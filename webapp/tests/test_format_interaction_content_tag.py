from django.test import SimpleTestCase

from webapp.templatetags.timeline_extras import format_interaction_content


class FormatInteractionContentTagTests(SimpleTestCase):
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

        self.assertEqual(result, expected)

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

        self.assertEqual(result, expected)

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

        self.assertEqual(result, expected)

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

        self.assertEqual(result, expected)

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

        self.assertEqual(result, expected)

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

        self.assertEqual(result, expected)

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

        self.assertEqual(result, expected)

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

        self.assertEqual(result, expected)
