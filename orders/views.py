# orders/views.py
from django.shortcuts import render, get_object_or_404, redirect, reverse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import CheckoutForm
from .models import Order, OrderItem, Purchase, PurchaseLog
from products.models import Product
from django.http import JsonResponse
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone

@login_required
def checkout(request, product_id):
    if getattr(request.user, 'user_type', None) != 'customer':
        messages.error(request, "Only customers can place orders. Please log in as a customer.")
        return redirect('products:product_list')  

    product = get_object_or_404(Product, id=product_id)

    if product.stock <= 0:
        messages.error(request, "This product is out of stock.")
        return redirect('products:product_detail', pk=product.id)  

    if request.method == 'POST':
        form = CheckoutForm(request.POST)
        if form.is_valid():
            qty = form.cleaned_data['quantity']
            address = form.cleaned_data['delivery_address']
            phone = form.cleaned_data['phone']
            payment_method = form.cleaned_data.get('payment_method', 'momo')
            mobile_number = form.cleaned_data.get('mobile_number', '')
            delivery_option = form.cleaned_data.get('delivery_option', 'standard')
            delivery_notes = form.cleaned_data.get('delivery_notes', '')
            
            # Calculate delivery cost
            delivery_cost = form.get_delivery_cost()
            
            # Calculate subtotal and tax
            subtotal = product.price * qty
            tax_rate = 0.18  # 18% VAT for Rwanda
            tax_amount = (subtotal + delivery_cost) * tax_rate
            total = subtotal + delivery_cost + tax_amount

            if qty > product.stock:
                form.add_error('quantity', 'Not enough stock available.')
            else:
                order = Order.objects.create(
                    customer=request.user,
                    total=total,
                    status='pending',
                    delivery_address=address,
                    phone=phone,
                    delivery_option=delivery_option,
                    delivery_cost=delivery_cost,
                    delivery_notes=delivery_notes,
                    payment_method=payment_method,
                    payment_reference=mobile_number if payment_method in ['momo', 'airtel', 'tigo'] else '',
                    tax_rate=tax_rate,
                    tax_amount=tax_amount
                )

                OrderItem.objects.create(
                    order=order,
                    product=product,
                    quantity=qty,
                    price=product.price
                )

                # Don't decrement stock or create purchase yet - wait for payment confirmation
                messages.success(request, "Order created successfully. Please complete payment.")
                return redirect('orders:payment_processing', order_id=order.id)
    else:
    
        initial = {
            'quantity': 1,
            'delivery_address': getattr(request.user, 'location', ''),
            'phone': getattr(request.user, 'phone', ''),
        }
        form = CheckoutForm(initial=initial)

    if form.is_bound:
        if form.is_valid():
            preview_qty = form.cleaned_data.get('quantity', 1)
        else:
            try:
                preview_qty = int(form.data.get('quantity', 1))
            except (TypeError, ValueError):
                preview_qty = int(form.initial.get('quantity', 1))
    else:
        preview_qty = int(form.initial.get('quantity', 1))

    total_preview = product.price * preview_qty
    return render(request, 'checkout.html', {
        'product': product,
        'form': form,
        'total_preview': total_preview,
    })


