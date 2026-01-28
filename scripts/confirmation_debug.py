import os, sys, django
from django.test import Client

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'SokoHub.settings')
django.setup()

from django.contrib.auth import get_user_model
User = get_user_model()

client = Client()
url = '/orders/confirmation/3/'

def print_result(resp):
    print('Status:', resp.status_code)
    print('Final URL:', resp.request.get('PATH_INFO'))
    print('Redirect chain:', resp.redirect_chain)
    print('Templates used:', [t.name for t in resp.templates])
    print('--- content excerpt ---')
    print(resp.content.decode('utf-8', errors='replace')[:800])
    print('\n========================\n')

print('\n=== Anonymous request ===')
resp = client.get(url, follow=True, HTTP_HOST='127.0.0.1')
print_result(resp)

username = 'test_customer'
password = 'testpass123'
user = User.objects.filter(username=username).first()
if user:
    client.login(username=username, password=password)
    print('\n=== Logged in as test_customer ===')
    resp = client.get(url, follow=True, HTTP_HOST='127.0.0.1')
    print_result(resp)
    client.logout()

other_username = 'other_user'
other = User.objects.filter(username=other_username).first()
if not other:
    other = User.objects.create(username=other_username, user_type='customer')
    other.set_password('otherpass')
    other.save()
client.login(username=other_username, password='otherpass')
print('\n=== Logged in as other_user ===')
resp = client.get(url, follow=True, HTTP_HOST='127.0.0.1')
print_result(resp)
