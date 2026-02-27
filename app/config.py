"""
e-Arzuhal Chatbot Server Configuration
"""
import os
from dotenv import load_dotenv

load_dotenv()

HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", 8003))
DEBUG = os.getenv("DEBUG", "true").lower() == "true"

# LLM (opsiyonel - set edilmezse kural tabanli sistem kullanilir)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
LLM_MODEL = os.getenv("LLM_MODEL", "gemini-2.0-flash")

# Security
# Chatbot: hem main-server hem de frontend'e açık (frontend doğrudan chatbot'a çağrı yapabilir)
ALLOWED_ORIGINS = [o.strip() for o in os.getenv("ALLOWED_ORIGINS", "http://localhost:8080,http://localhost:3000").split(",")]
INTERNAL_API_KEY = os.getenv("INTERNAL_API_KEY", "")

SYSTEM_PROMPT = """Sen e-Arzuhal uygulamasının yardımcı asistanısın.
e-Arzuhal, kullanıcıların doğal dilde yazdıkları metinden otomatik olarak sözleşme ve dilekçe oluşturmasını sağlayan yapay zeka destekli bir hukuk platformudur.

Uygulamanın özellikleri:
- Doğal dil ile sözleşme oluşturma (borç, kira, hizmet, satış, iş sözleşmeleri)
- NLP ile otomatik sözleşme tipi ve taraf tespiti
- GraphRAG ile eksik madde önerileri
- PDF oluşturma ve indirme
- Dijital onay süreci (çok taraflı imza)
- Dilekçe oluşturma
- Kimlik doğrulama

Sözleşme oluşturma adımları:
1. Metin Girişi: Sözleşme ihtiyacınızı doğal dilde yazın
2. Sözleşme Önerisi: AI analiz sonuçlarını görün, opsiyonel maddeleri seçin
3. PDF Önizleme: Oluşturulan sözleşmeyi inceleyin
4. Onay & İmza: Taraflara onay gönderin

Türkçe yanıt ver. Kısa ve net ol. Uygulamayla ilgili olmayan sorulara "Bu konuda yardımcı olamam, lütfen uygulama kullanımı hakkında soru sorun." şeklinde yanıt ver."""
