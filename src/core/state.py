from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field




class CommentData(BaseModel):
    comment_id: str
    platform: str
    username: str
    timestamp: datetime
    comment_text: str
    post_url: Optional[str] = None
    severity: Optional[str] = None
    categories: List[str] = Field(default_factory=list)




class InvestigationState(BaseModel):
    case_id: str
    case_name: str

    created_at: datetime = Field(default_factory=datetime.utcnow)

    raw_comments: List[CommentData] = Field(default_factory=list)

    sanitized_comments: List[CommentData] = Field(default_factory=list)

    # Populated by EvidenceAgent; typed as Any to avoid importing agent models here.
    evidence_records: List[Any] = Field(default_factory=list)
    extracted_entities: Dict[str, List[str]] = Field(default_factory=dict)

    campaign_clusters: Dict[str, List[str]] = Field(default_factory=dict)

    report_draft_markdown: Optional[str] = None

    is_approved: bool = False