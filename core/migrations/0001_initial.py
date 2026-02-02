from django.db import migrations, models
import django.core.validators
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('orders', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='SiteSettings',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('site_name', models.CharField(default='Inkingi Woods Ltd', max_length=100)),
                ('site_tagline', models.CharField(default='Premium Wood Products from Rwanda', max_length=255)),
                ('logo', models.ImageField(blank=True, null=True, upload_to='site/')),
                ('favicon', models.ImageField(blank=True, null=True, upload_to='site/')),
                ('banner_image', models.ImageField(blank=True, null=True, upload_to='site/banners/')),
                ('banner_title', models.CharField(default='Welcome to Inkingi Woods', max_length=255)),
                ('banner_subtitle', models.TextField(blank=True, default='Premium quality wood products from Rwanda')),
                ('banner_video', models.FileField(blank=True, help_text='Advertising video for the platform', null=True, upload_to='site/videos/')),
                ('banner_video_url', models.URLField(blank=True, help_text='YouTube/Vimeo URL for advertising video', null=True)),
                ('show_video_on_homepage', models.BooleanField(default=False)),
                ('contact_email', models.EmailField(default='info@inkingiwoods.rw', max_length=254)),
                ('contact_phone', models.CharField(default='+250 788 123 456', max_length=50)),
                ('contact_address', models.TextField(default='KG 7 Avenue, Kigali, Rwanda')),
                ('whatsapp_number', models.CharField(blank=True, default='+250788123456', max_length=50)),
                ('facebook_url', models.URLField(blank=True)),
                ('twitter_url', models.URLField(blank=True)),
                ('instagram_url', models.URLField(blank=True)),
                ('linkedin_url', models.URLField(blank=True)),
                ('tax_rate', models.DecimalField(decimal_places=2, default=18.0, help_text='Tax rate percentage (e.g., 18 for 18%)', max_digits=5, validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(100)])),
                ('standard_delivery_cost', models.DecimalField(decimal_places=2, default=2000, max_digits=10)),
                ('express_delivery_cost', models.DecimalField(decimal_places=2, default=5000, max_digits=10)),
                ('free_delivery_threshold', models.DecimalField(decimal_places=2, default=50000, help_text='Order amount above which delivery is free', max_digits=10)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Site Settings',
                'verbose_name_plural': 'Site Settings',
            },
        ),
        migrations.CreateModel(
            name='Currency',
            fields=[
                ('code', models.CharField(max_length=3, primary_key=True, serialize=False, unique=True)),
                ('name', models.CharField(max_length=50)),
                ('symbol', models.CharField(max_length=10)),
                ('exchange_rate', models.DecimalField(decimal_places=6, default=1.0, help_text='Exchange rate relative to RWF (base currency)', max_digits=12)),
                ('is_active', models.BooleanField(default=True)),
                ('decimal_places', models.PositiveSmallIntegerField(default=2)),
            ],
            options={
                'verbose_name_plural': 'Currencies',
                'ordering': ['code'],
            },
        ),
        migrations.CreateModel(
            name='DeliveryTracking',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.CharField(choices=[('pending', 'Pending Pickup'), ('picked_up', 'Picked Up'), ('in_transit', 'In Transit'), ('out_for_delivery', 'Out for Delivery'), ('delivered', 'Delivered'), ('failed', 'Delivery Failed')], default='pending', max_length=20)),
                ('driver_name', models.CharField(blank=True, max_length=100)),
                ('driver_phone', models.CharField(blank=True, max_length=20)),
                ('vehicle_number', models.CharField(blank=True, max_length=20)),
                ('current_latitude', models.DecimalField(blank=True, decimal_places=6, max_digits=9, null=True)),
                ('current_longitude', models.DecimalField(blank=True, decimal_places=6, max_digits=9, null=True)),
                ('destination_latitude', models.DecimalField(blank=True, decimal_places=6, max_digits=9, null=True)),
                ('destination_longitude', models.DecimalField(blank=True, decimal_places=6, max_digits=9, null=True)),
                ('estimated_delivery', models.DateTimeField(blank=True, null=True)),
                ('picked_up_at', models.DateTimeField(blank=True, null=True)),
                ('delivered_at', models.DateTimeField(blank=True, null=True)),
                ('notes', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('order', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='tracking', to='orders.order')),
            ],
            options={
                'verbose_name': 'Delivery Tracking',
                'verbose_name_plural': 'Delivery Tracking',
            },
        ),
        migrations.CreateModel(
            name='DeliveryTrackingHistory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('latitude', models.DecimalField(decimal_places=6, max_digits=9)),
                ('longitude', models.DecimalField(decimal_places=6, max_digits=9)),
                ('status', models.CharField(max_length=20)),
                ('note', models.CharField(blank=True, max_length=255)),
                ('recorded_at', models.DateTimeField(auto_now_add=True)),
                ('tracking', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='history', to='core.deliverytracking')),
            ],
            options={
                'verbose_name': 'Tracking History',
                'verbose_name_plural': 'Tracking History',
                'ordering': ['-recorded_at'],
            },
        ),
        migrations.CreateModel(
            name='AdvertisingBanner',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=100)),
                ('image', models.ImageField(upload_to='site/ads/')),
                ('link_url', models.URLField(blank=True)),
                ('is_active', models.BooleanField(default=True)),
                ('position', models.CharField(choices=[('homepage_top', 'Homepage Top'), ('homepage_middle', 'Homepage Middle'), ('sidebar', 'Sidebar'), ('product_page', 'Product Page')], default='homepage_top', max_length=20)),
                ('display_order', models.PositiveIntegerField(default=0)),
                ('start_date', models.DateTimeField(blank=True, null=True)),
                ('end_date', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'ordering': ['display_order', '-created_at'],
            },
        ),
    ]
