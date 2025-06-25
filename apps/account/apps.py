# apps/account/apps.py (Corrected Version)

from django.apps import AppConfig

class AccountConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.account'

    def ready(self):
        """
        Import signals here to ensure they are registered when the app loads.
        """
        import apps.account.signals # triggers signal registration

