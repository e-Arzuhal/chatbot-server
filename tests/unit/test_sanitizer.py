"""Unit tests for app/sanitizer.py — PII redaction patterns."""
import pytest
from app.sanitizer import redact, _PATTERNS


# ── redact() happy-path ──────────────────────────────────────────────────────

def test_tc_kimlik_redacted():
    text, found = redact("12345678901 numaralı şahıs")
    assert "[TC_KİMLİK]" in text
    assert "[TC_KİMLİK]" in found


def test_tc_not_matched_as_vergi():
    """11-digit number must match TC, not VERGİ_NO."""
    text, found = redact("12345678901")
    assert "[TC_KİMLİK]" in text
    assert "[VERGİ_NO]" not in found


def test_vergi_10digit():
    text, found = redact("1234567890")
    assert "[VERGİ_NO]" in text
    assert "[TC_KİMLİK]" not in found


def test_iban_uppercase():
    text, found = redact("TR330006100519786457841326")
    assert "[IBAN]" in text
    assert "[IBAN]" in found


def test_iban_lowercase():
    text, found = redact("tr330006100519786457841326")
    assert "[IBAN]" in text


def test_phone_with_country_prefix():
    text, found = redact("+905321234567")
    assert "[TELEFON]" in text


def test_phone_with_zero_prefix():
    text, found = redact("05321234567")
    assert "[TELEFON]" in text


def test_phone_with_spaces():
    text, found = redact("0532 123 45 67")
    assert "[TELEFON]" in text


def test_email_standard():
    text, found = redact("user@example.com")
    assert "[E-POSTA]" in text


def test_email_subdomain():
    text, found = redact("ali.veli@mail.company.org")
    assert "[E-POSTA]" in text


def test_card_16digit_nospace():
    text, found = redact("4111111111111111")
    assert "[KART_NO]" in text


def test_card_16digit_spaced():
    text, found = redact("4111 1111 1111 1111")
    assert "[KART_NO]" in text


def test_multiple_pii_types():
    text, found = redact("TC: 12345678901 email: user@test.com")
    assert "[TC_KİMLİK]" in text
    assert "[E-POSTA]" in text
    assert len(found) == 2


def test_no_pii_unchanged():
    text, found = redact("Merhaba dünya, nasılsınız?")
    assert text == "Merhaba dünya, nasılsınız?"
    assert found == []


def test_empty_string():
    text, found = redact("")
    assert text == ""
    assert found == []


def test_found_list_accumulates_labels():
    _, found = redact("12345678901 ve TR330006100519786457841326")
    assert "[TC_KİMLİK]" in found
    assert "[IBAN]" in found


def test_pii_removed_from_output():
    original = "TC 98765432109"
    text, _ = redact(original)
    assert "98765432109" not in text


# ── Pattern consistency regression ──────────────────────────────────────────

def test_pii_pattern_consistency_with_logging_filter():
    """
    Regression guard: sanitizer._PATTERNS and PIIRedactFilter must use the
    same pattern list (after Fix 2, logging_config lazy-imports from sanitizer).
    If this test fails someone added a pattern to one file but not the other.
    """
    from app.logging_config import PIIRedactFilter

    filter_instance = PIIRedactFilter()
    # Trigger _scrub with a dummy string to exercise the lazy import
    filter_instance._scrub("dummy")

    # Both should use the exact same object after Fix 2
    from app.sanitizer import _PATTERNS as san_patterns
    # Re-call _scrub to access patterns — verify labels match sanitizer
    san_labels = [label for _, label in san_patterns]

    # Build a string containing every pattern's trigger text and verify
    # the filter produces the same output as redact()
    test_string = (
        "12345678901 "         # TC
        "TR330006100519786457841326 "  # IBAN
        "05321234567 "         # TELEFON
        "a@b.com "             # E-POSTA
        "4111111111111111 "    # KART_NO
        "1234567890"           # VERGİ_NO
    )
    sanitizer_result, _ = redact(test_string)

    import logging
    record = logging.LogRecord(
        name="test", level=logging.INFO, pathname="", lineno=0,
        msg=test_string, args=(), exc_info=None,
    )
    PIIRedactFilter().filter(record)
    filter_result = str(record.msg)

    assert sanitizer_result == filter_result, (
        "PII redaction produces different results in sanitizer vs logging filter"
    )
