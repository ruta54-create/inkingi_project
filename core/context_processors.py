from django.conf import settings


def site_settings(request):
    """Add site settings to all template contexts"""
    try:
        from .models import SiteSettings, AdvertisingBanner
        from django.utils import timezone

        site = SiteSettings.get_settings()

        # Get active banners
        now = timezone.now()
        try:
            banners = AdvertisingBanner.objects.filter(is_active=True)

            # Filter by date if set
            active_banners = []
            for banner in banners:
                if banner.start_date and banner.start_date > now:
                    continue
                if banner.end_date and banner.end_date < now:
                    continue
                active_banners.append(banner)
        except Exception:
            active_banners = []

        return {
            'site_settings': site,
            'advertising_banners': active_banners,
        }
    except Exception:
        # Return empty context if database not ready
        return {
            'site_settings': None,
            'advertising_banners': [],
        }


def currency_context(request):
    """Add currency information to all template contexts"""
    try:
        from .models import Currency

        # Get current currency from session or cookie
        current_currency_code = request.session.get('currency')
        if not current_currency_code:
            current_currency_code = request.COOKIES.get(settings.CURRENCY_COOKIE_NAME, settings.DEFAULT_CURRENCY)

        # Get currency object
        try:
            current_currency = Currency.objects.get(code=current_currency_code, is_active=True)
        except Currency.DoesNotExist:
            # Fallback to RWF
            try:
                current_currency, _ = Currency.objects.get_or_create(
                    code='RWF',
                    defaults={'name': 'Rwandan Franc', 'symbol': 'RWF', 'exchange_rate': 1.0}
                )
            except Exception:
                current_currency = None

        # Get all active currencies
        try:
            currencies = Currency.objects.filter(is_active=True)
        except Exception:
            currencies = []

        return {
            'current_currency': current_currency,
            'currencies': currencies,
            'supported_currencies': settings.SUPPORTED_CURRENCIES,
        }
    except Exception:
        return {
            'current_currency': None,
            'currencies': [],
            'supported_currencies': settings.SUPPORTED_CURRENCIES,
        }


def language_context(request):
    """Add language information to all template contexts"""
    from django.utils import translation

    current_language = translation.get_language() or settings.LANGUAGE_CODE

    languages = [
        {'code': 'en', 'name': 'English', 'native_name': 'English'},
        {'code': 'fr', 'name': 'French', 'native_name': 'Français'},
        {'code': 'rw', 'name': 'Kinyarwanda', 'native_name': 'Ikinyarwanda'},
    ]

    return {
        'current_language': current_language,
        'available_languages': languages,
        'LANGUAGES': settings.LANGUAGES,
    }
