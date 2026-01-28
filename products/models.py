from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator



class Product(models.Model):
    STATUS_ACTIVE = 'active'
    STATUS_INACTIVE = 'inactive'
    STATUS_CHOICES = [
        (STATUS_ACTIVE, 'Active'),
        (STATUS_INACTIVE, 'Inactive'),
    ]

    vendor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='products'
    )

    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)

    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )

    stock = models.PositiveIntegerField(default=0)

    # ===== WOOD PRODUCT UNITS =====
   # UNIT_PCS = 'pcs'
    UNIT_METER = 'meter'
    UNIT_SQM = 'sqm'
    UNIT_CBM = 'cbm'
    #UNIT_BUNDLE = 'bundle'
    #UNIT_SET = 'set'

    UNIT_CHOICES = [
       # (UNIT_PCS, 'Pieces'),
        (UNIT_METER, ' Per Meter (m)'),
        (UNIT_SQM, 'per Square Meter (m²)'),
        #(UNIT_CBM, 'Cubic Meter (m³)'),
       # (UNIT_BUNDLE, 'Bundle'),
       # (UNIT_SET, 'Set'),
    ]

    unit = models.CharField(
        max_length=20,
        choices=UNIT_CHOICES,
        default=UNIT_METER
    )

    image = models.ImageField(upload_to='products/', blank=True, null=True)

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_ACTIVE
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.unit}) - {self.vendor.username}"