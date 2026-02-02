from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
from django.utils.translation import gettext_lazy as _



class Product(models.Model):
    STATUS_ACTIVE = 'active'
    STATUS_INACTIVE = 'inactive'
    STATUS_CHOICES = [
        (STATUS_ACTIVE, _('Active')),
        (STATUS_INACTIVE, _('Inactive')),
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
    # Common unit suggestions for vendors
    UNIT_METER = 'meter'
    UNIT_SQM = 'sqm'
    UNIT_CBM = 'cbm'
    UNIT_PCS = 'pcs'
    UNIT_KG = 'kg'
    UNIT_BUNDLE = 'bundle'
    UNIT_SET = 'set'

    # Suggested units for reference (not enforced)
    SUGGESTED_UNITS = [
        'pcs',           # Pieces
        'meter',         # Per Meter (m)
        'sqm',           # Square Meter (m²)
        'cbm',           # Cubic Meter (m³)
        'kg',            # Kilogram
        'bundle',        # Bundle
        'set',           # Set
        'pair',          # Pair
        'dozen',         # Dozen
        'ft',            # Feet
        'inch',          # Inch
        'cm',            # Centimeter
        'liter',         # Liter
        'board',         # Board
        'plank',         # Plank
    ]

    unit = models.CharField(
        max_length=50,  # Increased length for custom units
        default='pcs',
        help_text='Enter measurement unit (e.g., pcs, meter, sqm, kg, bundle, etc.)'
    )

    # ===== PRODUCT CATEGORIES =====
    # Professional categories matching the navigation dropdown
    CATEGORY_FURNITURE = 'furniture'
    CATEGORY_HOME_OFFICE = 'home_office'
    CATEGORY_OUTDOOR_GARDEN = 'outdoor_garden'
    CATEGORY_DOORS_CONSTRUCTION = 'doors_construction'
    CATEGORY_HANDCRAFTED = 'handcrafted'
    CATEGORY_CUSTOM_MADE = 'custom_made'
    CATEGORY_RAW_MATERIALS = 'raw_materials'
    CATEGORY_KIDS_SCHOOL = 'kids_school'
    CATEGORY_OTHER = 'other'

    CATEGORY_CHOICES = [
        (CATEGORY_FURNITURE, _('Furniture')),
        (CATEGORY_HOME_OFFICE, _('Home & Office')),
        (CATEGORY_OUTDOOR_GARDEN, _('Outdoor & Garden')),
        (CATEGORY_DOORS_CONSTRUCTION, _('Doors & Construction')),
        (CATEGORY_HANDCRAFTED, _('Handcrafted Products')),
        (CATEGORY_CUSTOM_MADE, _('Custom Made')),
        (CATEGORY_RAW_MATERIALS, _('Raw Materials')),
        (CATEGORY_KIDS_SCHOOL, _('Kids & School')),
        (CATEGORY_OTHER, _('Other')),
    ]

    category = models.CharField(
        max_length=30,
        choices=CATEGORY_CHOICES,
        default=CATEGORY_OTHER,
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