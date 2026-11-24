from orders import tax_cents, order_total_cents

CAT = {"S": {"price_cents": 2500}, "T": {"price_cents": 1050},
       "D": {"price_cents": 995}, "C": {"price_cents": 200}}

assert tax_cents(1050) == 95                 # 94.5 -> 95
assert tax_cents(1000) == 90

# free shipping when the discounted subtotal is AT LEAST the threshold
assert order_total_cents(CAT, [("S", 2)]) == 5000 + 450          # subtotal 5000 exactly: free
assert order_total_cents(CAT, [("T", 1)]) == 1050 + 95 + 499     # below threshold

# discounts flow through to orders
assert order_total_cents(CAT, [("D", 2)], 10) == 1791 + 161 + 499          # 2451
assert order_total_cents(CAT, [("D", 1), ("C", 5)], 10) == 1796 + 162 + 499  # 2457

print("ok")
