# e-Arzuhal – Chatbot Server

Kullanici rehberi ve SSS chatbot servisi — FastAPI ile yazilmis, kural tabanli + isteğe bagly LLM destekli.

---

## Genel Bakis

Bu servis kullanicilarin e-Arzuhal uygulamasi hakkinda sorularini yanitlar:

- Sozlesme olusturma adimlari
- Platform ozellikleri
- Sikca sorulan sorular (SSS)
- Yonlendirme onerleri

Chatbot, `GEMINI_API_KEY` set edilmemisse **kural tabanli** (pattern matching) modda calisir;
set edilirse **Google Gemini** LLM'i kullanir. Surecte yerel Qwen 2 entegrasyonu planlanmaktadir.

---

## Tech Stack

| Katman | Teknoloji |
|--------|-----------|
| Language | Python 3.11+ |
| Framework | FastAPI 0.115 |
| LLM (opsiyonel) | Google Gemini (gemini-2.0-flash) |
| Validation | Pydantic v2 |
| Port | 8003 |

---

## Kurulum

```bash
cd chatbot-server
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8003
```

---

## API Endpoints

### `GET /health`

```json
{
  "status": "healthy",
  "version": "0.1.0",
  "llm_enabled": false
}
```

`llm_enabled: true` ise `GEMINI_API_KEY` aktif demektir.

### `POST /api/chat`

Kullanicidan mesaj alip chatbot yaniti doner.

**Request:**
```json
{
  "message": "Sozlesme nasil olusturabilirim?",
  "history": [
    { "role": "user", "content": "Merhaba" },
    { "role": "assistant", "content": "Merhaba! Size nasil yardimci olabilirim?" }
  ]
}
```

**Response:**
```json
{
  "response": "Sozlesme olusturmak icin 'Yeni Sozlesme' butonuna tiklayin ve ihtiyacinizi dogal dilde aciklayin. Sistem otomatik olarak sozlesme turunu tespit eder.",
  "suggested_questions": [
    "Hangi sozlesme turleri destekleniyor?",
    "PDF nasil indiririm?"
  ]
}
```

### `GET /`

Servis bilgisi.

---

## Ortam Degiskenleri

`.env.example` dosyasindan kopyalayin:

```bash
cp .env.example .env
```

| Degisken | Varsayilan | Aciklama |
|----------|-----------|----------|
| `HOST` | `0.0.0.0` | Dinleme adresi |
| `PORT` | `8003` | Servis portu |
| `DEBUG` | `true` | Swagger UI + detayli log |
| `GEMINI_API_KEY` | _(bos)_ | Set edilmezse kural tabanli mod |
| `LLM_MODEL` | `gemini-2.0-flash` | Kullanilacak Gemini modeli |
| `ALLOWED_ORIGINS` | `http://localhost:8080,http://localhost:3000` | CORS whitelist |
| `INTERNAL_API_KEY` | _(bos)_ | Servisler arasi API anahtari |

---

## Guvenlik

### CORS

Chatbot servisi hem `main-server` hem de frontend tarafindan cagrilabilir (web + mobil).
Bu nedenle `ALLOWED_ORIGINS` varsayilan olarak iki origin icerir:

```
ALLOWED_ORIGINS=http://main-server:8080,http://frontend-web:3000
```

### Internal API Key Middleware

- `INTERNAL_API_KEY` **set edilmemisse** (dev): kontrol atlanir.
- **Set edilmisse** (prod): `X-Internal-API-Key` header'i eslesmeyen istekler `401` alir.
- `/health` ve `/` endpoint'leri her zaman serbest.

`main-server`'in `INTERNAL_API_KEY` degeriyle ayni olmalidir:

```bash
openssl rand -hex 32
```

### Swagger UI

- `DEBUG=true`: `/docs` ve `/redoc` erisilebilir.
- `DEBUG=false` (prod): Swagger tamamen devre disi.

---

## Proje Yapisi

```
chatbot-server/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI app + CORS + middleware
│   ├── config.py            # Konfigürasyon + sistem promptu
│   ├── models/
│   │   ├── __init__.py
│   │   └── schemas.py       # ChatRequest, ChatResponse, HealthResponse
│   ├── routers/
│   │   ├── __init__.py
│   │   └── chat.py          # POST /api/chat
│   └── services/
│       ├── __init__.py
│       └── chatbot.py       # Kural tabanli + LLM yanit uretici
├── requirements.txt
├── .env.example
└── README.md
```

---

## Mimari Not

Roadmap geregi chatbot servisi **dogrudan** GraphRAG veya Statistics servisine baglanmamali.
Gerekmesi halinde sorgu main-server uzerinden yapilmalidir:

```
Chatbot → main-server → (GraphRAG / Statistics)
```

---

## Ekip

- **Burak DERE** — AI & Data Engineer
- **Deniz Eren ARICI** — Frontend & UI Engineer
- **Enes Burak ATAY** — Lead & Mobile + Coordinator
