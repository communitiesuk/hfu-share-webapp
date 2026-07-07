import http.client

from django.urls import reverse

from accounts.tests.base import TestSessionTokenMixin
from ontology.tests.base import UamsBaseTestCase
from ontology.tests.factories import (
    MvAccommodationRequestFactory,
)
from user_management.tests.base import (
    get_admin_user,
    get_da_user,
    get_mhclg_user,
    get_service_support_user,
    get_ukvi_user,
)


class UamDetailLinkedRecordsViewTests(TestSessionTokenMixin, UamsBaseTestCase):
    def setUp(self):
        super().setUp()

        self.ar = MvAccommodationRequestFactory(
            id="1234567890",
            sponsorship_certification_number_id=[self.ltla_one_a_uam.reference],
            ltla_name=[self.ltla_one_a_name],
            title="Accommodation Request for LTLA One A UAM",
        )

        self.ar_other_la = MvAccommodationRequestFactory(
            id="abcdefghij",
            sponsorship_certification_number_id=[self.ltla_one_a_uam.reference],
            ltla_name=[self.ltla_one_b_name],
            title="Accommodation Request for LTLA One B UAM",
        )

    def test_dev_user_is_granted_access(self):
        user = get_admin_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "uams:detail-linked-records",
                kwargs={"pk": self.ltla_one_a_uam.pk},
            )
        )

        self.assertEqual(response.status_code, http.client.OK)

    def test_user_without_access_to_requested_uam_is_denied_access(self):
        la_user = self.ltla_two_a_user
        self.client.force_login(la_user)

        response = self.client.get(
            reverse(
                "uams:detail-linked-records",
                kwargs={"pk": self.ltla_one_a_uam.pk},
            )
        )

        self.assertEqual(response.status_code, http.client.NOT_FOUND)

    def test_la_user_is_granted_access(self):
        user = self.ltla_one_a_user
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "uams:detail-linked-records",
                kwargs={"pk": self.ltla_one_a_uam.pk},
            )
        )

        self.assertEqual(response.status_code, http.client.OK)

    def test_da_user_is_granted_access(self):
        user = get_da_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "uams:detail-linked-records",
                kwargs={"pk": self.scotland_da_uam.pk},
            )
        )

        self.assertEqual(response.status_code, http.client.OK)

    def test_mhclg_user_is_granted_access(self):
        user = get_mhclg_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "uams:detail-linked-records",
                kwargs={"pk": self.ltla_one_a_uam.pk},
            )
        )

        self.assertEqual(response.status_code, http.client.OK)

    def test_ukvi_user_is_granted_access(self):
        user = get_ukvi_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "uams:detail-linked-records",
                kwargs={"pk": self.ltla_one_a_uam.pk},
            )
        )

        self.assertEqual(response.status_code, http.client.OK)

    def test_service_support_user_is_granted_access(self):
        user = get_service_support_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "uams:detail-linked-records",
                kwargs={"pk": self.ltla_one_a_uam.pk},
            )
        )

        self.assertEqual(response.status_code, http.client.OK)

    def test_admin_user_sees_all_ar_linked_records(self):
        user = get_admin_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "uams:detail-linked-records",
                kwargs={"pk": self.ltla_one_a_uam.pk},
            )
        )

        self.assertContains(response, "Accommodation requests")
        self.assertContains(response, self.ar.title)
        self.assertContains(response, self.ar_other_la.title)

    def test_ltla_one_a_user_sees_correct_ar_linked_records(self):
        user = self.ltla_one_a_user
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "uams:detail-linked-records",
                kwargs={"pk": self.ltla_one_a_uam.pk},
            )
        )

        self.assertContains(response, "Accommodation requests")
        self.assertContains(response, self.ar.title)
        self.assertNotContains(response, self.ar_other_la.title)
