import os, sys, django
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'SokoHub.settings')
django.setup()

from orders.models import OrderItem, Order
order = Order.objects.filter(id=3).first()
if not order:
    print('Order 3 not found')
    sys.exit(0)

items = OrderItem.objects.filter(order=order)
print('Order', order.id, 'customer=', order.customer.username if order.customer else None)
for it in items:
    prod = it.product
    print('Item:', prod.name, 'qty=', it.quantity, 'vendor=', prod.vendor.username if prod.vendor else None)
