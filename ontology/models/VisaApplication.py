from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.db.models import (
    F,
    Func,
    IntegerField,
    Q,
)
from django.db.models.expressions import Value
from django.utils import timezone

from accounts.models import User
from ontology.mixins import LocalAuthorityPermissionsManagerMixin
from ontology.models.MvPerson import MvPerson
from ontology.models.MvVolunteer import MvVolunteer
from ontology.utils import LinkedRecordData


class VisaApplicationQuerySet(models.QuerySet):
    def with_applicant_age(self):
        return self.annotate(
            applicant_age=Func(
                Value("year"),
                Func(
                    Value(timezone.now().date()),
                    F("Q11b_applicant_date_of_birth"),
                    function="age",
                ),
                function="date_part",
                output_field=IntegerField(),
            )
        )


class VisaApplicationManager(LocalAuthorityPermissionsManagerMixin, models.Manager):
    def get_queryset(self):
        return VisaApplicationQuerySet(self.model, using=self._db).with_applicant_age()

    def _filter_by_ltla_name(self, ltla_names: list[str]) -> Q:
        return Q(ltla_name__in=ltla_names)

    def _filter_by_utla_name(self, utla_names: list[str]) -> Q:
        return Q(utla_name__in=utla_names)

    def _filter_by_viewer_group_name(self, viewer_group_names: list[str]) -> Q:
        return Q(viewer_group_names__overlap=viewer_group_names)


