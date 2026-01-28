import os, sys, django
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'SokoHub.settings')
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password

User = get_user_model()

vendor = User.objects.filter(user_type='vendor').first()
if not vendor:
    print('No vendor user found. Create one with createsuperuser or add a vendor user first.')
    sys.exit(1)

vendor.set_password('vendorpass')
vendor.save()

client = Client()
logged = client.login(username=vendor.username, password='vendorpass')
print('Logged in as vendor:', vendor.username, 'success=', logged)

url = '/orders/confirmation/3/'
resp = client.get(url, follow=True, HTTP_HOST='127.0.0.1')
print('GET', url, '=> status', resp.status_code)
print('Redirect chain:', resp.redirect_chain)
print('Final path:', resp.request.get('PATH_INFO'))
print('Templates used:', [t.name for t in resp.templates])
print('\nResponse excerpt:\n')
print(resp.content.decode('utf-8', errors='replace')[:800])
