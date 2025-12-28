"""Test configuration models."""

import pytest
from gym_agent.models.customer import Customer, CustomerStatus, HealthScore, MembershipType
from gym_agent.models.conversation import Conversation, Message, ConversationStatus, MessageDirection, Channel
from gym_agent.models.responses import AgentResponse, Intent
from datetime import date, datetime, timedelta
from uuid import uuid4


class TestCustomerModel:
    """Tests for Customer model."""
    
    def test_create_customer(self):
        """Test basic customer creation."""
        customer = Customer(
            id=uuid4(),
            phone="+972501234567",
            first_name="דניאל",
            last_name="כהן",
        )
        
        assert customer.first_name == "דניאל"
        assert customer.full_name == "דניאל כהן"
        assert customer.status == CustomerStatus.ACTIVE
        assert customer.health_score == 100
    
    def test_days_since_last_visit(self):
        """Test days since last visit calculation."""
        customer = Customer(
            id=uuid4(),
            phone="+972501234567",
            first_name="Test",
            last_visit=datetime.now() - timedelta(days=7),
        )
        
        assert customer.days_since_last_visit == 7
    
    def test_membership_expiring_soon(self):
        """Test membership expiring soon detection."""
        customer = Customer(
            id=uuid4(),
            phone="+972501234567",
            first_name="Test",
            membership_end_date=date.today() + timedelta(days=15),
        )
        
        assert customer.is_membership_expiring_soon is True
        
        customer.membership_end_date = date.today() + timedelta(days=60)
        assert customer.is_membership_expiring_soon is False


class TestHealthScore:
    """Tests for HealthScore model."""
    
    def test_calculate_health_score(self):
        """Test health score calculation with weights."""
        score = HealthScore.calculate(
            customer_id=uuid4(),
            frequency_score=80,  # 30% = 24
            trend_score=60,      # 25% = 15
            recency_score=100,   # 25% = 25
            expiry_score=50,     # 20% = 10
        )
        
        # 24 + 15 + 25 + 10 = 74
        assert score.score == 74


class TestConversationModel:
    """Tests for Conversation model."""
    
    def test_add_message_tracks_unanswered(self):
        """Test that unanswered count is tracked correctly."""
        conv = Conversation(
            id=uuid4(),
            customer_id=uuid4(),
            channel=Channel.TELEGRAM,
        )
        
        # Agent sends message
        outbound = Message(
            id=uuid4(),
            conversation_id=conv.id,
            direction=MessageDirection.OUTBOUND,
            content="Hello!",
        )
        conv.add_message(outbound)
        assert conv.unanswered_count == 1
        
        # Customer replies
        inbound = Message(
            id=uuid4(),
            conversation_id=conv.id,
            direction=MessageDirection.INBOUND,
            content="Hi!",
        )
        conv.add_message(inbound)
        assert conv.unanswered_count == 0


class TestAgentResponse:
    """Tests for AgentResponse model."""
    
    def test_create_response(self):
        """Test creating agent response."""
        response = AgentResponse(
            message="Hey! Everything okay?",
            intent=Intent.QUESTION,
            sentiment=0.5,
        )
        
        assert response.message == "Hey! Everything okay?"
        assert response.intent == Intent.QUESTION
        assert response.escalate is False
    
    def test_sentiment_bounds(self):
        """Test sentiment is bounded correctly."""
        response = AgentResponse(
            message="Test",
            intent=Intent.POSITIVE,
            sentiment=1.0,
        )
        assert response.sentiment == 1.0
        
        # Should raise validation error for out of bounds
        with pytest.raises(Exception):
            AgentResponse(
                message="Test",
                intent=Intent.POSITIVE,
                sentiment=1.5,
            )
