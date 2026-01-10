"""
Orchestrator Agent for GymAI.

The main agent that handles all incoming messages, classifies intent,
and routes to appropriate actions or specialized agents.
"""

from dataclasses import dataclass
from typing import Any
from uuid import UUID

from pydantic_ai import Agent, RunContext

from gym_agent.config import settings
from gym_agent.models.customer import Customer
from gym_agent.models.conversation import Channel, MessageDirection
from gym_agent.models.responses import AgentResponse, Intent
from gym_agent.services.mock_crm import MockCRMService
from gym_agent.services.database import DatabaseService, get_database
from gym_agent.agents.rag import RAGService, search_gym_info


@dataclass
class GymDependencies:
    """Dependencies injected into the agent at runtime."""
    
    customer: Customer
    gym_name: str
    crm: MockCRMService
    conversation_history: list[dict[str, str]] | None = None


# System prompt template
SYSTEM_PROMPT = """You are a friendly customer service agent for {gym_name}.

CORE PRINCIPLES:
1. Be conversational and natural - NOT robotic
2. Keep messages SHORT (1-3 sentences max)
3. Listen and respond to what the customer actually says
4. Never be pushy or send multiple unanswered messages
5. Escalate to human when appropriate

CUSTOMER CONTEXT:
- Name: {customer_name}
- Member since: {member_since}
- Last visit: {last_visit}
- Health Score: {health_score}/100
- Preferred classes: {preferred_classes}
- Membership expires: {membership_expires}
- Language preference: {language}

INTENT HANDLING:
- Time issues ("no time", "busy"): Offer flexible options (short classes, different hours)
- Money issues ("expensive", "budget"): Be empathetic, offer freeze or alternatives, escalate if needed
- Low motivation ("don't feel like it", "bored"): Encourage gently, suggest variety
- Health issues ("injured", "sick"): Show empathy, offer freeze, don't push
- Complaints ("bad service", "not happy"): Apologize sincerely, escalate immediately
- Questions: Answer from your knowledge, admit if you don't know
- Wants human ("talk to someone", "manager"): Immediately confirm and escalate, no resistance

TONE GUIDELINES:
- Professional but warm
- Brief and respectful of their time
- Use emojis sparingly (max 1 per message)
- If customer speaks Hebrew, respond in natural colloquial Hebrew
- If customer speaks English, respond in English

CRITICAL RULES:
❌ Never pretend to be human - if asked directly, admit you're an AI assistant
❌ Don't give medical or nutritional advice
❌ Don't make up information
❌ Don't be pushy
✅ Escalate to human when:
   - Customer explicitly asks for human
   - Complaint or serious dissatisfaction
   - Complex issues you can't resolve
   - After 3 messages without resolution
"""


def build_system_prompt(deps: GymDependencies) -> str:
    """Build the system prompt with customer context."""
    customer = deps.customer
    
    return SYSTEM_PROMPT.format(
        gym_name=deps.gym_name,
        customer_name=customer.first_name,
        member_since=customer.membership_start_date or "Unknown",
        last_visit=customer.last_visit.strftime("%Y-%m-%d") if customer.last_visit else "Never",
        health_score=customer.health_score,
        preferred_classes=", ".join(customer.preferred_classes) if customer.preferred_classes else "None specified",
        membership_expires=customer.membership_end_date or "Unknown",
        language="Hebrew" if customer.preferred_language == "he" else "English",
    )


def get_model_string() -> str:
    """Get the model string based on configuration."""
    from gym_agent.config import LLMProvider
    import os
    
    if settings.default_llm_provider == LLMProvider.OPENROUTER:
        # Set OpenRouter base URL for OpenAI-compatible API
        os.environ["OPENAI_BASE_URL"] = "https://openrouter.ai/api/v1"
        os.environ["OPENAI_API_KEY"] = settings.openrouter_api_key
        return f"openai:{settings.default_model}"
    elif settings.default_llm_provider == LLMProvider.GEMINI:
        # Ensure Google API key is in environment
        if settings.google_api_key:
            os.environ["GOOGLE_API_KEY"] = settings.google_api_key
        model = settings.default_model or "gemini-2.0-flash"
        return f"google-gla:{model}"
    else:
        return f"openai:{settings.default_model}"


# Initialize model configuration
_model_string = get_model_string()

