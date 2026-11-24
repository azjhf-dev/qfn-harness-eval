"""The bug: clamping must not cascade across intermediate months."""
from datetime import date
from recurrence import add_months

assert add_months(date(2024, 1, 31), 2) == date(2024, 3, 31)    # clamp only the final month
assert add_months(date(2024, 3, 31), -2) == date(2024, 1, 31)   # same backwards
assert add_months(date(2023, 1, 31), 13) == date(2024, 2, 29)   # clamp happens once, at the end

print("ok")
