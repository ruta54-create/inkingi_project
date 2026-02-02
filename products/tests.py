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
		# Valid 1x1 pixel GIF image
		gif_data = (
			b'GIF89a\x01\x00\x01\x00\x80\x00\x00\xff\xff\xff'
			b'\x00\x00\x00!\xf9\x04\x01\x00\x00\x00\x00,'
			b'\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;'
		)
		image = SimpleUploadedFile('test.gif', gif_data, content_type='image/gif')
		data = {
			'name': 'Test Product',
			'description': 'A test product',
			'price': '12.50',
			'stock': '5',
			'unit': 'meter',
			'category': 'furniture',
			'image': image,
		}
		response = self.client.post(url, data, follow=True)
		self.assertEqual(response.status_code, 200)
		self.assertTrue(Product.objects.filter(name='Test Product', vendor=self.user).exists())
		messages = list(response.context.get('messages', []))
		self.assertTrue(any('Product added successfully' in str(m) for m in messages))
