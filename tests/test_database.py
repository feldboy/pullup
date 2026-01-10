"""Tests for MongoDB Database Service."""

import pytest
from datetime import datetime
from uuid import uuid4

from gym_agent.services.database import DatabaseService
from gym_agent.models.conversation import (
    Channel,
    ConversationStatus,
    MessageDirection,
)


@pytest.fixture
async def db_service():
    """Create a test database service."""
    # Use a test database
    service = DatabaseService(
        connection_string="mongodb://localhost:27017",
        database_name="gym_ai_test",
    )
    await service.initialize()
    
    yield service
    
    # Clean up after tests
    await service._conversations.drop()
    await service._messages.drop()
    await service._escalations.drop()
    await service._analytics_events.drop()
    await service.close()


class TestConversations:
    """Tests for conversation operations."""
    
    @pytest.mark.asyncio
    async def test_create_conversation(self, db_service: DatabaseService) -> None:
        """Test creating a conversation."""
        customer_id = uuid4()
        
        conv = await db_service.create_conversation(
            customer_id=customer_id,
            channel=Channel.TELEGRAM,
        )
        
        assert conv.id is not None
        assert conv.customer_id == customer_id
        assert conv.channel == Channel.TELEGRAM
        assert conv.status == ConversationStatus.ACTIVE
    
    @pytest.mark.asyncio
    async def test_get_conversation(self, db_service: DatabaseService) -> None:
        """Test retrieving a conversation."""
        customer_id = uuid4()
        
        created = await db_service.create_conversation(
            customer_id=customer_id,
            channel=Channel.TELEGRAM,
        )
        
        retrieved = await db_service.get_conversation(created.id)
        
        assert retrieved is not None
        assert retrieved.id == created.id
        assert retrieved.customer_id == customer_id
    
    @pytest.mark.asyncio
    async def test_get_or_create_conversation(self, db_service: DatabaseService) -> None:
        """Test get or create conversation."""
        customer_id = uuid4()
        
        # First call creates
        conv1 = await db_service.get_or_create_conversation(
            customer_id=customer_id,
            channel=Channel.TELEGRAM,
        )
        
        # Second call returns existing
        conv2 = await db_service.get_or_create_conversation(
            customer_id=customer_id,
            channel=Channel.TELEGRAM,
        )
        
        assert conv1.id == conv2.id


class TestMessages:
    """Tests for message operations."""
    
    @pytest.mark.asyncio
    async def test_add_message(self, db_service: DatabaseService) -> None:
        """Test adding a message to conversation."""
        customer_id = uuid4()
        conv = await db_service.create_conversation(
            customer_id=customer_id,
            channel=Channel.TELEGRAM,
        )
        
        msg = await db_service.add_message(
            conversation_id=conv.id,
            direction=MessageDirection.INBOUND,
            content="Hello, what are your hours?",
            intent="question",
            sentiment=0.5,
        )
        
        assert msg.id is not None
        assert msg.conversation_id == conv.id
        assert msg.content == "Hello, what are your hours?"
        assert msg.intent == "question"
    
    @pytest.mark.asyncio
    async def test_get_conversation_messages(self, db_service: DatabaseService) -> None:
        """Test retrieving messages from conversation."""
        customer_id = uuid4()
        conv = await db_service.create_conversation(
            customer_id=customer_id,
            channel=Channel.TELEGRAM,
        )
        
        # Add multiple messages
        await db_service.add_message(
            conversation_id=conv.id,
            direction=MessageDirection.INBOUND,
            content="First message",
        )
        await db_service.add_message(
            conversation_id=conv.id,
            direction=MessageDirection.OUTBOUND,
            content="Response",
        )
        await db_service.add_message(
            conversation_id=conv.id,
            direction=MessageDirection.INBOUND,
            content="Second question",
        )
        
        messages = await db_service.get_conversation_messages(conv.id, limit=10)
        
        assert len(messages) == 3
        # Should be in chronological order
        assert messages[0].content == "First message"
        assert messages[2].content == "Second question"


class TestEscalations:
    """Tests for escalation operations."""
    
    @pytest.mark.asyncio
    async def test_create_escalation(self, db_service: DatabaseService) -> None:
        """Test creating an escalation."""
        customer_id = uuid4()
        conv = await db_service.create_conversation(
            customer_id=customer_id,
            channel=Channel.TELEGRAM,
        )
        
        escalation = await db_service.create_escalation(
            conversation_id=conv.id,
            reason="Customer complaint",
            priority="high",
        )
        
        assert escalation.id is not None
        assert escalation.reason == "Customer complaint"
        assert escalation.priority == "high"
        assert escalation.status == "pending"
        
        # Check conversation status was updated
        updated_conv = await db_service.get_conversation(conv.id)
        assert updated_conv is not None
        assert updated_conv.status == ConversationStatus.ESCALATED


class TestAnalyticsEvents:
    """Tests for analytics event tracking."""
    
    @pytest.mark.asyncio
    async def test_track_event(self, db_service: DatabaseService) -> None:
        """Test tracking an analytics event."""
        customer_id = uuid4()
        conversation_id = uuid4()
        
        # Should not raise
        await db_service.track_event(
            event_type="conversation.started",
            customer_id=customer_id,
            conversation_id=conversation_id,
            properties={"channel": "telegram"},
        )
        
        # Verify event was stored
        event = await db_service._analytics_events.find_one(
            {"event_type": "conversation.started"}
        )
        assert event is not None
        assert event["properties"]["channel"] == "telegram"
