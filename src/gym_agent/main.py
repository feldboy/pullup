"""
GymAI Agent - FastAPI Application.

Main entry point for the web API and webhooks.
"""

from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from gym_agent.config import settings
from gym_agent.agents.orchestrator import GymAgent
from gym_agent.services.mongo_crm import get_mongo_crm
from gym_agent.services.database import get_database


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    # Startup
    print(f"🏋️ Starting {settings.app_name}...")
    print(f"   Environment: {settings.environment.value}")
    print(f"   Debug: {settings.debug}")
    
    # Initialize services
    # Connect to MongoDB CRM
    crm = get_mongo_crm()
    db = get_database()
    
    app.state.crm = crm
    app.state.db = db
    app.state.agent = GymAgent(crm=crm, db=db)
    
    yield
    
    # Shutdown
    print("👋 Shutting down...")


app = FastAPI(
    title=settings.app_name,
    description="Intelligent AI Agent for Gym Customer Communication & Retention",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.is_dev else [],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==================== Health Check ====================

@app.get("/health")
async def health_check() -> dict[str, Any]:
    """Health check endpoint."""
    return {
        "status": "healthy",
        "environment": settings.environment.value,
        "version": "0.1.0",
    }


@app.get("/")
async def root() -> dict[str, str]:
    """Root endpoint."""
    return {
        "message": f"Welcome to {settings.app_name}",
        "docs": "/docs",
        "health": "/health",
    }


# ==================== API Models ====================

class MessageRequest(BaseModel):
    """Request model for sending a message."""
    customer_id: str
    message: str
    channel: str = "api"


class MessageResponse(BaseModel):
    """Response model from the agent."""
    message: str
    intent: str
    sentiment: float
    escalate: bool
    escalation_reason: str | None = None


# ==================== API Endpoints ====================

@app.post("/api/v1/message", response_model=MessageResponse)
async def process_message(request: MessageRequest) -> MessageResponse:
    """
    Process a customer message through the AI agent.
    
    For testing purposes - in production, messages come through
    WhatsApp/Telegram webhooks.
    """
    agent: GymAgent = app.state.agent
    crm = app.state.crm
    
    # Look up customer (search by ID or CRM ID)
    customer = None
    try:
        # Try UUID first
        from uuid import UUID
        customer_uuid = UUID(request.customer_id)
        customer = await crm.get_customer(customer_uuid)
    except ValueError:
        pass
        
    if not customer:
        # Fallback to scanning all (inefficient but matches old logic for flexibility)
        # Better: Add get_customer_by_crm_id to service
        for c in await crm.get_all_customers():
            if c.crm_id == request.customer_id:
                customer = c
                break
    
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    # Process message
    response = await agent.process_message(
        customer=customer,
        message=request.message,
    )
    
    return MessageResponse(
        message=response.message,
        intent=response.intent.value,
        sentiment=response.sentiment,
        escalate=response.escalate,
        escalation_reason=response.escalation_reason,
    )


@app.get("/api/v1/dashboard/stats")
async def get_dashboard_stats() -> dict[str, Any]:
    """Get high-level dashboard statistics."""
    crm = app.state.crm
    return await crm.get_stats()


@app.get("/api/v1/customers")
async def list_customers(
    search: str | None = None,
    status: str | None = None,
    health_below: int | None = None,
) -> list[dict[str, Any]]:
    """
    List all customers.
    
    Args:
        search: Optional search term (name/phone/email) - filtering not fully implemented in Mongo yet? 
                Actually get_all_customers returns all, we can filter in memory or implement search in CRM.
        status: Filter by status
        health_below: Filter by health score below X
    """
    crm = app.state.crm
    
    # If we have filter params, use search_customers
    from gym_agent.models.customer import CustomerStatus
    
    status_enum = None
    if status:
        try:
            status_enum = CustomerStatus(status)
        except ValueError:
            pass
            
    if status_enum or health_below:
        customers = await crm.search_customers(status=status_enum, health_score_below=health_below)
    else:
        customers = await crm.get_all_customers()
    
    # In-memory search for text (until we add text index/query to CRM)
    if search:
        search = search.lower()
        customers = [
            c for c in customers
            if search in c.full_name.lower() or 
               search in c.phone or 
               (c.email and search in c.email.lower())
        ]
    
    return [
        {
            "id": str(c.id),
            "crm_id": c.crm_id,
            "name": c.full_name,
            "phone": c.phone,
            "status": c.status.value,
            "health_score": c.health_score,
            "days_since_visit": c.days_since_last_visit,
            "membership_type": c.membership_type.value,
        }
        for c in customers
    ]

@app.get("/api/v1/conversations/{customer_id}")
async def get_customer_conversations(customer_id: str) -> list[dict[str, Any]]:
    """Get conversation history for a customer."""
    db = app.state.db
    from uuid import UUID
    
    try:
        cid = UUID(customer_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid customer ID")
        
    conversations = await db.get_customer_conversations(cid)
    
    # For each conversation, we might want messages? 
    # Or just the conversation metadata.
    # The dashboard likely wants the MESSAGES of the active conversation, or all conversations.
    # For now, let's return conversations extended with recent messages?
    # Or just return list of conversations, and another endpoint for messages?
    # US-002 AC says "Return chat history".
    # Usually chat history = messages.
    # So maybe for the ACTIVE conversation?
    
    # Let's return the simplified chat structure: list of messages from the most recent active conversation,
    # or just all messages flattened?
    # The prompt implies "show me the chat".
    
    # Let's get the active conversation first.
    # If no active, get the last one.
    
    if not conversations:
        return []
        
    # Get messages for the most recent conversation
    # We'll just return the conversations list for this endpoint, 
    # and maybe populate messages inside?
    
    result = []
    for conv in conversations:
        messages = await db.get_conversation_messages(conv.id, limit=50)
        conv_dict = {
            "id": str(conv.id),
            "status": conv.status.value,
            "channel": conv.channel.value,
            "started_at": conv.started_at,
            "messages": [
                {
                    "content": m.content,
                    "direction": m.direction.value,
                    "created_at": m.created_at,
                    "intent": m.intent,
                }
                for m in messages
            ]
        }
        result.append(conv_dict)
        
    return result


@app.get("/api/v1/customers/{customer_id}")
async def get_customer(customer_id: str) -> dict[str, Any]:
    """Get customer details."""
    crm = app.state.crm
    
    customer = None
    try:
        from uuid import UUID
        customer = await crm.get_customer(UUID(customer_id))
    except ValueError:
        pass
        
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    health_score = await crm.calculate_health_score(customer.id)
    
    return {
        "id": str(customer.id),
        "crm_id": customer.crm_id,
        "name": customer.full_name,
        "phone": customer.phone,
        "email": customer.email,
        "status": customer.status.value,
        "membership": {
            "type": customer.membership_type.value,
            "start_date": str(customer.membership_start_date) if customer.membership_start_date else None,
            "end_date": str(customer.membership_end_date) if customer.membership_end_date else None,
            "days_remaining": customer.days_until_expiry,
        },
        "activity": {
            "last_visit": str(customer.last_visit) if customer.last_visit else None,
            "days_since_visit": customer.days_since_last_visit,
            "total_visits": customer.total_visits,
            "preferred_classes": customer.preferred_classes,
        },
        "health_score": {
            "total": health_score.score if health_score else customer.health_score,
            "frequency": health_score.frequency_score if health_score else None,
            "trend": health_score.trend_score if health_score else None,
            "recency": health_score.recency_score if health_score else None,
            "expiry": health_score.expiry_score if health_score else None,
        },
    }


# ==================== Webhook Endpoints (Phase 2) ====================

@app.post("/webhooks/telegram")
async def telegram_webhook(request: Request) -> dict[str, str]:
    """
    Telegram webhook endpoint.
    
    Note: For development, use polling mode instead.
    This is for production deployment with webhooks.
    """
    # Will be implemented in Phase 2
    return {"status": "ok"}


@app.post("/webhooks/whatsapp")
async def whatsapp_webhook(request: Request) -> dict[str, str]:
    """
    WhatsApp webhook endpoint.
    
    Will be implemented in Phase 2.
    """
    return {"status": "not_implemented"}


@app.get("/webhooks/whatsapp")
async def whatsapp_verify(request: Request) -> Any:
    """
    WhatsApp webhook verification.
    
    Will be implemented in Phase 2.
    """
    # Verification challenge for WhatsApp
    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")
    
    if mode == "subscribe" and token == settings.whatsapp_verify_token:
        return int(challenge) if challenge else ""
    
    raise HTTPException(status_code=403, detail="Verification failed")


def main() -> None:
    """Run the FastAPI application."""
    import uvicorn
    
    uvicorn.run(
        "gym_agent.main:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=settings.is_dev,
    )


if __name__ == "__main__":
    main()
