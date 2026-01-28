import os, sys, django
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'SokoHub.settings')
django.setup()
from orders.models import Order
order = Order.objects.filter(id=3).first()
if not order:
    print('Order id=3 not found')
else:
    print('Order id=3: customer=', order.customer.username if order.customer else None, 'total=', order.total, 'status=', order.status)
