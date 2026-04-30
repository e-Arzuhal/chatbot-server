"""
e-Arzuhal Chatbot Service
Context-aware Gemini LLM entegrasyonu + FAQ fallback
"""
import logging

from app.config import GEMINI_API_KEY, LLM_MODEL, SYSTEM_PROMPT

logger = logging.getLogger("chatbot")

# Kural tabanli SSS: (anahtar_kelimeler, yanit, onerilen_sorular)
FAQ = [
    (
        ["sozlesme nasil", "nasil sozlesme", "sozlesme olustur", "yeni sozlesme", "baslangic"],
        "Sözleşme oluşturmak için sol menüden 'Yeni Sözleşme' seçeneğine tıklayın. "
        "Sözleşme ihtiyacınızı doğal dilde yazın (örn: 'Ahmet Yılmaz'a 50.000 TL borç vereceğim, 6 ayda geri ödenecek'). "
        "Sistem otomatik olarak sözleşme tipini ve detayları tespit edecektir.",
        ["PDF nasıl indirilir?", "Hangi sözleşme tipleri destekleniyor?", "Onay süreci nasıl işliyor?"],
    ),
    (
        ["pdf", "indir", "indirme"],
        "PDF indirmek için sözleşme oluşturduktan sonra 'PDF Önizleme' adımında 'PDF İndir' butonuna tıklayın. "
        "Ayrıca sözleşme detay sayfasından da PDF indirebilirsiniz.",
        ["Sözleşme nasıl oluşturulur?", "Onay süreci nasıl işliyor?"],
    ),
    (
        ["onay", "imza", "gonder", "taraf"],
        "Sözleşmeyi oluşturduktan sonra 'Onaya Gönder' butonuna basın. "
        "Karşı taraf e-posta ile bildirim alır ve onay sayfasından sözleşmeyi onaylayabilir veya reddedebilir. "
        "Tüm taraflar onayladığında sözleşme tamamlanmış sayılır.",
        ["PDF nasıl indirilir?", "Sözleşme durumunu nasıl görebilirim?"],
    ),
    (
        ["borclu", "borc sozlesme", "kira", "hizmet", "satis", "is sozlesme", "vekaletname", "taahhut", "tip", "cesit"],
        "e-Arzuhal şu sözleşme tiplerini desteklemektedir:\n"
        "• Borç Sözleşmesi\n• Kira Sözleşmesi\n• Hizmet Sözleşmesi\n• Satış Sözleşmesi\n"
        "• İş Sözleşmesi\n• Vekaletname\n• Taahhütname\n\n"
        "Metninizden otomatik olarak doğru tip tespit edilir.",
        ["Sözleşme nasıl oluşturulur?", "Dilekçe oluşturabilir miyim?"],
    ),
    (
        ["dilekce", "petition"],
        "Dilekçe oluşturmak için sol menüden 'Dilekçeler' bölümüne gidin. "
        "Standart dilekçe şablonlarından seçim yapabilir veya kendi metninizi girebilirsiniz.",
        ["Sözleşme nasıl oluşturulur?", "PDF nasıl indirilir?"],
    ),
    (
        ["durum", "takip", "bekliyor", "onaylandi", "reddedildi"],
        "Sözleşme durumunu 'Sözleşmelerim' sayfasından takip edebilirsiniz. "
        "Durumlar: Taslak, Onay Bekliyor, Onaylandı, Reddedildi.",
        ["Onay süreci nasıl işliyor?", "PDF nasıl indirilir?"],
    ),
    (
        ["hesap", "sifre", "profil", "ayar", "giris", "kayit"],
        "Hesap ayarlarınıza sol menüden 'Ayarlar' bölümünden ulaşabilirsiniz. "
        "Profil bilgilerinizi güncelleyebilir, şifrenizi değiştirebilir ve bildirim tercihlerinizi yönetebilirsiniz.",
        ["Sözleşme nasıl oluşturulur?"],
    ),
    (
        ["merhaba", "selam", "hello", "hi", "nasılsın", "nasilsin"],
        "Merhaba! Ben e-Arzuhal'ın yardımcı asistanıyım. "
        "Sözleşme oluşturma, PDF indirme veya onay süreci hakkında sorularınızı yanıtlayabilirim.",
        ["Sözleşme nasıl oluşturulur?", "PDF nasıl indirilir?", "Hangi sözleşme tipleri destekleniyor?"],
    ),
]

