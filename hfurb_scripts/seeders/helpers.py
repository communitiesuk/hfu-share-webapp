import random
import uuid
from datetime import date, timedelta
from typing import List, Optional

from django.utils import timezone
from faker import Faker

from accounts.models import GroupInfo
from ontology.models import (
    CheckType,
    MvAccommodation,
    MvAccommodationRequest,
    MvGroup,
    MvPerson,
    MvVolunteer,
    SponsorshipCertificationForm,
    VisaApplication,
)
from ontology.models.MvUkPostcode import MvUkPostcode
from ontology.tests.factories import (
    DevCheckV2Factory,
    MvAccommodationFactory,
    MvAccommodationRequestFactory,
    MvGroupFactory,
    MvPersonFactory,
    MvUkPostcodeFactory,
    MvVolunteerFactory,
    SponsorshipCertificationAttachmentMetadataFactory,
    SponsorshipCertificationFormFactory,
    VisaApplicationFactory,
)

fake = Faker("en_GB")


def get_group_info_from_ltla(ltla_name: str) -> Optional[GroupInfo]:
    return GroupInfo.objects.filter(ltla_name=ltla_name).first()


def create_mv_uk_postcode(ltla_name: str | None = None) -> MvUkPostcode:
    postcode_str = fake.postcode()

    return MvUkPostcodeFactory(  # type: ignore[return-value]
        id=f"postcode-{uuid.uuid4()}",
        postcode=postcode_str.replace(" ", ""),
        postcode_formatted=postcode_str,
        title=postcode_str,
        ltla_name=ltla_name,
    )


def create_mv_accommodation(
    ltla_name: str,
    accommodation_type: MvAccommodation.AccommodationType | None = None,
) -> MvAccommodation:
    group_info = get_group_info_from_ltla(ltla_name)

    if accommodation_type is None:
        accommodation_type = MvAccommodation.AccommodationType.SPONSOR_ACCOMMODATION

    return MvAccommodationFactory(  # type: ignore[return-value]
        id=f"accommodation-{uuid.uuid4()}",
        accommodation_type=accommodation_type,
        full_address=f"{fake.street_address()}, {ltla_name}",
        ltla_name=ltla_name,
        utla_name=group_info.utla_name if group_info else ltla_name,
        postcode=create_mv_uk_postcode(ltla_name),
        is_accommodation=True,
        is_available_for_rematch=True,
        is_eoi=False,
        is_principal=True,
    )


def create_mv_sponsor(
    sponsor_type: MvVolunteer.SponsorType | None = None,
) -> MvVolunteer:
    first_name = fake.first_name()
    last_name = fake.last_name()

    if sponsor_type is None:
        sponsor_type = MvVolunteer.SponsorType.INDIVIDUAL

    age = random.randint(21, 70)
    # Generate a valid date of birth matching the age
    date_of_birth = fake.date_of_birth(minimum_age=age, maximum_age=age)

    return MvVolunteerFactory(  # type: ignore[return-value]
        id=f"sponsor-{uuid.uuid4()}",
        first_name=first_name,
        last_name=last_name,
        full_name=f"{first_name} {last_name}",
        email=fake.email(),
        phone_number=[fake.phone_number()],
        is_sponsor=True,
        is_principal=True,
        is_eoi=False,
        is_available_for_rematch=True,
        sponsor_type=sponsor_type,
        age=age,
        date_of_birth=date_of_birth,
        sex=fake.random_element(elements=("Male", "Female")),
        passport_details=[
            fake.password(
                length=9,
                special_chars=False,
                digits=True,
                upper_case=True,
                lower_case=False,
            )
        ],
        residential_postcodes=[
            fake.postcode()
            for _ in range(random.choices([1, 2, 3], weights=[90, 7, 3])[0])
        ],  # noqa: E501
        nationality=[],
        other_nationalities=[random.choices(["No", "Yes"], weights=[80, 20])[0]],
        flag_unsuitable=random.choices([False, True], weights=[97, 3])[0],
        hosting_duration=random.randint(6, 15),
        requested_checks_latest_date=fake.date_time_between(
            start_date="-1y", end_date="now", tzinfo=timezone.get_current_timezone()
        ),
        last_updated_date=fake.date_time_between(
            start_date="-1y", end_date="now", tzinfo=timezone.get_current_timezone()
        ),
    )


def add_accommodation_to_sponsor(
    sponsor: MvVolunteer, accommodation: MvAccommodation
) -> None:
    sponsor.accommodations.add(accommodation)  # type: ignore
    sponsor.save()


