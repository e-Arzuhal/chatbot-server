"""
e-Arzuhal Chatbot Server - API Routes
"""
from fastapi import APIRouter, HTTPException, Request
from app.models.schemas import ChatRequest, ChatResponse
from app.services.chatbot import get_chat_response
from app.limiter import limiter

router = APIRouter(prefix="/api/chat", tags=["Chat"])


@router.post("", response_model=ChatResponse)
@limiter.limit("5/minute;20/day")
async def chat(request: Request, body: ChatRequest):
    """
    Kullanicidan mesaj alip chatbot yaniti doner.
    POST /api/chat

    Basit mod:    { "message": "...", "history": [...] }
    Enriched mod: { "message": "...", "history": [...], "intent": "...",
                    "sanitized_message": "...", "contract_context": "...",
                    "graphrag_context": "..." }
    """
    try:
        effective_message = body.sanitized_message or body.message

        response, suggested_questions = await get_chat_response(
            message=effective_message,
            history=body.history,
            intent=body.intent,
            contract_context=body.contract_context,
            graphrag_context=body.graphrag_context,
        )
        return ChatResponse(response=response, suggested_questions=suggested_questions)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
