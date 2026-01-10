"""
Rate Limiting Service for GymAI Agent.

Prevents spamming customers with too many messages.
"""

from datetime import datetime, timedelta
from typing import Any
from uuid import UUID

from gym_agent.services.database import DatabaseService, get_database
from gym_agent.models.conversation import Channel, MessageDirection
from gym_agent.config import settings


class RateLimiter:
    """
    Rate limiting service for customer messaging.
    
    Enforces:
    - Max messages per hour per customer
    - Max unanswered proactive messages
    - Minimum wait time between follow-ups
    """
    
    def __init__(
        self,
        db: DatabaseService | None = None,
        max_per_hour: int | None = None,
        max_unanswered: int | None = None,
        followup_wait_hours: int | None = None,
    ) -> None:
        """
        Initialize rate limiter.
        
        Args:
            db: Database service
            max_per_hour: Max outbound messages per hour per customer
            max_unanswered: Max unanswered proactive messages
            followup_wait_hours: Hours to wait before follow-up
        """
        self.db = db or get_database()
        self.max_per_hour = max_per_hour or settings.max_messages_per_hour
        self.max_unanswered = max_unanswered or settings.max_unanswered_messages
        self.followup_wait_hours = followup_wait_hours or settings.followup_wait_hours
    
    async def can_send_message(
        self,
        customer_id: UUID,
        channel: Channel = Channel.TELEGRAM,
        is_proactive: bool = False,
    ) -> tuple[bool, str | None]:
        """
        Check if we can send a message to this customer.
        
        Args:
            customer_id: Customer UUID
            channel: Communication channel
            is_proactive: True if this is a proactive outreach message
            
        Returns:
            Tuple of (can_send, rejection_reason)
        """
        # Get active conversation
        conversation = await self.db.get_active_conversation(
            customer_id=customer_id,
            channel=channel,
        )
        
        if not conversation:
            # No existing conversation, can send
            return (True, None)
        
        # Check hourly rate limit
        hourly_count = await self._get_hourly_message_count(
            conversation_id=conversation.id
        )
        if hourly_count >= self.max_per_hour:
            return (False, f"Hourly limit reached ({self.max_per_hour} messages)")
        
        # For proactive messages, check additional limits
        if is_proactive:
            # Check unanswered count
            if conversation.unanswered_count >= self.max_unanswered:
                return (
                    False, 
                    f"Max unanswered messages reached ({self.max_unanswered})"
                )
            
            # Check time since last message
            if conversation.last_message_at:
                hours_since = (
                    datetime.now() - conversation.last_message_at
                ).total_seconds() / 3600
                
                if hours_since < self.followup_wait_hours:
                    wait_more = self.followup_wait_hours - hours_since
                    return (
                        False, 
                        f"Must wait {wait_more:.1f} more hours before follow-up"
                    )
        
        return (True, None)
    
    async def _get_hourly_message_count(self, conversation_id: UUID) -> int:
        """Get count of outbound messages in the last hour."""
        one_hour_ago = datetime.now() - timedelta(hours=1)
        
        count = await self.db._messages.count_documents({
            "conversation_id": str(conversation_id),
            "direction": MessageDirection.OUTBOUND.value,
            "created_at": {"$gte": one_hour_ago},
        })
        
        return count
    
    async def record_rate_limit_hit(
        self,
        customer_id: UUID,
        reason: str,
    ) -> None:
        """Record that a rate limit was hit."""
        await self.db.track_event(
            event_type="rate_limit.blocked",
            customer_id=customer_id,
            properties={"reason": reason},
        )
    
    async def get_rate_limit_status(
        self,
        customer_id: UUID,
        channel: Channel = Channel.TELEGRAM,
    ) -> dict[str, Any]:
        """
        Get current rate limit status for a customer.
        
        Args:
            customer_id: Customer UUID
            channel: Communication channel
            
        Returns:
            Dict with rate limit status info
        """
        conversation = await self.db.get_active_conversation(
            customer_id=customer_id,
            channel=channel,
        )
        
        if not conversation:
            return {
                "can_send": True,
                "hourly_count": 0,
                "hourly_remaining": self.max_per_hour,
                "unanswered_count": 0,
                "unanswered_remaining": self.max_unanswered,
                "hours_until_followup": 0,
            }
        
        hourly_count = await self._get_hourly_message_count(conversation.id)
        
        hours_until_followup: float = 0
        if conversation.last_message_at:
            hours_since = (
                datetime.now() - conversation.last_message_at
            ).total_seconds() / 3600
            hours_until_followup = max(0.0, self.followup_wait_hours - hours_since)
        
        can_send, _ = await self.can_send_message(
            customer_id=customer_id,
            channel=channel,
            is_proactive=True,
        )
        
        return {
            "can_send": can_send,
            "hourly_count": hourly_count,
            "hourly_remaining": max(0, self.max_per_hour - hourly_count),
            "unanswered_count": conversation.unanswered_count,
            "unanswered_remaining": max(
                0, 
                self.max_unanswered - conversation.unanswered_count
            ),
            "hours_until_followup": hours_until_followup,
        }


# Singleton instance
_rate_limiter: RateLimiter | None = None


def get_rate_limiter() -> RateLimiter:
    """Get or create rate limiter instance."""
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = RateLimiter()
    return _rate_limiter


__all__ = ["RateLimiter", "get_rate_limiter"]
