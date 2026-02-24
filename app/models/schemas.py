"""
Chatbot Server - Pydantic Schemas
"""
from pydantic import BaseModel
from typing import List, Optional


class Message(BaseModel):
    role: str  # "user" | "assistant"
    content: str


class ChatRequest(BaseModel):
    message: str
    history: Optional[List[Message]] = []


class ChatResponse(BaseModel):
    response: str
    suggested_questions: Optional[List[str]] = []


class HealthResponse(BaseModel):
    status: str
    version: str
    llm_enabled: bool