@login_required
def payment_processing(request, order_id):
    """Display payment processing page with realistic payment gateway simulation"""
    order = get_object_or_404(Order, id=order_id, customer=request.user)
    
    # Simulate payment gateway selection based on payment method
    payment_gateways = {
        'momo': {
            'name': 'MTN Mobile Money',
            'logo': 'mtn-logo.png',
            'color': '#FFCC00',
            'instructions': 'You will be redirected to MTN Mobile Money to complete your payment.',
            'processing_time': '2-3 minutes'
        },
        'airtel': {
            'name': 'Airtel Money',
            'logo': 'airtel-logo.png', 
            'color': '#E60012',
            'instructions': 'You will be redirected to Airtel Money to complete your payment.',
            'processing_time': '2-3 minutes'
        },
        'tigo': {
            'name': 'Tigo Cash',
            'logo': 'tigo-logo.png',
            'color': '#0066CC',
            'instructions': 'You will be redirected to Tigo Cash to complete your payment.',
            'processing_time': '2-3 minutes'
        },
        'bank': {
            'name': 'Bank Transfer',
            'logo': 'bank-logo.png',
            'color': '#28A745',
            'instructions': 'You will be redirected to your bank\'s secure payment portal.',
            'processing_time': '3-5 minutes'
        },
        'card': {
            'name': 'Credit/Debit Card',
            'logo': 'card-logo.png',
            'color': '#007BFF',
            'instructions': 'You will be redirected to our secure card payment processor.',
            'processing_time': '1-2 minutes'
        },
        'cash': {
            'name': 'Cash on Delivery',
            'logo': 'cash-logo.png',
            'color': '#6C757D',
            'instructions': 'Your order is confirmed. Pay when you receive your items.',
            'processing_time': 'Immediate'
        }
    }
    
    gateway = payment_gateways.get(order.payment_method, payment_gateways['momo'])
    
    return render(request, 'orders/payment_processing.html', {
        'order': order,
        'gateway': gateway,
        'items': order.items.all()
    })


@login_required 
def payment_confirm(request, order_id):
    """Handle payment confirmation and simulate payment processing"""
    order = get_object_or_404(Order, id=order_id, customer=request.user)
    
    if request.method == 'POST':
        # Simulate payment processing delay and validation
        import time
        import uuid
        import random
        
        # Get payment details from form
        payment_reference = request.POST.get('payment_reference', '')
        payment_pin = request.POST.get('payment_pin', '')
        
        # Simulate payment processing
        processing_success = True  # In real world, this would be API response
        
        if processing_success:
            # Generate realistic transaction ID
            txid = f"{order.payment_method.upper()}-{uuid.uuid4().hex[:12].upper()}"
            
            # Update order with payment details
            order.payment_reference = payment_reference or txid
            order.status = Order.STATUS_PROCESSING
            order.save()
            
            # Create purchase records and track the first one for email
            first_purchase = None
            for item in order.items.all():
                purchase = Purchase.objects.create(
                    customer=request.user,
                    product=item.product,
                    quantity=item.quantity,
                    amount=item.price * item.quantity,
                    payment_method=order.payment_method,
                    transaction_id=txid,
                )
                
                if first_purchase is None:
                    first_purchase = purchase
                
                # Create purchase log
                PurchaseLog.objects.create(
                    purchase=purchase, 
                    action=PurchaseLog.ACTION_PURCHASE, 
                    actor=request.user, 
                    note=f'Order #{order.id} - {order.get_payment_method_display()}'
                )
                
                # Update stock
                item.product.stock -= item.quantity
                item.product.save()
            
            # Send confirmation emails
            try:
                from django.template.loader import render_to_string
                from django.core.mail import EmailMessage
                
                # Customer email - use first purchase for template
                html = render_to_string('emails/purchase.html', {
                    'purchase': first_purchase, 
                    'user': request.user,
                    'order': order
                })
                msg = EmailMessage(
                    subject=f'Payment Confirmed - Order #{order.id}',
                    body=html,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    to=[request.user.email]
                )
                msg.content_subtype = 'html'
                msg.send(fail_silently=True)
                
                # Vendor emails - create individual purchase records for each vendor
                for item in order.items.all():
                    vendor_email = getattr(item.product.vendor, 'email', None)
                    if vendor_email:
                        # Find the purchase record for this specific item
                        item_purchase = Purchase.objects.filter(
                            customer=request.user,
                            product=item.product,
                            transaction_id=txid
                        ).first()
                        
                        if item_purchase:
                            vhtml = render_to_string('emails/purchase.html', {
                                'purchase': item_purchase, 
                                'user': item.product.vendor,
                                'order': order
                            })
                            vmsg = EmailMessage(
                                subject=f'New Sale - {item.product.name}',
                                body=vhtml,
                                from_email=settings.DEFAULT_FROM_EMAIL,
                                to=[vendor_email]
                            )
                            vmsg.content_subtype = 'html'
                            vmsg.send(fail_silently=True)
            except Exception:
                pass
            
            messages.success(request, f'Payment successful! Transaction ID: {txid}')
            return redirect('orders:confirmation', order_id=order.id)
        else:
            messages.error(request, 'Payment failed. Please try again.')
            return redirect('orders:payment_processing', order_id=order.id)
    
    return redirect('orders:payment_processing', order_id=order.id)


