"""
e-Arzuhal Chatbot Server - API Routes
"""
from fastapi import APIRouter, HTTPException
from app.models.schemas import ChatRequest, ChatResponse
from app.services.chatbot import get_chat_response

router = APIRouter(prefix="/api/chat", tags=["Chat"])


@router.post("", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Kullanicidan mesaj alip chatbot yaniti doner.
    POST /api/chat

    Basit mod:    { "message": "...", "history": [...] }
    Enriched mod: { "message": "...", "history": [...], "intent": "...",
                    "sanitized_message": "...", "contract_context": "...",
                    "graphrag_context": "..." }
    """
    try:
        # Enriched mesaj varsa onu kullan, yoksa orijinal mesaj
        effective_message = request.sanitized_message or request.message

        response, suggested_questions = get_chat_response(
            message=effective_message,
            history=request.history,
            intent=request.intent,
            contract_context=request.contract_context,
            graphrag_context=request.graphrag_context,
        )
        return ChatResponse(response=response, suggested_questions=suggested_questions)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
