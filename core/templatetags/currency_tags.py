from django import template
from django.conf import settings
from decimal import Decimal

register = template.Library()


@register.filter
def currency(value, currency_code=None):
    """
    Format a value as currency.
    Usage: {{ price|currency }} or {{ price|currency:"USD" }}
    """
    if value is None:
        return ''

    try:
        value = Decimal(str(value))
    except:
        return value

    if currency_code is None:
        currency_code = 'RWF'

    currency_info = settings.SUPPORTED_CURRENCIES.get(currency_code, {})
    symbol = currency_info.get('symbol', currency_code)
    rate = Decimal(str(currency_info.get('rate', 1.0)))

    converted_value = value * rate

    # Format based on currency
    if currency_code in ['JPY', 'KES', 'UGX', 'TZS', 'RWF']:
        # No decimal places for these currencies
        formatted = f"{symbol} {converted_value:,.0f}"
    else:
        formatted = f"{symbol}{converted_value:,.2f}"

    return formatted


@register.simple_tag(takes_context=True)
def price_in_currency(context, value):
    """
    Convert and format price in user's selected currency.
    Usage: {% price_in_currency product.price %}
    """
    if value is None:
        return ''

    try:
        value = Decimal(str(value))
    except:
        return value

    # Get current currency from context
    current_currency = context.get('current_currency')
    if not current_currency:
        return f"RWF {value:,.0f}"

    converted = current_currency.convert_from_rwf(value)
    symbol = current_currency.symbol

    if current_currency.decimal_places == 0:
        return f"{symbol} {converted:,.0f}"
    else:
        return f"{symbol}{converted:,.2f}"


@register.filter
def convert_currency(value, currency_obj):
    """
    Convert a value from RWF to another currency.
    Usage: {{ price|convert_currency:current_currency }}
    """
    if value is None or currency_obj is None:
        return value

    try:
        value = Decimal(str(value))
    except:
        return value

    return currency_obj.convert_from_rwf(value)


@register.inclusion_tag('core/currency_selector.html', takes_context=True)
def currency_selector(context):
    """Render a currency selector dropdown"""
    return {
        'currencies': context.get('currencies', []),
        'current_currency': context.get('current_currency'),
        'request': context.get('request'),
    }


@register.inclusion_tag('core/language_selector.html', takes_context=True)
def language_selector(context):
    """Render a language selector dropdown"""
    return {
        'available_languages': context.get('available_languages', []),
        'current_language': context.get('current_language', 'en'),
        'request': context.get('request'),
    }
