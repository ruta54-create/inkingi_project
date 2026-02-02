from django.shortcuts import redirect
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.utils import translation
from django.conf import settings


def set_language(request):
    """Set the user's preferred language"""
    lang_code = request.GET.get('language') or request.POST.get('language', 'en')

    # Validate language code
    valid_languages = [code for code, name in settings.LANGUAGES]
    if lang_code not in valid_languages:
        lang_code = 'en'

    # Activate the language
    translation.activate(lang_code)

    # Get redirect URL
    next_url = request.GET.get('next') or request.POST.get('next') or request.META.get('HTTP_REFERER', '/')

    response = redirect(next_url)

    # Set language cookie
    response.set_cookie(
        settings.LANGUAGE_COOKIE_NAME,
        lang_code,
        max_age=settings.LANGUAGE_COOKIE_AGE
    )

    # Also store in session
    request.session['django_language'] = lang_code

    return response


def set_currency(request):
    """Set the user's preferred currency"""
    currency_code = request.GET.get('currency') or request.POST.get('currency', 'RWF')

    # Validate currency code
    if currency_code not in settings.SUPPORTED_CURRENCIES:
        currency_code = 'RWF'

    # Get redirect URL
    next_url = request.GET.get('next') or request.POST.get('next') or request.META.get('HTTP_REFERER', '/')

    response = redirect(next_url)

    # Set currency cookie
    response.set_cookie(
        settings.CURRENCY_COOKIE_NAME,
        currency_code,
        max_age=365 * 24 * 60 * 60  # 1 year
    )

    # Also store in session
    request.session['currency'] = currency_code

    return response


def get_exchange_rates(request):
    """API endpoint to get current exchange rates"""
    from .models import Currency

    currencies = Currency.objects.filter(is_active=True)
    rates = {c.code: {
        'name': c.name,
        'symbol': c.symbol,
        'rate': float(c.exchange_rate),
        'decimal_places': c.decimal_places
    } for c in currencies}

    return JsonResponse({
        'base_currency': 'RWF',
        'rates': rates
    })


def convert_price(request):
    """API endpoint to convert a price to a different currency"""
    from .models import Currency
    from decimal import Decimal

    amount = request.GET.get('amount', 0)
    from_currency = request.GET.get('from', 'RWF')
    to_currency = request.GET.get('to', 'USD')

    try:
        amount = Decimal(str(amount))
    except:
        return JsonResponse({'error': 'Invalid amount'}, status=400)

    try:
        from_curr = Currency.objects.get(code=from_currency)
        to_curr = Currency.objects.get(code=to_currency)
    except Currency.DoesNotExist:
        return JsonResponse({'error': 'Invalid currency'}, status=400)

    # Convert to RWF first, then to target currency
    rwf_amount = from_curr.convert_to_rwf(amount)
    converted_amount = to_curr.convert_from_rwf(rwf_amount)

    return JsonResponse({
        'original_amount': float(amount),
        'original_currency': from_currency,
        'converted_amount': converted_amount,
        'converted_currency': to_currency,
        'symbol': to_curr.symbol
    })
