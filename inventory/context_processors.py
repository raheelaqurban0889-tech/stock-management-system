from .models import Settings


def currency_context(request):
    """Make currency symbol and settings available in all templates"""
    try:
        settings_obj = Settings.get_settings()
        return {
            'currency_symbol': Settings.get_currency_symbol(),
            'settings': settings_obj,
        }
    except Exception:
        return {
            'currency_symbol': '₨',
            'settings': None,
        }