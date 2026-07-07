from django.test import TestCase

from ontology.models import MvPerson
from ontology.tests.factories import MvPersonFactory, SafeguardingReferralFactory


class SafeguardingReferralTestCase(TestCase):
    def test_get_person_works_fetches_related_person(self):
        person = MvPersonFactory()
        safeguarding_referral = SafeguardingReferralFactory(person=person)

        retrieved_person = safeguarding_referral.get_person()
        self.assertEqual(person, retrieved_person)

    def test_get_person_handles_related_person_being_none(self):
        safeguarding_referral = SafeguardingReferralFactory(person=None)

        retrieved_person = safeguarding_referral.get_person()
        self.assertEqual(None, retrieved_person)

    def test_get_person_handles_related_person_not_existing(self):
        # Intentionally not using the MvPersonFactory here so that we don't save to
        # the DB. This is testing a scenario we saw in prod where a referral had a FK
        # to a person, but no person with that key could be found in the MvPerson table
        person = MvPerson(id="1234")
        safeguarding_referral = SafeguardingReferralFactory(person=person)

        retrieved_person = safeguarding_referral.get_person()

        self.assertFalse(MvPerson.objects.filter(id=person.id).exists())
        self.assertEqual(None, retrieved_person)
