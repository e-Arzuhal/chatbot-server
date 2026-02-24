"""
e-Arzuhal Chatbot Service
Kural tabanli SSS + opsiyonel Gemini LLM entegrasyonu
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


def _find_faq_match(message: str):
    msg_lower = message.lower()
    for keywords, response, suggestions in FAQ:
        if any(kw in msg_lower for kw in keywords):
            return response, suggestions
    return None, None


def _call_llm(message: str, history: list) -> str:
    """Gemini API'ye istek at"""
    import google.generativeai as genai

    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel(
        model_name=LLM_MODEL,
        system_instruction=SYSTEM_PROMPT,
    )

    # Gemini history formatı: [{role, parts}]
    chat_history = []
    for h in history[-6:]:  # Son 6 mesaj (3 tur)
        role = "user" if h.role == "user" else "model"
        chat_history.append({"role": role, "parts": [h.content]})

    chat = model.start_chat(history=chat_history)
    response = chat.send_message(message)
    return response.text


def get_chat_response(message: str, history: list) -> tuple[str, list]:
    """
    Ana chatbot logic:
    1. Once FAQ eslesme dene
    2. LLM aktifse LLM'e gonder
    3. Fallback: varsayilan yanit
    """
    # 1. FAQ
    faq_response, faq_suggestions = _find_faq_match(message)
    if faq_response:
        return faq_response, faq_suggestions

    # 2. LLM
    if GEMINI_API_KEY:
        try:
            llm_response = _call_llm(message, history)
            return llm_response, DEFAULT_SUGGESTIONS
        except Exception as e:
            print(f"LLM hatasi: {e}")

    # 3. Fallback
    return DEFAULT_RESPONSE, DEFAULT_SUGGESTIONS
