"""Pricing rules. All money is integer cents. See test_pricing.py for the contract."""

def _round_half_up_div(num, den):
    """num / den rounded to the nearest integer, ties away from zero (num, den >= 0)."""
    return (2 * num + den) // (2 * den)

def unit_price_cents(catalog, sku):
    return catalog[sku]["price_cents"]

def discounted_cents(price_cents, percent_off):
    """price_cents discounted by percent_off (0-100), rounded to the nearest cent,
    ties away from zero."""
    return _round_half_up_div(price_cents * (100 - percent_off), 100)

def line_total_cents(catalog, sku, qty, percent_off=0):
    """Total for qty units of sku: percent_off applies to the line subtotal
    (unit price x qty), rounded once, ties away from zero."""
    subtotal = unit_price_cents(catalog, sku) * qty
    return _round_half_up_div(subtotal * (100 - percent_off), 100)
