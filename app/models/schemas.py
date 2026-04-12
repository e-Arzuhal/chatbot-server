"""
Chatbot Server - Pydantic Schemas
"""
from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field
from typing import List, Optional


class Message(BaseModel):
    role: str  # "user" | "assistant"
    content: str


class ChatRequest(BaseModel):
    """
    Chatbot isteği. Hem basit mod (message+history) hem de
    enriched mod (main-server orkestrasyon sonrası) desteklenir.
    """
    message: str
    history: Optional[List[Message]] = []

    # Enrichment alanları — main-server'dan gelir (opsiyonel, backward compatible)
    sanitized_message: Optional[str] = Field(default=None, alias="sanitizedMessage")
    intent: Optional[str] = None
    contract_context: Optional[str] = Field(default=None, alias="contractContext")
    graphrag_context: Optional[str] = Field(default=None, alias="graphRagContext")

    # Hem snake_case hem camelCase payload kabul et
    model_config = ConfigDict(populate_by_name=True)


class ChatResponse(BaseModel):
    response: str
    suggested_questions: Optional[List[str]] = []


class HealthResponse(BaseModel):
    status: str
    version: str
    llm_enabled: bool