@login_required
def confirmation(request, order_id):
 
    order = Order.objects.filter(id=order_id).first()
    if not order:
        messages.error(request, "Order not found.")
        return redirect('products:product_list')

    user_is_customer = (order.customer == request.user)
    user_is_staff = getattr(request.user, 'is_staff', False) or getattr(request.user, 'is_superuser', False)
    user_is_vendor = getattr(request.user, 'user_type', None) == 'vendor'

    vendor_has_item = False
    if user_is_vendor:
        vendor_has_item = OrderItem.objects.filter(order=order, product__vendor=request.user).exists()

    if not (user_is_customer or user_is_staff or vendor_has_item):
        messages.error(request, "Order not found or you don't have permission to view it.")

        if user_is_vendor:
            return redirect('orders:vendor_orders')
        return redirect('orders:my_orders')

    items = OrderItem.objects.filter(order=order)
    if user_is_customer:
        viewer_role = 'customer'
    elif user_is_vendor and vendor_has_item:
        viewer_role = 'vendor'
    elif user_is_staff:
        viewer_role = 'staff'
    else:
        viewer_role = 'other'
    return render(request, 'confirmation.html', {'order': order, 'items': items, 'viewer_role': viewer_role})

@login_required
def my_orders(request):
    if request.user.user_type != "customer":
        messages.error(request, "Only customers can view this page.")
        return redirect('products:product_list')

    orders = Order.objects.filter(customer=request.user).order_by('-created_at')
    purchases = Purchase.objects.filter(customer=request.user).order_by('-created_at')

    return render(request, 'my_orders.html', {"orders": orders, 'purchases': purchases})


from accounts.decorators import vendor_required
@vendor_required
def vendor_orders(request):
    vendor_items = OrderItem.objects.filter(product__vendor=request.user).select_related('order', 'product', 'order__customer').order_by('-order__created_at')
    return render(request, 'vendor_orders.html', {"items": vendor_items})

@login_required
def vendor_order_details(request, order_id):
    if request.user.user_type != "vendor":
        messages.error(request, "Only vendors can view this page.")
        return redirect('products:product_list')

    order = get_object_or_404(Order, id=order_id)

    items = OrderItem.objects.filter(order=order, product__vendor=request.user)

    return render(request, 'vendor_order_details.html', {
        "order": order,
        "items": items
    })


def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id, status='active')
    if request.method == 'POST':
        try:
            qty = int(request.POST.get('quantity', 1))
        except (TypeError, ValueError):
            qty = 1

        if qty < 1:
            messages.error(request, 'Invalid quantity.')
            return redirect('products:product_detail', pk=product.id)

        if qty > product.stock:
            messages.error(request, 'Not enough stock available.')
            return redirect('products:product_detail', pk=product.id)

        cart = request.session.get('cart', {})
        key = str(product.id)
        cart[key] = cart.get(key, 0) + qty
        if cart[key] > product.stock:
            cart[key] = product.stock

        request.session['cart'] = cart
        messages.success(request, f'Added {qty} x {product.name} to cart.')

    return redirect('orders:cart_view')


def cart_view(request):
    cart = request.session.get('cart', {})
    items = []
    total = 0
    for pid, qty in list(cart.items()):
        try:
            product = Product.objects.get(id=pid, status='active')
        except Product.DoesNotExist:
            cart.pop(pid, None)
            continue
        qty = int(qty)
        subtotal = product.price * qty
        total += subtotal
        items.append({'product': product, 'quantity': qty, 'subtotal': subtotal})

    request.session['cart'] = cart
    return render(request, 'cart.html', {'items': items, 'total': total})


