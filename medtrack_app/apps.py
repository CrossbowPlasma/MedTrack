from django.apps import AppConfig


class MedtrackAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'medtrack_app'

    def ready(self):
        import medtrack_app.signals
