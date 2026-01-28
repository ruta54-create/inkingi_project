from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile

from .models import Product


class AddProductTest(TestCase):
	def setUp(self):
		User = get_user_model()
		self.user = User.objects.create_user(
			username='vendor1', email='vendor@example.com', password='pass123', user_type='vendor'
		)
		self.client.login(username='vendor1', password='pass123')

	def test_vendor_can_add_product(self):
		url = reverse('products:add_product')
		image = SimpleUploadedFile('test.gif', b'GIF87a', content_type='image/gif')
		data = {
			'name': 'Test Product',
			'description': 'A test product',
			'price': '12.50',
			'stock': '5',
			'unit': 'meter',
			'category': 'bed',
		}
		response = self.client.post(url, data, files={'image': image}, follow=True)
		self.assertEqual(response.status_code, 200)
		self.assertTrue(Product.objects.filter(name='Test Product', vendor=self.user).exists())
		messages = list(response.context.get('messages', []))
		self.assertTrue(any('Product added successfully' in str(m) for m in messages))