# Create the main agent
gym_agent = Agent(
    _model_string,
    deps_type=GymDependencies,
    output_type=AgentResponse,
    system_prompt=SYSTEM_PROMPT,  # Will be overridden with dynamic prompt
)


@gym_agent.system_prompt
async def add_customer_context(ctx: RunContext[GymDependencies]) -> str:
    """Add dynamic customer context to the system prompt."""
    return build_system_prompt(ctx.deps)


@gym_agent.tool
async def get_customer_info(
    ctx: RunContext[GymDependencies],
    info_type: str,
) -> str:
    """
    Get customer information from CRM.
    
    Args:
        info_type: Type of info to retrieve:
            - 'profile': Basic customer info
            - 'attendance': Recent attendance history
            - 'membership': Membership details and status
            
    Returns:
        Requested customer data as string.
    """
    customer = ctx.deps.customer
    crm = ctx.deps.crm
    
    if info_type == "profile":
        return (
            f"Name: {customer.full_name}\n"
            f"Phone: {customer.phone}\n"
            f"Member since: {customer.membership_start_date}\n"
            f"Status: {customer.status.value}"
        )
    
    elif info_type == "attendance":
        visits_30d = await crm.get_visit_count(customer.id, days=30)
        visits_7d = await crm.get_visit_count(customer.id, days=7)
        return (
            f"Visits this week: {visits_7d}\n"
            f"Visits this month: {visits_30d}\n"
            f"Last visit: {customer.last_visit or 'Never'}\n"
            f"Total visits: {customer.total_visits}"
        )
    
    elif info_type == "membership":
        membership = await crm.get_membership_status(customer.id)
        expiring_warning = " ⚠️ Expiring soon!" if membership.get("is_expiring_soon") else ""
        return (
            f"Plan: {membership.get('plan', 'Unknown')}\n"
            f"Expires: {membership.get('end_date', 'Unknown')}{expiring_warning}\n"
            f"Days remaining: {membership.get('days_remaining', 'Unknown')}\n"
            f"Status: {membership.get('status', 'Unknown')}"
        )
    
    return f"Unknown info type: {info_type}"


@gym_agent.tool
async def search_gym_knowledge(
    ctx: RunContext[GymDependencies],
    query: str,
) -> str:
    """
    Search the gym's knowledge base for information.
    
    Use this tool when the customer asks questions about:
    - Operating hours (שעות פעילות)
    - Classes and services (שיעורים, אימונים)
    - Membership plans and pricing (מנויים, מחירים)
    - Policies (ביטול, הזמנה, ציוד)
    - Facilities (מתקנים, חניה)
    - Location (מיקום, איפה)
    
    Args:
        query: The question or topic to search for
        
    Returns:
        Relevant information from the gym's knowledge base.
    """
    rag_response = search_gym_info(query)
    
    if not rag_response.found_in_knowledge_base:
        return "Information not found in knowledge base. Consider asking the customer for more details or escalating."
    
    return rag_response.answer


@gym_agent.tool
async def escalate_to_human(
    ctx: RunContext[GymDependencies],
    reason: str,
    priority: str = "normal",
    notes: str = "",
) -> str:
    """
    Escalate conversation to human representative.
    
    Use this when:
    - Customer explicitly asks to speak with a person
    - Complaint or serious dissatisfaction
    - Complex financial issues requiring negotiation
    - Health/injury situations
    - 3+ messages without resolution
    
    Args:
        reason: Why escalating (complaint, request, complex_issue, info_not_found)
        priority: 'low', 'normal', 'high', 'urgent'
        notes: Additional context for the human rep
        
    Returns:
        Confirmation of escalation.
    """
    customer = ctx.deps.customer
    
    # In production, this would create an escalation record in the database
    # and notify staff. For now, just log and confirm.
    print(f"🚨 ESCALATION: Customer {customer.full_name}")
    print(f"   Reason: {reason}")
    print(f"   Priority: {priority}")
    print(f"   Notes: {notes}")
    
    return f"Escalation created. Reason: {reason}. A human representative will be notified."


