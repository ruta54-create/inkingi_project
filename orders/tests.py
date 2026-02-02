from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django.contrib.auth import get_user_model
from products.models import Product
from orders.models import Purchase
from django.core import mail
import json
from unittest.mock import patch
from django.conf import settings

User = get_user_model()

@override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
class MockPaymentTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.vendor = User.objects.create_user(username='vendor1', password='pass', user_type='vendor', email='v@example.com')
        self.customer = User.objects.create_user(username='cust1', password='pass', user_type='customer', email='c@example.com')
        self.product = Product.objects.create(vendor=self.vendor, name='Test Wood', price=100.00, stock=10)

    def test_mock_pay_creates_purchase(self):
        self.client.login(username='cust1', password='pass')
        url = reverse('orders:mock_pay', args=[self.product.id])
        resp = self.client.post(url, {'quantity': 2, 'payment_method': 'momo', 'mobile_number': '250788123456'})
        self.assertEqual(resp.status_code, 200)
        p = Purchase.objects.filter(customer=self.customer, product=self.product).first()
        self.assertIsNotNone(p)
        self.assertEqual(p.quantity, 2)
        self.assertEqual(p.payment_method, 'momo')
        # ensure an email was sent to the customer
        self.assertGreaterEqual(len(mail.outbox), 1)
        self.assertIn(self.product.name, mail.outbox[0].body)

    def test_checkout_cart_creates_purchases(self):
        # add to session cart
        session = self.client.session
        session['cart'] = {str(self.product.id): 3}
        session.save()
        self.client.login(username='cust1', password='pass')
        url = reverse('orders:checkout_cart')
        resp = self.client.post(url, {'payment_method': 'bank', 'mobile_number': ''})
        # Should redirect to confirmation
        self.assertEqual(resp.status_code, 302)
        p = Purchase.objects.filter(customer=self.customer, product=self.product).first()
        self.assertIsNotNone(p)
        self.assertEqual(p.quantity, 3)
        self.assertEqual(p.payment_method, 'bank')
        # ensure emails were sent (customer + possibly vendor)
        self.assertGreaterEqual(len(mail.outbox), 1)
        # at least one message should include product name
        bodies = '\n'.join(m.body for m in mail.outbox)
        self.assertIn(self.product.name, bodies)

    def test_refund_endpoint_restocks(self):
        # create staff user
        staff = User.objects.create_user(username='staff', password='pass', user_type='customer', email='s@example.com', is_staff=True)
        # create a purchase
        purchase = Purchase.objects.create(customer=self.customer, product=self.product, quantity=2, amount=200, payment_method='bank')
        # reduce stock to simulate sale
        self.product.stock = self.product.stock - 2
        self.product.save()
        self.client.login(username='staff', password='pass')
        url = reverse('company_admin:refund_purchase', args=[purchase.id])
        resp = self.client.post(url)
        self.assertEqual(resp.status_code, 302)
        purchase.refresh_from_db()
        self.product.refresh_from_db()
        self.assertTrue(purchase.refunded)
        self.assertEqual(self.product.stock, 10)  # original 10 restored

    def test_stripe_webhook_finalizes_order(self):
        # prepare an order server-side
        self.client.login(username='cust1', password='pass')
        order = None
        # create order and item using view flow
        from orders.models import Order, OrderItem
        order = Order.objects.create(customer=self.customer, total=100.0, status='pending', delivery_address='', phone='')
        OrderItem.objects.create(order=order, product=self.product, quantity=2, price=self.product.price)

        # simulate stripe webhook event payload
        fake_session = {
            'id': 'cs_test_123',
            'metadata': {'order_id': str(order.id)}
        }
        fake_event = {'type': 'checkout.session.completed', 'data': {'object': fake_session}}

        # patch stripe.Webhook.construct_event to return our fake event
        with patch('orders.views.stripe') as mock_stripe:
            mock_stripe.Webhook.construct_event.return_value = fake_event
            url = reverse('orders:stripe_webhook')
            resp = self.client.post(url, data=json.dumps({'dummy': 'data'}), content_type='application/json')
            self.assertEqual(resp.status_code, 200)

        # order should be marked completed and purchases created
        order.refresh_from_db()
        self.assertEqual(order.status, 'completed')
        from orders.models import Purchase
        p = Purchase.objects.filter(transaction_id='cs_test_123').first()
        self.assertIsNotNone(p)
        self.assertEqual(p.quantity, 2)

    def test_admin_reprocess_events(self):
        # create staff superuser
        staff = User.objects.create_user(username='admin', password='pass', email='a@example.com', is_staff=True, is_superuser=True)
        # prepare an order server-side
        order = None
        from orders.models import Order, OrderItem, StripeWebhookEvent
        order = Order.objects.create(customer=self.customer, total=100.0, status='pending', delivery_address='', phone='')
        OrderItem.objects.create(order=order, product=self.product, quantity=2, price=self.product.price)

        # fake stripe session and event
        fake_session = {
            'id': 'cs_test_admin_123',
            'metadata': {'order_id': str(order.id)}
        }
        fake_event = {'type': 'checkout.session.completed', 'data': {'object': fake_session}}

        # save a StripeWebhookEvent record as if persisted by webhook view
        ev = StripeWebhookEvent.objects.create(stripe_event_id='evt_admin_1', event_type='checkout.session.completed', payload=json.dumps(fake_event), headers='{}', processed=False)

        # login admin and call admin action to reprocess
        self.client.login(username='admin', password='pass')
        from django.urls import reverse

        # Step 1: Initiate reprocess action - this redirects to confirmation page
        url = reverse('admin:orders_stripewebhookevent_changelist')
        resp = self.client.post(url, {'action': 'reprocess_events', '_selected_action': [str(ev.id)]})
        self.assertEqual(resp.status_code, 302)  # Should redirect to confirmation

        # Step 2: Post to confirmation page with 'confirm' to actually process
        confirm_url = reverse('admin:orders_stripewebhookevent_reprocess_confirmation')
        resp = self.client.post(confirm_url, {'confirm': 'true', 'selected_ids': [str(ev.id)]})
        # admin redirects back to changelist on success
        self.assertIn(resp.status_code, (302, 200))

        # refresh and assert processed and order finalized
        ev.refresh_from_db()
        order.refresh_from_db()
        self.assertTrue(ev.processed)
        self.assertEqual(order.status, 'completed')
        from orders.models import Purchase
        p = Purchase.objects.filter(transaction_id='cs_test_admin_123').first()
        self.assertIsNotNone(p)
        self.assertEqual(p.quantity, 2)
