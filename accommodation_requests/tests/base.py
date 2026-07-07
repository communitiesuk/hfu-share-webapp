from django.test import TestCase

from accounts.enums import GroupType
from accounts.tests.factories import GroupInfoFactory
from ontology.models import CheckType, MvAccommodationRequest
from ontology.models import MvAccommodation as MvAcc
from ontology.tests.factories import (
    DevCheckV2Factory,
    MvAccommodationFactory,
    MvGroupFactory,
    MvPersonFactory,
    MvVolunteerFactory,
    UKLocalAuthorityFactory,
)
from ontology.tests.factories import MvAccommodationRequestFactory as AccReqFactory


class AccommodationRequestsBaseTestCase(TestCase):
    def setUp(self):
        super().setUp()

        self.checks_required_req = AccReqFactory(
            title="Checks required acc req",
            checks_status=MvAccommodationRequest.ChecksStatus.CHECKS_REQUIRED,
        )
        self.pre_arrival_checks_complete_req = AccReqFactory(
            title="Pre arrival checks complete acc req",
            checks_status=(
                MvAccommodationRequest.ChecksStatus.PRE_ARRIVAL_CHECKS_COMPLETE
            ),
        )
        self.checks_partially_complete_req = AccReqFactory(
            title="Checks partially complete acc req",
            checks_status=(
                MvAccommodationRequest.ChecksStatus.CHECKS_PARTIALLY_COMPLETED
            ),
        )
        self.checks_completed_req = AccReqFactory(
            title="Checks complete acc req",
            checks_status=MvAccommodationRequest.ChecksStatus.CHECKS_COMPLETED,
        )
        self.some_checks_failed_req = AccReqFactory(
            title="Some checks failed acc req",
            checks_status=MvAccommodationRequest.ChecksStatus.SOME_CHECKS_FAILED,
        )
        self.rematch_required_req = AccReqFactory(
            title="Rematch required acc req",
            checks_status=MvAccommodationRequest.ChecksStatus.REMATCH_REQUIRED,
        )
        self.in_temp_accommodation_req = AccReqFactory(
            title="In temporary accommodation acc req",
            checks_status=(
                MvAccommodationRequest.ChecksStatus.IN_TEMPORARY_ACCOMMODATION
            ),
        )
        self.closed_left_prog_acc_req = AccReqFactory(
            title="Closed left program acc req",
            checks_status=MvAccommodationRequest.ChecksStatus.CLOSED_LEFT_PROGRAMME,
        )
        self.closed_empty_acc_req = AccReqFactory(
            title="Closed empty acc req",
            checks_status=MvAccommodationRequest.ChecksStatus.CLOSED_EMPTY,
        )
        self.closed_duplicate_acc_req = AccReqFactory(
            title="Closed duplicate acc req",
            checks_status=MvAccommodationRequest.ChecksStatus.CLOSED_DUPLICATE,
        )
        self.cancelled_acc_req = AccReqFactory(
            title="Closed left program acc req",
            checks_status=MvAccommodationRequest.ChecksStatus.CANCELLED,
        )
        self.no_guests_acc_req = AccReqFactory(
            title="No guests acc req",
            checks_status=MvAccommodationRequest.ChecksStatus.CHECKS_REQUIRED,
            person_id=[],
        )

        self.guest = MvPersonFactory(first_name="John", last_name="Smith")
        self.guest_2 = MvPersonFactory(first_name="Jane", last_name="Doe")

        self.ltla_name = "test_ltla_name"
        self.english_ltla_name = "test_english_ltla_name"
        self.welsh_ltla_name = "test_welsh_ltla_name"
        self.scottish_ltla_name = "test_scottish_ltla_name"
        self.northern_irish_ltla_name = "test_northern_irish_ltla_name"

        self.utla_name = "test_utla_name"
        self.english_utla_name = "test_english_utla_name"
        self.welsh_utla_name = "test_welsh_utla_name"
        self.scottish_utla_name = "test_scottish_utla_name"
        self.northern_irish_utla_name = "test_northern_irish_utla_name"

        self.accommodation_one = MvAccommodationFactory(
            full_address="accommodation one, city a",
            is_available_for_rematch=True,
            ltla_name=self.ltla_name,
            utla_name=self.utla_name,
            is_principal=True,
        )
        self.accommodation_two = MvAccommodationFactory(
            full_address="accommodation two, city b",
            is_available_for_rematch=True,
            accommodation_type=MvAcc.AccommodationType.TEMPORARY_ACCOMMODATION,
            ltla_name=self.ltla_name,
            utla_name=self.utla_name,
            is_principal=True,
        )

        self.accomodation_three = MvAccommodationFactory(
            full_address="accommodation three, city c",
            is_available_for_rematch=False,
            ltla_name=self.ltla_name,
            utla_name=self.utla_name,
            is_principal=True,
        )

        self.la = GroupInfoFactory(
            ltla_name=self.ltla_name,
            utla_name=self.utla_name,
        )

        self.english_la = GroupInfoFactory(
            group_type=GroupType.LOCAL_AUTHORITY,
            da_name="England",
            ltla_name=self.english_ltla_name,
            utla_name=self.english_utla_name,
        )

        self.welsh_la = GroupInfoFactory(
            group_type=GroupType.LOCAL_AUTHORITY,
            da_name="Wales",
            is_utla=False,
            ltla_name=self.welsh_ltla_name,
            utla_name=self.welsh_utla_name,
        )

        self.scottish_la = GroupInfoFactory(
            group_type=GroupType.LOCAL_AUTHORITY,
            da_name="Scotland",
            ltla_name=self.scottish_ltla_name,
            utla_name=self.scottish_utla_name,
        )

        self.northern_irish_la = GroupInfoFactory(
            group_type=GroupType.LOCAL_AUTHORITY,
            da_name="Northern Ireland",
            ltla_name=self.northern_irish_ltla_name,
            utla_name=self.northern_irish_utla_name,
        )

        self.one_guest_acc_req = AccReqFactory(
            title="One guest acc req",
            checks_status=MvAccommodationRequest.ChecksStatus.CHECKS_REQUIRED,
            accommodation_id=[self.accommodation_one],
            number_of_people=1,
            person_id=[self.guest.pk],
            ltla_name=[self.ltla_name],
            utla_name=[self.utla_name],
        )
        self.multiple_guests_acc_req = AccReqFactory(
            title="Multiple guests acc req",
            checks_status=MvAccommodationRequest.ChecksStatus.CHECKS_REQUIRED,
            accommodation_id=[self.accommodation_one],
            number_of_people=2,
            person_id=[self.guest.pk, self.guest_2.pk],
            ltla_name=[self.ltla_name],
            utla_name=[self.utla_name],
        )

        self.sponsor_1 = MvVolunteerFactory(
            first_name="Sponsor", last_name="1", is_principal=True
        )
        self.sponsor_2 = MvVolunteerFactory(
            first_name="Sponsor", last_name="2", is_principal=True
        )
        self.sponsor_3 = MvVolunteerFactory(
            first_name="Sponsor", last_name="3", is_principal=True
        )
        self.active_host = MvVolunteerFactory(
            first_name="Active", last_name="Host", is_principal=True
        )
        self.dup_sponsor = MvVolunteerFactory(
            first_name="Dup", last_name="Sponsor", is_principal=False
        )
        self.group = MvGroupFactory(title="Test group")

        self.all_active_sponsors_req = AccReqFactory(
            title="All active sponsors acc req",
            checks_status=MvAccommodationRequest.ChecksStatus.CHECKS_REQUIRED,
            accommodation_id=[self.accommodation_one],
            sponsor_id=[
                self.sponsor_1.pk,
                self.sponsor_2.pk,
                self.sponsor_3.pk,
                self.dup_sponsor.pk,
            ],
            sponsor_withdrawn=[],
            group=self.group,
        )
        self.null_withdrawn_sponsors_req = AccReqFactory(
            title="All active sponsors acc req",
            checks_status=MvAccommodationRequest.ChecksStatus.CHECKS_REQUIRED,
            accommodation_id=[self.accommodation_one],
            sponsor_id=[
                self.sponsor_1.pk,
                self.sponsor_2.pk,
                self.sponsor_3.pk,
                self.dup_sponsor.pk,
            ],
            sponsor_withdrawn=None,
            group=self.group,
        )
        self.partial_active_sponsor_req = AccReqFactory(
            title="Partial active sponsors acc req",
            checks_status=MvAccommodationRequest.ChecksStatus.CHECKS_REQUIRED,
            accommodation_id=[self.accommodation_one],
            sponsor_id=[
                self.sponsor_1.pk,
                self.sponsor_2.pk,
                self.sponsor_3.pk,
                self.dup_sponsor.pk,
            ],
            sponsor_withdrawn=[self.sponsor_1.pk],
            group=self.group,
        )
        self.one_active_sponsor_req = AccReqFactory(
            title="Exactly one active sponsors acc req",
            checks_status=MvAccommodationRequest.ChecksStatus.CHECKS_REQUIRED,
            accommodation_id=[self.accommodation_one],
            sponsor_id=[
                self.sponsor_1.pk,
                self.sponsor_2.pk,
                self.sponsor_3.pk,
            ],
            sponsor_withdrawn=[self.sponsor_1.pk, self.sponsor_2.pk],
            group=self.group,
        )
        self.no_active_sponsors_req = AccReqFactory(
            title="No active sponsors acc req",
            checks_status=MvAccommodationRequest.ChecksStatus.CHECKS_REQUIRED,
            accommodation_id=[self.accommodation_one],
            sponsor_id=[self.sponsor_1.pk, self.sponsor_2.pk, self.sponsor_3.pk],
            sponsor_withdrawn=[self.sponsor_1.pk, self.sponsor_2.pk, self.sponsor_3.pk],
            group=self.group,
        )
        self.active_sponsor_from_other_la_req = AccReqFactory(
            title="No active sponsors acc req",
            checks_status=MvAccommodationRequest.ChecksStatus.CHECKS_REQUIRED,
            accommodation_id=[self.accommodation_one],
            sponsor_id=[
                self.sponsor_1.pk,
                self.sponsor_2.pk,
                self.sponsor_3.pk,
                self.dup_sponsor.pk,
            ],
            sponsor_withdrawn=[],
            group=self.group,
            ltla_name=["ltla_somerset"],
            utla_name=["utla_somerset"],
        )

        self.safeguarding_checks_accomodation_request = AccReqFactory(
            title="Safeguarding checks acc req",
            checks_status=MvAccommodationRequest.ChecksStatus.CHECKS_REQUIRED,
            primary_accommodation=self.accommodation_one,
            accommodation_id=[self.accommodation_one, self.accommodation_two],
            sponsor_id=[
                self.sponsor_1.pk,
                self.sponsor_2.pk,
                self.sponsor_3.pk,
                self.dup_sponsor.pk,
            ],
            sponsor_withdrawn=[],
            active_host=self.active_host,
            group=self.group,
            number_of_people=0,
            ltla_name=["ltla_somerset"],
            utla_name=["utla_somerset"],
        )

        self.accommodation_suitable_check = DevCheckV2Factory(
            check_type=CheckType.objects.get(id=CheckType.Id.ACCOMM_SUITABLE),
            AR=[self.safeguarding_checks_accomodation_request],
        )
        self.accommodation_suitable_check.accommodation.set([self.accommodation_one])

        self.accommodation_exists_check = DevCheckV2Factory(
            check_type=CheckType.objects.get(id=CheckType.Id.ACCOMM_EXISTS),
            AR=[self.safeguarding_checks_accomodation_request],
        )
        self.accommodation_exists_check.accommodation.set([self.accommodation_one])

        self.sponsor_dbs_check = DevCheckV2Factory(
            check_type=CheckType.objects.get(id=CheckType.Id.SPONSOR_DBS),
        )
        self.sponsor_dbs_check.sponsor.set([self.sponsor_1, self.dup_sponsor])

        self.active_host_dbs_check = DevCheckV2Factory(
            check_type=CheckType.objects.get(id=CheckType.Id.SPONSOR_DBS),
        )
        self.active_host_dbs_check.sponsor.set([self.active_host, self.dup_sponsor])

        self.guest_has_arrived_check = DevCheckV2Factory(
            id="guest_has_arrived_check_1",
            check_type=CheckType.objects.get(id=CheckType.Id.GROUP_ARRIVED),
        )
        self.guest_has_arrived_check_2 = DevCheckV2Factory(
            id="guest_has_arrived_check_2",
            check_type=CheckType.objects.get(id=CheckType.Id.GROUP_ARRIVED),
        )

        self.guest_has_arrived_check.group.set([self.group])
        self.guest_has_arrived_check_2.group.set([self.group])

        self.cannot_move_guests_acc_reqs = [
            self.closed_left_prog_acc_req,
            self.cancelled_acc_req,
            self.closed_duplicate_acc_req,
        ]

        self.closed_acc_reqs = [
            self.closed_left_prog_acc_req,
            self.closed_empty_acc_req,
            self.closed_duplicate_acc_req,
            self.cancelled_acc_req,
        ]

        self.closed_can_be_reopened_reqs = [
            self.closed_left_prog_acc_req,
            self.cancelled_acc_req,
        ]

        self.closed_cannot_be_reopened_reqs = [
            self.closed_empty_acc_req,
            self.closed_duplicate_acc_req,
        ]

        self.open_acc_reqs = [
            self.checks_required_req,
            self.pre_arrival_checks_complete_req,
            self.checks_partially_complete_req,
            self.checks_completed_req,
            self.some_checks_failed_req,
            self.rematch_required_req,
            self.in_temp_accommodation_req,
            self.all_active_sponsors_req,
            self.null_withdrawn_sponsors_req,
            self.partial_active_sponsor_req,
            self.one_active_sponsor_req,
            self.no_active_sponsors_req,
            self.safeguarding_checks_accomodation_request,
        ]

        self.accommodations_available_for_rematch = [
            self.accommodation_one,
            self.accommodation_two,
        ]

        self.accommodations_not_available_for_rematch = [self.accomodation_three]

        self.temporary_accommodations_available_for_rematch = [
            self.accommodation_two,
        ]

        self.sponsor_accommodations_available_for_rematch = [
            self.accommodation_one,
        ]


