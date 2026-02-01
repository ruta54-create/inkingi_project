from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.contrib.auth import get_user_model
from products.models import Product
from orders.models import Purchase, PurchaseLog
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from django.shortcuts import get_object_or_404



@staff_member_required
def dashboard(request):
    User = get_user_model()
    vendors = User.objects.filter(user_type='vendor')
    products = Product.objects.select_related('vendor').all()
    purchases = Purchase.objects.select_related('customer', 'product').all()[:200]
    return render(request, 'company_admin/dashboard.html', {
        'vendors': vendors,
        'products': products,
        'purchases': purchases,
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
