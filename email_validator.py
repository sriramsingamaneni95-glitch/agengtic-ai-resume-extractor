"""Tool: validate/clean an email address (Point 2)."""
import re

# BUG FIX: previous pattern only allowed a single dot in the domain, so
# common multi-level domains like "mail.co.in" or "example.co.uk" were
# incorrectly rejected. This pattern allows any number of subdomains.
EMAIL_RE = re.compile(r"^[\w\.\+\-]+@[\w\-]+(\.[\w\-]+)*\.[a-zA-Z]{2,}$")


def validate_email(email: str) -> tuple[bool, str]:
    if not email:
        return False, ""
    email = email.strip()
    return bool(EMAIL_RE.match(email)), email
