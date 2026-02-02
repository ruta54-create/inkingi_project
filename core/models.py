from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator


class SiteSettings(models.Model):
    """Singleton model for site-wide settings managed by admin"""

    # Branding
    site_name = models.CharField(max_length=100, default='Inkingi Woods Ltd')
    site_tagline = models.CharField(max_length=255, default='Premium Wood Products from Rwanda')
    logo = models.ImageField(upload_to='site/', blank=True, null=True)
    favicon = models.ImageField(upload_to='site/', blank=True, null=True)

    # Banner/Hero Section
    banner_image = models.ImageField(upload_to='site/banners/', blank=True, null=True)
    banner_title = models.CharField(max_length=255, default='Welcome to Inkingi Woods')
    banner_subtitle = models.TextField(blank=True, default='Premium quality wood products from Rwanda')
    banner_video = models.FileField(upload_to='site/videos/', blank=True, null=True,
                                     help_text='Advertising video for the platform')
    banner_video_url = models.URLField(blank=True, null=True,
                                        help_text='YouTube/Vimeo URL for advertising video')
    show_video_on_homepage = models.BooleanField(default=False)

    # Contact Information
    contact_email = models.EmailField(default='info@inkingiwoods.rw')
    contact_phone = models.CharField(max_length=50, default='+250 788 123 456')
    contact_address = models.TextField(default='KG 7 Avenue, Kigali, Rwanda')
    whatsapp_number = models.CharField(max_length=50, blank=True, default='+250788123456')

    # Social Media
    facebook_url = models.URLField(blank=True)
    twitter_url = models.URLField(blank=True)
    instagram_url = models.URLField(blank=True)
    linkedin_url = models.URLField(blank=True)

    # Business Settings
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=18.00,
                                   validators=[MinValueValidator(0), MaxValueValidator(100)],
                                   help_text='Tax rate percentage (e.g., 18 for 18%)')
    standard_delivery_cost = models.DecimalField(max_digits=10, decimal_places=2, default=2000)
    express_delivery_cost = models.DecimalField(max_digits=10, decimal_places=2, default=5000)
    free_delivery_threshold = models.DecimalField(max_digits=10, decimal_places=2, default=50000,
                                                   help_text='Order amount above which delivery is free')

    # Timestamps
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Site Settings'
        verbose_name_plural = 'Site Settings'

    def __str__(self):
        return self.site_name

    def save(self, *args, **kwargs):
        # Ensure only one instance exists
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def get_settings(cls):
        """Get or create the singleton settings instance"""
        obj, created = cls.objects.get_or_create(pk=1)
        return obj


class Currency(models.Model):
    """Currency model for multi-currency support"""
    code = models.CharField(max_length=3, unique=True, primary_key=True)
    name = models.CharField(max_length=50)
    symbol = models.CharField(max_length=10)
    exchange_rate = models.DecimalField(max_digits=12, decimal_places=6, default=1.0,
                                        help_text='Exchange rate relative to RWF (base currency)')
    is_active = models.BooleanField(default=True)
    decimal_places = models.PositiveSmallIntegerField(default=2)

    class Meta:
        verbose_name_plural = 'Currencies'
        ordering = ['code']

    def __str__(self):
        return f"{self.code} - {self.name}"

    def convert_from_rwf(self, amount):
        """Convert amount from RWF to this currency"""
        return round(float(amount) * float(self.exchange_rate), self.decimal_places)

    def convert_to_rwf(self, amount):
        """Convert amount from this currency to RWF"""
        if self.exchange_rate == 0:
            return amount
        return round(float(amount) / float(self.exchange_rate), 2)


class DeliveryTracking(models.Model):
    """GPS tracking for deliveries"""

    STATUS_PENDING = 'pending'
    STATUS_PICKED_UP = 'picked_up'
    STATUS_IN_TRANSIT = 'in_transit'
    STATUS_OUT_FOR_DELIVERY = 'out_for_delivery'
    STATUS_DELIVERED = 'delivered'
    STATUS_FAILED = 'failed'

    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending Pickup'),
        (STATUS_PICKED_UP, 'Picked Up'),
        (STATUS_IN_TRANSIT, 'In Transit'),
        (STATUS_OUT_FOR_DELIVERY, 'Out for Delivery'),
        (STATUS_DELIVERED, 'Delivered'),
        (STATUS_FAILED, 'Delivery Failed'),
    ]

    order = models.OneToOneField('orders.Order', on_delete=models.CASCADE, related_name='tracking')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)

    # Driver/Delivery person info
    driver_name = models.CharField(max_length=100, blank=True)
    driver_phone = models.CharField(max_length=20, blank=True)
    vehicle_number = models.CharField(max_length=20, blank=True)

    # GPS Coordinates
    current_latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    current_longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)

    # Destination coordinates
    destination_latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    destination_longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)

    # Tracking timestamps
    estimated_delivery = models.DateTimeField(null=True, blank=True)
    picked_up_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)

    # Notes
    notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Delivery Tracking'
        verbose_name_plural = 'Delivery Tracking'

    def __str__(self):
        return f"Tracking for Order #{self.order_id}"


class DeliveryTrackingHistory(models.Model):
    """History of GPS location updates"""
    tracking = models.ForeignKey(DeliveryTracking, on_delete=models.CASCADE, related_name='history')
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)
    status = models.CharField(max_length=20)
    note = models.CharField(max_length=255, blank=True)
    recorded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-recorded_at']
        verbose_name = 'Tracking History'
        verbose_name_plural = 'Tracking History'

    def __str__(self):
        return f"{self.tracking.order_id} - {self.recorded_at}"


class AdvertisingBanner(models.Model):
    """Promotional banners for the site"""
    title = models.CharField(max_length=100)
    image = models.ImageField(upload_to='site/ads/')
    link_url = models.URLField(blank=True)
    is_active = models.BooleanField(default=True)
    position = models.CharField(max_length=20, choices=[
        ('homepage_top', 'Homepage Top'),
        ('homepage_middle', 'Homepage Middle'),
        ('sidebar', 'Sidebar'),
        ('product_page', 'Product Page'),
    ], default='homepage_top')
    display_order = models.PositiveIntegerField(default=0)
    start_date = models.DateTimeField(null=True, blank=True)
    end_date = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['display_order', '-created_at']

    def __str__(self):
        return self.title
