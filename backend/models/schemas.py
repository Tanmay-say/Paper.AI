from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


class PaperSource(str, Enum):
    ARXIV = "arxiv"
    SEMANTIC_SCHOLAR = "semantic_scholar"
    USER_UPLOAD = "user_upload"


class PaperSearchRequest(BaseModel):
    query: str
    max_results: int = Field(default=10, le=100)
    source: PaperSource = PaperSource.ARXIV


class Author(BaseModel):
    name: str
    author_id: Optional[str] = None


class PaperMetadata(BaseModel):
    paper_id: str
    title: str
    authors: List[str]
    abstract: str
    year: int
    source: str
    pdf_url: Optional[str] = None
    arxiv_id: Optional[str] = None
    published_date: Optional[str] = None


class PaperDetail(BaseModel):
    paper_id: str
    title: str
    authors: List[str]
    abstract: str
    year: int
    source: str
    pdf_path: Optional[str] = None
    arxiv_id: Optional[str] = None
    published_date: Optional[str] = None
    citation_count: int = 0
    related_papers: List[str] = []


class ChatMessage(BaseModel):
    role: str  # 'user' or 'assistant'
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ChatQueryRequest(BaseModel):
    paper_id: str
    query: str
    selected_text: Optional[str] = None
    chat_history: List[ChatMessage] = []


class ChatResponse(BaseModel):
    response: str
    sources: List[Dict[str, Any]] = []
    paper_id: str


class GraphIntent(BaseModel):
    intent_type: str  # e.g., 'definition', 'comparison', 'methodology', 'citation'
    entities: List[str] = []
    relations: List[str] = []
    semantic_query: str
    retrieval_params: Dict[str, Any] = {}


class IngestionRequest(BaseModel):
    paper_ids: List[str]
    source: PaperSource = PaperSource.ARXIV


class IngestionStatus(BaseModel):
    job_id: str
    status: str  # 'pending', 'processing', 'completed', 'failed'
    total_papers: int
    processed_papers: int
    failed_papers: int = 0
    message: Optional[str] = None


class RetrievedContext(BaseModel):
    text: str
    paper_id: str
    chunk_id: str
    score: float
    metadata: Dict[str, Any] = {}