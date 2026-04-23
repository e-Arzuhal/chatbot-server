import re
import logging

logger = logging.getLogger("chatbot")

# TC Kimlik (11 hane) önce gelmeli — yoksa VERGİ_NO (10 hane) TC'nin ilk 10 hanesini yutar
_PATTERNS = [
    (re.compile(r'\b[1-9]\d{10}\b'),                                                   "[TC_KİMLİK]"),
    (re.compile(r'\bTR\d{24}\b', re.IGNORECASE),                                       "[IBAN]"),
    (re.compile(r'(\+90[\s\-]?|0[\s\-]?)?5\d{2}[\s\-]?\d{3}[\s\-]?\d{2}[\s\-]?\d{2}\b'), "[TELEFON]"),
    (re.compile(r'\b[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}\b'),             "[E-POSTA]"),
    (re.compile(r'\b\d{4}[\s\-]?\d{4}[\s\-]?\d{4}[\s\-]?\d{4}\b'),                   "[KART_NO]"),
    (re.compile(r'\b\d{10}\b'),                                                         "[VERGİ_NO]"),
]


def redact(text: str) -> tuple[str, list[str]]:
    """
    Hassas verileri anonim etiketlerle maskeler.
    Döner: (temizlenmiş_metin, bulunan_tipler)
    Bulunan tipler loglama için kullanılır — gerçek veri asla loglanmaz.
    """
    if not text:
        return text, []
    found = []
    for pattern, label in _PATTERNS:
        new_text, n = pattern.subn(label, text)
        if n:
            found.append(label)
            text = new_text
    return text, found
