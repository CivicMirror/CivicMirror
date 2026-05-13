from django.core.management.base import BaseCommand

from integrations.census.tasks import refresh_district_records


class Command(BaseCommand):
    help = 'Refreshes cached Census OCD divisions and updates stale district records.'

    def handle(self, *args, **options):
        result = refresh_district_records.apply().get()
        self.stdout.write(self.style.SUCCESS(f'District refresh complete: {result}'))
