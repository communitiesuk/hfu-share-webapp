import json
import os
from contextlib import contextmanager
from pathlib import Path

from django.conf import settings
from django.contrib.auth.models import Group
from django.core import serializers
from django.db import connection, transaction
from django.db.models.signals import (
    m2m_changed,
    post_delete,
    post_save,
    pre_delete,
    pre_save,
)

from accounts.enums import BROWSER_TEST_LA_GROUP_NAME
from accounts.models import User
from hfurb_scripts.browser_test_seed.records import (
    SEED_DATA_DIR,
    wipe_browser_test_la_data,
)

USER_PK_PLACEHOLDER = "__BROWSER_TEST_USER_PK__"
USER_EMAIL_PLACEHOLDER = "__BROWSER_TEST_USER_EMAIL__"
USER_USERNAME_PLACEHOLDER = "__BROWSER_TEST_USER_USERNAME__"
USER_FULL_NAME_PLACEHOLDER = "__BROWSER_TEST_USER_FULL_NAME__"


def browser_test_seeding_allowed() -> bool:
    return settings.ENVIRONMENT == "dev" or settings.DEBUG


def get_browser_test_author() -> User:
    group = Group.objects.get(name=BROWSER_TEST_LA_GROUP_NAME)

    browser_test_email = os.environ.get("BROWSER_TEST_USER_EMAIL")
    if browser_test_email:
        author = User.objects.filter(email=browser_test_email).first()
        if author:
            author.groups.set([group])
            return author

    author = User.objects.filter(groups=group).order_by("email").first()
    if author is None:
        raise ValueError(
            "No browser test user available: set BROWSER_TEST_USER_EMAIL to an "
            f"existing user's email or add a user to the "
            f"{BROWSER_TEST_LA_GROUP_NAME} group"
        )
    return author


@contextmanager
def signals_muted():
    signals = [pre_save, post_save, pre_delete, post_delete, m2m_changed]
    saved = [(signal, signal.receivers) for signal in signals]
    try:
        for signal in signals:
            signal.receivers = []
            signal.sender_receivers_cache.clear()
        yield
    finally:
        for signal, receivers in saved:
            signal.receivers = receivers
            signal.sender_receivers_cache.clear()


def _substitute(value, replacements: dict):
    if isinstance(value, str):
        return replacements.get(value, value)
    if isinstance(value, list):
        return [_substitute(item, replacements) for item in value]
    if isinstance(value, dict):
        return {key: _substitute(item, replacements) for key, item in value.items()}
    return value


def read_seed_data(directory: Path = SEED_DATA_DIR) -> list[dict]:
    records: list[dict] = []
    for path in sorted(directory.glob("*.json")):
        with open(path) as f:
            try:
                records.extend(json.load(f))
            except json.JSONDecodeError as exc:
                raise ValueError(
                    f"browser test seed data file {path.name} is not valid JSON: {exc}"
                ) from exc
    return records


def load_browser_test_seed_data(directory: Path = SEED_DATA_DIR) -> int:
    author = get_browser_test_author()
    replacements = {
        USER_PK_PLACEHOLDER: author.pk,
        USER_EMAIL_PLACEHOLDER: author.email,
        USER_USERNAME_PLACEHOLDER: author.username,
        USER_FULL_NAME_PLACEHOLDER: author.get_full_name(),
    }
    records = _substitute(read_seed_data(directory), replacements)

    with connection.constraint_checks_disabled():
        loaded = 0
        for deserialized in serializers.deserialize("python", records):
            deserialized.save()
            loaded += 1
    connection.check_constraints()
    return loaded


def reset_browser_test_la(directory: Path = SEED_DATA_DIR) -> int:
    if not browser_test_seeding_allowed():
        raise RuntimeError(
            "browser test seeding only runs in dev or local environments"
        )
    with signals_muted(), transaction.atomic():
        wipe_browser_test_la_data()
        loaded = load_browser_test_seed_data(directory)
    print(f"Loaded {loaded} browser test records from {directory}")
    return loaded
