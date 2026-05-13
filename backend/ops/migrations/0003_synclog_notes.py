from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('ops', '0002_synclog_cycle_year_synclog_records_skipped_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='synclog',
            name='notes',
            field=models.TextField(blank=True),
        ),
    ]
