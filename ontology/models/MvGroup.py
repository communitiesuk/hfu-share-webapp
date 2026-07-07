from copy import deepcopy
from uuid import uuid4

from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.db.models import QuerySet

from ontology.models import DevCheckV2, MvPerson


class MvGroup(models.Model):
    checks: QuerySet[DevCheckV2]

    application_number = ArrayField(
        models.TextField(), null=True, db_column="application_number"
    )
    created_at = models.DateTimeField(null=True, db_column="created_at")
    created_by = models.TextField(null=True, db_column="created_by")
    date_of_arrival = models.DateField(null=True, db_column="date_of_arrival")
    edited_at = models.DateTimeField(null=True, db_column="edited_at")
    edited_by = models.TextField(null=True, db_column="edited_by")
    first_arrival_date = models.DateField(null=True, db_column="first_arrival_date")
    geohash = models.TextField(null=True, db_column="geohash")
    old_split_group = models.ForeignKey(
        "ontology.MvGroup",
        on_delete=models.CASCADE,
        related_name="+",
        null=True,
        db_constraint=False,
        db_column="old_split_group",
    )
    id = models.TextField(primary_key=True, db_column="id")
    is_merged = models.BooleanField(null=True, db_column="is_merged")
    location_of_arrival = models.TextField(null=True, db_column="location_of_arrival")
    max_age = models.IntegerField(null=True, db_column="max_age")
    merged_group = models.ForeignKey(
        "ontology.MvGroup",
        on_delete=models.CASCADE,
        related_name="+",
        null=True,
        db_constraint=False,
        db_column="merged_group",
    )
    min_age = models.IntegerField(null=True, db_column="min_age")
    notional_data = models.BooleanField(null=True, db_column="notional_data")
    number_of_people_in_group = models.BigIntegerField(
        null=True, db_column="number_of_people_in_group"
    )
    primary_contact_can_be_contacted_by_phone = models.TextField(
        null=True, db_column="primary_contact_can_be_contacted_by_phone"
    )
    primary_contact_email = ArrayField(
        models.TextField(), null=True, db_column="primary_contact_email"
    )
    primary_contact_email_after_decision = ArrayField(
        models.TextField(), null=True, db_column="primary_contact_email_after_decision"
    )
    primary_contact_email_for_decision = ArrayField(
        models.TextField(), null=True, db_column="primary_contact_email_for_decision"
    )
    primary_contact_email_for_questions = ArrayField(
        models.TextField(), null=True, db_column="primary_contact_email_for_questions"
    )
    primary_contact_first_name = models.TextField(
        null=True, db_column="primary_contact_first_name"
    )
    primary_contact_last_name = models.TextField(
        null=True, db_column="primary_contact_last_name"
    )
    primary_contact_phone = ArrayField(
        models.TextField(), null=True, db_column="primary_contact_phone"
    )
    source = ArrayField(models.TextField(), null=True, db_column="source")
    title = models.TextField(null=True, db_column="title")
    viewer_group_names = ArrayField(
        models.TextField(), null=True, db_column="viewer_group_names"
    )
    wheelchair_required = models.BooleanField(
        null=True, db_column="wheelchair_required"
    )
    # Array of SponsorshipCertificationForm IDs
    sponsorship_certification_number_id = ArrayField(
        models.TextField(),
        null=True,
        blank=True,
        db_column="sponsorship_certification_number",
        verbose_name="Sponsorship certification application number",
    )
    edited_in_app = models.BooleanField(
        null=True, blank=True, db_column="edited_in_app"
    )

    def __str__(self):
        return self.title or super().__str__()

    def save(self, *args, **kwargs):
        self.edited_in_app = True
        super(MvGroup, self).save(*args, **kwargs)

    def _min_age(self, guests) -> int | None:
        return min((person.age for person in guests), default=None)

    def _max_age(self, guests) -> int | None:
        return max((person.age for person in guests), default=None)

    def _primary_contact(self, guests):
        # primary contact is oldest
        return max(guests, key=lambda person: person.age, default=None)

    def is_primary_contact(self, person: MvPerson) -> bool:
        from ontology.models import MvPerson

        guests = MvPerson.objects.filter(group_id=self.id).all()
        primary = self._primary_contact(guests)
        return bool(primary and str(primary.id) == str(person.id))

    def _primary_name(self) -> str:
        if self.primary_contact_first_name and self.primary_contact_last_name:
            return f"{self.primary_contact_first_name} {self.primary_contact_last_name}"

        return (
            self.primary_contact_first_name
            or self.primary_contact_last_name
            or "Unknown"
        )

    def _build_title(self) -> str:
        title = self._primary_name()

        if self.number_of_people_in_group > 1:
            others = self.number_of_people_in_group - 1
            title += f" and {others} other{'s' if others > 1 else ''}"

        return title

    def refresh_data(self):
        from ontology.models import MvPerson

        guests = MvPerson.objects.filter(group_id=self.id).all()

        self.application_number = [
            app_num
            for person in guests
            if person.application_number
            for app_num in person.application_number
        ]

        self.number_of_people_in_group = len(guests)

        self.min_age = self._min_age(guests)
        self.max_age = self._max_age(guests)

        # primary contact is oldest
        primary_contact = self._primary_contact(guests)

        self.primary_contact_first_name = None
        self.primary_contact_last_name = None
        self.primary_contact_phone = None
        self.primary_contact_email = None
        self.primary_contact_email_for_questions = None
        self.primary_contact_email_for_decision = None
        self.primary_contact_email_after_decision = None
        self.primary_contact_can_be_contacted_by_phone = None
        if primary_contact:
            self.primary_contact_first_name = primary_contact.first_name
            self.primary_contact_last_name = primary_contact.last_name
            self.primary_contact_phone = primary_contact.phone
            self.primary_contact_email = primary_contact.email
            self.primary_contact_email_for_questions = (
                primary_contact.email_for_questions
            )
            self.primary_contact_email_for_decision = primary_contact.email_for_decision
            self.primary_contact_email_after_decision = (
                primary_contact.email_after_decision
            )
            self.primary_contact_can_be_contacted_by_phone = (
                primary_contact.can_be_contacted_by_phone
            )

        self.title = self._build_title()
        self.save()

    def split_group(self, guest_ids: list[str]):
        from ontology.models import MvPerson

        new_group = deepcopy(self)
        new_group.id = uuid4()
        new_group.old_split_group_id = self.id
        new_group.save()

        # Update persons to point to the new group
        MvPerson.objects.filter(id__in=guest_ids).update(group_id=new_group.id)

        new_group.refresh_data()
        self.refresh_data()

        return new_group
