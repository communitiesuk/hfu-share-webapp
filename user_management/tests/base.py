from dataclasses import dataclass
from typing import cast

from django.contrib.auth.models import Group

from accounts.enums import GroupType
from accounts.models import User
from accounts.tests.factories import GroupFactory, UserFactory


@dataclass
class UserGroup:
    name: str
    type: GroupType | None = None


def get_user_with_groups(groups: list[UserGroup]):
    user = UserFactory()
    for group in groups:
        group_exists = Group.objects.filter(name=group.name).exists()
        if group_exists:
            group_instance = Group.objects.get(name=group.name)
        else:
            group_instance = cast(Group, GroupFactory(name=group.name))
            if group.type is not None and hasattr(group_instance, "groupinfo"):
                group_instance.groupinfo.group_type = group.type
                group_instance.groupinfo.ltla_name = group.name
                group_instance.groupinfo.save()
        cast(User, user).groups.add(group_instance)
    return user


def get_la_user():
    return get_user_with_groups(
        [UserGroup(name="ltla_somerset", type=GroupType.LOCAL_AUTHORITY)]
    )


def get_la_early_adopter_user():
    return get_user_with_groups(
        [
            UserGroup(name="ltla_somerset", type=GroupType.LOCAL_AUTHORITY),
            UserGroup(
                name="local_authority_early_adopters",
                type=GroupType.LOCAL_AUTHORITY_EARLY_ADOPTERS,
            ),
        ]
    )


def get_ea_user():
    return get_user_with_groups(
        [
            UserGroup(name="ltla_somerset", type=GroupType.LOCAL_AUTHORITY),
            UserGroup(
                name="early_adopter", type=GroupType.LOCAL_AUTHORITY_EARLY_ADOPTERS
            ),
        ]
    )


def get_user_with_no_access():
    return UserFactory()


def get_admin_user():
    return get_user_with_groups([UserGroup(name="dev", type=GroupType.DEV)])


def get_ukvi_user():
    return get_user_with_groups(
        [
            UserGroup(name="home_office_ops", type=GroupType.HOME_OFFICE),
        ]
    )


def get_mhclg_user():
    return get_user_with_groups(
        [
            UserGroup(name="mhclg", type=GroupType.MHCLG),
        ]
    )


def get_service_support_user():
    return get_user_with_groups(
        [
            UserGroup(name="service_support", type=GroupType.SERVICE_SUPPORT),
        ]
    )


def get_da_user():
    return get_user_with_groups(
        [
            UserGroup(name="da_scotland", type=GroupType.DEVOLVED_ADMINISTRATION),
        ]
    )
