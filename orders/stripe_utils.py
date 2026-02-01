import json
import decimal
import logging
from django.conf import settings
from .models import Purchase, PurchaseLog, Order
from django.template.loader import render_to_string
from django.core.mail import EmailMessage

logger = logging.getLogger(__name__)


def process_stripe_event(event, saved_event=None):
    """Process a Stripe event dict. Can be called from webhook or admin reprocess.

    - Handles checkout.session.completed with order_id metadata.
    - Creates Purchase records, PurchaseLog, decrements stock, sends emails.
    - Returns True if processed successfully, False otherwise.
    """
    try:
        etype = event.get('type')
        if etype != 'checkout.session.completed':
            return False

        session = event['data']['object']
        meta = session.get('metadata', {}) or {}
        order_id = meta.get('order_id')
        if not order_id:
            return False

        try:
            oid = int(order_id)
        except Exception:
            return False

        order = Order.objects.filter(id=oid).first()
        if not order:
            return False

        # idempotency: if any Purchase exists with this transaction id, skip
        txid = session.get('id')
        if txid and Purchase.objects.filter(transaction_id=txid).exists():
            return True

        for item in order.items.all():
            purchase = Purchase.objects.create(
                customer=order.customer,
                product=item.product,
                quantity=item.quantity,
                amount=item.price * item.quantity,
                payment_method='stripe',
                transaction_id=txid,
            )
            PurchaseLog.objects.create(purchase=purchase, action=PurchaseLog.ACTION_PURCHASE, actor=order.customer, note=f'Order #{order.id} (Stripe)')
            # send emails (best-effort)
            try:
                html = render_to_string('emails/purchase.html', {'purchase': purchase, 'user': order.customer})
                msg = EmailMessage(subject=f'Purchase #{purchase.id} recorded', body=html, from_email=settings.DEFAULT_FROM_EMAIL, to=[order.customer.email])
                msg.content_subtype = 'html'
                msg.send(fail_silently=True)
                vendor_email = getattr(item.product.vendor, 'email', None)
                if vendor_email:
                    vhtml = render_to_string('emails/purchase.html', {'purchase': purchase, 'user': item.product.vendor})
                    vmsg = EmailMessage(subject=f'Your product purchased: {purchase.product.name}', body=vhtml, from_email=settings.DEFAULT_FROM_EMAIL, to=[vendor_email])
                    vmsg.content_subtype = 'html'
                    vmsg.send(fail_silently=True)
            except Exception:
                logger.exception('Failed to send purchase emails')

            # decrement stock
            item.product.stock = item.product.stock - item.quantity
            item.product.save()

        # mark order completed
        order.status = Order.STATUS_COMPLETED
        order.save()
        if saved_event:
            saved_event.processed = True
            saved_event.save()
        return True
    except Exception:
        logger.exception('Error processing stripe event')
        return False
