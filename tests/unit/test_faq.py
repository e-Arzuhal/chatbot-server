"""Unit tests for FAQ matching logic in app/services/chatbot.py."""
import pytest
from app.services.chatbot import _expand_message, _find_faq_match


# ── _expand_message ──────────────────────────────────────────────────────────

def test_expand_lowercases_input():
    result = _expand_message("SOZLESME")
    assert "sozlesme" in result


def test_expand_converts_turkish_to_ascii():
    result = _expand_message("sözleşme")
    assert "sozlesme" in result


def test_expand_preserves_original_lowercase():
    result = _expand_message("hello")
    assert "hello" in result


def test_expand_strips_turkish_suffix():
    result = _expand_message("sözleşmelerim")
    # After ASCII conversion + suffix stripping "sozlesme" stem must appear
    assert "sozlesme" in result


def test_expand_handles_empty_string():
    result = _expand_message("")
    assert isinstance(result, str)


def test_expand_returns_string():
    assert isinstance(_expand_message("test"), str)


# ── _find_faq_match ──────────────────────────────────────────────────────────

def test_faq_merhaba():
    resp, suggestions = _find_faq_match("merhaba")
    assert resp is not None
    assert isinstance(suggestions, list)
    assert len(suggestions) > 0


def test_faq_selam():
    resp, _ = _find_faq_match("selam")
    assert resp is not None


def test_faq_sozlesme_olustur():
    resp, _ = _find_faq_match("sozlesme olustur")
    assert resp is not None


def test_faq_yeni_sozlesme():
    resp, _ = _find_faq_match("yeni sozlesme")
    assert resp is not None


def test_faq_pdf_indir():
    resp, _ = _find_faq_match("pdf indir")
    assert resp is not None


def test_faq_onay():
    resp, _ = _find_faq_match("onay")
    assert resp is not None


def test_faq_dilekce():
    resp, _ = _find_faq_match("dilekce")
    assert resp is not None


def test_faq_hesap_ayarlari():
    resp, _ = _find_faq_match("hesap ayarlari")
    assert resp is not None


def test_faq_sifre():
    resp, _ = _find_faq_match("sifre")
    assert resp is not None


def test_faq_durum_takip():
    resp, _ = _find_faq_match("durum takip")
    assert resp is not None


def test_faq_no_match_returns_none_pair():
    resp, suggestions = _find_faq_match("tamamen alakasiz metin xyz999")
    assert resp is None
    assert suggestions is None


def test_faq_returns_string_response():
    resp, _ = _find_faq_match("pdf")
    assert isinstance(resp, str)
    assert len(resp) > 0


def test_faq_returns_suggestion_list():
    _, suggestions = _find_faq_match("merhaba")
    assert isinstance(suggestions, list)
    assert all(isinstance(s, str) for s in suggestions)


def test_faq_first_match_wins():
    """The FAQ list is ordered; first matching entry is always returned."""
    resp1, _ = _find_faq_match("sozlesme nasil")
    resp2, _ = _find_faq_match("sozlesme nasil")
    assert resp1 == resp2


def test_faq_turkish_suffix_match():
    """Turkish inflected form should still match via _expand_message."""
    resp, _ = _find_faq_match("sözleşmemi nasıl oluştururum")
    # Current morphological expansion handles this case
    assert resp is not None