def add_visa_application_to_sponsor(
    sponsor: MvVolunteer, visa_application: VisaApplication
) -> None:
    sponsor.application_unique_application_number = [
        visa_application.application_unique_application_number
    ]
    sponsor.save()


def create_mv_person(
    upe_visa_status: MvPerson.UPEVisaStatus | None = None,
    visa_status: str | None = None,
) -> MvPerson:
    first_name = fake.first_name()
    last_name = fake.last_name()

    if upe_visa_status is None:
        upe_visa_status = MvPerson.UPEVisaStatus.ACCEPTED

    if visa_status is None:
        visa_status = "Confirmed"

    age = random.randint(18, 65)
    # Generate a valid date of birth matching the age
    date_of_birth = fake.date_of_birth(minimum_age=age, maximum_age=age)

    return MvPersonFactory(  # type: ignore[return-value]
        accommodation_request=None,
        id=f"person-{uuid.uuid4()}",
        first_name=first_name,
        last_name=last_name,
        email=[fake.email()],
        phone=[fake.phone_number()],
        is_principal=True,
        upe_visa_status=upe_visa_status,
        visa_status=visa_status,
        age=age,
        date_of_birth=date_of_birth,
        gender=fake.random_element(elements=("Male", "Female")),
        passport_id=[
            fake.password(
                length=9,
                special_chars=False,
                digits=True,
                upper_case=True,
                lower_case=False,
            )
        ],
    )


def add_accommodation_request_to_person(
    person: MvPerson, accommodation_request: MvAccommodationRequest
) -> None:
    person.accommodation_request = accommodation_request
    person.save()


def add_visa_application_to_person(
    person: MvPerson, visa_application: VisaApplication
) -> None:
    person.application_number = [visa_application.application_unique_application_number]
    person.save()


def create_mv_group(people: List[MvPerson]) -> MvGroup:
    # Find the oldest person as primary contact
    primary_contact = max(people, key=lambda p: p.age)

    # Build group title
    num_people = len(people)
    title = f"{primary_contact.first_name} {primary_contact.last_name}"
    if num_people > 1:
        title += f" and {num_people - 1} other{'s' if num_people > 2 else ''}"

    email = fake.email()

    return MvGroupFactory(  # type: ignore[return-value]
        id=f"group-{uuid.uuid4()}",
        title=title,
        number_of_people_in_group=num_people,
        primary_contact_first_name=primary_contact.first_name,
        primary_contact_last_name=primary_contact.last_name,
        primary_contact_email=[email],
        primary_contact_phone=[fake.phone_number()],
    )


def add_people_to_group(group: MvGroup, people: List[MvPerson]) -> None:
    for person in people:
        person.group = group
        person.save()


def create_mv_accommodation_request(
    accommodation: MvAccommodation,
    group: MvGroup,
    people: List[MvPerson],
    sponsor: MvVolunteer,
    status: MvAccommodationRequest.Status | None = None,
    checks_status: MvAccommodationRequest.ChecksStatus | None = None,
) -> MvAccommodationRequest:
    if status is None:
        status = MvAccommodationRequest.Status.ACCOMMODATION_ASSIGNED

    if checks_status is None:
        checks_status = MvAccommodationRequest.ChecksStatus.CHECKS_REQUIRED
    latest_application_date = timezone.now() - timedelta(days=random.randint(30, 365))
    return MvAccommodationRequestFactory(  # type: ignore[return-value]
        id=str(uuid.uuid4()),
        title=group.title + f" to {accommodation.full_address}",
        person_id=[person.id for person in people],
        accommodation_id=[accommodation.id],
        group_id=group.id,
        active_host=sponsor,
        sponsor_id=[sponsor.id],
        primary_sponsor=sponsor,
        ltla_name=[accommodation.ltla_name],
        utla_name=[accommodation.utla_name],
        primary_accommodation=accommodation,
        unique_application_number=[f"1313-0000-{str(uuid.uuid4()).upper()}"],
        number_of_people=group.number_of_people_in_group,
        status=status,
        is_principal=True,
        is_eoi_host=False,
        checks_status=checks_status,
        primary_contact_first_name=group.primary_contact_first_name,
        primary_contact_last_name=group.primary_contact_last_name,
        primary_contact_email=group.primary_contact_email,
        primary_contact_phone=group.primary_contact_phone,
        latest_application_date=latest_application_date,
        created_at=latest_application_date,
    )


