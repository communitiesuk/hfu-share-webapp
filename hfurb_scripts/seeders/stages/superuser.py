import os

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.db import transaction


def seed_superuser():
    User = get_user_model()
    email = os.environ.get("ADMIN_EMAIL")
    password = os.environ.get("LOCAL_USER_PASSWORD")
    username = email.split("@")[0]

    with transaction.atomic():
        user, created = User.objects.get_or_create(
            email=email,
            username=username,
            is_staff=True,
            is_superuser=True,
        )

        user.set_password(password)
        user.save()

        if created:
            print(f"Created superuser {email}")
        else:
            print(f"Updated superuser {email}")

        group = Group.objects.get(name="dev")
        group.user_set.add(user)

    print("Superuser seeding completed.")
