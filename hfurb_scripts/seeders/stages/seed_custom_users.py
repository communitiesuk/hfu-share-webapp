import os
from typing import TypedDict

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.db import transaction

from accounts.models import User as UserModel
from browser_tests.test_users import (
    MissingBrowserTestUserEnvVarsException,
    UserType,
    create_browser_test_user,
)


class UserData(TypedDict):
    email: str
    group_name: str


def seed_user(user_data: UserData, password: str, user_model: UserModel):
    email = user_data["email"]
    group_name = user_data["group_name"]
    username = email.split("@", maxsplit=1)[0]

    # Create or get the user
    user, created = user_model.objects.get_or_create(
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
    group.user_set.add(user)  # type: ignore[attr-defined]

    print(f"Added user {email} to group {group_name}")


def seed_browser_test_users():
    User = get_user_model()

    used_emails = []

    with transaction.atomic():
        for user_type in UserType:
            try:
                browser_test_user = create_browser_test_user(user_type)

                if browser_test_user.email in used_emails:
                    print(
                        "Skipping creation of browser test user for "
                        f"'{user_type.name}' as user already exists"
                    )
                    continue

                used_emails.append(browser_test_user.email)

                seed_user(
                    {
                        "email": browser_test_user.email,
                        "group_name": "ltla_hobbiton_browser_test",
                    },
                    browser_test_user.password,
                    User,
                )
            except MissingBrowserTestUserEnvVarsException as e:
                print(f"Skipping creation of browser test user for: {user_type.name}")
                print(e)

    print("Browser test users seeding completed.")


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
            seed_user(user_data, password, User)

    print("Custom users seeding completed.")
