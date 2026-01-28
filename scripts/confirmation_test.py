import os
import django
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'SokoHub.settings')
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model

User = get_user_model()
username = 'test_customer'
password = 'testpass123'

user = User.objects.filter(username=username).first()
if not user:
    print('Test user not found; create by running checkout_test first')
    sys.exit(1)

client = Client()
client.login(username=username, password=password)

url = '/orders/confirmation/3/'
resp = client.get(url, follow=True, HTTP_HOST='127.0.0.1')
print('GET', url, '=> status', resp.status_code)
if resp.redirect_chain:
    print('Redirect chain:', resp.redirect_chain)

content = resp.content.decode('utf-8', errors='replace')
print('Response excerpt:')
print(content[:1000])
