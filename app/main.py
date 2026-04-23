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

from app.config import HOST, PORT, DEBUG, LLM_ENABLED, ALLOWED_ORIGINS, INTERNAL_API_KEY
from app.limiter import limiter
from app.routers import chat
from app.models.schemas import HealthResponse

logging.basicConfig(
    level=logging.DEBUG if DEBUG else logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)
logger = logging.getLogger("chatbot")

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

    latency = (time.perf_counter() - start) * 1000
    logger.info(
        "[%s] %s %s status=%d latency=%.1fms",
        request_id, request.method, request.url.path,
        response.status_code, latency,
    )
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
    return HealthResponse(
        status="healthy",
        version="0.1.0",
        llm_enabled=LLM_ENABLED,
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=HOST, port=PORT, reload=DEBUG)