def update_cart(request):
    if request.method == 'POST':
        cart = request.session.get('cart', {})
        for key, value in request.POST.items():
            if key.startswith('qty_'):
                pid = key.split('_', 1)[1]
                try:
                    qty = int(value)
                except (TypeError, ValueError):
                    qty = 0
                if qty <= 0:
                    cart.pop(pid, None)
                else:
                    product = Product.objects.filter(id=pid).first()
                    if product:
                        cart[pid] = min(qty, product.stock)
        request.session['cart'] = cart
        messages.success(request, 'Cart updated.')
    return redirect('orders:cart_view')


def remove_from_cart(request, product_id):
    cart = request.session.get('cart', {})
    cart.pop(str(product_id), None)
    request.session['cart'] = cart
    messages.success(request, 'Item removed from cart.')
    return redirect('orders:cart_view')


@login_required
def checkout_cart(request):
    if getattr(request.user, 'user_type', None) != 'customer':
        messages.error(request, 'Only customers can place orders.')
        return redirect('products:product_list')

    cart = request.session.get('cart', {})
    if not cart:
        messages.error(request, 'Your cart is empty.')
        return redirect('products:product_list')

    items_data = []
    total = 0
    for pid, qty in cart.items():
        product = Product.objects.filter(id=pid, status='active').first()
        if not product:
            messages.error(request, 'One of the products in your cart is unavailable.')
            return redirect('orders:cart_view')
        qty = int(qty)
        if qty > product.stock:
            messages.error(request, f'Not enough stock for {product.name}.')
            return redirect('orders:cart_view')
        subtotal = product.price * qty
        total += subtotal
        items_data.append({'product': product, 'quantity': qty, 'price': product.price})

    
    order = Order.objects.create(
        customer=request.user,
        total=total,
        status='pending',
        delivery_address=request.user.location or '',
        phone=request.user.phone or ''
    )

    # payment method for the whole order (single txid)
    payment_method = request.POST.get('payment_method', 'bank')
    mobile_number = request.POST.get('mobile_number', '')
    # validate mobile number for mobile money
    if payment_method in ('momo', 'airtel'):
        import re
        if not re.match(r'^\+?\d{8,15}$', mobile_number or ''):
            messages.error(request, 'Provide a valid mobile number for mobile-money payments.')
            return redirect('orders:cart_view')
    import uuid
    txid = f"MOCK-{payment_method.upper()}-{uuid.uuid4().hex[:8]}"

    for it in items_data:
        OrderItem.objects.create(
            order=order,
            product=it['product'],
            quantity=it['quantity'],
            price=it['price']
        )
        # create purchase record per item using same txid
        purchase = Purchase.objects.create(
            customer=request.user,
            product=it['product'],
            quantity=it['quantity'],
            amount=it['price'] * it['quantity'],
            payment_method=payment_method,
            transaction_id=txid,
        )
        PurchaseLog.objects.create(purchase=purchase, action=PurchaseLog.ACTION_PURCHASE, actor=request.user, note=f'Order #{order.id}')
        try:
            from django.template.loader import render_to_string
            from django.core.mail import EmailMessage
            html = render_to_string('emails/purchase.html', {'purchase': purchase, 'user': request.user})
            msg = EmailMessage(
                subject=f'Purchase #{purchase.id} recorded',
                body=html,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[request.user.email]
            )
            msg.content_subtype = 'html'
            msg.send(fail_silently=True)

            vendor_email = getattr(it['product'].vendor, 'email', None)
            if vendor_email:
                vhtml = render_to_string('emails/purchase.html', {'purchase': purchase, 'user': it['product'].vendor})
                vmsg = EmailMessage(subject=f'Your product purchased: {purchase.product.name}', body=vhtml, from_email=settings.DEFAULT_FROM_EMAIL, to=[vendor_email])
                vmsg.content_subtype = 'html'
                vmsg.send(fail_silently=True)
        except Exception:
            pass
        it['product'].stock = it['product'].stock - it['quantity']
        it['product'].save()

    request.session['cart'] = {}
    messages.success(request, 'Order placed successfully.')
    return redirect('orders:confirmation', order_id=order.id)
    


