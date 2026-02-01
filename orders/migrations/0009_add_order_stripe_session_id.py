"""Auto migration: add stripe_session_id to Order."""

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0008_alter_purchase_options_purchase_refund_reason_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='stripe_session_id',
            field=models.CharField(max_length=255, null=True, blank=True),
        ),
    ]
