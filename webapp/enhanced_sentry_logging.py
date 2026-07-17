from functools import wraps
from typing import Any

from django.db import models

from case_management.settings import sentry_sdk


def _as_sentry_log_value(value: Any) -> Any:
    if isinstance(value, (bool, int, float)):
        return value
    if value is None:
        return "None"
    return str(value)


def _is_empty(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, (bool, int, float)):
        return False
    return not value


def _values_match_or_both_empty(in_memory: Any, in_db: Any) -> bool:
    if in_memory == in_db:
        return True
    return _is_empty(in_memory) and _is_empty(in_db)


def log_event(message: str, *, level: str = "info", **attributes: Any) -> None:
    safe_attributes = {
        key: _as_sentry_log_value(value) for key, value in attributes.items()
    }
    if level == "warning":
        sentry_sdk.logger.warning(message, **safe_attributes)
    else:
        sentry_sdk.logger.info(message, **safe_attributes)


def log_persistence_check(
    message: str,
    *,
    changes: dict[str, tuple[Any, Any]],
    before: dict[str, Any] | None = None,
    **attributes: Any,
) -> None:
    for field, value in (before or {}).items():
        attributes[f"{field}_before"] = value

    fields_not_persisted = [
        field
        for field, (in_memory, in_db) in changes.items()
        if not _values_match_or_both_empty(in_memory, in_db)
    ]

    for field, (in_memory, in_db) in changes.items():
        attributes[f"{field}_in_memory"] = in_memory
        attributes[f"{field}_persisted"] = in_db

    attributes["persisted_ok"] = not fields_not_persisted

    if fields_not_persisted:
        attributes["fields_not_persisted"] = fields_not_persisted

    log_event(
        message,
        level="warning" if fields_not_persisted else "info",
        **attributes,
    )


def db_values(instance: models.Model, *fields: str) -> dict[str, Any]:
    if hasattr(type(instance), "all_objects"):
        objects = type(instance).all_objects  # type: ignore[attr-defined]
    else:
        objects = type(instance).objects

    return objects.filter(pk=instance.pk).values(*fields).first() or {}


def in_memory_values(instance: models.Model, *fields: str) -> dict[str, Any]:
    snapshot: dict[str, Any] = {}
    for field in fields:
        value = getattr(instance, field)
        snapshot[field] = list(value) if isinstance(value, list) else value
    return snapshot


def exists_when_logging(queryset: models.QuerySet) -> bool:
    return queryset.exists()


def record_operation_outcome(record_type: str):
    def decorator(method):
        @wraps(method)
        def wrapper(self, *args, **kwargs):
            try:
                result = method(self, *args, **kwargs)
            except Exception:
                sentry_sdk.metrics.count(
                    f"{method.__name__}.failed",
                    1,
                    attributes={"record_type": record_type},
                )
                raise
            sentry_sdk.metrics.count(
                f"{method.__name__}.completed",
                1,
                attributes={"record_type": record_type},
            )
            return result

        return wrapper

    return decorator