@login_required
def mock_pay(request, product_id):
    """Simulate a payment for a single product (no real processing).
    GET: Show payment form
    POST: Process payment, create Purchase record and reduce stock
    """
    product = Product.objects.filter(id=product_id, status='active').first()
    if not product:
        messages.error(request, 'Product not found or unavailable.')
        return redirect('products:product_list')

    if getattr(request.user, 'user_type', None) != 'customer':
        messages.error(request, 'Only customers can make purchases.')
        return redirect('products:product_detail', pk=product.id)

    if request.method == 'GET':
        # Show payment form with available payment methods
        payment_methods = [
            ('bank', 'Bank Transfer'),
            ('momo', 'Momo Pay'),
            ('airtel', 'Airtel Money'),
        ]
        return render(request, 'orders/mock_pay.html', {'product': product, 'payment_methods': payment_methods})

    if request.method != 'POST':
        messages.error(request, 'Invalid request.')
        return redirect('products:product_detail', pk=product.id)

    try:
        qty = int(request.POST.get('quantity', 1))
    except (TypeError, ValueError):
        qty = 1

    if qty < 1:
        messages.error(request, 'Invalid quantity.')
        return redirect('products:product_detail', pk=product.id)

    if qty > product.stock:
        messages.error(request, 'Not enough stock available.')
        return redirect('products:product_detail', pk=product.id)

    amount = product.price * qty

    # determine payment method
    payment_method = request.POST.get('payment_method', 'bank')

    # generate a mock transaction id
    import uuid
    txid = f"MOCK-{payment_method.upper()}-{uuid.uuid4().hex[:8]}"

    # Create Purchase record
    from .models import Purchase
    purchase = Purchase.objects.create(
        customer=request.user,
        product=product,
        quantity=qty,
        amount=amount,
        payment_method=payment_method,
        transaction_id=txid
    )
    # log and notify
    PurchaseLog.objects.create(purchase=purchase, action=PurchaseLog.ACTION_PURCHASE, actor=request.user, note='Mock pay')
    try:
        from django.template.loader import render_to_string
        from django.core.mail import EmailMessage
        html = render_to_string('emails/purchase.html', {'purchase': purchase, 'user': request.user})
        msg = EmailMessage(
            subject=f'Purchase #{purchase.id} recorded',
            body=html,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[request.user.email]
        )
        msg.content_subtype = 'html'
        msg.send(fail_silently=True)

        vendor_email = getattr(product.vendor, 'email', None)
        if vendor_email:
            vhtml = render_to_string('emails/purchase.html', {'purchase': purchase, 'user': product.vendor})
            vmsg = EmailMessage(subject=f'Your product purchased: {product.name}', body=vhtml, from_email=settings.DEFAULT_FROM_EMAIL, to=[vendor_email])
            vmsg.content_subtype = 'html'
            vmsg.send(fail_silently=True)
    except Exception:
        pass

    # Decrement stock
    product.stock = product.stock - qty
    product.save()

    messages.success(request, f'Payment simulated via {payment_method}. Transaction {txid}')
    return render(request, 'orders/payment_success.html', {'purchase': purchase})


from django.contrib.admin.views.decorators import staff_member_required
import json
import decimal
import logging
try:
    import stripe
except Exception:
    stripe = None

logger = logging.getLogger(__name__)

@staff_member_required
def admin_dashboard(request):
    """Simple site admin dashboard listing products and mock purchases."""
    from .models import Purchase
    products = Product.objects.all().select_related('vendor')
    purchases = Purchase.objects.select_related('customer', 'product')[:200]
    return render(request, 'orders/admin_dashboard.html', {'products': products, 'purchases': purchases})


