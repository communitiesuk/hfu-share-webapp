from django.apps import AppConfig


class AccountsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "accounts"

    def ready(self):
        from auditlog.registry import auditlog
        from django.apps import apps

        models = apps.get_app_config("accounts").get_models()
        for model in models:
            if model.__name__ == "User":
                auditlog.register(model, mask_fields=["password"])
            else:
                auditlog.register(model)
