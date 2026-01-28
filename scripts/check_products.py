import os
import django
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'SokoHub.settings')
django.setup()

from products.models import Product

print('Total products:', Product.objects.count())
print('Active products:', Product.objects.filter(status='active').count())
for p in Product.objects.filter(status='active'):
    print('-', p.id, p.name, p.price, 'stock=', p.stock)