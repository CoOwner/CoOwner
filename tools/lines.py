import re
from datetime import date
from html import escape

BIRTH = date(2003, 8, 6)


def uptime(today=None, birth=BIRTH):
    t = today or date.today()
    y = t.year - birth.year
    m = t.month - birth.month
    d = t.day - birth.day
    if d < 0:
        m -= 1
        d += (date(t.year, t.month, 1) - date.resolution).day
    if m < 0:
        y -= 1
        m += 12
    part = lambda n, w: f"{n} {w}{'' if n == 1 else 's'}"
    return f"{part(y, 'year')}, {part(m, 'month')}, {part(d, 'day')}"


def uptime_spans(text):
    return "".join(
        f'<tspan class="n">{escape(p)}</tspan>' if p.isdigit() else f'<tspan class="v">{escape(p)}</tspan>'
        for p in re.split(r"(\d+)", text) if p
    )


def num(n):
    return "—" if n is None else f"{n:,}"