class GymAgent:
    """
    High-level wrapper for the Gym AI agent.
    
    Provides a simpler interface for processing messages.
    Integrates with MongoDB for conversation persistence.
    """
    
    def __init__(
        self,
        gym_name: str = "EloozFit - אילוזפיט",  # Real gym name from PDF
        crm: MockCRMService | None = None,
        db: DatabaseService | None = None,
    ):
        """
        Initialize the agent.
        
        Args:
            gym_name: Name of the gym
            crm: CRM service (uses mock if not provided)
            db: Database service for persistence (uses default if not provided)
        """
        self.gym_name = gym_name
        self.crm = crm or MockCRMService()
        self.db = db or get_database()
        self._agent = gym_agent
    
    async def process_message(
        self,
        customer: Customer,
        message: str,
        channel: Channel = Channel.TELEGRAM,
        conversation_history: list[dict[str, str]] | None = None,
    ) -> AgentResponse:
        """
        Process a customer message and generate a response.
        
        Args:
            customer: Customer object
            message: The customer's message
            channel: Communication channel
            conversation_history: Optional list of previous messages (overrides DB lookup)
            
        Returns:
            AgentResponse with message, intent, sentiment, etc.
        """
        # Get or create conversation
        conversation = await self.db.get_or_create_conversation(
            customer_id=customer.id,
            channel=channel,
        )
        
        # Store incoming message
        await self.db.add_message(
            conversation_id=conversation.id,
            direction=MessageDirection.INBOUND,
            content=message,
        )
        
        # Load conversation history from database if not provided
        if conversation_history is None:
            db_messages = await self.db.get_conversation_messages(
                conversation_id=conversation.id,
                limit=10,
            )
            conversation_history = [
                {
                    "role": "user" if m.direction == MessageDirection.INBOUND else "assistant",
                    "content": m.content,
                }
                for m in db_messages[:-1]  # Exclude the message we just added
            ]
        
        deps = GymDependencies(
            customer=customer,
            gym_name=self.gym_name,
            crm=self.crm,
            conversation_history=conversation_history,
        )
        
        # Build message with history context if available
        prompt = message
        if conversation_history:
            history_text = "\n".join([
                f"{'Customer' if m['role'] == 'user' else 'Agent'}: {m['content']}"
                for m in conversation_history[-5:]  # Last 5 messages
            ])
            prompt = f"Conversation history:\n{history_text}\n\nNew message: {message}"
        
        result = await self._agent.run(prompt, deps=deps)
        response = result.output
        
        # Store outgoing message
        await self.db.add_message(
            conversation_id=conversation.id,
            direction=MessageDirection.OUTBOUND,
            content=response.message,
            intent=response.intent.value,
            sentiment=response.sentiment,
            agent_type="orchestrator",
        )
        
        # Track analytics event
        await self.db.track_event(
            event_type="conversation.message_received",
            customer_id=customer.id,
            conversation_id=conversation.id,
            properties={
                "intent": response.intent.value,
                "sentiment": response.sentiment,
                "escalated": response.escalate,
            },
        )
        
        # Handle escalation if needed
        if response.escalate:
            await self.db.create_escalation(
                conversation_id=conversation.id,
                reason=response.escalation_reason or "Agent requested escalation",
                priority="high" if response.intent == Intent.COMPLAINT else "normal",
            )
            print(f"🚨 ESCALATION: Customer {customer.full_name}")
            print(f"   Reason: {response.escalation_reason}")
        
        return response
    
    async def get_customer_by_telegram(self, telegram_id: int) -> Customer | None:
        """Look up customer by Telegram ID."""
        return await self.crm.get_customer_by_telegram(telegram_id)
    
    async def create_test_customer(
        self,
        telegram_id: int,
        first_name: str,
    ) -> Customer:
        """Create a test customer for development."""
        return self.crm.add_test_customer(
            telegram_id=telegram_id,
            first_name=first_name,
        )
    
    async def get_conversation_history(
        self,
        customer_id: UUID,
        channel: Channel = Channel.TELEGRAM,
        limit: int = 10,
    ) -> list[dict[str, str]]:
        """
        Get conversation history for a customer.
        
        Args:
            customer_id: Customer UUID
            channel: Communication channel
            limit: Maximum messages to retrieve
            
        Returns:
            List of messages as dicts with 'role' and 'content'
        """
        conversation = await self.db.get_active_conversation(
            customer_id=customer_id,
            channel=channel,
        )
        
        if not conversation:
            return []
        
        messages = await self.db.get_conversation_messages(
            conversation_id=conversation.id,
            limit=limit,
        )
        
        return [
            {
                "role": "user" if m.direction == MessageDirection.INBOUND else "assistant",
                "content": m.content,
            }
            for m in messages
        ]
