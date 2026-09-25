from django import template
from django.contrib.humanize.templatetags.humanize import intcomma
from decimal import Decimal

register = template.Library()


@register.filter(name='currency')
def currency(value, symbol='$'):
    """
    Format a number as currency, prefixed with the given symbol.
    Usage: {{ value|currency:currency_symbol }}
    Example: 1234567.89 becomes $1,234,567.89 (symbol defaults to $ if not supplied)
    """
    if value is None:
        return f'{symbol}0.00'

    try:
        value = Decimal(str(value))
        formatted = intcomma(f"{value:,.2f}")
        return f"{symbol}{formatted}"
    except (ValueError, TypeError):
        return f'{symbol}0.00'


@register.filter(name='currency_no_symbol')
def currency_no_symbol(value):
    """
    Format a number as currency without any currency symbol.
    Example: 1234567.89 becomes 1,234,567.89
    """
    if value is None:
        return '0.00'

    try:
        value = Decimal(str(value))
        return f"{value:,.2f}"
    except (ValueError, TypeError):
        return '0.00'


@register.filter(name='currency_short')
def currency_short(value, symbol='$'):
    """
    Format large numbers in short form, prefixed with the given symbol.
    Usage: {{ value|currency_short:currency_symbol }}
    Example: 1234567 becomes $1.23M (symbol defaults to $ if not supplied)
    """
    if value is None:
        return f'{symbol}0'

    try:
        value = float(value)
        if value >= 1_000_000_000:
            return f"{symbol}{value / 1_000_000_000:.2f}B"
        elif value >= 1_000_000:
            return f"{symbol}{value / 1_000_000:.2f}M"
        elif value >= 1_000:
            return f"{symbol}{value / 1_000:.2f}K"
        else:
            return f"{symbol}{value:,.2f}"
    except (ValueError, TypeError):
        return f'{symbol}0'
