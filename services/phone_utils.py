import re


def classify_phone(raw: str | None) -> str:
    """Classify an Indian phone number as 'mobile', 'landline', or 'unknown'.
    Indian mobiles are 10 digits starting with 6-9 (after stripping country code / trunk prefix)."""
    if not raw:
        return "unknown"
    digits = re.sub(r"\D", "", raw)
    if digits.startswith("91") and len(digits) == 12:
        digits = digits[2:]
    elif digits.startswith("0") and len(digits) == 11:
        digits = digits[1:]
    if len(digits) == 10 and digits[0] in "6789":
        return "mobile"
    if len(digits) >= 7:
        return "landline"
    return "unknown"
