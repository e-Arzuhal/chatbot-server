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
    message: str = Field(..., min_length=1, max_length=2000)
    history: Optional[List[Message]] = Field(default=[], max_length=20)

    # Enrichment alanları — main-server'dan gelir (opsiyonel, backward compatible)
    sanitized_message: Optional[str] = Field(default=None, alias="sanitizedMessage", max_length=2000)
    intent: Optional[str] = Field(default=None, max_length=50)
    contract_context: Optional[str] = Field(default=None, alias="contractContext", max_length=5000)
    graphrag_context: Optional[str] = Field(default=None, alias="graphRagContext", max_length=5000)

    # Hem snake_case hem camelCase payload kabul et
    model_config = ConfigDict(populate_by_name=True)


class ChatResponse(BaseModel):
    response: str
    suggested_questions: Optional[List[str]] = []


class HealthResponse(BaseModel):
    status: str
    version: str
    llm_enabled: bool
