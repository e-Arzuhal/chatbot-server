"""
e-Arzuhal Chatbot Server - API Routes
"""
import json
import logging

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
from app.models.schemas import ChatRequest, ChatResponse
from app.services.chatbot import (
    get_chat_response, _iter_llm_stream, _find_faq_match,
    _build_enriched_prompt, INTENT_SUGGESTIONS, DEFAULT_SUGGESTIONS, LEGAL_DISCLAIMER,
)
from app.sanitizer import redact
from app.limiter import limiter

logger = logging.getLogger("chatbot")

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
        rid = getattr(request.state, "request_id", "-")
        effective_message = body.sanitized_message or body.message
        logger.debug("[%s] intent=%s msg=%.80s", rid, body.intent or "NONE", effective_message)

        response, suggested_questions = await get_chat_response(
            message=effective_message,
            history=body.history,
            intent=body.intent,
            contract_context=body.contract_context,
            graphrag_context=body.graphrag_context,
        )
        return ChatResponse(response=response, suggested_questions=suggested_questions)
    except Exception as e:
        logger.error("[%s] chat error: %s", rid, e)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stream")
@limiter.limit("5/minute;20/day")
async def chat_stream(request: Request, body: ChatRequest):
    """
    LLM yanıtını Server-Sent Events ile chunk chunk döner.
    POST /api/chat/stream

    SSE formatı:
      data: {"text": "..."}\n\n   — metin parçası
      data: {"suggestions": [...], "done": true}\n\n  — son mesaj
    """
    from app.config import GEMINI_API_KEY

    rid = getattr(request.state, "request_id", "-")
    effective_message = body.sanitized_message or body.message
    logger.debug("[%s] stream intent=%s msg=%.80s", rid, body.intent or "NONE", effective_message)

    # FAQ eşleşmesi varsa tek chunk olarak gönder
    if not body.intent or body.intent == "GENERAL_HELP":
        faq_response, faq_suggestions = _find_faq_match(effective_message)
        if faq_response:
            async def _faq_stream():
                yield f"data: {json.dumps({'text': faq_response}, ensure_ascii=False)}\n\n"
                yield f"data: {json.dumps({'suggestions': faq_suggestions, 'done': True}, ensure_ascii=False)}\n\n"
            return StreamingResponse(_faq_stream(), media_type="text/event-stream")

    # LLM yoksa fallback
    if not GEMINI_API_KEY:
        from app.services.chatbot import DEFAULT_RESPONSE
        async def _fallback():
            yield f"data: {json.dumps({'text': DEFAULT_RESPONSE}, ensure_ascii=False)}\n\n"
            yield f"data: {json.dumps({'suggestions': DEFAULT_SUGGESTIONS, 'done': True}, ensure_ascii=False)}\n\n"
        return StreamingResponse(_fallback(), media_type="text/event-stream")

    clean_msg, found_msg = redact(effective_message)
    clean_contract, found_ctx = redact(body.contract_context or "")
    clean_graphrag, found_rag = redact(body.graphrag_context or "")
    all_found = found_msg + found_ctx + found_rag
    if all_found:
        logger.warning("[%s] stream PII redacted: %s", rid, all_found)

    system_override = None
    if body.intent and body.intent != "GENERAL_HELP":
        system_override = _build_enriched_prompt(
            body.intent, clean_contract or None, clean_graphrag or None
        )
    suggestions = INTENT_SUGGESTIONS.get(body.intent, DEFAULT_SUGGESTIONS)

    def _generate():
        try:
            for chunk in _iter_llm_stream(clean_msg, body.history, system_override):
                yield f"data: {json.dumps({'text': chunk}, ensure_ascii=False)}\n\n"
            yield f"data: {json.dumps({'text': LEGAL_DISCLAIMER, 'suggestions': suggestions, 'done': True}, ensure_ascii=False)}\n\n"
        except Exception as e:
            logger.error("[%s] stream error: %s", rid, e)
            yield f"data: {json.dumps({'error': str(e), 'done': True}, ensure_ascii=False)}\n\n"

    return StreamingResponse(_generate(), media_type="text/event-stream")
