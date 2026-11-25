import phonenumbers
from phonenumbers import NumberParseException, PhoneNumberFormat, PhoneNumberType

PK_PHONE_ERROR = (
    "Enter a valid Pakistani mobile number (e.g. 0300 1234567 or +923001234567)."
)


def normalize_pakistani_phone(raw: str) -> str:
    """Validate and normalize a Pakistani mobile number to E.164 (+923XXXXXXXXX)."""
    cleaned = (raw or "").strip()
    if not cleaned:
        raise ValueError(PK_PHONE_ERROR)

    try:
        parsed = phonenumbers.parse(cleaned, "PK")
    except NumberParseException as exc:
        raise ValueError(PK_PHONE_ERROR) from exc

    if not phonenumbers.is_valid_number(parsed):
        raise ValueError(PK_PHONE_ERROR)

    if phonenumbers.region_code_for_number(parsed) != "PK":
        raise ValueError(PK_PHONE_ERROR)

    number_type = phonenumbers.number_type(parsed)
    if number_type not in (
        PhoneNumberType.MOBILE,
        PhoneNumberType.FIXED_LINE_OR_MOBILE,
    ):
        raise ValueError(PK_PHONE_ERROR)

    national_digits = str(parsed.national_number)
    if len(national_digits) != 10 or not national_digits.startswith("3"):
        raise ValueError(PK_PHONE_ERROR)

    return phonenumbers.format_number(parsed, PhoneNumberFormat.E164)


def validate_password_strength(value: str) -> str:
    """Validate password length and bcrypt 72-byte UTF-8 limit."""
    if len(value) < 8:
        raise ValueError("Password must be at least 8 characters.")

    if len(value.encode("utf-8")) > 72:
        raise ValueError("Password must not exceed 72 UTF-8 bytes.")

    return value