@login_required
def stripe_checkout(request, product_id):
    """Create a Stripe Checkout Session for a single product and redirect the user."""
    if stripe is None:
        messages.error(request, 'Stripe library not installed. Install stripe package to use payments.')
        return redirect('products:product_detail', pk=product_id)

    product = Product.objects.filter(id=product_id, status='active').first()
    if not product:
        messages.error(request, 'Product not found.')
        return redirect('products:product_list')

    if getattr(request.user, 'user_type', None) != 'customer':
        messages.error(request, 'Only customers can make purchases.')
        return redirect('products:product_detail', pk=product.id)

    # parse desired quantity
    try:
        qty = int(request.POST.get('quantity', 1)) if request.method == 'POST' else int(request.GET.get('quantity', 1))
    except (TypeError, ValueError):
        qty = 1

    if qty < 1 or qty > product.stock:
        messages.error(request, 'Invalid quantity or not enough stock.')
        return redirect('products:product_detail', pk=product.id)

    # Create a server-side Order and OrderItem so we can reconcile in webhook
    order = Order.objects.create(
        customer=request.user,
        total=product.price * qty,
        status='pending',
        delivery_address=getattr(request.user, 'location', '') or '',
        phone=getattr(request.user, 'phone', '') or ''
    )
    OrderItem.objects.create(order=order, product=product, quantity=qty, price=product.price)

    # If GET, show a simple checkout form
    if request.method == 'GET':
        return render(request, 'orders/stripe_checkout.html', {'product': product})

    # configure stripe
    stripe.api_key = settings.STRIPE_API_KEY
    unit_amount = int(decimal.Decimal(product.price) * 100)

    success_url = settings.STRIPE_SUCCESS_URL.format(order_id=order.id)
    cancel_url = settings.STRIPE_CANCEL_URL.format(order_id=order.id)

    try:
        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': settings.STRIPE_CURRENCY,
                    'product_data': {'name': product.name},
                    'unit_amount': unit_amount,
                },
                'quantity': qty,
            }],
            mode='payment',
            success_url=success_url,
            cancel_url=cancel_url,
            metadata={'order_id': str(order.id)}
        )
    except Exception:
        logger.exception('Stripe session creation failed')
        messages.error(request, 'Failed to start payment session.')
        # on failure delete the created order and items to avoid orphaned pending orders
        order.delete()
        return redirect('products:product_detail', pk=product.id)

    # store stripe session id on order for idempotency (optional)
    try:
        order.stripe_session_id = session.id
        order.save()
    except Exception:
        pass

    # redirect to Stripe hosted checkout
    return redirect(session.url)


from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse


