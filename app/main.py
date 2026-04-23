"""
e-Arzuhal Chatbot Server
FastAPI uygulama giris noktasi
"""
import logging
import time
import uuid

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.config import HOST, PORT, DEBUG, LLM_ENABLED, ALLOWED_ORIGINS, INTERNAL_API_KEY, GEMINI_API_KEY
from app.logging_config import setup_logging
from app.limiter import limiter
from app.routers import chat
from app.models.schemas import HealthResponse, FeedbackRequest

import os
setup_logging(level=os.getenv("LOG_LEVEL", "DEBUG" if DEBUG else "INFO"))
logger = logging.getLogger(__name__)
logger.info("Chatbot server başlatılıyor", extra={"debug": DEBUG})

app = FastAPI(
    title="e-Arzuhal Chatbot Server",
    description="Kullanici rehberi ve SSS chatbot servisi",
    version="0.1.0",
    docs_url="/docs" if DEBUG else None,
    redoc_url="/redoc" if DEBUG else None,
)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS — izin verilen origin'ler env'den okunur
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


@app.middleware("http")
async def request_middleware(request: Request, call_next):
    """API key doğrulama + istek loglama."""
    request_id = uuid.uuid4().hex[:8]
    request.state.request_id = request_id
    start = time.perf_counter()

    public = {"/health", "/"}
    debug_only = {"/docs", "/redoc", "/openapi.json"}

    if request.url.path in public or (DEBUG and request.url.path in debug_only):
        response = await call_next(request)
    elif not INTERNAL_API_KEY:
        response = JSONResponse(status_code=503, content={"detail": "Server misconfigured: INTERNAL_API_KEY is required"})
    elif request.headers.get("X-Internal-API-Key") != INTERNAL_API_KEY:
        response = JSONResponse(status_code=401, content={"detail": "Geçersiz veya eksik API anahtarı"})
    else:
        response = await call_next(request)

    if request.url.path not in public:
        logger.info("http_request", extra={
            "request_id": request_id,
            "method":     request.method,
            "path":       request.url.path,
            "status":     response.status_code,
            "ms":         int((time.perf_counter() - start) * 1000),
        })
    return response

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
    llm_status = "disabled"
    if LLM_ENABLED and GEMINI_API_KEY:
        try:
            from google import genai
            client = genai.Client(api_key=GEMINI_API_KEY)
            from app.config import LLM_MODEL
            client.models.get(model=LLM_MODEL)
            llm_status = "ok"
        except Exception:
            llm_status = "error"
    return HealthResponse(
        status="healthy",
        version="0.1.0",
        llm_enabled=LLM_ENABLED,
        llm_status=llm_status,
    )


@app.post("/api/feedback", status_code=204, tags=["Feedback"])
async def feedback(request: Request, body: FeedbackRequest):
    logger.info("feedback", extra={
        "request_id": getattr(request.state, "request_id", "-"),
        "rating":     body.rating,
        "intent":     body.intent or "NONE",
        "msg_prefix": body.message[:60],
    })


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=HOST, port=PORT, reload=DEBUG)
