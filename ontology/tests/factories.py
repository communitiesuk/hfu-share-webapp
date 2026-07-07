import uuid

import factory
from auditlog.models import LogEntry
from factory import Sequence, SubFactory
from factory.django import DjangoModelFactory

from ontology.models import (
    AccommodationMasterRecord,
    Announcement,
    Comment,
    CommentAttachment,
    CommentAttachmentMetadata,
    DevCheckV2,
    EoiHost,
    ExportToolObject,
    MvAccommodation,
    MvAccommodationRequest,
    MvGroup,
    MvInteraction,
    MvInteractionAttachmentMetadata,
    MvPerson,
    MvUkPostcode,
    MvVolunteer,
    PersonMasterRecord,
    ReassignmentRequest,
    SafeguardingNotification,
    SafeguardingReferral,
    SponsorMasterRecord,
    SponsorshipCertificationAttachmentMetadata,
    SponsorshipCertificationForm,
    UkLocalAuthority,
    VisaApplication,
    VisaInformationRequest,
    VisaInformationRequestComments,
)


class VisaApplicationFactory(DjangoModelFactory):
    visa_application_id = Sequence(str)

    class Meta:
        model = VisaApplication


class MvGroupFactory(DjangoModelFactory):
    id = Sequence(str)

    class Meta:
        model = MvGroup


class MvPersonFactory(DjangoModelFactory):
    id = Sequence(str)

    accommodation_request = SubFactory(
        "ontology.tests.factories.MvAccommodationRequestFactory"
    )

    class Meta:
        model = MvPerson


class MvVolunteerFactory(DjangoModelFactory):
    id = Sequence(str)
    is_editable = True

    class Meta:
        model = MvVolunteer


class MvUkPostcodeFactory(DjangoModelFactory):
    id = Sequence(str)

    class Meta:
        model = MvUkPostcode


class MvAccommodationFactory(DjangoModelFactory):
    id = Sequence(str)
    is_editable = True
    postcode = SubFactory("ontology.tests.factories.MvUkPostcodeFactory")

    class Meta:
        model = MvAccommodation


class MvAccommodationRequestFactory(DjangoModelFactory):
    id = Sequence(str)

    class Meta:
        model = MvAccommodationRequest


class PersonMasterRecordFactory(DjangoModelFactory):
    record_id = Sequence(str)

    class Meta:
        model = PersonMasterRecord


class ExportToolObjectFactory(DjangoModelFactory):
    id = factory.LazyFunction(uuid.uuid4)
    export_tool_id = factory.LazyFunction(uuid.uuid4)

    class Meta:
        model = ExportToolObject


class SafeguardingReferralFactory(DjangoModelFactory):
    id = factory.LazyFunction(lambda: f"safeguarding_referral-{uuid.uuid4()}")
    person = SubFactory("ontology.tests.factories.MvPersonFactory")

    class Meta:
        model = SafeguardingReferral


class SafeguardingNotificationFactory(DjangoModelFactory):
    id = factory.LazyFunction(lambda: str(uuid.uuid4()))

    class Meta:
        model = SafeguardingNotification


class DevCheckV2Factory(DjangoModelFactory):
    id = factory.LazyFunction(uuid.uuid4)

    @factory.post_generation
    def AR(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            for ar in extracted:
                self.AR.add(ar)

    @factory.post_generation
    def person(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            for person in extracted:
                self.person.add(person)

    class Meta:
        model = DevCheckV2


class ReassignmentRequestFactory(DjangoModelFactory):
    id = Sequence(lambda n: n)

    class Meta:
        model = ReassignmentRequest


class EoiHostFactory(DjangoModelFactory):
    host_id = Sequence(str)

    class Meta:
        model = EoiHost


class VIRFactory(DjangoModelFactory):
    visa_information_request_id = factory.LazyFunction(lambda: str(uuid.uuid4()))

    class Meta:
        model = VisaInformationRequest


class VIRCommentFactory(DjangoModelFactory):
    id = Sequence(lambda n: n)

    class Meta:
        model = VisaInformationRequestComments


class SponsorshipCertificationFormFactory(DjangoModelFactory):
    reference = Sequence(lambda n: n)

    class Meta:
        model = SponsorshipCertificationForm


class SponsorshipCertificationAttachmentMetadataFactory(DjangoModelFactory):
    id = Sequence(lambda n: n)

    class Meta:
        model = SponsorshipCertificationAttachmentMetadata


class AnnouncementFactory(DjangoModelFactory):
    class Meta:
        model = Announcement


class InteractionFactory(DjangoModelFactory):
    id = Sequence(str)

    class Meta:
        model = MvInteraction


class InteractionAttachmentMetadataFactory(DjangoModelFactory):
    id = Sequence(str)

    class Meta:
        model = MvInteractionAttachmentMetadata


class CommentFactory(DjangoModelFactory):
    id = factory.LazyFunction(lambda: str(uuid.uuid4()))

    class Meta:
        model = Comment


class CommentAttachmentFactory(DjangoModelFactory):
    id = factory.LazyFunction(lambda: str(uuid.uuid4()))

    class Meta:
        model = CommentAttachment


class CommentAttachmentMetadataFactory(DjangoModelFactory):
    class Meta:
        model = CommentAttachmentMetadata


class SponsorMasterRecordFactory(DjangoModelFactory):
    record_id = Sequence(str)

    class Meta:
        model = SponsorMasterRecord


class AccommodationMasterRecordFactory(DjangoModelFactory):
    record_id = Sequence(str)

    class Meta:
        model = AccommodationMasterRecord


class AuditLogEntryFactory(DjangoModelFactory):
    class Meta:
        model = LogEntry


class UKLocalAuthorityFactory(DjangoModelFactory):
    class Meta:
        model = UkLocalAuthority