def create_visa_application(
    person: MvPerson,
    sponsor: MvVolunteer,
    accommodation: MvAccommodation,
    accommodation_request: MvAccommodationRequest | None,
    visa_status: str | None = None,
) -> VisaApplication:
    group_info = get_group_info_from_ltla(accommodation.ltla_name)

    if visa_status is None:
        visa_status = "Confirmed"

    # Generate random visa decision date (between 30 and 180 days ago)
    visa_decision_date = timezone.now() - timedelta(days=random.randint(30, 180))

    return VisaApplicationFactory(  # type: ignore[return-value]
        visa_application_id=str(uuid.uuid4()),
        gwf=f"GWF{uuid.uuid4().hex[:8].upper()}",
        application_unique_application_number=(
            accommodation_request.unique_application_number[0]
            if accommodation_request and accommodation_request.unique_application_number
            else None
        ),
        Q44b_given_name=person.first_name,
        Q44c_family_name=person.last_name,
        Q44g_full_name=f"{person.first_name} {person.last_name}",
        Q11b_applicant_date_of_birth=date(
            2024 - person.age, random.randint(1, 12), random.randint(1, 28)
        )
        if person.age
        else None,
        Q14b_applicant_email_address=(person.email[0] if person.email else None),
        Q97a_sponsor_given_name=sponsor.first_name,
        Q97b_sponsor_family_name=sponsor.last_name,
        Q97c_sponsor_name=f"{sponsor.first_name} {sponsor.last_name}",
        ltla_name=accommodation.ltla_name,
        utla_name=(group_info.utla_name if group_info else accommodation.ltla_name),
        country=group_info.da_name if group_info else "England",
        visa_decision_date=visa_decision_date,
        title=(
            f"{person.first_name} {person.last_name} "
            f"sponsored by {sponsor.first_name} "
            f"{sponsor.last_name} to {accommodation.ltla_name}"
        ),
        visa_status=visa_status,
        application_event_datetime=timezone.now()
        - timedelta(days=random.randint(30, 365)),
    )


def create_uam(
    person: MvPerson, sponsor: MvVolunteer, accommodation: MvAccommodation
) -> SponsorshipCertificationForm:
    return SponsorshipCertificationFormFactory(  # type: ignore[return-value]
        reference=f"UAM-{str(uuid.uuid4())[:8].upper()}",
        certificate_reference=f"CERT-{fake.random_number(digits=8)}",
        given_name=sponsor.first_name,
        family_name=sponsor.last_name,
        email=sponsor.email,
        phone_number=sponsor.phone_number[0],
        sponsor_date_of_birth=sponsor.date_of_birth,
        residential_line_1=accommodation.full_address,
        residential_line_2=None,
        residential_town=None,
        residential_postcode=accommodation.postcode.postcode,
        identification_type="Passport",
        identification_number=fake.random_number(digits=8),
        minor_given_name=person.first_name,
        minor_family_name=person.last_name,
        minor_date_of_birth=person.date_of_birth,
        minor_email=person.email[0],
        minor_phone_number=person.phone[0],
        minor_contact_type=["email"],
        created_at=timezone.now() - timedelta(days=random.randint(30, 365)),
        ltla_name=[accommodation.ltla_name],
        uk_parental_consent_filename="uk_parental_consent.txt",
        ukraine_parental_consent_filename="ukraine_parental_consent.txt",
    )


def add_uam_and_docs_to_person(
    person: MvPerson,
    uam: SponsorshipCertificationForm,
) -> None:
    person.sponsorship_certification_number_id = [uam.reference]
    person.save()

    DevCheckV2Factory(
        check_type=CheckType.objects.get(id=CheckType.Id.UK_FORM_UPLOADED),
        document=uam.reference + "-uk",
        person=[person],
    )
    DevCheckV2Factory(
        check_type=CheckType.objects.get(id=CheckType.Id.UKR_FORM_UPLOADED),
        document=uam.reference + "-ukr",
        person=[person],
    )


def add_uam_to_sponsor(
    sponsor: MvVolunteer,
    uam: SponsorshipCertificationForm,
) -> None:
    sponsor.sponsorship_certification_number_id = [uam.reference]
    sponsor.save()


def add_uam_to_accommodation_request(
    accommodation_request: MvAccommodationRequest,
    uam: SponsorshipCertificationForm,
) -> None:
    accommodation_request.sponsorship_certification_number_id = [uam.reference]
    accommodation_request.save()


