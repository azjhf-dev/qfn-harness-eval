"""Monthly recurrence helpers."""
import calendar

def add_months(d, n):
    """Return the date n months after d (n may be negative).

    Keeps d's day-of-month where possible; if the target month is shorter it
    clamps to that month's last day. Clamping must NOT cascade:
    add_months(date(2024, 1, 31), 2) is 2024-03-31, not 2024-03-29.
    """
    y, m, day = d.year, d.month, d.day
    step = 1 if n >= 0 else -1
    for _ in range(abs(n)):
        m += step
        if m > 12:
            y += 1
            m = 1
        if m < 1:
            y -= 1
            m = 12
        day = min(day, calendar.monthrange(y, m)[1])
    return d.replace(year=y, month=m, day=day)
