"""Agent response models for GymAI Agent."""

from enum import Enum

from pydantic import BaseModel, Field


class Intent(str, Enum):
    """Detected customer intent categories."""
    
    TIME_CONSTRAINT = "time_constraint"
    FINANCIAL_ISSUE = "financial_issue"
    LOW_MOTIVATION = "low_motivation"
    HEALTH_INJURY = "health_injury"
    POSITIVE = "positive"
    QUESTION = "question"
    COMPLAINT = "complaint"
    WANTS_HUMAN = "wants_human"
    GREETING = "greeting"
    UNKNOWN = "unknown"


class AgentResponse(BaseModel):
    """Structured response from the GymAI agent."""
    
    message: str = Field(
        description="Response message to send to the customer"
    )
    intent: Intent = Field(
        description="Detected customer intent"
    )
    sentiment: float = Field(
        default=0.0,
        ge=-1,
        le=1,
        description="Sentiment score: -1 (negative) to 1 (positive)"
    )
    escalate: bool = Field(
        default=False,
        description="Whether to escalate to human representative"
    )
    escalation_reason: str | None = Field(
        default=None,
        description="Reason for escalation if escalate=True"
    )
    action_taken: str | None = Field(
        default=None,
        description="Action taken by the agent (e.g., 'sent_schedule', 'offered_freeze')"
    )
    follow_up_scheduled: bool = Field(
        default=False,
        description="Whether a follow-up message is scheduled"
    )
    confidence: float = Field(
        default=1.0,
        ge=0,
        le=1,
        description="Agent's confidence in the response"
    )


class RAGSearchResult(BaseModel):
    """Result from knowledge base search."""
    
    content: str
    source_file: str | None = None
    page_number: int | None = None
    relevance_score: float = Field(ge=0, le=1)


class RAGResponse(BaseModel):
    """Response from RAG agent."""
    
    answer: str
    sources: list[RAGSearchResult] = Field(default_factory=list)
    found_in_knowledge_base: bool = True
    confidence: float = Field(default=1.0, ge=0, le=1)
