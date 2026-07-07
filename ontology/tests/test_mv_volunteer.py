from django.test import TestCase

from ontology.models import MvVolunteer
from ontology.tests.factories import MvVolunteerFactory


class MvVolunteerTestCase(TestCase):
    def test_should_auto_generate_id_with_correct_format_on_save(self):
        sponsor = MvVolunteer.objects.create(is_editable=True)
        sponsor.save()

        sponsor.refresh_from_db()

        self.assertRegex(
            sponsor.pk,
            r"^sponsor-[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
        )

    def test_display_link_data_creates_correct_title(self):
        sponsor = MvVolunteerFactory(
            first_name="Test", last_name="Sponsor", email="abc@example.com"
        )

        data = sponsor.display_link_data(None, None)

        self.assertEqual(data.title, "Test Sponsor (abc@example.com)")

    def test_display_link_data_with_email_but_no_name_creates_correct_title(self):
        sponsor = MvVolunteerFactory(email="abc@example.com")

        data = sponsor.display_link_data(None, None)

        self.assertEqual(data.title, "(abc@example.com)")