LEGAL_DISCLAIMER = (
    "\n\n---\n*Bu yanıt yalnızca bilgilendirme amaçlıdır ve hukuki tavsiye niteliği taşımaz.*"
)

DEFAULT_RESPONSE = (
    "Bu sorunun cevabı bende yok; uydurmamak için emin olmadığımı belirtmeliyim. "
    "Sözleşme oluşturma, PDF indirme veya onay süreci hakkında soru sorabilirsiniz."
)
DEFAULT_SUGGESTIONS = [
    "Sözleşme nasıl oluşturulur?",
    "PDF nasıl indirilir?",
    "Hangi sözleşme tipleri destekleniyor?",
]

# Niyete göre önerilen sorular
INTENT_SUGGESTIONS = {
    "CONTRACT_CLAUSE_QUESTION": [
        "Bu maddeler zorunlu mu?",
        "Başka hangi maddeler eklenebilir?",
        "Sözleşmedeki riskler neler?",
    ],
    "MISSING_CLAUSE_QUESTION": [
        "Bu eksik maddeler ne işe yarar?",
        "Hangileri zorunlu, hangileri opsiyonel?",
        "Eksik maddeleri nasıl eklerim?",
    ],
    "LEGAL_QUESTION": [
        "İlgili kanun maddeleri neler?",
        "Benzer Yargıtay kararları var mı?",
        "Hukuki riskler neler?",
    ],
    "LAW_REFERENCE": [
        "Bu madde ne anlama geliyor?",
        "Uygulamada nasıl yorumlanıyor?",
        "Ceza hükmü var mı?",
    ],
}


_TR_SUFFIXES = [
    "lerim", "lerin", "lerini", "lerinde", "lerinden", "lerine", "leriyle",
    "larım", "ların", "larını", "larında", "larından", "larına", "larıyla",
    "imin", "imin", "imde", "imden", "ime", "imle",
    "inin", "inde", "inden", "ine", "inle",
    "unun", "unda", "undan", "una", "unla",
    "ünün", "ünde", "ünden", "üne", "ünle",
    "ler", "lar", "ım", "im", "um", "üm",
    "ın", "in", "un", "ün",
    "da", "de", "dan", "den",
    "ya", "ye", "yı", "yi", "yu", "yü",
    "nın", "nin", "nun", "nün",
    "nda", "nde", "ndan", "nden",
    "na", "ne", "mı", "mi", "mu", "mü",
    "la", "le", "ca", "ce",
]

_TR_TO_ASCII = str.maketrans("çğışöüÇĞİŞÖÜ", "cgisoucgiSOU".lower())


def _ascii(text: str) -> str:
    """Türkçe karakterleri ASCII karşılıklarına çevirir."""
    return text.translate(_TR_TO_ASCII)


_CONSONANT_HARDEN = str.maketrans("bdgc", "ptkç")


def _strip_suffix(word: str) -> str:
    """Kelimeden yaygın Türkçe ekleri çıkarır, ünsüz yumuşamasını geri alır."""
    for suffix in _TR_SUFFIXES:
        if word.endswith(suffix) and len(word) - len(suffix) >= 3:
            stem = word[: -len(suffix)]
            # hesab→hesap, kayd→kayıt gibi yumuşamaları geri al
            return stem[:-1] + stem[-1].translate(_CONSONANT_HARDEN) if stem else stem
    return word


def _expand_message(message: str) -> str:
    """
    Eşleşme yüzeyini genişletir:
    orijinal + ASCII karşılığı + ek çıkarılmış ASCII karşılığı
    """
    lower = message.lower()
    ascii_msg = _ascii(lower)
    words = ascii_msg.split()
    once = [_strip_suffix(w) for w in words]
    twice = [_strip_suffix(w) for w in once]
    return lower + " " + ascii_msg + " " + " ".join(once) + " " + " ".join(twice)


def _find_faq_match(message: str):
    expanded = _expand_message(message)
    for keywords, response, suggestions in FAQ:
        if any(kw in expanded for kw in keywords):
            return response, suggestions
    return None, None


