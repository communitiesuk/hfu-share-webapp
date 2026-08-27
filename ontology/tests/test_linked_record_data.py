from django.test import SimpleTestCase

from ontology.utils import LinkedRecordData


class LinkedRecordDataTestCase(SimpleTestCase):
    def test_keeps_title_when_present(self):
        data = LinkedRecordData("guests:detail-overview", 1, "First Last")

        self.assertEqual(data.title, "First Last")

    def test_falls_back_when_title_is_none(self):
        data = LinkedRecordData("guests:detail-overview", 1, None)

        self.assertEqual(data.title, "Unknown")

    def test_falls_back_when_title_is_empty(self):
        data = LinkedRecordData("guests:detail-overview", 1, "")

        self.assertEqual(data.title, "Unknown")
