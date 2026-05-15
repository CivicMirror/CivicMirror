import datetime

from django.db import migrations


def seed_initial_terms_version(apps, schema_editor):
    TermsOfUseVersion = apps.get_model('legal', 'TermsOfUseVersion')
    TermsOfUseVersion.objects.update_or_create(
        version='2025-01',
        defaults={
            'content_checksum': 'initial-terms-2025-01',
            'published_at': datetime.datetime(2025, 1, 1, tzinfo=datetime.timezone.utc),
            'is_active': True,
        },
    )


def reverse_seed(apps, schema_editor):
    TermsOfUseVersion = apps.get_model('legal', 'TermsOfUseVersion')
    TermsOfUseVersion.objects.filter(version='2025-01').delete()


class Migration(migrations.Migration):

    dependencies = [
        ('legal', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(seed_initial_terms_version, reverse_code=reverse_seed),
    ]
