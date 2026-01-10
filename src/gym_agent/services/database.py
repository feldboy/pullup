"""
MongoDB Database Service for GymAI Agent.

Provides persistent storage for conversations, messages, and escalations.
Uses local MongoDB instance.
"""

from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from gym_agent.models.customer import Customer, CustomerStatus, MembershipType

from gym_agent.config import settings
from gym_agent.models.conversation import (
    Conversation,
    ConversationStatus,
    Channel,
    Message,
    MessageDirection,
    Escalation,
)


class DatabaseService:
    """
    MongoDB Database Service.
    
    Provides:
    - Conversation CRUD operations
    - Message storage and retrieval
    - Escalation management
    - Customer management
    """
    
    def __init__(
        self,
        connection_string: str = "mongodb://localhost:27017",
        database_name: str = "gym_ai",
    ) -> None:
        """
        Initialize database connection.
        
        Args:
            connection_string: MongoDB connection string
            database_name: Name of the database to use
        """
        self._client: AsyncIOMotorClient[Any] = AsyncIOMotorClient(connection_string)
        self._db: AsyncIOMotorDatabase[Any] = self._client[database_name]
        
        # Collections
        self._conversations = self._db.conversations
        self._messages = self._db.messages
        self._escalations = self._db.escalations
        self._analytics_events = self._db.analytics_events
        self._customers = self._db.customers

    # ... initialize and close methods are fine ...
    
    # ==================== Customers ====================
    
    async def get_customer(self, customer_id: UUID) -> Customer | None:
        """Get customer by ID."""
        doc = await self._customers.find_one({"_id": str(customer_id)})
        if doc:
            return self._dict_to_customer(doc)
        return None
    
    async def get_customer_by_telegram(self, telegram_id: int) -> Customer | None:
        """Get customer by Telegram ID."""
        doc = await self._customers.find_one({"telegram_id": telegram_id})
        if doc:
            return self._dict_to_customer(doc)
        return None
        
    async def save_customer(self, customer: Customer) -> None:
        """Save (upsert) customer."""
        await self._customers.update_one(
            {"_id": str(customer.id)},
            {"$set": self._customer_to_dict(customer)},
            upsert=True
        )

    # ... Conversations, Messages, Escalations, Analytics ...
    
    # ==================== Conversion Helpers ====================
    
    def _customer_to_dict(self, customer: Customer) -> dict[str, Any]:
        """Convert Customer to MongoDB document."""
        return {
            "_id": str(customer.id),
            "crm_id": customer.crm_id,
            "phone": customer.phone,
            "first_name": customer.first_name,
            "last_name": customer.last_name,
            "email": customer.email,
            "membership_type": customer.membership_type.value,
            "membership_start_date": customer.membership_start_date.isoformat() if customer.membership_start_date else None,
            "membership_end_date": customer.membership_end_date.isoformat() if customer.membership_end_date else None,
            "status": customer.status.value,
            "health_score": customer.health_score,
            "total_visits": customer.total_visits,
            "last_visit": customer.last_visit,
            "preferred_classes": customer.preferred_classes,
            "preferred_language": customer.preferred_language,
            "telegram_id": customer.telegram_id,
            "metadata": customer.metadata,
        }
        
    def _dict_to_customer(self, doc: dict[str, Any]) -> Customer:
        """Convert MongoDB document to Customer."""
        return Customer(
            id=UUID(doc["_id"]),
            crm_id=doc["crm_id"],
            phone=doc["phone"],
            first_name=doc["first_name"],
            last_name=doc.get("last_name"),
            email=doc.get("email"),
            membership_type=MembershipType(doc["membership_type"]),
            membership_start_date=datetime.fromisoformat(doc["membership_start_date"]).date() if doc.get("membership_start_date") else None,
            membership_end_date=datetime.fromisoformat(doc["membership_end_date"]).date() if doc.get("membership_end_date") else None,
            status=CustomerStatus(doc["status"]),
            health_score=doc.get("health_score", 0),
            total_visits=doc.get("total_visits", 0),
            last_visit=doc.get("last_visit"),
            preferred_classes=doc.get("preferred_classes", []),
            preferred_language=doc.get("preferred_language", "he"),
            telegram_id=doc.get("telegram_id"),
            metadata=doc.get("metadata", {}),
        )

    # ... existing helpers ...
    async def initialize(self) -> None:
        """Create indexes for collections."""
        # Conversations indexes
        await self._conversations.create_index("customer_id")
        await self._conversations.create_index("status")
        await self._conversations.create_index([("customer_id", 1), ("channel", 1)])
        
        # Messages indexes
        await self._messages.create_index("conversation_id")
        await self._messages.create_index("created_at")
        
        # Escalations indexes
        await self._escalations.create_index("conversation_id")
        await self._escalations.create_index("status")
        
        # Analytics events indexes
        await self._analytics_events.create_index("event_type")
        await self._analytics_events.create_index("created_at")
        
        # Customers indexes
        await self._customers.create_index("telegram_id", unique=True, sparse=True)
        await self._customers.create_index("phone", unique=True, sparse=True)
        await self._customers.create_index("email", unique=True, sparse=True)
    
    async def close(self) -> None:
        """Close database connection."""
        self._client.close()
    
    # ==================== Conversations ====================
    
    async def create_conversation(
        self,
        customer_id: UUID,
        channel: Channel,
    ) -> Conversation:
        """
        Create a new conversation.
        
        Args:
            customer_id: Customer's UUID
            channel: Communication channel
            
        Returns:
            The created conversation
        """
        conversation = Conversation(
            id=uuid4(),
            customer_id=customer_id,
            channel=channel,
            status=ConversationStatus.ACTIVE,
            started_at=datetime.now(),
        )
        
        await self._conversations.insert_one(
            self._conversation_to_dict(conversation)
        )
        
        return conversation
    
    async def get_conversation(self, conversation_id: UUID) -> Conversation | None:
        """Get conversation by ID."""
        doc = await self._conversations.find_one({"_id": str(conversation_id)})
        if doc:
            return self._dict_to_conversation(doc)
        return None
    
    async def get_active_conversation(
        self,
        customer_id: UUID,
        channel: Channel,
    ) -> Conversation | None:
        """Get active conversation for a customer on a channel."""
        doc = await self._conversations.find_one({
            "customer_id": str(customer_id),
            "channel": channel.value,
            "status": ConversationStatus.ACTIVE.value,
        })
        if doc:
            return self._dict_to_conversation(doc)
        return None
    
    async def get_or_create_conversation(
        self,
        customer_id: UUID,
        channel: Channel,
    ) -> Conversation:
        """Get existing active conversation or create a new one."""
        conversation = await self.get_active_conversation(customer_id, channel)
        if conversation:
            return conversation
        return await self.create_conversation(customer_id, channel)
    
    async def update_conversation_status(
        self,
        conversation_id: UUID,
        status: ConversationStatus,
    ) -> None:
        """Update conversation status."""
        await self._conversations.update_one(
            {"_id": str(conversation_id)},
            {"$set": {"status": status.value}}
        )
    
    async def update_conversation(
        self,
        conversation: Conversation,
    ) -> None:
        """Update full conversation document."""
        await self._conversations.replace_one(
            {"_id": str(conversation.id)},
            self._conversation_to_dict(conversation)
        )
    
    # ==================== Messages ====================
    
    async def add_message(
        self,
        conversation_id: UUID,
        direction: MessageDirection,
        content: str,
        intent: str | None = None,
        sentiment: float | None = None,
        agent_type: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> Message:
        """
        Add a message to a conversation.
        
        Args:
            conversation_id: Conversation UUID
            direction: Inbound or outbound
            content: Message text
            intent: Detected intent (optional)
            sentiment: Sentiment score (optional)
            agent_type: Which agent handled this (optional)
            metadata: Additional metadata (optional)
            
        Returns:
            The created message
        """
        message = Message(
            id=uuid4(),
            conversation_id=conversation_id,
            direction=direction,
            content=content,
            intent=intent,
            sentiment=sentiment,
            agent_type=agent_type,
            created_at=datetime.now(),
            metadata=metadata or {},
        )
        
        await self._messages.insert_one(
            self._message_to_dict(message)
        )
        
        # Update conversation last_message_at and unanswered_count
        update: dict[str, Any] = {"$set": {"last_message_at": message.created_at}}
        if direction == MessageDirection.OUTBOUND:
            update["$inc"] = {"unanswered_count": 1}
        else:
            update["$set"]["unanswered_count"] = 0
        
        await self._conversations.update_one(
            {"_id": str(conversation_id)},
            update
        )
        
        return message
    
    async def get_conversation_messages(
        self,
        conversation_id: UUID,
        limit: int = 10,
    ) -> list[Message]:
        """
        Get recent messages from a conversation.
        
        Args:
            conversation_id: Conversation UUID
            limit: Maximum number of messages to return
            
        Returns:
            List of messages, most recent last
        """
        cursor = self._messages.find(
            {"conversation_id": str(conversation_id)}
        ).sort("created_at", -1).limit(limit)
        
        messages = []
        async for doc in cursor:
            messages.append(self._dict_to_message(doc))
        
        # Return in chronological order
        return list(reversed(messages))
    
    # ==================== Escalations ====================
    
    async def create_escalation(
        self,
        conversation_id: UUID,
        reason: str,
        priority: str = "normal",
        notes: str | None = None,
    ) -> Escalation:
        """
        Create an escalation record.
        
        Args:
            conversation_id: Conversation UUID
            reason: Why escalating
            priority: Escalation priority
            notes: Additional notes
            
        Returns:
            The created escalation
        """
        escalation = Escalation(
            id=uuid4(),
            conversation_id=conversation_id,
            reason=reason,
            priority=priority,
            status="pending",
            notes=notes,
            created_at=datetime.now(),
        )
        
        await self._escalations.insert_one(
            self._escalation_to_dict(escalation)
        )
        
        # Update conversation status
        await self.update_conversation_status(
            conversation_id,
            ConversationStatus.ESCALATED
        )
        
        return escalation
    
    async def get_pending_escalations(self) -> list[Escalation]:
        """Get all pending escalations."""
        cursor = self._escalations.find(
            {"status": "pending"}
        ).sort("created_at", 1)
        
        escalations = []
        async for doc in cursor:
            escalations.append(self._dict_to_escalation(doc))
        
        return escalations
    
    # ==================== Analytics Events ====================
    
    async def track_event(
        self,
        event_type: str,
        customer_id: UUID | None = None,
        conversation_id: UUID | None = None,
        properties: dict[str, Any] | None = None,
    ) -> None:
        """
        Track an analytics event.
        
        Args:
            event_type: Type of event (e.g., 'conversation.started')
            customer_id: Associated customer (optional)
            conversation_id: Associated conversation (optional)
            properties: Additional event properties (optional)
        """
        await self._analytics_events.insert_one({
            "_id": str(uuid4()),
            "event_type": event_type,
            "customer_id": str(customer_id) if customer_id else None,
            "conversation_id": str(conversation_id) if conversation_id else None,
            "properties": properties or {},
            "created_at": datetime.now(),
        })
    
    # ==================== Conversion Helpers ====================
    
    def _conversation_to_dict(self, conv: Conversation) -> dict[str, Any]:
        """Convert Conversation to MongoDB document."""
        return {
            "_id": str(conv.id),
            "customer_id": str(conv.customer_id),
            "channel": conv.channel.value,
            "status": conv.status.value,
            "started_at": conv.started_at,
            "last_message_at": conv.last_message_at,
            "escalated_at": conv.escalated_at,
            "escalated_to": conv.escalated_to,
            "escalation_reason": conv.escalation_reason,
            "unanswered_count": conv.unanswered_count,
            "metadata": conv.metadata,
        }
    
    def _dict_to_conversation(self, doc: dict[str, Any]) -> Conversation:
        """Convert MongoDB document to Conversation."""
        return Conversation(
            id=UUID(doc["_id"]),
            customer_id=UUID(doc["customer_id"]),
            channel=Channel(doc["channel"]),
            status=ConversationStatus(doc["status"]),
            started_at=doc["started_at"],
            last_message_at=doc.get("last_message_at"),
            escalated_at=doc.get("escalated_at"),
            escalated_to=doc.get("escalated_to"),
            escalation_reason=doc.get("escalation_reason"),
            unanswered_count=doc.get("unanswered_count", 0),
            metadata=doc.get("metadata", {}),
        )
    
    def _message_to_dict(self, msg: Message) -> dict[str, Any]:
        """Convert Message to MongoDB document."""
        return {
            "_id": str(msg.id),
            "conversation_id": str(msg.conversation_id),
            "direction": msg.direction.value,
            "content": msg.content,
            "intent": msg.intent,
            "sentiment": msg.sentiment,
            "agent_type": msg.agent_type,
            "created_at": msg.created_at,
            "metadata": msg.metadata,
        }
    
    def _dict_to_message(self, doc: dict[str, Any]) -> Message:
        """Convert MongoDB document to Message."""
        return Message(
            id=UUID(doc["_id"]),
            conversation_id=UUID(doc["conversation_id"]),
            direction=MessageDirection(doc["direction"]),
            content=doc["content"],
            intent=doc.get("intent"),
            sentiment=doc.get("sentiment"),
            agent_type=doc.get("agent_type"),
            created_at=doc["created_at"],
            metadata=doc.get("metadata", {}),
        )
    
    def _escalation_to_dict(self, esc: Escalation) -> dict[str, Any]:
        """Convert Escalation to MongoDB document."""
        return {
            "_id": str(esc.id),
            "conversation_id": str(esc.conversation_id),
            "reason": esc.reason,
            "priority": esc.priority,
            "status": esc.status,
            "assigned_to": esc.assigned_to,
            "notes": esc.notes,
            "created_at": esc.created_at,
            "resolved_at": esc.resolved_at,
        }
    
    def _dict_to_escalation(self, doc: dict[str, Any]) -> Escalation:
        """Convert MongoDB document to Escalation."""
        return Escalation(
            id=UUID(doc["_id"]),
            conversation_id=UUID(doc["conversation_id"]),
            reason=doc["reason"],
            priority=doc.get("priority", "normal"),
            status=doc.get("status", "pending"),
            assigned_to=doc.get("assigned_to"),
            notes=doc.get("notes"),
            created_at=doc["created_at"],
            resolved_at=doc.get("resolved_at"),
        )


# Global database instance (lazy initialization)
_db_service: DatabaseService | None = None


def get_database(
    connection_string: str = "mongodb://localhost:27017",
    database_name: str = "gym_ai",
) -> DatabaseService:
    """
    Get or create database service instance.
    
    Args:
        connection_string: MongoDB connection string
        database_name: Database name
        
    Returns:
        DatabaseService instance
    """
    global _db_service
    if _db_service is None:
        _db_service = DatabaseService(connection_string, database_name)
    return _db_service
