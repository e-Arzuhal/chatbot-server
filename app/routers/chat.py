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
    { "message": "...", "history": [...] }
    """
    try:
        response, suggested_questions = get_chat_response(request.message, request.history)
        return ChatResponse(response=response, suggested_questions=suggested_questions)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
