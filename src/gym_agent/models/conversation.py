"""Conversation and Message models for GymAI Agent."""

from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class ConversationStatus(str, Enum):
    """Status of a conversation."""
    ACTIVE = "active"
    RESOLVED = "resolved"
    ESCALATED = "escalated"
    CLOSED = "closed"


class MessageDirection(str, Enum):
    """Direction of a message."""
    INBOUND = "inbound"    # From customer
    OUTBOUND = "outbound"  # To customer


class Channel(str, Enum):
    """Communication channels."""
    TELEGRAM = "telegram"
    WHATSAPP = "whatsapp"
    SMS = "sms"


class Message(BaseModel):
    """A single message in a conversation."""
    
    id: UUID
    conversation_id: UUID
    direction: MessageDirection
    content: str
    
    # Analysis (filled by agent)
    intent: str | None = None
    sentiment: float | None = Field(default=None, ge=-1, le=1)
    
    # Metadata
    agent_type: str | None = None  # 'orchestrator', 'rag', 'retention', etc.
    created_at: datetime = Field(default_factory=datetime.now)
    metadata: dict[str, Any] = Field(default_factory=dict)


class Conversation(BaseModel):
    """A conversation thread with a customer."""
    
    id: UUID
    customer_id: UUID
    channel: Channel
    status: ConversationStatus = ConversationStatus.ACTIVE
    
    # Timestamps
    started_at: datetime = Field(default_factory=datetime.now)
    last_message_at: datetime | None = None
    
    # Escalation
    escalated_at: datetime | None = None
    escalated_to: str | None = None
    escalation_reason: str | None = None
    
    # Conversation context
    messages: list[Message] = Field(default_factory=list)
    unanswered_count: int = 0  # Messages sent without customer response
    
    # Metadata
    metadata: dict[str, Any] = Field(default_factory=dict)
    
    @property
    def message_count(self) -> int:
        """Get total number of messages."""
        return len(self.messages)
    
    @property
    def is_escalated(self) -> bool:
        """Check if conversation is escalated."""
        return self.status == ConversationStatus.ESCALATED
    
    def add_message(self, message: Message) -> None:
        """Add a message to the conversation."""
        self.messages.append(message)
        self.last_message_at = message.created_at
        
        # Track unanswered messages
        if message.direction == MessageDirection.OUTBOUND:
            self.unanswered_count += 1
        else:
            self.unanswered_count = 0


class Escalation(BaseModel):
    """Record of a conversation escalation to human."""
    
    id: UUID
    conversation_id: UUID
    reason: str
    priority: str = "normal"  # 'low', 'normal', 'high', 'urgent'
    status: str = "pending"   # 'pending', 'assigned', 'resolved'
    
    assigned_to: str | None = None
    notes: str | None = None
    
    created_at: datetime = Field(default_factory=datetime.now)
    resolved_at: datetime | None = None
