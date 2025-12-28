# GymAI Agent

> Intelligent AI Agent for Gym Customer Communication & Retention

Built with **Pydantic AI** framework for type-safe, multi-agent AI systems.

## Features

- 🤖 **Multi-Agent Architecture**: Orchestrator, RAG, Retention, Billing, Marketing agents
- 💬 **Two-Way Conversations**: Not just automated messages - real conversations
- 📚 **RAG Knowledge Base**: Answer questions from gym's PDF documentation
- 📊 **Health Score System**: Detect at-risk customers before they churn
- 📱 **Multi-Channel**: Telegram (testing), WhatsApp (production), SMS (fallback)
- 🔄 **Multi-LLM Support**: OpenAI, Gemini, OpenRouter

## Quick Start

### Prerequisites

- Python 3.11+
- Supabase account (free tier works)
- Telegram Bot Token

### Installation

```bash
# Clone and enter directory
cd pullup

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -e ".[dev]"

# Set up environment
cp .env.example .env
# Edit .env with your API keys
```

### Run Telegram Bot (Development)

```bash
# Start the Telegram bot in polling mode
python -m gym_agent.channels.telegram_bot
```

### Run API Server

```bash
# Start FastAPI server
uvicorn gym_agent.main:app --reload
```

## Project Structure

```
pullup/
├── src/
│   └── gym_agent/
│       ├── __init__.py
│       ├── main.py              # FastAPI app entry point
│       ├── config.py            # Settings and configuration
│       ├── agents/              # Pydantic AI agents
│       │   ├── orchestrator.py  # Main routing agent
│       │   ├── rag.py           # Knowledge base agent
│       │   └── retention.py     # Customer retention agent
│       ├── channels/            # Communication channels
│       │   ├── telegram_bot.py  # Telegram integration
│       │   └── whatsapp.py      # WhatsApp (Phase 2)
│       ├── services/            # Business logic
│       │   ├── database.py      # Supabase client
│       │   ├── llm.py           # Multi-LLM provider
│       │   └── mock_crm.py      # Mock CRM data
│       ├── models/              # Pydantic models
│       │   ├── customer.py
│       │   ├── conversation.py
│       │   └── responses.py
│       └── utils/               # Utilities
│           └── pdf_processor.py
├── tests/                       # Test files
├── migrations/                  # Database migrations
├── docs/                        # Documentation
├── pyproject.toml              # Project configuration
├── .env.example                # Environment template
└── README.md
```

## Development

### Run Tests

```bash
pytest
```

### Code Quality

```bash
ruff check .
mypy src/
```

## Configuration

See [.env.example](.env.example) for all configuration options.

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `ENVIRONMENT` | dev, preprod, prod | Yes |
| `OPENAI_API_KEY` | OpenAI API key | Yes (if using OpenAI) |
| `GOOGLE_API_KEY` | Google Gemini API key | Optional |
| `SUPABASE_URL` | Supabase project URL | Yes |
| `TELEGRAM_BOT_TOKEN` | Telegram bot token | Yes |

## License

MIT
