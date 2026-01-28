from django import template

register = template.Library()


@register.simple_tag(takes_context=True)
def cart_item_count(context):
    """Return total number of items in the session cart."""
    request = context.get('request')
    if not request:
        return 0
    cart = request.session.get('cart', {}) or {}
    try:
        return sum(int(v) for v in cart.values())
    except Exception:
        # In case of unexpected data, be safe
        return 0


@register.simple_tag(takes_context=True)
def cart_total_amount(context):
    """Return approximate total amount (not used by default) - helper if needed."""
    request = context.get('request')
    if not request:
        return 0
    cart = request.session.get('cart', {}) or {}
    total = 0
    from products.models import Product
    for pid, qty in cart.items():
        try:
            p = Product.objects.filter(id=pid, status='active').first()
            if p:
                total += p.price * int(qty)
        except Exception:
            continue
    return total
