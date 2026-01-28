import os
import django
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'SokoHub.settings')
django.setup()

from django.contrib.auth import get_user_model
from products.models import Product

User = get_user_model()

vendor, created = User.objects.get_or_create(username='vendor_sample', defaults={'email': 'vendor@example.com', 'user_type': 'vendor'})
if created:
    vendor.set_password('vendorpass')
    vendor.save()
    print('Created vendor_sample / vendorpass')

customer, created = User.objects.get_or_create(username='customer_sample', defaults={'email': 'customer@example.com', 'user_type': 'customer'})
if created:
    customer.set_password('customerpass')
    customer.save()
    print('Created customer_sample / customerpass')

prod1, p1c = Product.objects.get_or_create(name='Sample Product 1', defaults={'description': 'Auto-created product', 'price': 1500.00, 'stock': 20, 'vendor': vendor, 'status': 'active'})
prod2, p2c = Product.objects.get_or_create(name='Sample Product 2', defaults={'description': 'Auto-created product', 'price': 750.00, 'stock': 10, 'vendor': vendor, 'status': 'active'})
if p1c or p2c:
    print('Sample products created')

print('Done.')
