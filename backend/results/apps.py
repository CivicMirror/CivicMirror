from django.apps import AppConfig


class ResultsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'results'
    verbose_name = 'Results'

    def ready(self):
        import results.adapters.ca  # noqa: F401
        import results.adapters.co  # noqa: F401
        import results.adapters.ma  # noqa: F401
