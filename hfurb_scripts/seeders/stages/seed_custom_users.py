import os

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.db import transaction


def seed_custom_users():
    User = get_user_model()
    password = os.environ.get("LOCAL_USER_PASSWORD")

    users_to_create = [
        {
            "email": "mhclg_ops@example.com",
            "group_name": "mhclg_ops",
        },
        {
            "email": "home_office_ops@example.com",
            "group_name": "home_office_ops",
        },
        {
            "email": "service_support@example.com",
            "group_name": "service_support",
        },
        {
            "email": "da@example.com",
            "group_name": "devolved_administration",
        },
        {
            "email": "croydon@example.com",
            "group_name": "ltla_croydon",
        },
        {
            "email": "bromley@example.com",
            "group_name": "ltla_bromley",
        },
        {
            "email": "lewisham@example.com",
            "group_name": "ltla_lewisham",
        },
    ]

    with transaction.atomic():
        for user_data in users_to_create:
            email = user_data["email"]
            group_name = user_data["group_name"]
            username = email.split("@", maxsplit=1)[0]

            # Create or get the user
            user, created = User.objects.get_or_create(
                email=email,
                username=username,
                is_staff=False,
                is_superuser=False,
            )

            user.set_password(password)
            user.save()

            if created:
                print(f"Created user {email}")
            else:
                print(f"Updated user {email}")

            # Add user to the specified group
            group = Group.objects.get(name=group_name)
            group.user_set.add(user)

            print(f"Added user {email} to group {group_name}")

    print("Custom users seeding completed.")
