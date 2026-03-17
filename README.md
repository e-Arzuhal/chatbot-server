# e-Arzuhal – Chatbot Server

Kullanıcı rehberi ve SSS chatbot servisi — FastAPI, kural tabanlı mod.

---

## Genel Bakış

Bu servis kullanıcıların e-Arzuhal uygulaması hakkındaki sorularını yanıtlar:

- Sözleşme oluşturma adımları
- Platform özellikleri
- Sıkça sorulan sorular (SSS)
- Yönlendirme önerileri

Chatbot varsayılan olarak **kural tabanlı** (pattern matching) modda çalışır.
Google Gemini entegrasyonu kaldırılmıştır; ilerleyen dönemde yerel Qwen 2 entegrasyonu planlanmaktadır.

---

## Tech Stack

| Katman | Teknoloji |
|--------|-----------|
| Language | Python 3.11+ |
| Framework | FastAPI 0.115 |
| Validation | Pydantic v2 |
| Port | 8003 |

---

## Kurulum

```bash
cd chatbot-server
python -m venv venv
venv\Scripts\activate   # Windows
# source venv/bin/activate  # Linux/macOS
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8003
```

---

## API Endpoints

### GET /health

```json
{ "status": "healthy", "version": "0.1.0" }
```

### POST /api/chat

**İstek:**
```json
{
  "message": "Sözleşme nasıl oluşturabilirim?",
  "history": [
    { "role": "user", "content": "Merhaba" },
    { "role": "assistant", "content": "Merhaba! Size nasıl yardımcı olabilirim?" }
  ]
}
```

**Yanıt:**
```json
{
  "response": "Sözleşme oluşturmak için 'Yeni Sözleşme' butonuna tıklayın ve ihtiyacınızı doğal dilde açıklayın.",
  "suggested_questions": [
    "Hangi sözleşme türleri destekleniyor?",
    "PDF nasıl indiririm?"
  ]
}
```

---

## Ortam Değişkenleri

| Değişken | Varsayılan | Açıklama |
|----------|-----------|----------|
| `HOST` | `0.0.0.0` | Dinleme adresi |
| `PORT` | `8003` | Port |
| `DEBUG` | `true` | Swagger UI + detaylı log |
| `ALLOWED_ORIGINS` | `http://localhost:8080,http://localhost:3000` | CORS whitelist |
| `INTERNAL_API_KEY` | _(boş)_ | Prod'da main-server ile aynı olmalı |

---

## Güvenlik

- `INTERNAL_API_KEY` set edilmemişse (dev) kontrol atlanır; set edilmişse `X-Internal-API-Key` header zorunlu.
- `/health` ve `/` her zaman serbesttir.
- `DEBUG=false` (prod): Swagger devre dışı.

---

## Proje Yapısı

```
chatbot-server/
├── app/
│   ├── main.py
│   ├── config.py
│   ├── models/schemas.py
│   ├── routers/chat.py
│   └── services/chatbot.py    # Kural tabanlı yanıt üretici
├── requirements.txt
└── .env.example
```

---

## Mimari Not

Chatbot servisi **doğrudan** GraphRAG veya Statistics servisine bağlanmamalıdır.
Gerekirse sorgu main-server üzerinden yapılmalıdır:

```
Chatbot → main-server → (GraphRAG / Statistics)
```

---

## Ekip

- **Burak DERE** — AI & Data Engineer
- **Deniz Eren ARICI** — Frontend & UI
- **Enes Burak ATAY** — Lead & Mobile
