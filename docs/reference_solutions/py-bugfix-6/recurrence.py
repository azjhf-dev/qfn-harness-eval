"""Monthly recurrence helpers."""
import calendar

def add_months(d, n):
    """Return the date n months after d (n may be negative).

    Keeps d's day-of-month where possible; if the target month is shorter it
    clamps to that month's last day. Clamping must NOT cascade:
    add_months(date(2024, 1, 31), 2) is 2024-03-31, not 2024-03-29.
    """
    total = d.year * 12 + (d.month - 1) + n
    y, m0 = divmod(total, 12)
    day = min(d.day, calendar.monthrange(y, m0 + 1)[1])
    return d.replace(year=y, month=m0 + 1, day=day)
