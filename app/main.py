"""
e-Arzuhal Chatbot Server
FastAPI uygulama giris noktasi
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import HOST, PORT, DEBUG, GEMINI_API_KEY
from app.routers import chat
from app.models.schemas import HealthResponse

app = FastAPI(
    title="e-Arzuhal Chatbot Server",
    description="Kullanici rehberi ve SSS chatbot servisi",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
