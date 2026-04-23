"""
e-Arzuhal Chatbot Service
Context-aware Gemini LLM entegrasyonu + FAQ fallback
"""
from app.config import GEMINI_API_KEY, LLM_MODEL, SYSTEM_PROMPT

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

DEFAULT_RESPONSE = (
    "Bu konuda yardımcı olabileceğim bir bilgiye sahip değilim. "
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


def _find_faq_match(message: str):
    msg_lower = message.lower()
    for keywords, response, suggestions in FAQ:
        if any(kw in msg_lower for kw in keywords):
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


def get_chat_response(message: str, history: list, intent: str = None,
                      contract_context: str = None,
                      graphrag_context: str = None) -> tuple[str, list]:
    """
    Ana chatbot logic:
    1. GENERAL_HELP veya enrichment yoksa → FAQ eşleşme dene
    2. Enrichment varsa → intent'e göre prompt oluştur ve LLM'e gönder
    3. Fallback: varsayılan yanıt
    """
    # 1. FAQ kontrolü (GENERAL_HELP veya enrichment yoksa)
    if not intent or intent == "GENERAL_HELP":
        faq_response, faq_suggestions = _find_faq_match(message)
        if faq_response:
            return faq_response, faq_suggestions

    # 2. LLM ile context-aware yanıt
    if GEMINI_API_KEY:
        try:
            # Enrichment varsa özel prompt oluştur
            system_override = None
            if intent and intent != "GENERAL_HELP":
                system_override = _build_enriched_prompt(
                    intent, contract_context, graphrag_context
                )

            llm_response = _call_llm(message, history, system_override=system_override)
            suggestions = INTENT_SUGGESTIONS.get(intent, DEFAULT_SUGGESTIONS)
            return llm_response, suggestions
        except Exception as e:
            print(f"LLM hatasi: {e}")

    # 3. Fallback
    return DEFAULT_RESPONSE, DEFAULT_SUGGESTIONS
