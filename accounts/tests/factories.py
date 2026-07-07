from datetime import timezone

import factory.django
from django.contrib.auth.models import Group
from django.db.models.signals import post_save
from factory import Faker, RelatedFactory, Sequence, SubFactory
from factory.django import DjangoModelFactory

from accounts.enums import GroupType
from accounts.models import AccessRequest, GroupInfo, User


@factory.django.mute_signals(post_save)
class GroupInfoFactory(DjangoModelFactory):
    ltla_name = Faker("city")
    group = SubFactory("accounts.tests.factories.GroupFactory", groupinfo=None)

    class Meta:
        model = GroupInfo


@factory.django.mute_signals(post_save)
class GroupFactory(DjangoModelFactory):
    name = Sequence(lambda n: f"Group {n}")
    groupinfo = RelatedFactory(GroupInfoFactory, factory_related_name="group")

    class Meta:
        model = Group


class UserFactory(DjangoModelFactory):
    username = Faker("user_name")
    email = Faker("email")
    first_name = Faker("first_name")
    last_name = Faker("last_name")
    entra_tid = Faker("uuid4")
    entra_oid = Faker("uuid4")
    last_login = Faker(
        "date_time_between", start_date="-30d", end_date="now", tzinfo=timezone.utc
    )

    class Meta:
        model = User

    @factory.post_generation
    def is_dev(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            dev_group, _ = Group.objects.get_or_create(name="dev")
            dev_group.groupinfo.group_type = GroupType.DEV
            dev_group.groupinfo.save()
            self.groups.set([dev_group])


class AccessRequestFactory(DjangoModelFactory):
    requester = SubFactory("accounts.tests.factories.UserFactory")
    group_info = SubFactory("accounts.tests.factories.GroupInfoFactory")
    group_type = GroupType.LOCAL_AUTHORITY

    class Meta:
        model = AccessRequest
