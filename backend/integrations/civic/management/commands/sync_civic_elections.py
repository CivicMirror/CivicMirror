from django.core.management.base import BaseCommand

from integrations.civic.tasks import sync_elections


class Command(BaseCommand):
    help = 'Synchronously imports elections, then queues representative address race sync tasks.'

    def handle(self, *args, **options):
        result = sync_elections.apply().get()
        self.stdout.write(self.style.SUCCESS(f"Election sync complete: {result}"))
