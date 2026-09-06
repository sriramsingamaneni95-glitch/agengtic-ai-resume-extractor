"""Tool: normalize messy resume dates like 'Jan 2020', '2020-01', 'Present' (Point 2)."""
from datetime import datetime

MONTHS = {
    "jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
    "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12,
}


def parse_date(date_str: str):
    if not date_str:
        return None
    s = date_str.strip().lower()
    if s in ("present", "current", "now", "ongoing"):
        return "present"
    for fmt in ("%Y-%m-%d", "%Y-%m", "%b %Y", "%B %Y", "%m/%Y", "%Y"):
        try:
            return datetime.strptime(date_str.strip(), fmt).strftime("%Y-%m")
        except ValueError:
            continue
    return date_str  # fall back to raw string if unparseable
