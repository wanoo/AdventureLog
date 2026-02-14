# Generated manually

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('worldtravel', '0019_country_currency_exchangerate'),
        ('adventures', '0085_visit_price_fields'),
    ]

    operations = [
        # Add country, region, city to Lodging
        migrations.AddField(
            model_name='lodging',
            name='country',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='lodgings', to='worldtravel.country'),
        ),
        migrations.AddField(
            model_name='lodging',
            name='region',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='lodgings', to='worldtravel.region'),
        ),
        migrations.AddField(
            model_name='lodging',
            name='city',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='lodgings', to='worldtravel.city'),
        ),
        # Add origin_country and destination_country to Transportation
        migrations.AddField(
            model_name='transportation',
            name='origin_country',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='transportation_origins', to='worldtravel.country'),
        ),
        migrations.AddField(
            model_name='transportation',
            name='destination_country',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='transportation_destinations', to='worldtravel.country'),
        ),
    ]
