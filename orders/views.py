# orders/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import CheckoutForm
from .models import Order, OrderItem
from products.models import Product
from django.http import JsonResponse
from django.shortcuts import reverse

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

            if qty > product.stock:
                form.add_error('quantity', 'Not enough stock available.')
            else:
            
                order = Order.objects.create(
                    customer=request.user,
                    total=product.price * qty,
                    status='pending',
                    delivery_address=address,
                    phone=phone
                )

                OrderItem.objects.create(
                    order=order,
                    product=product,
                    quantity=qty,
                    price=product.price
                )

                product.stock = product.stock - qty
                product.save()

                messages.success(request, "Order placed successfully.")
                return redirect('orders:confirmation', order_id=order.id)
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

    return render(request, 'my_orders.html', {"orders": orders})


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

    for it in items_data:
        OrderItem.objects.create(
            order=order,
            product=it['product'],
            quantity=it['quantity'],
            price=it['price']
        )
        it['product'].stock = it['product'].stock - it['quantity']
        it['product'].save()

    request.session['cart'] = {}
    messages.success(request, 'Order placed successfully.')
    return redirect('orders:confirmation', order_id=order.id)
    


@login_required
def mock_pay(request, product_id):
    """Simulate a payment for a single product (no real processing).
    Creates a Purchase record and reduces stock accordingly, then shows confirmation.
    """
    product = Product.objects.filter(id=product_id, status='active').first()
    if not product:
        messages.error(request, 'Product not found or unavailable.')
        return redirect('products:product_list')

    if getattr(request.user, 'user_type', None) != 'customer':
        messages.error(request, 'Only customers can make purchases.')
        return redirect('products:product_detail', pk=product.id)

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

    # Create Purchase record
    from .models import Purchase
    purchase = Purchase.objects.create(
        customer=request.user,
        product=product,
        quantity=qty,
        amount=amount
    )

    # Decrement stock
    product.stock = product.stock - qty
    product.save()

    return render(request, 'orders/payment_success.html', {'purchase': purchase})


from django.contrib.admin.views.decorators import staff_member_required

@staff_member_required
def admin_dashboard(request):
    """Simple site admin dashboard listing products and mock purchases."""
    from .models import Purchase
    products = Product.objects.all().select_related('vendor')
    purchases = Purchase.objects.select_related('customer', 'product')[:200]
    return render(request, 'orders/admin_dashboard.html', {'products': products, 'purchases': purchases})




