from factory import Sequence
from factory.django import DjangoModelFactory

from deduplication.models import (
    AccommodationDuplicateGroup,
    GuestDuplicateGroup,
    SponsorDuplicateGroup,
)


class SponsorDuplicateGroupFactory(DjangoModelFactory):
    id = Sequence(int)

    class Meta:
        model = SponsorDuplicateGroup


class GuestDuplicateGroupFactory(DjangoModelFactory):
    id = Sequence(int)

    class Meta:
        model = GuestDuplicateGroup


class AccommodationDuplicateGroupFactory(DjangoModelFactory):
    id = Sequence(int)

    class Meta:
        model = AccommodationDuplicateGroup
