from django.apps import AppConfig


class CivicConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'integrations.civic'
    label = 'civic'
    verbose_name = 'Civic Integrations'
