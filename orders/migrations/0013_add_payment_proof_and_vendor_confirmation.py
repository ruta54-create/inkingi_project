from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('orders', '0012_order_tax_amount_order_tax_rate'),
    ]

    operations = [
        # Add GPS coordinates for delivery
        migrations.AddField(
            model_name='order',
            name='delivery_latitude',
            field=models.DecimalField(blank=True, decimal_places=6, max_digits=9, null=True),
        ),
        migrations.AddField(
            model_name='order',
            name='delivery_longitude',
            field=models.DecimalField(blank=True, decimal_places=6, max_digits=9, null=True),
        ),
        # Add payment proof fields
        migrations.AddField(
            model_name='order',
            name='payment_proof',
            field=models.ImageField(blank=True, help_text='Upload screenshot/proof of payment', null=True, upload_to='payment_proofs/'),
        ),
        migrations.AddField(
            model_name='order',
            name='payment_proof_uploaded_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        # Add vendor confirmation fields
        migrations.AddField(
            model_name='order',
            name='vendor_confirmed',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='order',
            name='vendor_confirmed_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='order',
            name='vendor_confirmed_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='confirmed_orders', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='order',
            name='vendor_rejection_reason',
            field=models.TextField(blank=True, null=True),
        ),
        # Update status choices to include awaiting_confirmation
        migrations.AlterField(
            model_name='order',
            name='status',
            field=models.CharField(choices=[('pending', 'Pending Payment'), ('awaiting_confirmation', 'Awaiting Vendor Confirmation'), ('processing', 'Processing'), ('shipped', 'Shipped'), ('delivered', 'Delivered'), ('completed', 'Completed'), ('cancelled', 'Cancelled')], default='pending', max_length=20),
        ),
    ]
