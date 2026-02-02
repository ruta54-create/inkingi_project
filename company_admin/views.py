from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.contrib.auth import get_user_model
from products.models import Product
from orders.models import Purchase, PurchaseLog, Order, OrderItem
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from django.shortcuts import get_object_or_404
from django.db.models import Sum, Count, Avg
from django.db.models.functions import TruncDate, TruncMonth
from decimal import Decimal


@staff_member_required
def dashboard(request):
    User = get_user_model()

    # Get statistics
    total_vendors = User.objects.filter(user_type='vendor').count()
    total_customers = User.objects.filter(user_type='customer').count()
    total_products = Product.objects.count()
    active_products = Product.objects.filter(status='active').count()
    total_orders = Order.objects.count()
    pending_orders = Order.objects.filter(status__in=['pending', 'awaiting_confirmation']).count()
    processing_orders = Order.objects.filter(status='processing').count()
    completed_orders = Order.objects.filter(status__in=['delivered', 'completed']).count()

    # Revenue statistics
    total_revenue = Purchase.objects.filter(refunded=False).aggregate(total=Sum('amount'))['total'] or Decimal('0')
    today_revenue = Purchase.objects.filter(
        refunded=False,
        created_at__date=timezone.now().date()
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0')

    # Recent data
    vendors = User.objects.filter(user_type='vendor').order_by('-date_joined')[:10]
    customers = User.objects.filter(user_type='customer').order_by('-date_joined')[:10]
    products = Product.objects.select_related('vendor').all()[:20]
    recent_orders = Order.objects.select_related('customer').prefetch_related('items')[:20]
    purchases = Purchase.objects.select_related('customer', 'product').all()[:50]

    # Top vendors by sales
    top_vendors = User.objects.filter(user_type='vendor').annotate(
        total_sales=Sum('products__purchases__amount')
    ).order_by('-total_sales')[:5]

    # Orders awaiting confirmation
    awaiting_confirmation = Order.objects.filter(status='awaiting_confirmation').select_related('customer')[:10]

    return render(request, 'company_admin/dashboard.html', {
        'total_vendors': total_vendors,
        'total_customers': total_customers,
        'total_products': total_products,
        'active_products': active_products,
        'total_orders': total_orders,
        'pending_orders': pending_orders,
        'processing_orders': processing_orders,
        'completed_orders': completed_orders,
        'total_revenue': total_revenue,
        'today_revenue': today_revenue,
        'vendors': vendors,
        'customers': customers,
        'products': products,
        'recent_orders': recent_orders,
        'purchases': purchases,
        'top_vendors': top_vendors,
        'awaiting_confirmation': awaiting_confirmation,
    })


@staff_member_required
def vendor_management(request):
    """View all vendors and their performance"""
    User = get_user_model()

    vendors = User.objects.filter(user_type='vendor').annotate(
        product_count=Count('products'),
        total_sales=Sum('products__purchases__amount'),
        order_count=Count('products__purchases', distinct=True)
    ).order_by('-total_sales')

    return render(request, 'company_admin/vendor_management.html', {
        'vendors': vendors,
    })


@staff_member_required
def vendor_detail(request, vendor_id):
    """View detailed vendor information and performance"""
    User = get_user_model()
    vendor = get_object_or_404(User, id=vendor_id, user_type='vendor')

    # Vendor statistics
    products = Product.objects.filter(vendor=vendor)
    total_products = products.count()
    active_products = products.filter(status='active').count()

    # Sales statistics
    purchases = Purchase.objects.filter(product__vendor=vendor)
    total_sales = purchases.filter(refunded=False).aggregate(total=Sum('amount'))['total'] or Decimal('0')
    total_orders = purchases.count()
    refunded_count = purchases.filter(refunded=True).count()

    # Recent orders
    recent_orders = OrderItem.objects.filter(product__vendor=vendor).select_related(
        'order', 'order__customer', 'product'
    ).order_by('-order__created_at')[:20]

    # Monthly sales trend (last 6 months)
    monthly_sales = purchases.filter(
        refunded=False,
        created_at__gte=timezone.now() - timezone.timedelta(days=180)
    ).annotate(
        month=TruncMonth('created_at')
    ).values('month').annotate(
        total=Sum('amount'),
        count=Count('id')
    ).order_by('month')

    return render(request, 'company_admin/vendor_detail.html', {
        'vendor': vendor,
        'products': products,
        'total_products': total_products,
        'active_products': active_products,
        'total_sales': total_sales,
        'total_orders': total_orders,
        'refunded_count': refunded_count,
        'recent_orders': recent_orders,
        'monthly_sales': list(monthly_sales),
    })


@staff_member_required
def order_management(request):
    """View all orders with filtering and management"""
    status_filter = request.GET.get('status', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')

    orders = Order.objects.select_related('customer').prefetch_related('items', 'items__product')

    if status_filter:
        orders = orders.filter(status=status_filter)
    if date_from:
        orders = orders.filter(created_at__date__gte=date_from)
    if date_to:
        orders = orders.filter(created_at__date__lte=date_to)

    orders = orders.order_by('-created_at')[:100]

    return render(request, 'company_admin/order_management.html', {
        'orders': orders,
        'status_filter': status_filter,
        'date_from': date_from,
        'date_to': date_to,
        'status_choices': Order.STATUS_CHOICES,
    })


@staff_member_required
def order_detail_admin(request, order_id):
    """Admin view of order details"""
    order = get_object_or_404(Order, id=order_id)
    items = order.items.select_related('product', 'product__vendor')

    # Get tracking info if exists
    from core.models import DeliveryTracking
    try:
        tracking = DeliveryTracking.objects.get(order=order)
    except DeliveryTracking.DoesNotExist:
        tracking = None

    return render(request, 'company_admin/order_detail.html', {
        'order': order,
        'items': items,
        'tracking': tracking,
    })


@staff_member_required
def update_order_status(request, order_id):
    """Update order status"""
    order = get_object_or_404(Order, id=order_id)

    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status in dict(Order.STATUS_CHOICES):
            old_status = order.status
            order.status = new_status
            order.save()

            # Create tracking if shipped
            if new_status == Order.STATUS_SHIPPED:
                from core.models import DeliveryTracking
                DeliveryTracking.objects.get_or_create(
                    order=order,
                    defaults={
                        'status': 'in_transit',
                        'destination_latitude': order.delivery_latitude,
                        'destination_longitude': order.delivery_longitude,
                    }
                )

            messages.success(request, f'Order #{order.id} status updated to {order.get_status_display()}.')
        else:
            messages.error(request, 'Invalid status.')

    return redirect('company_admin:order_detail', order_id=order.id)


@staff_member_required
def delivery_management(request):
    """View all deliveries and their tracking status"""
    from core.models import DeliveryTracking

    status_filter = request.GET.get('status', '')

    trackings = DeliveryTracking.objects.select_related('order', 'order__customer')

    if status_filter:
        trackings = trackings.filter(status=status_filter)

    trackings = trackings.order_by('-updated_at')[:100]

    return render(request, 'company_admin/delivery_management.html', {
        'trackings': trackings,
        'status_filter': status_filter,
        'status_choices': DeliveryTracking.STATUS_CHOICES,
    })


@staff_member_required
def user_management(request):
    """View and manage all users"""
    User = get_user_model()

    user_type = request.GET.get('type', '')
    search = request.GET.get('search', '')

    users = User.objects.all()

    if user_type:
        users = users.filter(user_type=user_type)
    if search:
        users = users.filter(
            models__icontains=search
        ) if False else users.filter(username__icontains=search) | users.filter(email__icontains=search)

    users = users.order_by('-date_joined')[:100]

    return render(request, 'company_admin/user_management.html', {
        'users': users,
        'user_type': user_type,
        'search': search,
    })


@staff_member_required
def site_settings(request):
    """Manage site settings"""
    from core.models import SiteSettings

    settings_obj = SiteSettings.get_settings()

    if request.method == 'POST':
        # Update settings
        settings_obj.site_name = request.POST.get('site_name', settings_obj.site_name)
        settings_obj.site_tagline = request.POST.get('site_tagline', settings_obj.site_tagline)
        settings_obj.banner_title = request.POST.get('banner_title', settings_obj.banner_title)
        settings_obj.banner_subtitle = request.POST.get('banner_subtitle', settings_obj.banner_subtitle)
        settings_obj.contact_email = request.POST.get('contact_email', settings_obj.contact_email)
        settings_obj.contact_phone = request.POST.get('contact_phone', settings_obj.contact_phone)
        settings_obj.contact_address = request.POST.get('contact_address', settings_obj.contact_address)
        settings_obj.whatsapp_number = request.POST.get('whatsapp_number', settings_obj.whatsapp_number)
        settings_obj.facebook_url = request.POST.get('facebook_url', settings_obj.facebook_url)
        settings_obj.twitter_url = request.POST.get('twitter_url', settings_obj.twitter_url)
        settings_obj.instagram_url = request.POST.get('instagram_url', settings_obj.instagram_url)
        settings_obj.banner_video_url = request.POST.get('banner_video_url', settings_obj.banner_video_url)
        settings_obj.show_video_on_homepage = request.POST.get('show_video_on_homepage') == 'on'

        # Handle file uploads
        if 'logo' in request.FILES:
            settings_obj.logo = request.FILES['logo']
        if 'banner_image' in request.FILES:
            settings_obj.banner_image = request.FILES['banner_image']
        if 'banner_video' in request.FILES:
            settings_obj.banner_video = request.FILES['banner_video']

        try:
            settings_obj.tax_rate = Decimal(request.POST.get('tax_rate', settings_obj.tax_rate))
            settings_obj.standard_delivery_cost = Decimal(request.POST.get('standard_delivery_cost', settings_obj.standard_delivery_cost))
            settings_obj.express_delivery_cost = Decimal(request.POST.get('express_delivery_cost', settings_obj.express_delivery_cost))
            settings_obj.free_delivery_threshold = Decimal(request.POST.get('free_delivery_threshold', settings_obj.free_delivery_threshold))
        except:
            pass

        settings_obj.save()
        messages.success(request, 'Site settings updated successfully.')
        return redirect('company_admin:site_settings')

    return render(request, 'company_admin/site_settings.html', {
        'settings': settings_obj,
    })


@staff_member_required
def currency_management(request):
    """Manage currencies and exchange rates"""
    from core.models import Currency

    currencies = Currency.objects.all()

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'update':
            code = request.POST.get('code')
            try:
                currency = Currency.objects.get(code=code)
                currency.exchange_rate = Decimal(request.POST.get('exchange_rate', 1))
                currency.is_active = request.POST.get('is_active') == 'on'
                currency.save()
                messages.success(request, f'Currency {code} updated.')
            except Currency.DoesNotExist:
                messages.error(request, 'Currency not found.')

        elif action == 'add':
            code = request.POST.get('new_code', '').upper()[:3]
            name = request.POST.get('new_name', '')
            symbol = request.POST.get('new_symbol', code)
            rate = Decimal(request.POST.get('new_rate', 1))

            if code and name:
                Currency.objects.get_or_create(
                    code=code,
                    defaults={
                        'name': name,
                        'symbol': symbol,
                        'exchange_rate': rate,
                    }
                )
                messages.success(request, f'Currency {code} added.')

    return render(request, 'company_admin/currency_management.html', {
        'currencies': currencies,
    })


@staff_member_required
def refund_purchase(request, purchase_id):
    purchase = get_object_or_404(Purchase, id=purchase_id)
    if purchase.refunded:
        messages.info(request, 'Purchase already refunded.')
        return redirect('company_admin:dashboard')
    # get reason from POST (fallback message)
    reason = request.POST.get('reason', '').strip() or 'Refunded via admin dashboard'

    # Restock product
    product = purchase.product
    product.stock = product.stock + purchase.quantity
    product.save()

    # mark refunded and record metadata
    purchase.refunded = True
    purchase.refunded_at = timezone.now()
    purchase.refunded_by = request.user
    purchase.refund_reason = reason
    purchase.save()

    # log and notify using HTML templates
    PurchaseLog.objects.create(purchase=purchase, action=PurchaseLog.ACTION_REFUND, actor=request.user, note=reason)
    try:
        from django.template.loader import render_to_string
        from django.core.mail import EmailMessage
        html = render_to_string('emails/refund.html', {'purchase': purchase, 'user': purchase.customer})
        msg = EmailMessage(subject=f'Purchase #{purchase.id} refunded', body=html, from_email=settings.DEFAULT_FROM_EMAIL, to=[purchase.customer.email])
        msg.content_subtype = 'html'
        msg.send(fail_silently=True)
        vendor_email = getattr(product.vendor, 'email', None)
        if vendor_email:
            vhtml = render_to_string('emails/refund.html', {'purchase': purchase, 'user': product.vendor})
            vmsg = EmailMessage(subject=f'Purchase #{purchase.id} refunded', body=vhtml, from_email=settings.DEFAULT_FROM_EMAIL, to=[vendor_email])
            vmsg.content_subtype = 'html'
            vmsg.send(fail_silently=True)
    except Exception:
        pass

    messages.success(request, f'Purchase #{purchase.id} refunded and {purchase.quantity} items restocked.')
    return redirect('company_admin:dashboard')
