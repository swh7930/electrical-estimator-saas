import re

# Simple, pragmatic patterns
_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
_CITY_RE = re.compile(r"^[A-Za-z][A-Za-z .'\-]{0,98}[A-Za-z.]?$")
_DIGITS_RE = re.compile(r"\d+")
_STATE_RE = re.compile(r"^[A-Za-z]{2}$")
_ZIP_RE = re.compile(r"^\d{5}(-\d{4})?$")

def clean_str(val: str | None, max_len: int = 255) -> str | None:
    """
    Collapse whitespace, trim, enforce max length. Returns None if empty after cleaning.
    """
    if val is None:
        return None
    s = re.sub(r"\s+", " ", val).strip()
    if not s:
        return None
    return s[:max_len]

def is_valid_email(val: str | None) -> bool:
    if not val:
        return True
    return bool(_EMAIL_RE.match(val))

def normalize_phone(val: str | None) -> str | None:
    """
    Normalize US phone to (###) ###-####. Accept 10 digits or 11 starting with '1'.
    Returns None if invalid or empty.
    """
    if not val:
        return None
    digits = "".join(re.findall(r"\d", val))
    if len(digits) == 11 and digits.startswith("1"):
        digits = digits[1:]
    if len(digits) != 10:
        return None
    return f"({digits[0:3]}) {digits[3:6]}-{digits[6:]}"

def is_valid_city(val: str | None) -> bool:
    if not val:
        return True
    return bool(_CITY_RE.match(val))

def derive_city_from_address(address: str | None) -> str | None:
    """
    Very light parser: if address contains a comma, take the token after the first comma.
    """
    if not address:
        return None
    if "," not in address:
        return None
    part = address.split(",", 1)[1].strip()
    return clean_str(part, max_len=100)

def is_valid_state(val: str | None) -> bool:
    if not val:
        return True
    return bool(_STATE_RE.match(val.strip()))

def is_valid_zip(val: str | None) -> bool:
    if not val:
        return True
    return bool(_ZIP_RE.match(val.strip()))