from django.contrib.auth.models import AbstractUser
from django.db import models


# Create your models here.
class CustomUser(AbstractUser):
    VENDOR = 'vendor'
    CUSTOMER = 'customer'
    USER_TYPE_CHOICES = [
        (VENDOR, 'Vendor'),
        (CUSTOMER, 'Customer'),
    ]

    user_type = models.CharField(max_length=20, choices=USER_TYPE_CHOICES, default=CUSTOMER)
    email = models.EmailField(blank=False)
    phone = models.CharField(max_length=20, blank=True)
    location = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return f"{self.username} ({self.get_user_type_display()})"


