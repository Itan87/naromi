from django.apps import AppConfig


class GestionGeneralConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'gestion_general'

    def ready(self):
        import gestion_general.signals  # Register signals