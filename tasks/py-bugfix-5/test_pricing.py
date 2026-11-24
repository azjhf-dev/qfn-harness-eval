from pricing import unit_price_cents, discounted_cents, line_total_cents

CAT = {"A": {"price_cents": 995}, "B": {"price_cents": 101}, "C": {"price_cents": 200}}

assert unit_price_cents(CAT, "A") == 995

# rounding to the nearest cent, ties away from zero
assert discounted_cents(995, 10) == 896      # 895.5 -> 896
assert discounted_cents(1000, 10) == 900
assert discounted_cents(750, 0) == 750
assert discounted_cents(750, 100) == 0

# discount applies to the line subtotal, rounded once
assert line_total_cents(CAT, "A", 1, 10) == 896
assert line_total_cents(CAT, "B", 3, 50) == 152   # 303 x 0.5 = 151.5 -> 152, not 3 x 50
assert line_total_cents(CAT, "C", 5, 0) == 1000

print("ok")
