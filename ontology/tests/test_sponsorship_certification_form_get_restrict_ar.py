from ontology.tests.base import LocalAuthorityBaseTestCaseMixin
from ontology.tests.factories import (
    MvAccommodationRequestFactory,
    SponsorshipCertificationFormFactory,
)


class SponsorshipCertificationFormGetRestrictArTests(LocalAuthorityBaseTestCaseMixin):
    def setUp(self):
        super().setUp()

        # UAM with two ARs (one ltla_one_a_name, one ltla_one_b_name)
        self.uam_with_two_ars = SponsorshipCertificationFormFactory(
            reference="SCF001",
            ltla_name=[self.ltla_one_a_name],
        )
        self.ar_ltla_one_a_name = MvAccommodationRequestFactory(
            id="AR001",
            sponsorship_certification_number_id=[
                self.uam_with_two_ars.reference,
            ],
            ltla_name=[self.ltla_one_a_name],
        )
        self.ar_ltla_one_b_name = MvAccommodationRequestFactory(
            id="AR002",
            sponsorship_certification_number_id=[
                self.uam_with_two_ars.reference,
            ],
            ltla_name=[self.ltla_one_b_name],
        )

        # UAM with only one AR from ltla_one_a_name
        self.uam_with_ar_from_one_ltla_one_a = SponsorshipCertificationFormFactory(
            reference="SCF002",
            ltla_name=[self.ltla_one_a_name],
        )
        self.ar_ltla_one_a_name_2 = MvAccommodationRequestFactory(
            id="AR003",
            sponsorship_certification_number_id=[
                self.uam_with_ar_from_one_ltla_one_a.reference,
            ],
            ltla_name=[self.ltla_one_a_name],
        )

        # UAM with one AR from ltla_one_b_name
        self.uam_with_ar_from_one_ltla_one_b = SponsorshipCertificationFormFactory(
            reference="SCF003",
            ltla_name=[self.ltla_one_b_name],
        )
        self.ar_ltla_one_b_name_2 = MvAccommodationRequestFactory(
            id="AR004",
            sponsorship_certification_number_id=[
                self.uam_with_ar_from_one_ltla_one_b.reference,
            ],
            ltla_name=[self.ltla_one_b_name],
        )

        # UAM with no ARs
        self.uam_with_no_ars = SponsorshipCertificationFormFactory(
            reference="SCF004",
            ltla_name=[self.ltla_one_a_name],
        )

    def test_admin_user_gets_all_ars_for_uam_with_two_ars(self):
        admin_user = self.ltla_user_dev

        uam_with_two_ars = (
            self.uam_with_two_ars.get_accommodation_requests_restrict_for_user(
                admin_user
            )
        )

        ar_ids = [ar.id for ar in uam_with_two_ars]
        self.assertIn("AR001", ar_ids)
        self.assertIn("AR002", ar_ids)
        self.assertEqual(len(ar_ids), 2)

    def test_admin_user_gets_all_ars_for_uam_with_ar_from_one_ltla_one_a(self):
        admin_user = self.ltla_user_dev
        tested_uam = self.uam_with_ar_from_one_ltla_one_a

        uam_with_ar_from_one_ltla_one_a = (
            tested_uam.get_accommodation_requests_restrict_for_user(admin_user)
        )

        ar_ids = [ar.id for ar in uam_with_ar_from_one_ltla_one_a]
        self.assertIn("AR003", ar_ids)
        self.assertEqual(len(ar_ids), 1)

    def test_admin_user_gets_all_ars_for_uam_with_ar_from_one_ltla_one_b(self):
        admin_user = self.ltla_user_dev
        tested_uam = self.uam_with_ar_from_one_ltla_one_b

        ars = tested_uam.get_accommodation_requests_restrict_for_user(admin_user)

        ar_ids = [ar.id for ar in ars]

        self.assertIn("AR004", ar_ids)
        self.assertEqual(len(ar_ids), 1)

    def test_admin_user_gets_all_ars_for_uam_with_uam_with_no_ars(self):
        admin_user = self.ltla_user_dev
        tested_uam = self.uam_with_no_ars

        ars = tested_uam.get_accommodation_requests_restrict_for_user(admin_user)

        ar_ids = [ar.id for ar in ars]

        self.assertEqual(len(ar_ids), 0)

    def test_ltla_one_a_user_gets_correct_ars_for_uam_with_two_ars(self):
        tested_uam = self.uam_with_two_ars

        ars = tested_uam.get_accommodation_requests_restrict_for_user(
            self.ltla_one_a_user
        )

        ar_ids = [ar.id for ar in ars]

        self.assertIn("AR001", ar_ids)
        self.assertNotIn("AR002", ar_ids)
        self.assertEqual(len(ar_ids), 1)

    def test_ltla_one_a_user_gets_correct_ars_for_uam_with_ar_from_one_ltla_one_a(self):
        tested_uam = self.uam_with_ar_from_one_ltla_one_a

        ars = tested_uam.get_accommodation_requests_restrict_for_user(
            self.ltla_one_a_user
        )

        ar_ids = [ar.id for ar in ars]

        self.assertIn("AR003", ar_ids)
        self.assertEqual(len(ar_ids), 1)

    def test_ltla_one_a_user_gets_correct_ars_for_uam_with_ar_from_one_ltla_one_b(self):
        tested_uam = self.uam_with_ar_from_one_ltla_one_b

        ars = tested_uam.get_accommodation_requests_restrict_for_user(
            self.ltla_one_a_user
        )

        ar_ids = [ar.id for ar in ars]

        self.assertEqual(len(ar_ids), 0)

    def test_ltla_one_a_user_gets_correct_ars_for_uam_with_no_ars(self):
        tested_uam = self.uam_with_no_ars

        ars = tested_uam.get_accommodation_requests_restrict_for_user(
            self.ltla_one_a_user
        )

        ar_ids = [ar.id for ar in ars]

        self.assertEqual(len(ar_ids), 0)

    def test_ltla_one_b_user_gets_correct_ars_for_uam_with_two_ars(self):
        tested_uam = self.uam_with_two_ars
        ars = tested_uam.get_accommodation_requests_restrict_for_user(
            self.ltla_one_b_user
        )

        ar_ids = [ar.id for ar in ars]

        self.assertNotIn("AR001", ar_ids)
        self.assertIn("AR002", ar_ids)
        self.assertEqual(len(ar_ids), 1)

    def test_ltla_one_b_user_gets_correct_ars_for_uam_with_ar_from_one_ltla_one_a(self):
        tested_uam = self.uam_with_ar_from_one_ltla_one_a

        ars = tested_uam.get_accommodation_requests_restrict_for_user(
            self.ltla_one_b_user
        )

        ar_ids = [ar.id for ar in ars]

        self.assertEqual(len(ar_ids), 0)

    def test_ltla_one_b_user_gets_correct_ars_for_uam_with_ar_from_one_ltla_one_b(self):
        tested_uam = self.uam_with_ar_from_one_ltla_one_b

        ars = tested_uam.get_accommodation_requests_restrict_for_user(
            self.ltla_one_b_user
        )

        ar_ids = [ar.id for ar in ars]

        self.assertIn("AR004", ar_ids)
        self.assertEqual(len(ar_ids), 1)

    def test_ltla_one_b_user_gets_correct_ars_for_uam_with_no_ars(self):
        tested_uam = self.uam_with_no_ars

        ars = tested_uam.get_accommodation_requests_restrict_for_user(
            self.ltla_one_b_user
        )

        ar_ids = [ar.id for ar in ars]

        self.assertEqual(len(ar_ids), 0)
