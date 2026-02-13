from django.db import migrations, models
import djmoney.models.fields


class Migration(migrations.Migration):

    dependencies = [
        ("adventures", "0084_collection_adventure_type"),
    ]

    operations = [
        # Add currency field first (required by MoneyField)
        migrations.AddField(
            model_name="visit",
            name="total_price_currency",
            field=djmoney.models.fields.CurrencyField(
                default="USD", editable=False, max_length=3
            ),
        ),
        # Add the MoneyField for total_price
        migrations.AddField(
            model_name="visit",
            name="total_price",
            field=djmoney.models.fields.MoneyField(
                blank=True,
                decimal_places=2,
                default_currency="USD",
                max_digits=12,
                null=True,
            ),
        ),
        # Add number_of_people field
        migrations.AddField(
            model_name="visit",
            name="number_of_people",
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
    ]
