from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "kill_bill.core"

    def ready(self):
        import kill_bill.core.signals
