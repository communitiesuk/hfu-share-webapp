from django.contrib.auth.models import Group
from django.db import transaction

from accounts.enums import GroupType
from accounts.models.GroupInfo import GroupInfo


def seed_group():
    groups_to_create = [
        (
            "dev",
            GroupType.DEV,
            "Development team",
        ),
        (
            "local_authority",
            GroupType.LOCAL_AUTHORITY,
            "Local Authority",
        ),
        (
            "devolved_administration",
            GroupType.DEVOLVED_ADMINISTRATION,
            "Devolved administration team",
        ),
        (
            "mhclg_ops",
            GroupType.MHCLG,
            "MHCLG operations team",
        ),
        (
            "home_office_ops",
            GroupType.HOME_OFFICE,
            "Home Office operations team",
        ),
        (
            "service_support",
            GroupType.SERVICE_SUPPORT,
            "Service support team",
        ),
    ]

    with transaction.atomic():
        for group_name, group_type, description in groups_to_create:
            group, group_created = Group.objects.get_or_create(name=group_name)

            if group_created:
                print(f"Created group '{group_name}'")
            else:
                print(f"Group '{group_name}' already exists")

            # Create or update GroupInfo
            group_info, info_created = GroupInfo.objects.get_or_create(
                group=group,
                defaults={
                    "group_type": group_type,
                    "description": description,
                },
            )

            if info_created:
                print(f"Created GroupInfo for '{group_name}' with type {group_type}")
            elif group_info.group_type != group_type:
                group_info.group_type = group_type
                group_info.description = description
                group_info.save()
                print(f"Updated GroupInfo for '{group_name}' with type {group_type}")

    print("Group seeding completed.")
