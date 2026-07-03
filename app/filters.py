"""Shared Jinja2 filters registered on every templates instance."""
from datetime import timezone, timedelta

_KST = timezone(timedelta(hours=9))


def to_kst(dt):
    if dt is None:
        return dt
    return dt.replace(tzinfo=timezone.utc).astimezone(_KST)


def hex_color_name(hex_str: str) -> str:
    if not hex_str:
        return ""
    h = hex_str.lstrip("#")
    if len(h) < 6:
        return ""
    try:
        r = int(h[0:2], 16) / 255
        g = int(h[2:4], 16) / 255
        b = int(h[4:6], 16) / 255
    except ValueError:
        return ""

    max_c, min_c = max(r, g, b), min(r, g, b)
    lum = (max_c + min_c) / 2
    delta = max_c - min_c

    if delta < 0.05:
        if lum < 0.15: return "검정"
        if lum < 0.45: return "진회색"
        if lum < 0.70: return "회색"
        if lum < 0.90: return "밝은 회색"
        return "흰색"

    sat = delta / (2 - max_c - min_c) if lum > 0.5 else delta / (max_c + min_c)
    if sat < 0.12:
        if lum < 0.20: return "검정"
        if lum < 0.50: return "진회색"
        if lum < 0.75: return "회색"
        return "흰색"

    if max_c == r:
        hue = ((g - b) / delta) % 6
    elif max_c == g:
        hue = (b - r) / delta + 2
    else:
        hue = (r - g) / delta + 4
    hue *= 60

    if   hue < 15  or hue >= 345: base = "빨간색"
    elif hue < 40:                 base = "주황색"
    elif hue < 70:                 base = "노란색"
    elif hue < 155:                base = "초록색"
    elif hue < 195:                base = "청록색"
    elif hue < 255:                base = "파란색"
    elif hue < 290:                base = "보라색"
    else:                          base = "분홍색"

    if lum < 0.25: return "진한 " + base
    if lum > 0.75: return "밝은 " + base
    return base


def register(templates):
    """Register all shared filters on a Jinja2Templates instance."""
    templates.env.filters["kst"] = to_kst
    templates.env.filters["hex_color_name"] = hex_color_name
