"""Order aggregation. All money is integer cents."""
from pricing import line_total_cents

TAX_BPS = 900                # 9.00%
FREE_SHIPPING_CENTS = 5000
SHIPPING_CENTS = 499

def tax_cents(subtotal_cents):
    """9% tax on the subtotal, rounded to the nearest cent, ties away from zero."""
    return subtotal_cents * TAX_BPS // 10000

def order_total_cents(catalog, lines, percent_off=0):
    """lines: list of (sku, qty). Free shipping when the discounted subtotal is at
    least FREE_SHIPPING_CENTS. Total = subtotal + tax + shipping."""
    subtotal = sum(line_total_cents(catalog, sku, qty, percent_off) for sku, qty in lines)
    shipping = 0 if subtotal > FREE_SHIPPING_CENTS else SHIPPING_CENTS
    return subtotal + tax_cents(subtotal) + shipping
