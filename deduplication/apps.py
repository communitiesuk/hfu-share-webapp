from django.apps import AppConfig

GROUP_MEMBERSHIP_FIELDS_TO_AUDIT = {
    "SponsorDuplicateGroup": ["sponsors"],
    "GuestDuplicateGroup": ["guests"],
    "AccommodationDuplicateGroup": ["accommodations"],
}


class DeduplicationConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "deduplication"

    def ready(self):
        from auditlog.registry import auditlog
        from django.apps import apps

        models = apps.get_app_config("deduplication").get_models()
        for model in models:
            auditlog.register(
                model,
                m2m_fields=GROUP_MEMBERSHIP_FIELDS_TO_AUDIT.get(model.__name__),
            )
