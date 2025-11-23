# notificaciones/apps.py
from django.apps import AppConfig

class NotificacionesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'notifications'

    def ready(self):
        import notifications.signals