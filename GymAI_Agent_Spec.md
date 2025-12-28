# GymAI Agent - Product & Technical Specification

> Intelligent AI Agent for Gym Customer Communication & Retention  
> Built with Pydantic AI Framework

---

## Table of Contents

1. [Overview](#1-overview)
2. [Problem Statement](#2-problem-statement)
3. [Conversation Philosophy](#3-conversation-philosophy)
4. [Target Audience](#4-target-audience)
5. [Agent Identity](#5-agent-identity)
6. [Core Capabilities](#6-core-capabilities)
7. [Technical Architecture](#7-technical-architecture)
8. [Database & Infrastructure](#8-database--infrastructure)
9. [Security & Compliance](#9-security--compliance)
10. [Analytics & Monitoring](#10-analytics--monitoring)
11. [Communication Channels](#11-communication-channels)
12. [Code Examples](#12-code-examples)
13. [Human Escalation](#13-human-escalation)
14. [Message Examples](#14-message-examples)
15. [Success Metrics](#15-success-metrics)
16. [Development Roadmap](#16-development-roadmap)

---

## 1. Overview

You are an AI agent functioning as a **virtual customer service representative** for gyms and fitness studios.

### Primary Goals
- Improve customer **retention** (reduce churn)
- Provide excellent **customer experience**
- Optimize **communication** between business and members
- Answer **open-ended questions** from business PDF
- Handle **billing reminders** professionally
- Celebrate **milestones** and build loyalty

### Integration Points
- **CRM Systems**: Arbox, Leap, Fizikal
- **Messaging**: WhatsApp Business API, Telegram (testing)
- **Knowledge Base**: PDF documents from gym owner
- **Payments**: Payment gateway integration

---

## 2. Problem Statement

### 2.1 Current State

Gyms today use basic automations that send generic messages:

- "We haven't seen you" messages after a fixed period
- Automatic birthday greetings
- Subscription renewal reminders
- ❌ No conversation continuity or context understanding
- ❌ No response to questions - customer must call or wait
- ❌ No personalization based on behavior

### 2.2 The Gap

- Customers feel messages are **"spam"**
- No **early detection** of at-risk customers
- No ability to manage **two-way conversations**
- No quick answers to simple questions like "What are your hours on Saturday?"
- Staff wastes time on **repetitive inquiries**

---

## 3. Conversation Philosophy

### 3.1 Core Principle: Proactive, Not Pushy

> **The agent initiates conversations intelligently, then LISTENS and ADAPTS based on the customer's response. This is NOT about bombarding customers with messages.**

### 3.2 The Conversation Flow

```
┌─────────────────────────────────────────────────────────────┐
│  1. INITIATE  →  2. LISTEN  →  3. UNDERSTAND  →            │
│                                                             │
│  4. RESPOND  →  5. RESOLVE or ESCALATE                     │
└─────────────────────────────────────────────────────────────┘
```

| Step | Description |
|------|-------------|
| **1. Initiate** | Send a short, personalized message based on trigger (absence, milestone, etc.) |
| **2. Listen** | Wait for customer response. Don't send follow-ups immediately. |
| **3. Understand** | Analyze intent and sentiment. Extract the REAL reason. |
| **4. Respond** | Provide helpful, contextual response addressing their specific situation. |
| **5. Resolve/Escalate** | Either solve the issue or smoothly hand off to human rep. |

### 3.3 Example Conversation Flow

```
Agent:    Hey Sarah, everything okay? Haven't seen you this week.

Customer: Yeah, work has been crazy lately

Agent:    Totally get it. We have 30-min express classes at 6am and 8pm 
          if that helps. Want me to send you the schedule?

Customer: Actually yeah, that would be great

Agent:    Done! Check your messages. See you soon 💪
```

### 3.4 Intent Detection & Response Strategy

| Detected Intent | Example Response | Agent Strategy |
|-----------------|------------------|----------------|
| **Time constraint** | "No time", "Busy with work" | Offer short classes, flexible hours, weekend options |
| **Financial issue** | "Too expensive", "Tight budget" | Offer freeze, alternative plan, escalate for payment plans |
| **Low motivation** | "Don't feel like it", "Bored" | Encourage, suggest new classes, buddy workout, PT trial |
| **Health/Injury** | "Got injured", "Feeling sick" | Express empathy, offer freeze, escalate if needed |
| **Positive engagement** | "Coming tomorrow!", "Thanks!" | Acknowledge positively, end conversation gracefully |
| **Question** | "What time do you close?" | Use RAG to answer from business PDF |
| **Complaint** | "Bad service", "Not happy" | Apologize, acknowledge, IMMEDIATELY escalate to human |
| **Wants human** | "Talk to someone", "Manager" | Immediately confirm and escalate, no resistance |

### 3.5 Response Timing Rules

```python
RESPONSE_TIMING = {
    "immediate": ["complaint", "wants_human", "urgent_question"],
    "within_1_hour": ["question", "positive_engagement"],
    "within_4_hours": ["time_constraint", "low_motivation"],
    "next_business_day": ["no_response_followup"]
}

# Never send more than 2 messages without customer response
MAX_UNANSWERED_MESSAGES = 2

# Wait time before follow-up (if no response)
FOLLOWUP_WAIT_HOURS = 48
```

---

## 4. Target Audience

### 4.1 Business Types

- Boutique gyms
- Large gym chains
- Yoga and Pilates studios
- CrossFit boxes
- Personal training studios
- Martial arts academies
- Swimming pools / Aqua fitness

### 4.2 End Users

- **Active members** - Regular attendees
- **Inactive members** - Haven't visited recently
- **At-risk members** - Showing churn signals
- **Potential customers** - Leads
- **Former members** - Win-back candidates

---

## 5. Agent Identity

### 5.1 Character & Communication

You are a **virtual customer service rep** - not a trainer, not a friend.

**Tone Guidelines:**
- ✅ Professional but warm and approachable
- ✅ Supportive and encouraging, never judgmental
- ✅ Brief and to the point - short messages, no walls of text
- ✅ Natural, conversational language
- ✅ Minimal emoji use - only when it feels natural
- ✅ Respectful of customer's time

**Language Style:**
```
❌ BAD:  "Dear valued customer, we have noticed that your attendance 
         has decreased significantly over the past few weeks. We would 
         like to inquire if there is anything we can assist you with..."

✅ GOOD: "Hey Mike, everything okay? Haven't seen you lately."
```

### 5.2 Boundaries

- ❌ Never pretend to be human - if asked, admit you're AI
- ❌ Don't give medical or nutritional advice
- ❌ Don't make up information - only use PDF or CRM data
- ❌ Don't be pushy or send too many messages
- ✅ Escalate to human when needed
- ✅ Protect privacy and personal information

### 5.3 Personality Traits

```python
AGENT_PERSONALITY = {
    "empathy": 0.9,        # High empathy in responses
    "professionalism": 0.8, # Professional but not stiff
    "friendliness": 0.7,   # Friendly but not overly casual
    "persistence": 0.4,    # Not pushy
    "humor": 0.3          # Occasional light humor, context-dependent
}
```

---

## 6. Core Capabilities

### 6.1 FAQ Answering (RAG)

Answer customer questions based on PDF provided by gym owner:

| Question Type | Examples |
|---------------|----------|
| Operating hours | "When do you open on Saturday?", "What time do you close?" |
| Pricing & plans | "How much is a membership?", "Do you have student discounts?" |
| Policies | "What's the cancellation policy?", "Can I freeze my membership?" |
| Facilities | "Is there parking?", "Do I need to bring a towel?" |
| Classes | "What classes do you offer?", "When is yoga?" |

**If information NOT found:**
```
"I don't have that info on hand, but I'm passing your question 
to the team. Someone will get back to you shortly."
```

### 6.2 Churn Risk Detection (Health Score)

Calculate a **Health Score (1-100)** for each customer:

| Parameter | Weight | Description |
|-----------|--------|-------------|
| Workout frequency | 30% | Weekly average vs. historical |
| Trend direction | 25% | Increasing/decreasing frequency |
| Days since last visit | 25% | 0-7 = good, 30+ = critical |
| Subscription expiry | 20% | 30 days before = red flag |

**Action Triggers:**
- `Score < 50`: Immediate intervention
- `Score 50-70`: Proactive follow-up
- `Score > 70`: Regular maintenance

```python
def calculate_health_score(customer: Customer) -> int:
    frequency_score = calculate_frequency_score(customer)  # 0-100
    trend_score = calculate_trend_score(customer)          # 0-100
    recency_score = calculate_recency_score(customer)      # 0-100
    expiry_score = calculate_expiry_score(customer)        # 0-100
    
    return int(
        frequency_score * 0.30 +
        trend_score * 0.25 +
        recency_score * 0.25 +
        expiry_score * 0.20
    )
```

### 6.3 Personalized Communication

- Use **first name**
- Reference **preferred workout types** ("Haven't seen you at Zumba lately")
- Send at times when customer **usually visits**
- Adjust tone based on **tenure** (new vs. veteran member)
- Remember **previous conversation context**

### 6.4 Marketing & Promotions

- Send relevant promotions based on customer profile
- Promote new classes based on preferences
- Offer upgrades (personal training, nutrition plans)
- Birthday and anniversary specials

### 6.5 Billing & Payments

- Send payment reminders with respectful tone
- Escalate gradually: friendly → formal → human rep
- Enable payment via direct link
- Offer payment plans when appropriate

### 6.6 Milestone Celebrations

- Birthdays
- Workout milestones (50th, 100th, 200th)
- Membership anniversaries
- Return after long absence
- Personal records (if tracked)

---

## 7. Technical Architecture

### 7.1 Framework: Pydantic AI

Built on **Pydantic AI** - a modern, production-ready agent framework:

- ✅ **Type-safe** - Compile-time type checking
- ✅ **Model-agnostic** - Supports OpenAI, Anthropic, Google, Groq
- ✅ **Dependency Injection** - Clean dependency management
- ✅ **Structured Output** - Validated output with Pydantic models
- ✅ **Tools System** - Flexible function calling
- ✅ **Multi-Agent Support** - Agent delegation and handoff

### 7.2 System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    COMMUNICATION LAYER                          │
│         WhatsApp API  |  Telegram Bot  |  SMS Gateway           │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                      FASTAPI APPLICATION                         │
│              Webhook Handler  |  REST API  |  Admin UI           │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                     ORCHESTRATOR AGENT                           │
│          Intent Detection  |  Routing  |  State Management       │
│                                                                  │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐        │
│  │   RAG    │  │Retention │  │ Billing  │  │ Marketing│        │
│  │  Agent   │  │  Agent   │  │  Agent   │  │  Agent   │        │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘        │
└─────────────────────────────────────────────────────────────────┘
         │              │              │              │
         ▼              ▼              ▼              ▼
┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐
│  PostgreSQL │ │     CRM     │ │   Payment   │ │    Redis    │
│  + pgvector │ │   (Arbox)   │ │   Gateway   │ │   (Cache)   │
└─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘
```

### 7.3 Multi-Agent Structure

#### Orchestrator Agent (Main)
Central coordinator that handles routing and decision-making:
- Receives incoming messages
- Classifies intent and sentiment
- Routes to appropriate specialized agent
- Decides when to escalate to human
- Maintains conversation state

#### RAG Agent (Knowledge Base)
Handles questions using the gym's PDF documentation:
- PDF ingestion and chunking
- Embedding generation and storage
- Semantic search for relevant info
- Response generation with context

#### Retention Agent
Manages customer retention:
- Health Score calculation
- Personalized outreach messages
- Response tracking and follow-up
- Win-back campaigns

#### Billing Agent
Handles payment-related interactions:
- Payment reminders
- Escalation management
- Payment gateway integration
- Payment plan discussions

#### Marketing Agent
Handles promotional communications:
- Campaign targeting
- Offer personalization
- A/B testing support

---

## 8. Database & Infrastructure

### 8.1 Primary Database: PostgreSQL

PostgreSQL is the recommended primary database:

| Feature | Benefit |
|---------|---------|
| **pgvector extension** | Native vector similarity search for RAG |
| **JSONB support** | Flexible schema for conversation history |
| **Full-text search** | Built-in text search capabilities |
| **Proven reliability** | Battle-tested in production |
| **Cost effective** | Open source, no vendor lock-in |

#### Database Schema

```sql
-- Customers (synced from CRM)
CREATE TABLE customers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    crm_id VARCHAR(100) UNIQUE NOT NULL,
    phone VARCHAR(20) UNIQUE NOT NULL,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    email VARCHAR(255),
    membership_type VARCHAR(50),
    membership_end_date DATE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'
);

-- Conversations
CREATE TABLE conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id UUID REFERENCES customers(id),
    channel VARCHAR(20) NOT NULL, -- 'whatsapp', 'telegram', 'sms'
    status VARCHAR(20) DEFAULT 'active', -- 'active', 'resolved', 'escalated'
    started_at TIMESTAMP DEFAULT NOW(),
    last_message_at TIMESTAMP,
    escalated_at TIMESTAMP,
    escalated_to VARCHAR(100),
    metadata JSONB DEFAULT '{}'
);

-- Messages
CREATE TABLE messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID REFERENCES conversations(id),
    direction VARCHAR(10) NOT NULL, -- 'inbound', 'outbound'
    content TEXT NOT NULL,
    intent VARCHAR(50),
    sentiment FLOAT,
    agent_type VARCHAR(50), -- 'orchestrator', 'rag', 'retention', etc.
    created_at TIMESTAMP DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'
);

-- Knowledge Base (RAG)
CREATE TABLE knowledge_chunks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    gym_id UUID NOT NULL,
    content TEXT NOT NULL,
    embedding vector(1536), -- OpenAI ada-002 dimension
    source_file VARCHAR(255),
    page_number INT,
    chunk_index INT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX ON knowledge_chunks 
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- Health Scores
CREATE TABLE health_scores (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id UUID REFERENCES customers(id),
    score INT NOT NULL CHECK (score >= 0 AND score <= 100),
    frequency_score INT,
    trend_score INT,
    recency_score INT,
    expiry_score INT,
    calculated_at TIMESTAMP DEFAULT NOW()
);

-- Escalations
CREATE TABLE escalations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID REFERENCES conversations(id),
    reason VARCHAR(100) NOT NULL,
    priority VARCHAR(20) DEFAULT 'normal',
    status VARCHAR(20) DEFAULT 'pending', -- 'pending', 'assigned', 'resolved'
    assigned_to VARCHAR(100),
    notes TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    resolved_at TIMESTAMP
);

-- Analytics Events
CREATE TABLE analytics_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_type VARCHAR(50) NOT NULL,
    customer_id UUID REFERENCES customers(id),
    conversation_id UUID REFERENCES conversations(id),
    properties JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_analytics_events_type ON analytics_events(event_type);
CREATE INDEX idx_analytics_events_created ON analytics_events(created_at);
```

### 8.2 Caching Layer: Redis

Redis for fast access and session management:

| Use Case | Implementation |
|----------|----------------|
| **Conversation state** | Active conversation context (TTL: 24h) |
| **Rate limiting** | Prevent message flooding (per customer) |
| **Customer cache** | Frequently accessed customer data (TTL: 1h) |
| **Session management** | Track active sessions |
| **Queue management** | Message queuing for async processing |

```python
REDIS_KEYS = {
    "conversation": "conv:{customer_id}",      # Current conversation state
    "rate_limit": "rate:{customer_id}",        # Rate limiting counter
    "customer": "customer:{customer_id}",      # Cached customer data
    "pending_messages": "pending:{gym_id}",    # Message queue
}

REDIS_TTL = {
    "conversation": 86400,    # 24 hours
    "rate_limit": 3600,       # 1 hour
    "customer": 3600,         # 1 hour
}
```

### 8.3 Vector Database Options

| Option | Pros | Best For |
|--------|------|----------|
| **pgvector ⭐** | Single DB, no extra cost, SQL familiar | MVP, small-medium scale |
| **Supabase** | Managed, pgvector built-in, easy setup | Quick start, hosted |
| **Pinecone** | Purpose-built, highly scalable | Large scale, enterprise |
| **Qdrant** | Open source, fast, rich filtering | Self-hosted, complex queries |

> 💡 **Recommendation**: Start with pgvector in PostgreSQL. It's free, already in your stack, and handles typical gym scale easily.

### 8.4 Complete Tech Stack

| Layer | Technology | Purpose |
|-------|------------|---------|
| Agent Framework | Pydantic AI | Multi-agent orchestration |
| LLM Provider | OpenAI / Anthropic | Language understanding |
| Web Framework | FastAPI | Webhooks + REST API |
| Primary Database | PostgreSQL + pgvector | Data + Vector search |
| Cache | Redis | Sessions + rate limiting |
| Task Queue | Celery / ARQ | Scheduled messages |
| Messaging | WhatsApp Business API | Production communication |
| Testing Channel | Telegram Bot | Local development & testing |
| PDF Processing | PyMuPDF / Docling | PDF text extraction |
| Embeddings | OpenAI text-embedding-3-small | Vector embeddings |
| Observability | Pydantic Logfire | Monitoring + debugging |
| Hosting | Railway / Render / AWS | Cloud infrastructure |

---

## 9. Security & Compliance

### 9.1 Data Protection

#### Encryption
```python
SECURITY_CONFIG = {
    "encryption": {
        "at_rest": "AES-256",           # Database encryption
        "in_transit": "TLS 1.3",        # All API communications
        "pii_fields": [                  # Fields requiring extra protection
            "phone", "email", "first_name", "last_name"
        ]
    },
    "data_retention": {
        "messages": "2 years",
        "analytics": "3 years",
        "logs": "90 days"
    }
}
```

#### PII Handling
- All PII encrypted at rest
- Minimal PII in logs (masked)
- Right to deletion support
- Data export capability

### 9.2 Authentication & Authorization

```python
AUTH_CONFIG = {
    "api_auth": "JWT + API Keys",
    "webhook_verification": "HMAC-SHA256",
    "admin_access": "OAuth 2.0 + MFA",
    "rate_limits": {
        "api": "1000 req/min",
        "webhooks": "100 req/sec",
        "per_customer_messages": "10 msg/hour"
    }
}
```

#### Role-Based Access Control (RBAC)
| Role | Permissions |
|------|-------------|
| **Super Admin** | Full access, multi-gym management |
| **Gym Admin** | Manage own gym, view analytics, configure agent |
| **Staff** | View conversations, handle escalations |
| **API** | Programmatic access (scoped) |

### 9.3 API Security

```python
# Webhook verification
def verify_webhook(request: Request, signature: str) -> bool:
    payload = await request.body()
    expected = hmac.new(
        WEBHOOK_SECRET.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(signature, expected)

# Rate limiting middleware
@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    client_id = get_client_identifier(request)
    
    if await is_rate_limited(client_id):
        raise HTTPException(status_code=429, detail="Too many requests")
    
    await increment_request_count(client_id)
    return await call_next(request)
```

### 9.4 Compliance Checklist

- [ ] **GDPR Compliance** (if serving EU customers)
  - Consent management
  - Data portability
  - Right to erasure
  - Privacy policy
  
- [ ] **Israeli Privacy Law**
  - Data minimization
  - Purpose limitation
  - Security measures
  
- [ ] **WhatsApp Business Policy**
  - Message templates approval
  - Opt-in requirements
  - 24-hour messaging window

### 9.5 Audit Logging

```python
class AuditLog(BaseModel):
    timestamp: datetime
    action: str
    actor_type: str  # 'agent', 'admin', 'system'
    actor_id: str
    resource_type: str
    resource_id: str
    changes: dict
    ip_address: str | None
    
# Log all sensitive actions
AUDIT_ACTIONS = [
    "customer.view",
    "customer.update",
    "customer.delete",
    "conversation.escalate",
    "settings.change",
    "api_key.create",
    "api_key.revoke"
]
```

---

## 10. Analytics & Monitoring

### 10.1 Key Metrics Dashboard

#### Customer Metrics
```python
CUSTOMER_METRICS = {
    "health_score_distribution": "Histogram of health scores",
    "churn_rate": "Monthly churn percentage",
    "retention_rate": "Monthly retention percentage",
    "at_risk_customers": "Count of score < 50",
    "win_back_rate": "Returned customers / Lost customers"
}
```

#### Conversation Metrics
```python
CONVERSATION_METRICS = {
    "total_conversations": "Daily/weekly/monthly count",
    "response_rate": "Customer responses / Messages sent",
    "resolution_rate": "Resolved without escalation",
    "avg_conversation_length": "Messages per conversation",
    "avg_response_time": "Time to first response",
    "escalation_rate": "Escalated / Total conversations"
}
```

#### Agent Performance
```python
AGENT_METRICS = {
    "intent_accuracy": "Correctly identified intents",
    "rag_hit_rate": "Questions answered from knowledge base",
    "sentiment_accuracy": "Sentiment detection accuracy",
    "handoff_quality": "Successful handoffs to human"
}
```

### 10.2 Real-Time Monitoring

#### Pydantic Logfire Integration
```python
import logfire

logfire.configure(send_to_logfire='if-token-present')
logfire.instrument_pydantic_ai()  # Instrument all agents
logfire.instrument_asyncpg()      # Database queries
logfire.instrument_httpx()        # HTTP requests

# Custom spans for business logic
with logfire.span("calculate_health_score", customer_id=customer_id):
    score = calculate_health_score(customer)
    logfire.info(f"Health score calculated: {score}")
```

#### Alert Conditions
```python
ALERT_CONDITIONS = {
    "high_escalation_rate": {
        "condition": "escalation_rate > 0.3",
        "severity": "warning",
        "channel": "slack"
    },
    "api_errors": {
        "condition": "error_rate > 0.05",
        "severity": "critical",
        "channel": "pagerduty"
    },
    "response_time": {
        "condition": "p95_latency > 5000ms",
        "severity": "warning",
        "channel": "slack"
    },
    "queue_backup": {
        "condition": "pending_messages > 100",
        "severity": "critical",
        "channel": "pagerduty"
    }
}
```

### 10.3 Analytics Events

Track these events for analysis:

```python
ANALYTICS_EVENTS = [
    # Conversation events
    "conversation.started",
    "conversation.message_sent",
    "conversation.message_received",
    "conversation.resolved",
    "conversation.escalated",
    
    # Intent events
    "intent.detected",
    "intent.changed",
    
    # RAG events
    "rag.query",
    "rag.hit",
    "rag.miss",
    
    # Retention events
    "retention.outreach_sent",
    "retention.customer_returned",
    "retention.customer_churned",
    
    # Billing events
    "billing.reminder_sent",
    "billing.payment_received",
    "billing.payment_failed"
]

# Event tracking function
async def track_event(
    event_type: str,
    customer_id: str | None,
    conversation_id: str | None,
    properties: dict
):
    await db.execute("""
        INSERT INTO analytics_events 
        (event_type, customer_id, conversation_id, properties)
        VALUES ($1, $2, $3, $4)
    """, event_type, customer_id, conversation_id, json.dumps(properties))
```

### 10.4 Reporting

#### Daily Report
- Messages sent/received
- Conversations started/resolved
- Escalation count and reasons
- Top intents detected
- RAG hit/miss rate

#### Weekly Report
- Retention metrics
- Health score trends
- Customer feedback summary
- Agent performance metrics
- Comparison to previous week

#### Monthly Report
- Churn analysis
- ROI calculation
- Feature usage statistics
- Recommendations for improvement

---

## 11. Communication Channels

### 11.1 WhatsApp Business API (Production)

Primary production channel:

```python
WHATSAPP_CONFIG = {
    "provider": "Meta Cloud API",  # or Twilio, 360dialog
    "webhook_path": "/webhooks/whatsapp",
    "message_types": ["text", "template", "interactive"],
    "features": {
        "read_receipts": True,
        "typing_indicator": True,
        "media_support": True
    }
}
```

#### Message Templates
Pre-approved templates for proactive messaging:

```python
WHATSAPP_TEMPLATES = {
    "absence_checkin": {
        "name": "absence_checkin",
        "language": "he",
        "components": [
            {"type": "body", "text": "היי {{1}}, הכל בסדר? לא ראינו אותך השבוע."}
        ]
    },
    "subscription_reminder": {
        "name": "subscription_reminder", 
        "language": "he",
        "components": [
            {"type": "body", "text": "היי {{1}}, המנוי שלך מסתיים בעוד {{2}} ימים."}
        ]
    },
    "payment_reminder": {
        "name": "payment_reminder",
        "language": "he", 
        "components": [
            {"type": "body", "text": "היי {{1}}, יש תשלום פתוח. אפשר להסדיר כאן: {{2}}"}
        ]
    }
}
```

### 11.2 Telegram Bot (Development & Testing)

Use Telegram for local development and testing:

```python
TELEGRAM_CONFIG = {
    "bot_token": "BOT_TOKEN_HERE",
    "webhook_path": "/webhooks/telegram",
    "polling_mode": True,  # Use polling for local dev
    "features": {
        "commands": True,
        "inline_keyboards": True,
        "media_support": True
    }
}
```

#### Telegram Bot Setup

```python
from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, MessageHandler, filters

# Initialize bot
bot = Bot(token=TELEGRAM_CONFIG["bot_token"])
app = Application.builder().token(TELEGRAM_CONFIG["bot_token"]).build()

# Command handlers
async def start_command(update: Update, context):
    """Handle /start command - simulate new customer"""
    await update.message.reply_text(
        "🏋️ GymAI Test Bot\n\n"
        "Commands:\n"
        "/setcustomer <id> - Set customer ID\n"
        "/simulate <scenario> - Run test scenario\n"
        "/reset - Reset conversation\n\n"
        "Or just send a message to test the agent!"
    )

async def set_customer_command(update: Update, context):
    """Set customer ID for testing"""
    customer_id = context.args[0] if context.args else "test_customer_1"
    context.user_data["customer_id"] = customer_id
    await update.message.reply_text(f"✅ Customer ID set to: {customer_id}")

async def simulate_command(update: Update, context):
    """Simulate test scenarios"""
    scenario = context.args[0] if context.args else "absent_customer"
    
    scenarios = {
        "absent_customer": "Customer hasn't visited in 2 weeks",
        "payment_due": "Customer has overdue payment",
        "expiring_membership": "Membership expires in 7 days",
        "complaint": "Customer complaint scenario",
        "question": "FAQ question scenario"
    }
    
    if scenario in scenarios:
        # Trigger the scenario
        await trigger_test_scenario(update, context, scenario)
    else:
        await update.message.reply_text(
            f"Available scenarios:\n" + 
            "\n".join([f"• {k}: {v}" for k, v in scenarios.items()])
        )

async def handle_message(update: Update, context):
    """Handle regular messages - pass to agent"""
    customer_id = context.user_data.get("customer_id", "test_customer")
    message_text = update.message.text
    
    # Process through agent
    response = await process_customer_message(
        customer_id=customer_id,
        message=message_text,
        channel="telegram"
    )
    
    await update.message.reply_text(response.message)

# Register handlers
app.add_handler(CommandHandler("start", start_command))
app.add_handler(CommandHandler("setcustomer", set_customer_command))
app.add_handler(CommandHandler("simulate", simulate_command))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
```

#### Local Development with Telegram

```bash
# 1. Create a bot via @BotFather on Telegram
# 2. Get the bot token
# 3. Set environment variable
export TELEGRAM_BOT_TOKEN="your_bot_token"

# 4. Run in polling mode (no webhook needed for local dev)
python -m gym_agent.telegram_bot --polling

# 5. Open Telegram and message your bot to test
```

### 11.3 SMS Gateway (Backup)

Fallback channel for customers without WhatsApp:

```python
SMS_CONFIG = {
    "provider": "Twilio",  # or local Israeli provider
    "features": {
        "two_way": True,
        "unicode": True,
        "delivery_reports": True
    },
    "use_cases": [
        "whatsapp_fallback",
        "urgent_notifications",
        "payment_reminders"
    ]
}
```

### 11.4 Channel Router

```python
class ChannelRouter:
    """Route messages to appropriate channel"""
    
    async def send_message(
        self,
        customer: Customer,
        message: str,
        message_type: str = "text"
    ) -> SendResult:
        # Determine best channel
        channel = self.get_preferred_channel(customer)
        
        if channel == "whatsapp":
            return await self.whatsapp_client.send(customer.phone, message)
        elif channel == "telegram":
            return await self.telegram_client.send(customer.telegram_id, message)
        elif channel == "sms":
            return await self.sms_client.send(customer.phone, message)
        
    def get_preferred_channel(self, customer: Customer) -> str:
        """Get customer's preferred/available channel"""
        if customer.whatsapp_opted_in:
            return "whatsapp"
        elif customer.telegram_id:
            return "telegram"
        else:
            return "sms"
```

---

## 12. Code Examples

### 12.1 Main Agent Structure

```python
from dataclasses import dataclass
from pydantic import BaseModel, Field
from pydantic_ai import Agent, RunContext
from enum import Enum

class Intent(str, Enum):
    TIME_CONSTRAINT = "time_constraint"
    FINANCIAL_ISSUE = "financial_issue"
    LOW_MOTIVATION = "low_motivation"
    HEALTH_INJURY = "health_injury"
    POSITIVE = "positive"
    QUESTION = "question"
    COMPLAINT = "complaint"
    WANTS_HUMAN = "wants_human"
    UNKNOWN = "unknown"

@dataclass
class GymDependencies:
    customer_id: str
    gym_id: str
    crm: ArboxClient
    vector_db: AsyncPGVector
    redis: Redis
    gym_name: str

class AgentResponse(BaseModel):
    message: str = Field(description="Response message to customer")
    intent: Intent = Field(description="Detected customer intent")
    sentiment: float = Field(description="Sentiment score -1 to 1", ge=-1, le=1)
    escalate: bool = Field(default=False, description="Should escalate to human")
    escalation_reason: str | None = Field(default=None)
    action_taken: str | None = Field(default=None)
    follow_up_scheduled: bool = Field(default=False)

SYSTEM_PROMPT = """
You are a friendly customer service agent for {gym_name}.

CORE PRINCIPLES:
1. Be conversational and natural - NOT robotic
2. Keep messages SHORT (1-3 sentences max)
3. Listen and respond to what the customer actually says
4. Never be pushy or send multiple unanswered messages
5. Escalate to human when appropriate

INTENT HANDLING:
- Time issues: Offer flexible options (short classes, different hours)
- Money issues: Be empathetic, offer freeze or alternatives, escalate if needed
- Low motivation: Encourage gently, suggest variety
- Health issues: Show empathy, offer freeze, don't push
- Complaints: Apologize sincerely, escalate immediately
- Questions: Use knowledge base, admit if you don't know

TONE:
- Professional but warm
- Brief and respectful of their time
- Use emojis sparingly (max 1 per message)
- Hebrew should be natural/colloquial, not formal
"""

gym_agent = Agent(
    'openai:gpt-4o',
    deps_type=GymDependencies,
    output_type=AgentResponse,
    instructions=SYSTEM_PROMPT,
)

@gym_agent.instructions
async def add_customer_context(ctx: RunContext[GymDependencies]) -> str:
    """Add dynamic customer context to instructions"""
    customer = await ctx.deps.crm.get_customer(ctx.deps.customer_id)
    health_score = await get_health_score(ctx.deps.customer_id)
    
    return f"""
    Customer Context:
    - Name: {customer.first_name}
    - Member since: {customer.member_since}
    - Last visit: {customer.last_visit}
    - Health Score: {health_score}/100
    - Preferred classes: {customer.preferred_classes}
    - Membership expires: {customer.membership_end_date}
    """
```

### 12.2 RAG Search Tool

```python
@gym_agent.tool
async def search_gym_info(
    ctx: RunContext[GymDependencies],
    query: str
) -> str:
    """Search gym knowledge base for relevant information.
    
    Use this tool when the customer asks a question about:
    - Operating hours
    - Pricing and membership plans
    - Facilities and amenities
    - Class schedules
    - Policies (cancellation, freeze, etc.)
    - Location and parking
    
    Args:
        query: The customer's question or topic to search for
        
    Returns:
        Relevant information from the gym's knowledge base,
        or indication that info was not found.
    """
    results = await ctx.deps.vector_db.similarity_search(
        query=query,
        k=3,
        filter={"gym_id": ctx.deps.gym_id}
    )
    
    if not results or results[0].score < 0.7:
        return "Information not found in knowledge base. Consider escalating or asking for clarification."
    
    context = "\n\n".join([r.content for r in results])
    return f"Found relevant information:\n{context}"
```

### 12.3 Customer Data Tool

```python
@gym_agent.tool
async def get_customer_data(
    ctx: RunContext[GymDependencies],
    data_type: str
) -> str:
    """Get customer information from CRM.
    
    Args:
        data_type: Type of data to retrieve:
            - 'profile': Basic customer info
            - 'attendance': Recent attendance history
            - 'membership': Membership details and status
            - 'payments': Payment history and status
            
    Returns:
        Requested customer data formatted as string.
    """
    customer_id = ctx.deps.customer_id
    crm = ctx.deps.crm
    
    if data_type == "profile":
        customer = await crm.get_customer(customer_id)
        return f"Name: {customer.first_name} {customer.last_name}, Member since: {customer.member_since}"
    
    elif data_type == "attendance":
        visits = await crm.get_recent_visits(customer_id, days=30)
        return f"Visits in last 30 days: {len(visits)}, Last visit: {visits[0].date if visits else 'N/A'}"
    
    elif data_type == "membership":
        membership = await crm.get_membership(customer_id)
        return f"Plan: {membership.plan_name}, Expires: {membership.end_date}, Status: {membership.status}"
    
    elif data_type == "payments":
        payments = await crm.get_payment_status(customer_id)
        return f"Balance: {payments.balance}, Last payment: {payments.last_payment_date}"
    
    return "Unknown data type requested"
```

### 12.4 Escalation Tool

```python
@gym_agent.tool
async def escalate_to_human(
    ctx: RunContext[GymDependencies],
    reason: str,
    priority: str = "normal",
    notes: str = ""
) -> str:
    """Escalate conversation to human representative.
    
    Use this when:
    - Customer explicitly asks to speak with a person
    - Complaint or serious dissatisfaction
    - Complex financial issues requiring negotiation
    - Health/injury situations
    - 3+ messages without resolution
    - Information not available to answer their question
    
    Args:
        reason: Why escalating (complaint, request, complex_issue, etc.)
        priority: 'low', 'normal', 'high', 'urgent'
        notes: Additional context for the human rep
        
    Returns:
        Confirmation of escalation.
    """
    escalation = await create_escalation(
        conversation_id=ctx.deps.conversation_id,
        customer_id=ctx.deps.customer_id,
        reason=reason,
        priority=priority,
        notes=notes
    )
    
    # Notify staff
    await notify_staff_of_escalation(escalation)
    
    return f"Escalation created (ID: {escalation.id}). Human rep will be notified."
```

### 12.5 FastAPI Webhook Handler

```python
from fastapi import FastAPI, Request, HTTPException, BackgroundTasks
from pydantic import BaseModel

app = FastAPI(title="GymAI Agent API")

class WebhookPayload(BaseModel):
    message_id: str
    from_number: str
    message_text: str
    timestamp: str

@app.post("/webhooks/whatsapp")
async def whatsapp_webhook(
    request: Request,
    background_tasks: BackgroundTasks
):
    # Verify webhook signature
    signature = request.headers.get("X-Hub-Signature-256")
    if not verify_webhook_signature(await request.body(), signature):
        raise HTTPException(status_code=401, detail="Invalid signature")
    
    payload = await request.json()
    
    # Parse WhatsApp webhook format
    message = parse_whatsapp_webhook(payload)
    if not message:
        return {"status": "ok"}  # Acknowledge non-message webhooks
    
    # Process in background
    background_tasks.add_task(
        process_incoming_message,
        phone=message.from_number,
        text=message.text,
        channel="whatsapp"
    )
    
    return {"status": "ok"}

@app.post("/webhooks/telegram")
async def telegram_webhook(
    request: Request,
    background_tasks: BackgroundTasks
):
    payload = await request.json()
    
    # Parse Telegram update
    if "message" in payload:
        message = payload["message"]
        chat_id = message["chat"]["id"]
        text = message.get("text", "")
        
        background_tasks.add_task(
            process_incoming_message,
            chat_id=chat_id,
            text=text,
            channel="telegram"
        )
    
    return {"status": "ok"}

async def process_incoming_message(
    text: str,
    channel: str,
    phone: str = None,
    chat_id: int = None
):
    """Process incoming message through agent"""
    
    # Get or create customer
    if channel == "whatsapp":
        customer = await get_customer_by_phone(phone)
    else:
        customer = await get_customer_by_telegram(chat_id)
    
    if not customer:
        # Handle unknown customer
        await send_unknown_customer_response(channel, phone or chat_id)
        return
    
    # Get or create conversation
    conversation = await get_or_create_conversation(customer.id, channel)
    
    # Save incoming message
    await save_message(
        conversation_id=conversation.id,
        direction="inbound",
        content=text
    )
    
    # Process through agent
    deps = GymDependencies(
        customer_id=customer.id,
        gym_id=customer.gym_id,
        crm=arbox_client,
        vector_db=pgvector_client,
        redis=redis_client,
        gym_name=customer.gym_name
    )
    
    result = await gym_agent.run(text, deps=deps)
    
    # Save and send response
    await save_message(
        conversation_id=conversation.id,
        direction="outbound",
        content=result.output.message,
        intent=result.output.intent,
        sentiment=result.output.sentiment
    )
    
    await send_message(
        channel=channel,
        recipient=phone or chat_id,
        message=result.output.message
    )
    
    # Handle escalation if needed
    if result.output.escalate:
        await handle_escalation(
            conversation_id=conversation.id,
            reason=result.output.escalation_reason
        )
    
    # Track analytics
    await track_event(
        event_type="conversation.message_received",
        customer_id=customer.id,
        conversation_id=conversation.id,
        properties={
            "intent": result.output.intent,
            "sentiment": result.output.sentiment,
            "escalated": result.output.escalate
        }
    )
```

---

## 13. Human Escalation

### 13.1 Escalation Triggers

Escalate to human representative when:

| Trigger | Priority | Notes |
|---------|----------|-------|
| Customer explicitly requests | High | Immediate, no resistance |
| Complaint detected | High | Apologize first, then escalate |
| Negative sentiment persists | Normal | After 2+ negative messages |
| Complex financial issue | Normal | Payment plans, disputes |
| Health/injury mentioned | Normal | Show empathy, offer help |
| 3 exchanges without progress | Normal | Agent can't resolve |
| Info not in knowledge base | Low | Pass question to team |

### 13.2 Escalation Response Templates

```python
ESCALATION_RESPONSES = {
    "customer_request": 
        "Of course! I'm connecting you with someone from our team. They'll be in touch shortly.",
    
    "complaint":
        "I'm really sorry about this experience. I'm getting one of our team members to help you directly. They'll reach out soon.",
    
    "complex_issue":
        "This needs a bit more attention than I can give it. Let me pass this to someone who can help properly.",
    
    "info_not_found":
        "I don't have that info on hand. I'm passing your question to the team and someone will get back to you today."
}
```

### 13.3 Escalation Handoff

```python
async def handle_escalation(
    conversation_id: str,
    reason: str,
    priority: str = "normal"
):
    """Handle escalation to human rep"""
    
    # Get conversation summary
    messages = await get_conversation_messages(conversation_id)
    summary = await summarize_conversation(messages)
    
    # Create escalation record
    escalation = await db.execute("""
        INSERT INTO escalations 
        (conversation_id, reason, priority, notes)
        VALUES ($1, $2, $3, $4)
        RETURNING *
    """, conversation_id, reason, priority, summary)
    
    # Notify appropriate staff
    if priority == "urgent":
        await send_urgent_notification(escalation)
    else:
        await add_to_escalation_queue(escalation)
    
    # Update conversation status
    await db.execute("""
        UPDATE conversations 
        SET status = 'escalated', escalated_at = NOW()
        WHERE id = $1
    """, conversation_id)
    
    return escalation
```

---

## 14. Message Examples

### Style Guidelines

Messages should sound **natural and human** - like they were written by a real customer service rep, not a robot.

```
❌ ROBOTIC:
"Dear valued customer, we have observed that your attendance frequency 
has diminished over the past 14 days. We would like to inquire as to 
whether there are any issues we can assist you with at this time."

✅ HUMAN:
"Hey Mike, everything okay? Haven't seen you lately."
```

### 14.1 Absence Check-in

```
Hey Daniel, everything okay? Haven't seen you this week. 
If something came up or you need help with anything, I'm here.
```

### 14.2 Frequency Drop

```
What's up Michelle? Noticed you've been coming in less lately. 
Anything we can help with? Maybe the schedule doesn't work or 
you want to try different classes?
```

### 14.3 Subscription Expiring

```
Hey Alex, just a heads up - your membership ends in two weeks. 
Want me to set up the renewal? Happy to answer any questions about the plans.
```

### 14.4 Payment Reminder

```
Hey Rachel, there's an open payment from last month. 
You can take care of it easily here: [link]. Let me know if you need anything.
```

### 14.5 Milestone Celebration

```
Joe! 100 workouts completed today. That's seriously impressive, nice work 💪
```

### 14.6 FAQ Answer (RAG)

**Customer:** What time do you close on Saturday?

```
We're open 8am-2pm on Saturdays. Anything else?
```

### 14.7 Info Not Found

**Customer:** Do you have scuba diving lessons?

```
Not sure about that one. Let me pass this to the team and 
someone will get back to you today.
```

### 14.8 Handling Objections

**Customer:** I don't have time anymore

```
Totally get it, life gets busy. We actually have 30-minute express 
classes at 6am and 8pm if that helps. Want me to send you the schedule?
```

**Customer:** It's too expensive

```
I hear you. We do have some options - you could freeze for a bit, 
or there might be a different plan that works better. Want me to 
have someone from the team reach out to go over the options?
```

---

## 15. Success Metrics (KPIs)

### 15.1 Primary Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Churn reduction | 15%+ | Compare to previous period |
| Response rate | 40%+ | Responses / Messages sent |
| Auto-resolved questions | 80%+ | Resolved / Total questions |
| Staff time saved | 10+ hrs/week | Staff reporting |
| Collection success | 70%+ | Paid / Reminders sent |
| Customer satisfaction | 4.5/5 | Post-conversation survey |

### 15.2 Secondary Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Avg response time | < 5 min | Time to first response |
| Escalation rate | < 15% | Escalated / Total conversations |
| Intent accuracy | > 90% | Manual review sample |
| RAG accuracy | > 85% | Correct answers / Questions |
| Conversation length | 3-5 messages | Messages per resolution |
| Win-back rate | 20%+ | Returned / Churned customers |

---

## 16. Development Roadmap

### Phase 1 - MVP (Weeks 1-4)

- [ ] Set up Pydantic AI infrastructure
- [ ] Basic Orchestrator Agent
- [ ] RAG Agent with single PDF
- [ ] PostgreSQL + pgvector setup
- [ ] Basic Arbox integration (read-only)
- [ ] Telegram bot for testing
- [ ] Basic conversation flow

### Phase 2 - Core Features (Weeks 5-8)

- [ ] Health Score calculation
- [ ] Retention Agent with conversational flow
- [ ] Advanced intent detection
- [ ] Human escalation workflow
- [ ] WhatsApp Business API integration
- [ ] Redis caching layer
- [ ] Basic admin dashboard
- [ ] Analytics event tracking

### Phase 3 - Enhancement (Weeks 9-12)

- [ ] Billing Agent
- [ ] Marketing Agent
- [ ] Multi-turn conversation memory
- [ ] A/B testing framework
- [ ] Advanced analytics dashboard
- [ ] Leap and Fizikal CRM support
- [ ] SMS fallback channel

### Phase 4 - Scale (Weeks 13-16)

- [ ] ML-based churn prediction
- [ ] Multi-gym support
- [ ] White-label capabilities
- [ ] Advanced reporting
- [ ] API for third-party integrations
- [ ] Performance optimization

---

## Quick Start

### Prerequisites

```bash
# Python 3.11+
python --version

# PostgreSQL with pgvector
docker run -d \
  --name gym-ai-postgres \
  -e POSTGRES_PASSWORD=postgres \
  -p 5432:5432 \
  pgvector/pgvector:pg16

# Redis
docker run -d \
  --name gym-ai-redis \
  -p 6379:6379 \
  redis:alpine
```

### Installation

```bash
# Clone repository
git clone https://github.com/your-org/gym-ai-agent.git
cd gym-ai-agent

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -e ".[dev]"

# Set up environment variables
cp .env.example .env
# Edit .env with your API keys

# Run database migrations
alembic upgrade head

# Start the application
uvicorn gym_agent.main:app --reload
```

### Testing with Telegram

```bash
# Set Telegram bot token
export TELEGRAM_BOT_TOKEN="your_token_here"

# Run Telegram bot in polling mode
python -m gym_agent.telegram_bot --polling

# Open Telegram and message your bot!
```

---

## Environment Variables

```bash
# LLM
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...

# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/gym_ai
REDIS_URL=redis://localhost:6379

# CRM
ARBOX_API_KEY=...
ARBOX_API_SECRET=...

# Messaging
WHATSAPP_ACCESS_TOKEN=...
WHATSAPP_PHONE_NUMBER_ID=...
WHATSAPP_VERIFY_TOKEN=...
TELEGRAM_BOT_TOKEN=...

# Security
JWT_SECRET_KEY=...
WEBHOOK_SECRET=...

# Monitoring
LOGFIRE_TOKEN=...
SENTRY_DSN=...
```

---

**Document Version:** 1.0  
**Last Updated:** December 2024  
**Framework:** Pydantic AI  
**Database:** PostgreSQL + pgvector  
**Cache:** Redis
