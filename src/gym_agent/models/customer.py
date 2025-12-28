"""Customer models for GymAI Agent."""

from datetime import date, datetime
from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class CustomerStatus(str, Enum):
    """Customer status in the gym."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    AT_RISK = "at_risk"
    CHURNED = "churned"
    LEAD = "lead"


class MembershipType(str, Enum):
    """Types of gym memberships."""
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"
    TRIAL = "trial"
    FROZEN = "frozen"


class Customer(BaseModel):
    """Customer/Member profile."""
    
    id: UUID
    crm_id: str | None = None
    phone: str
    first_name: str
    last_name: str | None = None
    email: str | None = None
    
    # Membership
    membership_type: MembershipType = MembershipType.MONTHLY
    membership_start_date: date | None = None
    membership_end_date: date | None = None
    
    # Status
    status: CustomerStatus = CustomerStatus.ACTIVE
    health_score: int = Field(default=100, ge=0, le=100)
    
    # Engagement
    last_visit: datetime | None = None
    total_visits: int = 0
    preferred_classes: list[str] = Field(default_factory=list)
    preferred_visit_times: list[str] = Field(default_factory=list)
    
    # Communication
    telegram_id: int | None = None
    whatsapp_opted_in: bool = False
    preferred_language: str = "he"  # Hebrew default
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    
    # Flexible metadata
    metadata: dict[str, Any] = Field(default_factory=dict)
    
    @property
    def full_name(self) -> str:
        """Get customer's full name."""
        if self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.first_name
    
    @property
    def days_since_last_visit(self) -> int | None:
        """Calculate days since last gym visit."""
        if not self.last_visit:
            return None
        delta = datetime.now() - self.last_visit
        return delta.days
    
    @property
    def days_until_expiry(self) -> int | None:
        """Calculate days until membership expires."""
        if not self.membership_end_date:
            return None
        delta = self.membership_end_date - date.today()
        return delta.days
    
    @property
    def is_membership_expiring_soon(self) -> bool:
        """Check if membership expires within 30 days."""
        days = self.days_until_expiry
        return days is not None and 0 < days <= 30


class HealthScore(BaseModel):
    """Customer health score breakdown."""
    
    customer_id: UUID
    score: int = Field(ge=0, le=100)
    
    # Component scores (0-100 each)
    frequency_score: int = Field(ge=0, le=100)
    trend_score: int = Field(ge=0, le=100)
    recency_score: int = Field(ge=0, le=100)
    expiry_score: int = Field(ge=0, le=100)
    
    calculated_at: datetime = Field(default_factory=datetime.now)
    
    @classmethod
    def calculate(
        cls,
        customer_id: UUID,
        frequency_score: int,
        trend_score: int,
        recency_score: int,
        expiry_score: int,
    ) -> "HealthScore":
        """Calculate weighted health score."""
        # Weights from spec
        total_score = int(
            frequency_score * 0.30 +
            trend_score * 0.25 +
            recency_score * 0.25 +
            expiry_score * 0.20
        )
        
        return cls(
            customer_id=customer_id,
            score=total_score,
            frequency_score=frequency_score,
            trend_score=trend_score,
            recency_score=recency_score,
            expiry_score=expiry_score,
        )
