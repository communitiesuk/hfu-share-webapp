from django.forms import CheckboxSelectMultiple, RadioSelect, Textarea
from django.test import TestCase

from ontology.models.VisaInformationRequest import VisaInformationRequest
from visa_applications.forms import StartVIRForm


class StartVIRFormTest(TestCase):
    def test_required_fields(self):
        form = StartVIRForm(data={})
        self.assertFalse(form.is_valid())
        self.assertIn("request_type", form.errors)
        self.assertIn("requested_check_type_id", form.errors)
        self.assertIn("comment", form.errors)
        self.assertEqual(
            form.errors["request_type"], ["You must select a request type."]
        )
        self.assertEqual(
            form.errors["requested_check_type_id"],
            ["You must select at least one check."],
        )
        self.assertEqual(
            form.errors["comment"], ["You must start a VIR with a comment."]
        )

    def test_valid_form(self):
        data = {
            "request_type": "General",
            "requested_check_type_id": ["2", "3"],
            "comment": "Test comment",
        }
        form = StartVIRForm(data=data)
        self.assertTrue(form.is_valid())
        instance = form.save(commit=False)
        self.assertIsInstance(instance, VisaInformationRequest)
        self.assertEqual(instance.request_type, "General")
        self.assertEqual(instance.requested_check_type_id, ["2", "3"])

    def test_max_length_comment(self):
        data = {
            "request_type": "General",
            "requested_check_type_id": ["2"],
            "comment": "a" * 501,
        }
        form = StartVIRForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn("comment", form.errors)
        self.assertIn(
            "Ensure this value has at most 500 characters",
            form.errors["comment"][0],
        )

    def test_invalid_request_type(self):
        data = {
            "request_type": "not_a_choice",
            "requested_check_type_id": ["2"],
            "comment": "Test",
        }
        form = StartVIRForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn("request_type", form.errors)

    def test_invalid_requested_check_type_id(self):
        data = {
            "request_type": "General",
            "requested_check_type_id": ["NOT_A_CHECK"],
            "comment": "Test",
        }
        form = StartVIRForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn("requested_check_type_id", form.errors)

    def test_field_help_text_and_widgets(self):
        form = StartVIRForm()
        self.assertEqual(
            form.fields["request_type"].help_text, "You can only select one option."
        )
        self.assertIsInstance(form.fields["request_type"].widget, RadioSelect)
        self.assertEqual(
            form.fields["requested_check_type_id"].help_text,
            "You can select more than one option.",
        )
        self.assertIsInstance(
            form.fields["requested_check_type_id"].widget, CheckboxSelectMultiple
        )
        self.assertTrue(
            form.fields["comment"].help_text.startswith("You can add a reason")
        )
        self.assertIsInstance(form.fields["comment"].widget, Textarea)
