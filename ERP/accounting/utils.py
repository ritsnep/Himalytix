from django.core.cache import cache

from .models import Currency

CACHE_TIMEOUT_SHORT = 60 * 5  # 5 minutes

def get_active_currency_choices():
    """Return active currency choices, cached to avoid database hits."""
    key = "active_currency_choices"
    choices = cache.get(key)
    if choices is None:
        choices = [
            (c.currency_code, f"{c.currency_code} - {c.currency_name}- {c.symbol}")
            for c in Currency.objects.filter(is_active=True)
        ]
        cache.set(key, choices, CACHE_TIMEOUT_SHORT)
    return choices