# e-Arzuhal Chatbot Server — Geliştirme Planı

## Mevcut Durum

3-aşamalı yanıt mantığı: **FAQ keyword match → Gemini LLM → Fallback**

Çalışıyor ama production kalitesinde değil. Aşağıdaki eksikler var.

---

## 1. KRİTİK DÜZELTMELER

### 1a. Async LLM Çağrısı — `app/services/chatbot.py`
**Sorun:** `_call_llm()` senkron. FastAPI async event loop'u blokluyor — tek LLM çağrısı diğer tüm istekleri dondurur.  
**Çözüm:** `asyncio.to_thread()` ile sync çağrıyı thread pool'a taşı, `get_chat_response()` async'e dönüştür.

### 1b. Rate Limiting — `app/main.py`
**Sorun:** Gemini free tier 20 RPD. Tek kullanıcı tüm kotayı bitirebilir.  
**Çözüm:** `slowapi` ile IP başına `20/day; 5/minute` limiti.

### 1c. Yasal Disclaimer — `app/services/chatbot.py`
**Sorun:** Hukuk platformu için her LLM yanıtının disclaimer içermesi zorunlu.  
**Çözüm:** LLM yanıtlarına otomatik ekle (FAQ yanıtlarına eklenmez).

```
⚠️ Bu yanıt bilgilendirme amaçlıdır, hukuki tavsiye niteliği taşımaz.
```

---

## 2. GELİŞTİRMELER

### 2a. Türkçe Morfolojik FAQ Eşleşmesi — `app/services/chatbot.py`
**Sorun:** `"sözleşmem"` → `"sözleşme"` eşleşmiyor. Türkçe eklemeli dil, basit `in` kontrolü yetersiz.  
**Çözüm:** Harici kütüphane olmadan basit suffix stripping + normalizasyon. Her kelimeyi normalize edip FAQ keyword listesiyle karşılaştır.

### 2b. Yapılandırılmış Loglama — `app/main.py`
**Sorun:** Sadece `print()` var, production'da analiz edilemiyor.  
**Çözüm:** Her isteğe `request_id` ekle; intent, latency, status code'u JSON formatında logla.

### 2c. Streaming Endpoint — `app/routers/chat.py`
**Sorun:** LLM yanıtı 2-5 saniye bekletiliyor, kullanıcı ekranda hiçbir şey görmüyor.  
**Çözüm:** `POST /api/chat/stream` → Server-Sent Events (SSE). `google-genai` SDK streaming destekliyor.

### 2d. Gelişmiş Health Check — `app/main.py`
**Sorun:** `/health` sadece "sunucu ayakta" diyor, Gemini bağlantısını test etmiyor.  
**Çözüm:** Minimal Gemini ping; `llm_status: "ok" | "error" | "disabled"` alanı ekle.

### 2e. Feedback Endpoint — `app/routers/chat.py`
**Amaç:** Kullanıcı yanıtı beğendi mi? Zamanla FAQ'ı iyileştirmek için veri topla.  
**Çözüm:** `POST /api/chat/feedback` — `rating (1-5)`, `message`, `intent` alanlarını al, logla. İleride DB'ye yaz.

---

## Öncelik Sırası

| # | Değişiklik | Dosya | Etki |
|---|-----------|-------|------|
| 1 | Async LLM | `services/chatbot.py`, `routers/chat.py` | Kritik |
| 2 | Rate limiting | `main.py`, `requirements.txt` | Kritik |
| 3 | Legal disclaimer | `services/chatbot.py` | Kritik |
| 4 | Türkçe morfoloji | `services/chatbot.py` | Yüksek |
| 5 | Yapılandırılmış loglama | `main.py` | Yüksek |
| 6 | Streaming endpoint | `routers/chat.py`, `services/chatbot.py` | Orta |
| 7 | Gelişmiş health check | `main.py`, `schemas.py` | Orta |
| 8 | Feedback endpoint | `routers/chat.py`, `schemas.py` | Düşük |

---

## Değişmeyecek Şeyler

- 3-aşamalı yanıt mantığı (FAQ → LLM → Fallback) — doğru tasarım
- Pydantic şema validasyonları — iyi durumda
- Internal API key güvenliği — yeterli
- CORS yapısı — yeterli
- Mevcut intent sistemi — genişletilebilir ama kırılmayacak
