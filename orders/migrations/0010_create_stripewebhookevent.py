"""Create StripeWebhookEvent model."""

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0009_add_order_stripe_session_id'),
    ]

    operations = [
        migrations.CreateModel(
            name='StripeWebhookEvent',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('stripe_event_id', models.CharField(blank=True, max_length=255, null=True, help_text='Stripe event id (e.g. evt_...)')),
                ('event_type', models.CharField(blank=True, max_length=128, null=True)),
                ('payload', models.TextField(blank=True, null=True)),
                ('headers', models.TextField(blank=True, null=True)),
                ('processed', models.BooleanField(default=False)),
                ('received_at', models.DateTimeField(auto_now_add=True)),
                ('order', models.ForeignKey(blank=True, null=True, on_delete=models.CASCADE, related_name='webhook_events', to='orders.order')),
            ],
            options={
                'ordering': ['-received_at'],
            },
        ),
    ]