def add_attachments_to_uam(
    uam: SponsorshipCertificationForm,
) -> None:
    uk_path = "uk-form-id/uk_parental_consent.txt"
    ukr_path = "ukr-form-id/ukraine_parental_consent.txt"

    if random.choice([True, False]):
        SponsorshipCertificationAttachmentMetadataFactory(
            sponsorship_certification_form=uam,
            filename="consent-form-uk.txt",
            file_path=uk_path,
        )
        SponsorshipCertificationAttachmentMetadataFactory(
            sponsorship_certification_form=uam,
            filename="consent-form-ukr.txt",
            file_path=ukr_path,
        )
    else:
        SponsorshipCertificationAttachmentMetadataFactory(
            rid=uam.reference + "-uk",
            filename="consent-form-uk.txt",
            file_path=uk_path,
        )
        SponsorshipCertificationAttachmentMetadataFactory(
            rid=uam.reference + "-ukr",
            filename="consent-form-ukr.txt",
            file_path=ukr_path,
        )


def build_complete_accommodation_scenario(
    num_guests: int,
    ltla_name: str,
    accommodation_type: MvAccommodation.AccommodationType | None = None,
    sponsor_type: MvVolunteer.SponsorType | None = None,
    upe_visa_status: MvPerson.UPEVisaStatus | None = None,
    checks_status: MvAccommodationRequest.ChecksStatus | None = None,
    visa_statuses: List[str] | None = None,
) -> MvAccommodationRequest:
    accommodation = create_mv_accommodation(ltla_name, accommodation_type)
    sponsor = create_mv_sponsor(sponsor_type)

    if visa_statuses is None:
        visa_statuses = ["Confirmed"] * num_guests

    people = [
        create_mv_person(upe_visa_status, visa_statuses[i]) for i in range(num_guests)
    ]

    group = create_mv_group(people)

    add_people_to_group(group, people)
    add_accommodation_to_sponsor(sponsor, accommodation)

    accommodation_request = create_mv_accommodation_request(
        accommodation=accommodation,
        group=group,
        people=people,
        sponsor=sponsor,
        checks_status=checks_status,
    )

    # randomize a number from 0 to 4
    one_in_five = random.randint(0, 4)
    make_uam = (one_in_five == 0) and (num_guests == 1)
    if not make_uam:
        for i, person in enumerate(people):
            add_accommodation_request_to_person(person, accommodation_request)
            visa_application = create_visa_application(
                person,
                sponsor,
                accommodation,
                accommodation_request,
                visa_statuses[i],
            )
            add_visa_application_to_person(person, visa_application)
            add_visa_application_to_sponsor(sponsor, visa_application)
    else:
        person = people[0]
        add_accommodation_request_to_person(person, accommodation_request)
        uam = create_uam(person, sponsor, accommodation)
        add_uam_and_docs_to_person(person, uam)
        add_uam_to_sponsor(sponsor, uam)
        add_attachments_to_uam(uam)
        add_uam_to_accommodation_request(accommodation_request, uam)

    return accommodation_request


def create_new_accommodation_request_for_person(person: MvPerson):
    accommodation = random.choice(list(MvAccommodation.objects.all()))
    sponsor = random.choice(list(MvVolunteer.objects.all()))
    group = create_mv_group([person])

    add_people_to_group(group, [person])

    accommodation_request = create_mv_accommodation_request(
        accommodation=accommodation,
        group=group,
        people=[person],
        sponsor=sponsor,
    )

    add_accommodation_request_to_person(person, accommodation_request)


def create_new_visa_application_for_person(person: MvPerson):
    if accommodation_request := person.accommodation_request:
        primary_sponsor = accommodation_request.get_primary_sponsor()
        sponsor = (
            primary_sponsor
            if primary_sponsor and primary_sponsor.is_editable
            else random.choice(list(MvVolunteer.objects.filter(is_editable=True)))
        )

        primary_accommodation = accommodation_request.get_primary_accommodation()
        accommodation = (
            primary_accommodation
            if primary_accommodation and primary_accommodation.is_editable
            else random.choice(list(MvAccommodation.objects.filter(is_editable=True)))
        )
    else:
        sponsor = random.choice(list(MvVolunteer.objects.filter(is_editable=True)))
        accommodation = random.choice(
            list(MvAccommodation.objects.filter(is_editable=True))
        )

    visa_application = create_visa_application(
        person,
        sponsor,
        accommodation,
        accommodation_request,
        person.visa_status,
    )

    add_visa_application_to_person(person, visa_application)
    add_visa_application_to_sponsor(sponsor, visa_application)
