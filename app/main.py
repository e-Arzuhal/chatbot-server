"""
e-Arzuhal Chatbot Server
FastAPI uygulama giris noktasi
"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import HOST, PORT, DEBUG, GEMINI_API_KEY, ALLOWED_ORIGINS, INTERNAL_API_KEY
from app.routers import chat
from app.models.schemas import HealthResponse

app = FastAPI(
    title="e-Arzuhal Chatbot Server",
    description="Kullanici rehberi ve SSS chatbot servisi",
    version="0.1.0",
    docs_url="/docs" if DEBUG else None,
    redoc_url="/redoc" if DEBUG else None,
)

# CORS — izin verilen origin'ler env'den okunur
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


@app.middleware("http")
async def api_key_middleware(request: Request, call_next):
    """Internal API key kontrolü. INTERNAL_API_KEY set edilmemişse (dev) pas geçer."""
    if request.url.path in ("/health", "/"):
        return await call_next(request)
    if INTERNAL_API_KEY and request.headers.get("X-Internal-API-Key") != INTERNAL_API_KEY:
        return JSONResponse(status_code=401, content={"detail": "Geçersiz veya eksik API anahtarı"})
    return await call_next(request)

app.include_router(chat.router)


@app.get("/", tags=["Root"])
async def root():
    return {
        "service": "e-Arzuhal Chatbot Server",
        "version": "0.1.0",
        "docs": "/docs",
    }


@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    return HealthResponse(
        status="healthy",
        version="0.1.0",
        llm_enabled=bool(GEMINI_API_KEY),
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=HOST, port=PORT, reload=DEBUG)
