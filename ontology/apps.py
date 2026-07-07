from django.apps import AppConfig


class OntologyConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "ontology"

    def ready(self):
        from auditlog.registry import auditlog
        from django.apps import apps

        models = apps.get_app_config("ontology").get_models()
        for model in models:
            auditlog.register(model)
        import ontology.signals  # noqa