class SafeguardingChecksBaseTestCase(TestCase):
    def setUp(self):
        super().setUp()

        self.uklocalauthority = UKLocalAuthorityFactory(
            id="test-ltla", ltla_name="Test LTLA"
        )

        self.sponsor = MvVolunteerFactory(first_name="Sponsor", last_name="1")
        self.active_host = MvVolunteerFactory(first_name="Active", last_name="Host")
        self.guest = MvPersonFactory()
        self.accommodation = MvAccommodationFactory()
        self.group = MvGroupFactory()
        self.ar = AccReqFactory(
            accommodation_id=[self.accommodation.pk],
            primary_accommodation=self.accommodation,
            primary_sponsor=self.sponsor,
            group=self.group,
            person_id=[self.guest.id],
            ltla_code_id=[self.uklocalauthority.id],
        )
        self.guest.accommodation_request = self.ar
        self.guest.save()

        # related AR + guest
        self.guest2 = MvPersonFactory()
        self.group2 = MvGroupFactory()
        self.ar2 = AccReqFactory(
            accommodation_id=[self.accommodation.pk],
            primary_accommodation=self.accommodation,
            primary_sponsor=self.sponsor,
            group=self.group2,
            person_id=[self.guest2.id],
        )
        self.guest2.accommodation_request = self.ar2
        self.guest2.save()

        self.sponsor2 = MvVolunteerFactory(first_name="Sponsor", last_name="2")
        self.active_host2 = MvVolunteerFactory(first_name="Active", last_name="Host")
        self.guest3 = MvPersonFactory()
        self.accommodation2 = MvAccommodationFactory()
        self.group3 = MvGroupFactory()
        self.ar3 = AccReqFactory(
            accommodation_id=[self.accommodation2.pk],
            primary_accommodation=self.accommodation2,
            primary_sponsor=self.sponsor2,
            group=self.group3,
            person_id=[self.guest3.id],
        )
        self.guest3.accommodation_request = self.ar3
        self.guest3.save()
