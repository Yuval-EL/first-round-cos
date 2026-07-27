"""Small shared helpers: escaping, dates, search blobs.

Escaping discipline: components escape every string argument, view code never
calls esc() directly. Pre-built HTML is passed through as Raw(...).
Any esc() call outside components.py is a smell.
"""

import html
import re
from datetime import date, timedelta

ID_RE = re.compile(r"\b(?:per|co|deal|thr|mtg|prj|agt)_[a-z0-9_]+\b")

MONTHS = ("Jan", "Feb", "Mar", "Apr", "May", "Jun",
          "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")


class Raw(str):
    """A string that is already HTML and must not be escaped again."""
    __slots__ = ()


def esc(value):
    if value is None:
        return ""
    if isinstance(value, Raw):
        return str(value)
    return html.escape(str(value))


def as_date(value):
    """Accept 'YYYY-MM-DD' or a full ISO timestamp; return a date."""
    return date.fromisoformat(str(value)[:10])


def days_between(earlier, later):
    return (as_date(later) - as_date(earlier)).days


def shift_days(value, delta):
    return (as_date(value) + timedelta(days=delta)).isoformat()


def fmt_date(value):
    """2026-07-28 -> 'Jul 28'."""
    d = as_date(value)
    return f"{MONTHS[d.month - 1]} {d.day}"


def fmt_date_full(value):
    d = as_date(value)
    return f"{MONTHS[d.month - 1]} {d.day}, {d.year}"


def fmt_weekday(value):
    d = as_date(value)
    names = ("Monday", "Tuesday", "Wednesday", "Thursday",
             "Friday", "Saturday", "Sunday")
    return names[d.weekday()]


def fmt_time(iso):
    """'2026-07-28T09:30:00-04:00' -> '9:30 AM'."""
    hh, mm = int(iso[11:13]), iso[14:16]
    suffix = "AM" if hh < 12 else "PM"
    display = hh % 12 or 12
    return f"{display}:{mm} {suffix}"


def ago(value, today):
    """Human relative age, always measured against meta.today (never now())."""
    n = days_between(value, today)
    if n <= 0:
        return "today"
    if n == 1:
        return "yesterday"
    if n < 7:
        return f"{n}d ago"
    if n < 60:
        weeks = round(n / 7)
        return f"{weeks}w ago"
    return f"{round(n / 30)}mo ago"


def until(value, today):
    """Human countdown. Negative means overdue."""
    n = days_between(today, value)
    if n < 0:
        return f"overdue by {abs(n)}d"
    if n == 0:
        return "today"
    if n == 1:
        return "tomorrow"
    if n < 14:
        return f"in {n}d"
    return f"in {round(n / 7)}w"


def plural(n, singular, suffix="s"):
    return singular if n == 1 else singular + suffix


def search_blob(*parts):
    """Lowercased haystack for the client-side search box."""
    out = []
    for part in parts:
        if part is None:
            continue
        if isinstance(part, (list, tuple)):
            out.extend(str(p) for p in part if p)
        else:
            out.append(str(part))
    return " ".join(out).lower()
