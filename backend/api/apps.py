from django.apps import AppConfig


class AppsConfig(AppConfig):
    name = 'backend.api'

    def ready(self):
        from .signals import receivers
