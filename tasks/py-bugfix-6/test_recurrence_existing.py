"""Behaviour that is correct as shipped. Any fix that breaks these is a regression."""
from datetime import date
from recurrence import add_months

assert add_months(date(2024, 5, 10), 0) == date(2024, 5, 10)
assert add_months(date(2024, 3, 15), 1) == date(2024, 4, 15)
assert add_months(date(2024, 1, 31), 1) == date(2024, 2, 29)    # leap year clamp, one step
assert add_months(date(2023, 1, 31), 1) == date(2023, 2, 28)    # non-leap clamp, one step
assert add_months(date(2023, 12, 15), 1) == date(2024, 1, 15)   # year rollover
assert add_months(date(2024, 3, 31), -1) == date(2024, 2, 29)   # negative step with clamp
assert add_months(date(2024, 1, 15), -1) == date(2023, 12, 15)  # negative year rollover
assert add_months(date(2023, 6, 20), 12) == date(2024, 6, 20)   # whole years keep the day

print("ok")
