from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('adventures', '0079_fix_state_and_add_visit_rating'),
    ]

    operations = [
        migrations.AddField(
            model_name='location',
            name='average_rating',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='transportation',
            name='average_rating',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='lodging',
            name='average_rating',
            field=models.FloatField(blank=True, null=True),
        ),
    ]