def _build_enriched_prompt(intent: str, contract_context: str = None,
                           graphrag_context: str = None) -> str:
    """Intent ve bağlama göre Gemini system prompt oluşturur."""
    parts = [SYSTEM_PROMPT, "\n\n--- BAĞLAM BİLGİSİ ---\n"]

    if intent == "CONTRACT_CLAUSE_QUESTION":
        parts.append("Kullanıcı, oluşturduğu sözleşmenin maddeleri hakkında soru soruyor.\n")
    elif intent == "MISSING_CLAUSE_QUESTION":
        parts.append("Kullanıcı, sözleşmesindeki eksik maddeler hakkında bilgi istiyor.\n")
    elif intent == "LEGAL_QUESTION":
        parts.append("Kullanıcı genel bir hukuki soru soruyor. İlgili kanun maddelerini referans vererek yanıtla.\n")
    elif intent == "LAW_REFERENCE":
        parts.append("Kullanıcı belirli kanun maddeleri (TBK/HMK vb.) hakkında bilgi istiyor.\n")

    if contract_context:
        parts.append(f"\nKullanıcının aktif sözleşmesi:\n{contract_context}\n")

    if graphrag_context:
        parts.append(f"\nBilgi Grafiği (GraphRAG) analiz sonucu:\n{graphrag_context}\n")

    parts.append("\nYukarıdaki bağlam bilgisini kullanarak kullanıcının sorusuna Türkçe, kısa ve net yanıt ver.")
    return "".join(parts)


def _call_llm(message: str, history: list, system_override: str = None) -> str:
    """Gemini API'ye istek at"""
    from google import genai
    from google.genai import types

    client = genai.Client(api_key=GEMINI_API_KEY)

    # Gemini history formatı: [{role, parts}]
    chat_history = []
    for h in history[-6:]:  # Son 6 mesaj (3 tur)
        role = "user" if h.role == "user" else "model"
        chat_history.append(types.Content(role=role, parts=[types.Part(text=h.content)]))

    chat = client.chats.create(
        model=LLM_MODEL,
        config=types.GenerateContentConfig(
            system_instruction=system_override or SYSTEM_PROMPT,
        ),
        history=chat_history,
    )
    response = chat.send_message(message)
    return response.text


def _iter_llm_stream(message: str, history: list, system_override: str = None):
    """Gemini streaming sync generator — her chunk'ı yield eder."""
    from google import genai
    from google.genai import types

    client = genai.Client(api_key=GEMINI_API_KEY)

    contents = []
    for h in history[-6:]:
        role = "user" if h.role == "user" else "model"
        contents.append(types.Content(role=role, parts=[types.Part(text=h.content)]))
    contents.append(types.Content(role="user", parts=[types.Part(text=message)]))

    for chunk in client.models.generate_content_stream(
        model=LLM_MODEL,
        contents=contents,
        config=types.GenerateContentConfig(
            system_instruction=system_override or SYSTEM_PROMPT,
        ),
    ):
        if chunk.text:
            yield chunk.text


async def get_chat_response(message: str, history: list, intent: str = None,
                            contract_context: str = None,
                            graphrag_context: str = None) -> tuple[str, list]:
    """
    Ana chatbot logic:
    1. GENERAL_HELP veya enrichment yoksa → FAQ eşleşme dene
    2. Enrichment varsa → intent'e göre prompt oluştur ve LLM'e gönder
    3. Fallback: varsayılan yanıt
    """
    import asyncio

    # 1. FAQ kontrolü (GENERAL_HELP veya enrichment yoksa)
    if not intent or intent == "GENERAL_HELP":
        faq_response, faq_suggestions = _find_faq_match(message)
        if faq_response:
            return faq_response, faq_suggestions

    # 2. LLM ile context-aware yanıt
    if GEMINI_API_KEY:
        try:
            from app.sanitizer import redact

            clean_msg, found_msg = redact(message)
            clean_contract, found_ctx = redact(contract_context or "")
            clean_graphrag, found_rag = redact(graphrag_context or "")
            all_found = found_msg + found_ctx + found_rag
            if all_found:
                logger.warning("PII redacted before LLM: %s", all_found)

            system_override = None
            if intent and intent != "GENERAL_HELP":
                system_override = _build_enriched_prompt(
                    intent,
                    clean_contract or None,
                    clean_graphrag or None,
                )

            # Sync Gemini çağrısını thread pool'a taşı — event loop bloklanmaz
            llm_response = await asyncio.to_thread(
                _call_llm, clean_msg, history, system_override
            )
            suggestions = INTENT_SUGGESTIONS.get(intent, DEFAULT_SUGGESTIONS)
            return llm_response + LEGAL_DISCLAIMER, suggestions
        except Exception as e:
            logger.error("LLM hatası: %s", e, exc_info=True)

    # 3. Fallback
    return DEFAULT_RESPONSE, DEFAULT_SUGGESTIONS
