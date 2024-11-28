from typing import Optional

from pydantic import BaseModel
from pydantic import Field


class ContextRequest(BaseModel):
    article_title: str
    date: str
    url: str
    article_name: str
    content: str


class RAGRequest(BaseModel):
    context: ContextRequest = Field(..., description="Legal context for the question")
    question: str = Field(..., description="Specific legal question")
    code_rag: Optional[str] = None