@csrf_exempt
def stripe_webhook(request):
    """Handle Stripe webhooks; create Purchase on checkout.session.completed."""
    if stripe is None:
        return HttpResponse(status=501)

    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE', '')
    endpoint_secret = settings.STRIPE_WEBHOOK_SECRET

    try:
        event = stripe.Webhook.construct_event(payload=payload, sig_header=sig_header, secret=endpoint_secret)
    except ValueError:
        return HttpResponse(status=400)
    except Exception as e:
        # handle signature error if stripe is available
        if stripe is not None:
            try:
                from stripe.error import SignatureVerificationError
                if isinstance(e, SignatureVerificationError):
                    return HttpResponse(status=400)
            except Exception:
                pass
        logger.exception('Unexpected error while parsing webhook')
        return HttpResponse(status=400)

    # Handle the checkout.session.completed event
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        # persist raw webhook for debugging
        try:
            from .models import StripeWebhookEvent
            from .security_utils import redact_request_headers, safe_json_dump
            
            # Use hardened header redaction utility
            masked_headers = redact_request_headers(request)
            
            saved = StripeWebhookEvent.objects.create(
                stripe_event_id=event.get('id'),
                event_type=event.get('type'),
                payload=payload.decode('utf-8', errors='ignore') if isinstance(payload, (bytes, bytearray)) else str(payload),
                headers=safe_json_dump(masked_headers),
            )
            # process via shared util
            from .stripe_utils import process_stripe_event
            try:
                process_stripe_event(event, saved_event=saved)
            except Exception:
                logger.exception('Processing saved webhook failed')
        except Exception:
            logger.exception('Failed to persist webhook event')
        meta = session.get('metadata', {}) or {}
        # Prefer an order-based flow: if order_id is provided, finalize that Order
        order_id = meta.get('order_id')
        if order_id:
            try:
                from .models import OrderItem, Order
                oid = int(order_id)
                order = Order.objects.filter(id=oid).first()
                if not order:
                    return HttpResponse(status=200)
                # idempotency: if we already have a Purchase with this session id, skip
                existing = Purchase.objects.filter(transaction_id=session.get('id')).first()
                if existing:
                    return HttpResponse(status=200)

                # create purchases for each order item
                for item in order.items.all():
                    purchase = Purchase.objects.create(
                        customer=order.customer,
                        product=item.product,
                        quantity=item.quantity,
                        amount=item.price * item.quantity,
                        payment_method='stripe',
                        transaction_id=session.get('id')
                    )
                    PurchaseLog.objects.create(purchase=purchase, action=PurchaseLog.ACTION_PURCHASE, actor=order.customer, note=f'Order #{order.id} (Stripe)')
                    try:
                        from django.template.loader import render_to_string
                        from django.core.mail import EmailMessage
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
                        pass
                    # decrement stock
                    item.product.stock = item.product.stock - item.quantity
                    item.product.save()

                # mark order completed
                order.status = Order.STATUS_COMPLETED
                order.save()
            except Exception:
                logger.exception('Error finalizing order from webhook')
            return HttpResponse(status=200)

        # Fallback: older flow expecting product_id/quantity/user_id in metadata
        try:
            prod_id = int(meta.get('product_id'))
            qty = int(meta.get('quantity', 1))
            user_id = int(meta.get('user_id'))
        except Exception:
            return HttpResponse(status=200)

        product = Product.objects.filter(id=prod_id).first()
        if not product:
            return HttpResponse(status=200)

        from django.contrib.auth import get_user_model
        User = get_user_model()
        customer = User.objects.filter(id=user_id).first()
        # idempotency: don't create duplicate purchase for same session id
        existing = Purchase.objects.filter(transaction_id=session.get('id')).first()
        if existing:
            return HttpResponse(status=200)

        # create the purchase
        amount = (decimal.Decimal(product.price) * qty)
        purchase = Purchase.objects.create(
            customer=customer,
            product=product,
            quantity=qty,
            amount=amount,
            payment_method='stripe',
            transaction_id=session.get('id')
        )
        PurchaseLog.objects.create(purchase=purchase, action=PurchaseLog.ACTION_PURCHASE, actor=customer, note='Stripe checkout')
        # decrement stock
        product.stock = product.stock - qty
        product.save()

    return HttpResponse(status=200)


@login_required
def stripe_success(request, order_id):
    """Show a friendly success page and poll order status until webhook finalizes it."""
    order = Order.objects.filter(id=order_id).first()
    if not order:
        messages.error(request, 'Order not found.')
        return redirect('products:product_list')
    return render(request, 'orders/stripe_success.html', {'order': order})


@login_required
def stripe_cancel(request, order_id):
    """Show cancelled payment page with retry options."""
    order = Order.objects.filter(id=order_id).first()
    if not order:
        messages.error(request, 'Order not found.')
        return redirect('products:product_list')
    return render(request, 'orders/stripe_cancel.html', {'order': order})


@login_required
def stripe_order_status(request, order_id):
    """Return JSON status for polling on the success page."""
    order = Order.objects.filter(id=order_id).first()
    if not order:
        return JsonResponse({'status': 'not_found'}, status=404)
    return JsonResponse({'status': order.status})


@login_required
def purchase_detail(request, pk):
    from .models import Purchase
    purchase = Purchase.objects.select_related('product', 'customer').filter(id=pk).first()
    if not purchase:
        messages.error(request, 'Purchase not found.')
        return redirect('orders:my_orders')

    # permissions: customer who bought it, staff, or vendor who owns product
    user_is_customer = (purchase.customer == request.user)
    user_is_staff = getattr(request.user, 'is_staff', False) or getattr(request.user, 'is_superuser', False)
    user_is_vendor = getattr(request.user, 'user_type', None) == 'vendor' and purchase.product.vendor == request.user

    if not (user_is_customer or user_is_staff or user_is_vendor):
        messages.error(request, 'You do not have permission to view this purchase.')
        return redirect('orders:my_orders')

    return render(request, 'orders/purchase_detail.html', {'purchase': purchase})


# Import the enhanced admin dashboard function
from .admin import enhanced_admin_dashboard




