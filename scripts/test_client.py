import os
import django
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'SokoHub.settings')
try:
    django.setup()
except Exception as e:
    print('Django setup error:', e)
    sys.exit(1)

from django.test import Client

client = Client()
paths = ['/accounts/', '/orders/my-orders/', '/products/add/', '/']

for p in paths:
    print('\nREQUEST ->', p)
    try:
        resp = client.get(p, follow=True, HTTP_HOST='127.0.0.1')
    except Exception as e:
        print('Request raised exception:', type(e).__name__, e)
        continue
    print('Status code:', resp.status_code)
    if resp.redirect_chain:
        print('Redirect chain:', resp.redirect_chain)
    content = resp.content.decode('utf-8', errors='replace')
    excerpt = content[:1500]
    print('Response content excerpt:\n')
    print(excerpt)
    print('\n--- End of response ---')
