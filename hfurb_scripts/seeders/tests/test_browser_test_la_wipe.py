from auditlog.models import LogEntry
from django.test import TestCase

from accounts.enums import (
    BROWSER_TEST_LA_GROUP_NAME,
    BROWSER_TEST_LTLA_NAMES,
    GroupType,
)
from accounts.tests.factories import GroupFactory
from deduplication.models import GuestDuplicateGroup
from hfurb_scripts.seeders.helpers import build_complete_accommodation_scenario
from hfurb_scripts.seeders.stages.seed_browser_test_la import (
    BROWSER_TEST_ID_PREFIX,
    wipe_browser_test_la_data,
)
from ontology.models import (
    Comment,
    MvAccommodation,
    MvAccommodationRequest,
    MvPerson,
    MvVolunteer,
    ReassignmentRequest,
    SafeguardingNotification,
    SafeguardingReferral,
    VisaApplication,
    VisaInformationRequest,
    VisaInformationRequestComments,
)
from ontology.tests.factories import (
    CommentFactory,
    ReassignmentRequestFactory,
    SafeguardingNotificationFactory,
    SafeguardingReferralFactory,
    VIRCommentFactory,
    VIRFactory,
)


class BrowserTestLaWipeCompletenessTestCase(TestCase):
    def setUp(self):
        GroupFactory(
            name=BROWSER_TEST_LA_GROUP_NAME,
            groupinfo__ltla_name=BROWSER_TEST_LTLA_NAMES[0],
            groupinfo__group_type=GroupType.LOCAL_AUTHORITY_BROWSER_TEST,
        )

    def test_wipe_removes_all_browser_test_records_and_leaves_other_las(self):
        ltla_name = BROWSER_TEST_LTLA_NAMES[0]
        ar = build_complete_accommodation_scenario(
            num_guests=2,
            ltla_name=ltla_name,
            id_prefix=BROWSER_TEST_ID_PREFIX,
            make_uam=False,
        )
        guest = MvPerson.objects.filter(accommodation_request=ar).first()

        SafeguardingReferralFactory(person=guest)
        SafeguardingNotificationFactory(ar=ar)
        vir = VIRFactory(
            visa_application=VisaApplication.objects.filter(ltla_name=ltla_name).first()
        )
        VIRCommentFactory(visa_information_request=vir)
        CommentFactory(attached_accommodation_request_id=ar)
        ReassignmentRequestFactory(
            accommodation_request=ar, source_ltla_name=[ltla_name]
        )
        dedup_group = GuestDuplicateGroup.objects.create()
        dedup_group.guests.set([guest])

        other_ar = build_complete_accommodation_scenario(
            num_guests=1, ltla_name="Realshire"
        )

        wipe_browser_test_la_data()

        self.assertFalse(
            MvAccommodationRequest.objects.filter(
                ltla_name__overlap=[ltla_name]
            ).exists(),
            "no accommodation request may remain in the browser test LA",
        )
        for model in [
            MvAccommodationRequest,
            MvPerson,
            MvVolunteer,
            MvAccommodation,
            VisaApplication,
        ]:
            self.assertFalse(
                model.objects.filter(
                    pk__startswith=f"{BROWSER_TEST_ID_PREFIX}-"
                ).exists(),
                f"{model.__name__} still has browser test records",
            )
        self.assertEqual(SafeguardingReferral.objects.count(), 0)
        self.assertEqual(SafeguardingNotification.objects.count(), 0)
        self.assertEqual(VisaInformationRequest.objects.count(), 0)
        self.assertEqual(VisaInformationRequestComments.objects.count(), 0)
        self.assertEqual(Comment.objects.count(), 0)
        self.assertEqual(ReassignmentRequest.objects.count(), 0)
        self.assertEqual(GuestDuplicateGroup.objects_including_archived.count(), 0)
        self.assertFalse(
            LogEntry.objects.filter(
                object_pk__startswith=f"{BROWSER_TEST_ID_PREFIX}-"
            ).exists(),
            "audit log entries for wiped records must be purged",
        )

        self.assertTrue(
            MvAccommodationRequest.objects.filter(pk=other_ar.pk).exists(),
            "records in other local authorities must be untouched",
        )
        self.assertTrue(
            MvPerson.objects.filter(accommodation_request=other_ar).exists()
        )