class VisaApplication(models.Model):
    objects = VisaApplicationManager()

    address_preference = models.TextField(
        null=True, blank=True, db_column="address_preference"
    )
    applicant_arrival_time = models.DateTimeField(
        null=True, blank=True, db_column="applicant_arrival_time"
    )
    applicant_final_address = models.TextField(
        null=True, blank=True, db_column="applicant_final_address"
    )
    application_event_datetime = models.DateTimeField(
        null=True, blank=True, db_column="application_event_datetime"
    )
    country = models.TextField(null=True, blank=True, db_column="country")
    ingestion_time = models.DateTimeField(null=True, blank=True)
    gwf = models.TextField(null=True, blank=True, db_column="gwf", verbose_name="GWF")
    is_notional = models.BooleanField(null=True, blank=True, db_column="is_notional")
    ltla_name = models.TextField(
        null=True, blank=True, db_column="ltla_name", verbose_name="Lower tier LA name"
    )
    mapping_postcode = models.TextField(
        null=True, blank=True, db_column="mapping_postcode"
    )
    mapping_postcode_FL = models.TextField(
        null=True, blank=True, db_column="mapping_postcode_FL"
    )
    Q101a_uk_address_staying = models.TextField(
        null=True,
        blank=True,
        db_column="Q101a_uk_address_staying",
        verbose_name="Q101a UK address staying",
    )
    Q101b_uk_address_staying_local_authority = models.TextField(
        null=True,
        blank=True,
        db_column="Q101b_uk_address_staying_local_authority",
        verbose_name="Q101b UK address staying local authority",
    )
    Q101c_uk_address_staying_country = models.TextField(
        null=True,
        blank=True,
        db_column="Q101c_uk_address_staying_country",
        verbose_name="Q101c UK address staying country",
    )
    Q10a_is_one_member_family_ukraine_citizen = models.TextField(
        null=True,
        blank=True,
        db_column="Q10a_is_one_member_family_ukraine_citizen",
        verbose_name="Q10a is one member family Ukraine citizen",
    )
    Q11b_applicant_date_of_birth = models.DateField(
        null=True, blank=True, db_column="Q11b_applicant_date_of_birth"
    )
    Q12a_applicant_known_passport_travel_number = models.TextField(
        null=True, blank=True, db_column="Q12a_applicant_known_passport_travel_number"
    )
    Q12b_applicant_passport_travel_number = models.TextField(
        null=True, blank=True, db_column="Q12b_applicant_passport_travel_number"
    )
    Q13a_applicant_passport_issuing_authority = models.TextField(
        null=True, blank=True, db_column="Q13a_applicant_passport_issuing_authority"
    )
    Q13b_applicant_passport_issue_date = models.DateField(
        null=True, blank=True, db_column="Q13b_applicant_passport_issue_date"
    )
    Q13c_applicant_passport_expiry_date = models.DateField(
        null=True, blank=True, db_column="Q13c_applicant_passport_expiry_date"
    )
    Q14b_applicant_email_address = models.TextField(
        null=True, blank=True, db_column="Q14b_applicant_email_address"
    )
    Q15a_sponsor_other_name = models.TextField(
        null=True, blank=True, db_column="Q15a_sponsor_other_name"
    )
    Q16a_sponsor_other_name_details = ArrayField(
        models.TextField(),
        null=True,
        blank=True,
        db_column="Q16a_sponsor_other_name_details",
    )
    Q18a_sponsor_is_in_address_uk = models.TextField(
        null=True,
        blank=True,
        db_column="Q18a_sponsor_is_in_address_uk",
        verbose_name="Q18a sponsor is in address UK",
    )
    Q18b_sponsor_address_uk = models.TextField(
        null=True,
        blank=True,
        db_column="Q18b_sponsor_address_uk",
        verbose_name="Q18b sponsor address UK",
    )
    Q18c_sponsor_address_uk_local_authority = models.TextField(
        null=True,
        blank=True,
        db_column="Q18c_sponsor_address_uk_local_authority",
        verbose_name="Q18c sponsor address UK local authority",
    )
    Q18d_sponsor_address_uk_country = models.TextField(
        null=True,
        blank=True,
        db_column="Q18d_sponsor_address_uk_country",
        verbose_name="Q18d sponsor address UK country",
    )
    Q18f_sponsor_address_started_living_at = models.DateField(
        null=True, blank=True, db_column="Q18f_sponsor_address_started_living_at"
    )
    Q19a_sponsor_addresses_2_years = ArrayField(
        models.TextField(),
        null=True,
        blank=True,
        db_column="Q19a_sponsor_addresses_2_years",
    )
    Q21a_application_sex = models.TextField(
        null=True, blank=True, db_column="Q21a_application_sex"
    )
    Q21b_applicant_relationship_status = models.TextField(
        null=True, blank=True, db_column="Q21b_applicant_relationship_status"
    )
    Q22a_sponsor_id_is_valid = models.TextField(
        null=True,
        blank=True,
        db_column="Q22a_sponsor_id_is_valid",
        verbose_name="Q22a sponsor ID is valid",
    )
    Q22b_sponsor_id_card_number = models.TextField(
        null=True,
        blank=True,
        db_column="Q22b_sponsor_id_card_number",
        verbose_name="Q22b sponsor ID card number",
    )
    Q22c_sponsor_id_issuing_authority = models.TextField(
        null=True,
        blank=True,
        db_column="Q22c_sponsor_id_issuing_authority",
        verbose_name="Q22c sponsor ID issuing authority",
    )
    Q22d_sponsor_id_issue_date = models.DateField(
        null=True,
        blank=True,
        db_column="Q22d_sponsor_id_issue_date",
        verbose_name="Q22d sponsor ID issue date",
    )
    Q22e_sponsor_id_expiry_date = models.DateField(
        null=True,
        blank=True,
        db_column="Q22e_sponsor_id_expiry_date",
        verbose_name="Q22e sponsor ID expiry date",
    )
    Q25a_sponsor_other_nationality_details = ArrayField(
        models.TextField(),
        null=True,
        blank=True,
        db_column="Q25a_sponsor_other_nationality_details",
    )
    Q29a_applicant_will_stay_at_sponsor_address = models.TextField(
        null=True, blank=True, db_column="Q29a_applicant_will_stay_at_sponsor_address"
    )
    Q2a_living_ukraine_before_jan_22 = models.TextField(
        null=True,
        blank=True,
        db_column="Q2a_living_ukraine_before_jan_22",
        verbose_name="Q2a living Ukraine before Jan 22",
    )
    Q31a_other_people_will_live_at_address = models.TextField(
        null=True, blank=True, db_column="Q31a_other_people_will_live_at_address"
    )
    Q32a_other_household_member_given_name = models.TextField(
        null=True, blank=True, db_column="Q32a_other_household_member_given_name"
    )
    Q32b_other_household_member_family_name = models.TextField(
        null=True, blank=True, db_column="Q32b_other_household_member_family_name"
    )
    Q32c_other_household_member_date_of_birth = models.DateField(
        null=True, blank=True, db_column="Q32c_other_household_member_date_of_birth"
    )
    Q32d_other_household_member_nationality = models.TextField(
        null=True, blank=True, db_column="Q32d_other_household_member_nationality"
    )
    Q32e_other_household_member_passport = models.TextField(
        null=True, blank=True, db_column="Q32e_other_household_member_passport"
    )
    Q33a_other_people_will_live_at_address = ArrayField(
        models.TextField(),
        null=True,
        blank=True,
        db_column="Q33a_other_people_will_live_at_address",
    )
    Q34a_email_owner = models.TextField(
        null=True, blank=True, db_column="Q34a_email_owner"
    )
    Q34b_email_address = models.TextField(
        null=True, blank=True, db_column="Q34b_email_address"
    )
    Q35a_has_email_address = models.TextField(
        null=True, blank=True, db_column="Q35a_has_email_address"
    )
    Q35b_email_address = models.TextField(
        null=True, blank=True, db_column="Q35b_email_address"
    )
    Q36a_has_other_email_address = models.TextField(
        null=True, blank=True, db_column="Q36a_has_other_email_address"
    )
    Q36b_which_email_contact_applicant = models.TextField(
        null=True, blank=True, db_column="Q36b_which_email_contact_applicant"
    )
    Q36d_which_email_application_decision = models.TextField(
        null=True, blank=True, db_column="Q36d_which_email_application_decision"
    )
    Q36f_which_email_communicate_after_application = models.TextField(
        null=True,
        blank=True,
        db_column="Q36f_which_email_communicate_after_application",
    )
    Q37a_add_other_email = models.TextField(
        null=True, blank=True, db_column="Q37a_add_other_email"
    )
    Q37b_email_address_owner = models.TextField(
        null=True, blank=True, db_column="Q37b_email_address_owner"
    )
    Q39b_which_email_contact_applicant = models.TextField(
        null=True, blank=True, db_column="Q39b_which_email_contact_applicant"
    )
    Q39d_explanation_no_email_questions = models.TextField(
        null=True, blank=True, db_column="Q39d_explanation_no_email_questions"
    )
    Q39f_which_email_application_decision = models.TextField(
        null=True, blank=True, db_column="Q39f_which_email_application_decision"
    )
    Q39h_explanation_no_email_application_decision = models.TextField(
        null=True,
        blank=True,
        db_column="Q39h_explanation_no_email_application_decision",
    )
    Q39j_which_email_communicate_after_application = models.TextField(
        null=True,
        blank=True,
        db_column="Q39j_which_email_communicate_after_application",
    )
    Q39l_explanation_no_email_communicate_after_application = models.TextField(
        null=True,
        blank=True,
        db_column="Q39l_explanation_no_email_communicate_after_application",
        verbose_name="Q39l explanation no email communicate after applications",
    )
    Q3a_sponsor_uk_permission = models.TextField(
        null=True,
        blank=True,
        db_column="Q3a_sponsor_uk_permission",
        verbose_name="Q3a sponsor UK permission",
    )
    Q3b_sponsor_description = models.TextField(
        null=True, blank=True, db_column="Q3b_sponsor_description"
    )
    Q3c_sponsor_immigration_status = models.TextField(
        null=True, blank=True, db_column="Q3c_sponsor_immigration_status"
    )
    Q40a_telephone_number_details = ArrayField(
        models.TextField(),
        null=True,
        blank=True,
        db_column="Q40a_telephone_number_details",
    )
    # sic "telephon" not "telephone"
    Q42a_can_be_contacted_by_telephon = models.TextField(
        null=True,
        blank=True,
        db_column="Q42a_can_be_contacted_by_telephon",
        verbose_name="Q42a can be contacted by telephone",
    )
    Q42b_explanation_no_contact_sms = models.TextField(
        null=True, blank=True, db_column="Q42b_explanation_no_contact_sms"
    )
    Q42c_explanation_no_contact_call = models.TextField(
        null=True, blank=True, db_column="Q42c_explanation_no_contact_call"
    )
    Q42d_explanation_no_contact_call_or_text = models.TextField(
        null=True, blank=True, db_column="Q42d_explanation_no_contact_call_or_text"
    )
    Q43a_preferred_contact_number = models.TextField(
        null=True, blank=True, db_column="Q43a_preferred_contact_number"
    )
    Q44b_given_name = models.TextField(
        null=True, blank=True, db_column="Q44b_given_name"
    )
    Q44c_family_name = models.TextField(
        null=True, blank=True, db_column="Q44c_family_name"
    )
    Q44g_full_name = models.TextField(null=True, blank=True, db_column="Q44g_full_name")
    Q45a_other_name_details = ArrayField(
        models.TextField(), null=True, blank=True, db_column="Q45a_other_name_details"
    )
    # sic "lass" not "last"
    Q47a_lass_ukraine_address = models.TextField(
        null=True,
        blank=True,
        db_column="Q47a_lass_ukraine_address",
        verbose_name="Q47a last Ukraine address",
    )
    Q52c_place_of_birth = models.TextField(
        null=True, blank=True, db_column="Q52c_place_of_birth"
    )
    Q52d_date_of_birth = models.DateField(
        null=True, blank=True, db_column="Q52d_date_of_birth"
    )
    Q54a_other_nationality_details = ArrayField(
        models.TextField(),
        null=True,
        blank=True,
        db_column="Q54a_other_nationality_details",
    )
    Q5b_applicant_email_address = models.TextField(
        null=True, blank=True, db_column="Q5b_applicant_email_address"
    )
    Q5c_applicant_repeat_email_address = models.TextField(
        null=True, blank=True, db_column="Q5c_applicant_repeat_email_address"
    )
    Q5f_applicant_email_creation_date = models.DateTimeField(
        null=True, blank=True, db_column="Q5f_applicant_email_creation_date"
    )
    Q5g_application_email_creation_person = models.TextField(
        null=True, blank=True, db_column="Q5g_application_email_creation_person"
    )
    Q63a_has_family_members_applying = models.TextField(
        null=True, blank=True, db_column="Q63a_has_family_members_applying"
    )
    Q64a_relationship_with_applicant = models.TextField(
        null=True, blank=True, db_column="Q64a_relationship_with_applicant"
    )
    Q64b_family_member_names = models.TextField(
        null=True, blank=True, db_column="Q64b_family_member_names"
    )
    Q64c_family_member_family_name = models.TextField(
        null=True, blank=True, db_column="Q64c_family_member_family_name"
    )
    Q64d_family_member_date_of_birth = models.DateField(
        null=True, blank=True, db_column="Q64d_family_member_date_of_birth"
    )
    Q64e_is_family_member_travelling_uk = models.TextField(
        null=True,
        blank=True,
        db_column="Q64e_is_family_member_travelling_uk",
        verbose_name="Q64e is family member travelling UK",
    )
    Q64f_family_member_country_of_nationality = models.TextField(
        null=True, blank=True, db_column="Q64f_family_member_country_of_nationality"
    )
    Q64g_family_member_passport_number = models.TextField(
        null=True, blank=True, db_column="Q64g_family_member_passport_number"
    )
    Q66a_uk_arrival_date = models.DateField(
        null=True,
        blank=True,
        db_column="Q66a_uk_arrival_date",
        verbose_name="Q66a UK arrival date",
    )
    Q68a_immigration_problem_details = ArrayField(
        models.TextField(),
        null=True,
        blank=True,
        db_column="Q68a_immigration_problem_details",
    )
    Q6c_person_joining_given_name = models.TextField(
        null=True, blank=True, db_column="Q6c_person_joining_given_name"
    )
    Q6d_person_joining_family_name = models.TextField(
        null=True, blank=True, db_column="Q6d_person_joining_family_name"
    )
    Q6e_person_joining_full_name = models.TextField(
        null=True, blank=True, db_column="Q6e_person_joining_full_name"
    )
    Q70a_breach_uk_immigration_law = ArrayField(
        models.TextField(),
        null=True,
        blank=True,
        db_column="Q70a_breach_uk_immigration_law",
        verbose_name="Q70a breach UK immigration law",
    )
    Q73a_conviction_and_other_penalties = models.TextField(
        null=True, blank=True, db_column="Q73a_conviction_and_other_penalties"
    )
    Q86a_data_sharing_permission = models.TextField(
        null=True, blank=True, db_column="Q86a_data_sharing_permission"
    )
    Q89a_third_party_capacity_representing = models.TextField(
        null=True, blank=True, db_column="Q89a_third_party_capacity_representing"
    )
    Q89b_third_party_relation_to_applicant = models.TextField(
        null=True, blank=True, db_column="Q89b_third_party_relation_to_applicant"
    )
    Q89c_third_party_capacity_details = models.TextField(
        null=True, blank=True, db_column="Q89c_third_party_capacity_details"
    )
    Q90a_third_party_full_name = models.TextField(
        null=True, blank=True, db_column="Q90a_third_party_full_name"
    )
    Q90b_third_party_name = models.TextField(
        null=True, blank=True, db_column="Q90b_third_party_name"
    )
    Q90c_third_party_telephone_number = models.TextField(
        null=True, blank=True, db_column="Q90c_third_party_telephone_number"
    )
    Q90d_third_party_email_address = models.TextField(
        null=True, blank=True, db_column="Q90d_third_party_email_address"
    )
    Q90e_third_party_address = models.TextField(
        null=True, blank=True, db_column="Q90e_third_party_address"
    )
    Q90f_third_party_state = models.TextField(
        null=True, blank=True, db_column="Q90f_third_party_state"
    )
    Q90g_third_party_country = models.TextField(
        null=True, blank=True, db_column="Q90g_third_party_country"
    )
    Q91b_permission_uk_postcode = models.TextField(
        null=True,
        blank=True,
        db_column="Q91b_permission_uk_postcode",
        verbose_name="Q91b permission UK postcode",
    )
    Q91c_permission_acl_code = models.TextField(
        null=True,
        blank=True,
        db_column="Q91c_permission_acl_code",
        verbose_name="Q91c permission ACL code",
    )
    Q91d_permission_brp_collection_location = models.TextField(
        null=True,
        blank=True,
        db_column="Q91d_permission_brp_collection_location",
        verbose_name="Q91d permission BRP collection location",
    )
    Q95a_external_reference = models.TextField(
        null=True, blank=True, db_column="Q95a_external_reference"
    )
    Q96a_enrollment_organisation = models.TextField(
        null=True, blank=True, db_column="Q96a_enrollment_organisation"
    )
    Q97a_sponsor_given_name = models.TextField(
        null=True, blank=True, db_column="Q97a_sponsor_given_name"
    )
    Q97b_sponsor_family_name = models.TextField(
        null=True, blank=True, db_column="Q97b_sponsor_family_name"
    )
    Q97c_sponsor_name = models.TextField(
        null=True, blank=True, db_column="Q97c_sponsor_name"
    )
    Q98a_sponsoring_organisation = models.TextField(
        null=True, blank=True, db_column="Q98a_sponsoring_organisation"
    )
    Q99a_sponsor_relationship_status = models.TextField(
        null=True, blank=True, db_column="Q99a_sponsor_relationship_status"
    )
    Q99b_sponsor_relationship_sex = models.TextField(
        null=True, blank=True, db_column="Q99b_sponsor_relationship_sex"
    )
    source = models.TextField(null=True, blank=True, db_column="source")
    submission_guid = models.TextField(
        null=True,
        blank=True,
        db_column="submission_guid",
        verbose_name="Submission GUID",
    )
    title = models.TextField(null=True, blank=True, db_column="title")
    application_unique_application_number = models.TextField(
        null=True,
        blank=True,
        db_column="application_unique_application_number",
        verbose_name="Unique application number (UAN)",
    )
    utla_name = models.TextField(
        null=True, blank=True, db_column="utla_name", verbose_name="Upper tier LA name"
    )
    viewer_group_names = ArrayField(
        models.TextField(), null=True, blank=True, db_column="viewer_group_names"
    )
    viewer_group_names_multi_la = ArrayField(
        models.TextField(),
        null=True,
        blank=True,
        db_column="viewer_group_names_multi_la",
        verbose_name="Viewer group names multi LA",
    )
    visa_application_id = models.TextField(
        primary_key=True,
        db_column="visa_application_id",
        verbose_name="Visa application ID",
    )
    visa_decision_date = models.DateTimeField(
        null=True, blank=True, db_column="visa_decision_date"
    )
    visa_status = models.TextField(null=True, blank=True, db_column="visa_status")

    def display_link_data(self, linked_from, linked_as) -> LinkedRecordData:
        return LinkedRecordData(
            "visa-applications:detail-overview", self.visa_application_id, self.title
        )

    def get_accommodation_requests_restrict_for_user(self, user: User):
        from ontology.models.MvAccommodationRequest import MvAccommodationRequest

        if self.application_unique_application_number:
            return MvAccommodationRequest.objects.get_for_user(user).filter(
                unique_application_number__contains=[
                    self.application_unique_application_number
                ]
            )
        return MvAccommodationRequest.objects.none()

    def get_guests_restrict_for_user(self, user: User):
        from ontology.models.MvPerson import MvPerson

        if self.application_unique_application_number:
            return MvPerson.objects.get_for_user(user).filter(
                application_number__contains=[
                    self.application_unique_application_number
                ]
            )
        return MvPerson.objects.none()

    def get_sponsors_restrict_for_user(self, user: User):
        if self.application_unique_application_number:
            return MvVolunteer.objects.get_for_user(user).filter(
                application_unique_application_number__contains=[
                    self.application_unique_application_number
                ]
            )
        return MvVolunteer.objects.none()

    def get_accommodations_restrict_for_user(self, user: User):
        from ontology.models.MvAccommodation import MvAccommodation

        if self.application_unique_application_number:
            return MvAccommodation.objects.get_for_user(user).filter(
                application_unique_application_number__contains=[
                    self.application_unique_application_number
                ]
            )
        return MvAccommodation.objects.none()

    def get_primary_contact_initials(self) -> str:
        initials = ""

        if self.Q44b_given_name and len(self.Q44b_given_name) > 0:
            initials += self.Q44b_given_name[0]

        if self.Q44c_family_name and len(self.Q44c_family_name) > 0:
            initials += self.Q44c_family_name[0]

        return initials.upper()

    def get_pii_safe_record_name(self) -> str:
        return self.get_primary_contact_initials()

    class Meta:
        verbose_name = "Visa Application"

    @property
    def sponsor(self) -> MvVolunteer:
        return MvVolunteer.objects.get(
            application_unique_application_number=[
                self.application_unique_application_number
            ]
        )

    @property
    def persons(self) -> MvPerson:
        return MvPerson.objects.filter(
            application_number__contains=[self.application_unique_application_number]
        )
