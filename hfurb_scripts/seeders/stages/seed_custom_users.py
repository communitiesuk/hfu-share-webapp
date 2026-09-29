import os

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.db import transaction

from accounts.models import User as UserModel

from ..users import (
    CUSTOM_USERS_TO_CREATE,
    CustomUser,
    MissingBrowserTestUserEnvVarsException,
    UserType,
    build_browser_test_user,
)


def seed_user(custom_user: CustomUser, user_model: UserModel):
    username = custom_user.email.split("@", maxsplit=1)[0]

    # Create or get the user
    user, created = user_model.objects.get_or_create(
        email=custom_user.email,
        username=username,
        is_staff=False,
        is_superuser=False,
    )

    user.set_password(custom_user.password)
    user.save()

    if created:
        print(f"Created user {custom_user.email}")
    else:
        print(f"Updated user {custom_user.email}")

    # Add user to the specified group
    group = Group.objects.get(name=custom_user.group_name)
    group.user_set.add(user)  # type: ignore[attr-defined]

    print(f"Added user {custom_user.email} to group {custom_user.group_name}")


def seed_browser_test_users():
    User = get_user_model()

    used_emails = []

    with transaction.atomic():
        for user_type in UserType:
            try:
                browser_test_user = build_browser_test_user(user_type)

                if browser_test_user.email in used_emails:
                    print(
                        "Skipping creation of browser test user for "
                        f"'{user_type.name}' as user already exists"
                    )
                    continue

                used_emails.append(browser_test_user.email)

                seed_user(
                    browser_test_user,
                    User,
                )
            except MissingBrowserTestUserEnvVarsException as e:
                print(f"Skipping creation of browser test user for: {user_type.name}")
                print(e)

    print("Browser test users seeding completed.")


def seed_custom_users():
    User = get_user_model()
    password = os.environ.get("LOCAL_USER_PASSWORD")

    with transaction.atomic():
        for email, group_name in CUSTOM_USERS_TO_CREATE:
            seed_user(
                CustomUser(
                    email=email,
                    group_name=group_name,
                    password=password,
                ),
                User,
            )

    print("Custom users seeding completed.")
