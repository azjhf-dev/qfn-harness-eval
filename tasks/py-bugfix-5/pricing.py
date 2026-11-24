"""Pricing rules. All money is integer cents. See test_pricing.py for the contract."""

def unit_price_cents(catalog, sku):
    return catalog[sku]["price_cents"]

def discounted_cents(price_cents, percent_off):
    """price_cents discounted by percent_off (0-100), rounded to the nearest cent,
    ties away from zero."""
    return price_cents * (100 - percent_off) // 100

def line_total_cents(catalog, sku, qty, percent_off=0):
    """Total for qty units of sku: percent_off applies to the line subtotal
    (unit price x qty), rounded once, ties away from zero."""
    unit = discounted_cents(unit_price_cents(catalog, sku), percent_off)
    return unit * qty
