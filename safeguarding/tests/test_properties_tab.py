import http.client

from django.urls import reverse

from accounts.enums import GroupType
from accounts.tests.base import TestSessionTokenMixin
from ontology.tests.factories import (
    MvAccommodationFactory,
    MvAccommodationRequestFactory,
    MvPersonFactory,
    MvVolunteerFactory,
    SafeguardingReferralFactory,
    SponsorshipCertificationFormFactory,
    VisaApplicationFactory,
)
from safeguarding.tests.base import SafeguardingBaseTestCase
from user_management.tests.base import (
    UserGroup,
    get_admin_user,
    get_da_user,
    get_la_user,
    get_mhclg_user,
    get_service_support_user,
    get_ukvi_user,
    get_user_with_groups,
    get_user_with_no_access,
)


class SafeguardingDetailPropertiesViewTests(
    TestSessionTokenMixin, SafeguardingBaseTestCase
):
    def setUp(self):
        super().setUp()

        self.uan = VisaApplicationFactory(
            ltla_name="ltla_somerset",
            application_unique_application_number="123456",
            title="Visa Application for Guest",
        )

        self.uam = SponsorshipCertificationFormFactory(reference="uam-111-111")

        self.guest = MvPersonFactory(
            id="person-123-321",
            first_name="Guest",
            last_name="Person",
            sponsorship_certification_number_id=[self.uam.pk],
        )

        self.sponsor = MvVolunteerFactory(
            id="sponsor-123-123", first_name="LA Sponsor", last_name="Spon"
        )
        self.host = MvVolunteerFactory(
            id="sponsor-321-123", first_name="Host", last_name="Host"
        )

        self.accommodation = MvAccommodationFactory(
            id="acc-222-111",
            ltla_name="ltla_somerset",
            full_address="Somerset accommodation",
        )
        self.accommodation.hosts.set([self.host.id])

        self.ar = MvAccommodationRequestFactory(
            title="Guest Person to Somerset accom",
            ltla_name=["ltla_somerset"],
            utla_name=["utla_somerset"],
            primary_accommodation=self.accommodation,
            person_id=[self.guest.id],
            number_of_people=1,
            primary_sponsor=self.sponsor,
            sponsor_id=[self.sponsor.id],
            active_host=self.host,
            unique_application_number=[
                self.uan.application_unique_application_number,
            ],
            sponsorship_certification_number_id=[self.uam.pk],
        )

        self.safeguarding_referral = SafeguardingReferralFactory(person=self.guest)

        self.guest.accommodation_request = self.ar
        self.guest.save()

    def test_dev_user_is_granted_access(self):
        user = get_admin_user()
        self.client.force_login(user)

        kwargs = {
            "pk": self.guest.pk,
            "referral_id": self.safeguarding_referral.pk,
        }
        response = self.client.get(
            reverse("safeguarding:detail-properties", kwargs=kwargs)
        )

        self.assertEqual(response.status_code, http.client.OK)

    def test_user_without_access_is_denied_access(self):
        user = get_user_with_no_access()
        self.client.force_login(user)

        kwargs = {
            "pk": self.guest.pk,
            "referral_id": self.safeguarding_referral.pk,
        }
        response = self.client.get(
            reverse("safeguarding:detail-properties", kwargs=kwargs)
        )

        self.assertEqual(response.status_code, http.client.NOT_FOUND)

    def test_la_user_is_denied_access(self):
        user = get_la_user()
        self.client.force_login(user)

        kwargs = {
            "pk": self.guest.pk,
            "referral_id": self.safeguarding_referral.pk,
        }
        response = self.client.get(
            reverse("safeguarding:detail-properties", kwargs=kwargs)
        )

        self.assertEqual(response.status_code, http.client.NOT_FOUND)

    def test_da_user_is_denied_access(self):
        user = get_da_user()
        self.client.force_login(user)

        kwargs = {
            "pk": self.guest.pk,
            "referral_id": self.safeguarding_referral.pk,
        }
        response = self.client.get(
            reverse("safeguarding:detail-properties", kwargs=kwargs)
        )

        self.assertEqual(response.status_code, http.client.NOT_FOUND)

    def test_la_user_outside_person_la_has_no_access(self):
        user = get_user_with_groups(
            [UserGroup(name="Lewisham", type=GroupType.LOCAL_AUTHORITY)]
        )
        self.client.force_login(user)

        kwargs = {
            "pk": self.guest.pk,
            "referral_id": self.safeguarding_referral.pk,
        }
        response = self.client.get(
            reverse("safeguarding:detail-properties", kwargs=kwargs)
        )

        self.assertEqual(response.status_code, http.client.NOT_FOUND)

    def test_mhclg_user_is_granted_access(self):
        user = get_mhclg_user()
        self.client.force_login(user)

        kwargs = {
            "pk": self.guest.pk,
            "referral_id": self.safeguarding_referral.pk,
        }
        response = self.client.get(
            reverse("safeguarding:detail-properties", kwargs=kwargs)
        )

        self.assertEqual(response.status_code, http.client.OK)

    def test_ukvi_user_is_granted_access(self):
        user = get_ukvi_user()
        self.client.force_login(user)

        kwargs = {
            "pk": self.guest.pk,
            "referral_id": self.safeguarding_referral.pk,
        }
        response = self.client.get(
            reverse("safeguarding:detail-properties", kwargs=kwargs)
        )

        self.assertEqual(response.status_code, http.client.OK)

    def test_service_support_user_is_granted_access(self):
        user = get_service_support_user()
        self.client.force_login(user)

        kwargs = {
            "pk": self.guest.pk,
            "referral_id": self.safeguarding_referral.pk,
        }
        response = self.client.get(
            reverse("safeguarding:detail-properties", kwargs=kwargs)
        )

        self.assertEqual(response.status_code, http.client.OK)

    def test_renders_properties_correctly(self):
        admin_user = get_admin_user()
        self.client.force_login(admin_user)

        self.ar.primary_accommodation = None
        self.ar.primary_sponsor = None
        self.ar.sponsor_id = []
        self.ar.save()

        kwargs = {
            "pk": self.guest.pk,
            "referral_id": self.safeguarding_referral.pk,
        }
        response = self.client.get(
            reverse("safeguarding:detail-properties", kwargs=kwargs)
        )

        # page didn't 500 due to missing linked objects
        self.assertEqual(response.status_code, http.client.OK)

        # primary_accommodation_id
        self.assertNotContains(response, "acc-222-111")
        # primary_sponsor_id
        self.assertNotContains(response, "sponsor-123-123")
