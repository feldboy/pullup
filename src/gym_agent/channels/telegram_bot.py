"""
Telegram Bot for GymAI Agent.

Development and testing channel for the AI agent.
Run in polling mode for local development (no webhook needed).
"""

import asyncio
import logging
from typing import Any

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

from gym_agent.config import settings
from gym_agent.agents.orchestrator import GymAgent
from gym_agent.models.customer import CustomerStatus, MembershipType
from gym_agent.services.mock_crm import get_mock_crm

# Set up logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO if not settings.debug else logging.DEBUG,
)
logger = logging.getLogger(__name__)

# Initialize the AI agent
agent = GymAgent(
    gym_name="EloozFit - אילוזפיט",  # Real gym from Nordiya
    crm=get_mock_crm(),
)

# Store conversation history per user (in-memory for development)
conversation_history: dict[int, list[dict[str, str]]] = {}


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start command - Welcome message and help."""
    user = update.effective_user
    logger.info(f"Start command from user: {user.id} ({user.first_name})")
    
    welcome_message = (
        "🏋️ *GymAI Test Bot*\n\n"
        "שלום! אני העוזר הוירטואלי של הג'ים.\n"
        "Hi! I'm the gym's virtual assistant.\n\n"
        "*Commands:*\n"
        "/start - Show this help message\n"
        "/setcustomer <type> - Set test customer type\n"
        "/simulate <scenario> - Run test scenario\n"
        "/status - Show current customer status\n"
        "/reset - Reset conversation\n"
        "/customers - List all test customers\n\n"
        "*Customer Types:*\n"
        "• `active` - Active healthy customer\n"
        "• `atrisk` - At-risk customer (hasn't visited)\n"
        "• `inactive` - Inactive customer\n"
        "• `new` - New trial member\n"
        "• `expiring` - Membership expiring soon\n\n"
        "Or just send a message to test the agent!"
    )
    
    await update.message.reply_text(welcome_message, parse_mode="Markdown")
    
    # Try to find or create customer
    customer = await agent.get_customer_by_telegram(user.id)
    if not customer:
        # Create a default test customer for this user
        customer = await agent.create_test_customer(
            telegram_id=user.id,
            first_name=user.first_name or "User",
        )
        logger.info(f"Created new test customer for Telegram user {user.id}")


async def set_customer_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /setcustomer command - Switch to different test customer type."""
    user = update.effective_user
    
    if not context.args:
        await update.message.reply_text(
            "Usage: /setcustomer <type>\n"
            "Types: active, atrisk, inactive, new, expiring"
        )
        return
    
    customer_type = context.args[0].lower()
    crm = get_mock_crm()
    customers = crm.get_all_customers()
    
    # Map type to customer status
    type_mapping = {
        "active": CustomerStatus.ACTIVE,
        "atrisk": CustomerStatus.AT_RISK,
        "inactive": CustomerStatus.INACTIVE,
        "new": None,  # Special case: trial membership
        "expiring": None,  # Special case: check days until expiry
    }
    
    if customer_type not in type_mapping:
        await update.message.reply_text(f"Unknown type: {customer_type}")
        return
    
    # Find matching customer
    selected = None
    for c in customers:
        if customer_type == "new" and c.membership_type == MembershipType.TRIAL:
            selected = c
            break
        elif customer_type == "expiring" and c.is_membership_expiring_soon:
            selected = c
            break
        elif type_mapping.get(customer_type) and c.status == type_mapping[customer_type]:
            selected = c
            break
    
    if selected:
        # Update telegram mapping to this customer
        crm._telegram_mapping[user.id] = selected.id
        # Clear conversation history for fresh start
        conversation_history.pop(user.id, None)
        
        await update.message.reply_text(
            f"✅ Now acting as: *{selected.full_name}*\n"
            f"Status: {selected.status.value}\n"
            f"Health Score: {selected.health_score}/100\n"
            f"Last Visit: {selected.days_since_last_visit or 0} days ago",
            parse_mode="Markdown"
        )
    else:
        await update.message.reply_text(f"No customer found for type: {customer_type}")


async def simulate_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /simulate command - Trigger test scenarios."""
    user = update.effective_user
    
    scenarios = {
        "absent": "Simulate receiving absence check-in message",
        "payment": "Simulate payment reminder",
        "expiring": "Simulate membership expiring message",
        "complaint": "How to simulate a complaint scenario",
        "question": "How to test FAQ questions",
    }
    
    if not context.args:
        scenarios_text = "\n".join([f"• `{k}`: {v}" for k, v in scenarios.items()])
        await update.message.reply_text(
            f"*Available Scenarios:*\n{scenarios_text}\n\n"
            "Usage: /simulate <scenario>",
            parse_mode="Markdown"
        )
        return
    
    scenario = context.args[0].lower()
    
    if scenario == "absent":
        # Simulate agent-initiated absence check-in
        await update.message.reply_text(
            "היי, הכל בסדר? לא ראינו אותך השבוע 🤔"
        )
    elif scenario == "payment":
        await update.message.reply_text(
            "היי, יש תשלום פתוח מהחודש שעבר. "
            "אפשר להסדיר כאן: [link]. תודיע לי אם צריך עזרה."
        )
    elif scenario == "expiring":
        await update.message.reply_text(
            "היי, רק להזכיר - המנוי שלך מסתיים בעוד שבוע. "
            "רוצה שאסדר את החידוש?"
        )
    elif scenario == "complaint":
        await update.message.reply_text(
            "To test complaint handling, try sending:\n"
            "• 'השירות פה גרוע'\n"
            "• 'I'm not happy with the gym'\n"
            "• 'רוצה לדבר עם מנהל'"
        )
    elif scenario == "question":
        await update.message.reply_text(
            "To test FAQ handling, try asking:\n"
            "• 'מתי אתם פתוחים בשבת?'\n"
            "• 'What classes do you have?'\n"
            "• 'איך אפשר להקפיא מנוי?'"
        )
    else:
        await update.message.reply_text(f"Unknown scenario: {scenario}")


async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /status command - Show current customer status."""
    user = update.effective_user
    customer = await agent.get_customer_by_telegram(user.id)
    
    if not customer:
        await update.message.reply_text("No customer profile found. Send any message to create one.")
        return
    
    # Get health score
    crm = get_mock_crm()
    health_score = await crm.calculate_health_score(customer.id)
    
    status_text = (
        f"👤 *{customer.full_name}*\n\n"
        f"📱 Phone: `{customer.phone}`\n"
        f"📧 Email: {customer.email or 'N/A'}\n\n"
        f"🏋️ *Membership*\n"
        f"• Type: {customer.membership_type.value}\n"
        f"• Status: {customer.status.value}\n"
        f"• Expires: {customer.membership_end_date or 'N/A'}\n"
        f"• Days left: {customer.days_until_expiry or 'N/A'}\n\n"
        f"📊 *Activity*\n"
        f"• Last visit: {customer.days_since_last_visit or 0} days ago\n"
        f"• Total visits: {customer.total_visits}\n"
        f"• Preferred: {', '.join(customer.preferred_classes) or 'None'}\n\n"
        f"❤️ *Health Score*: {health_score.score if health_score else customer.health_score}/100\n"
    )
    
    if health_score:
        status_text += (
            f"  • Frequency: {health_score.frequency_score}%\n"
            f"  • Trend: {health_score.trend_score}%\n"
            f"  • Recency: {health_score.recency_score}%\n"
            f"  • Expiry: {health_score.expiry_score}%"
        )
    
    await update.message.reply_text(status_text, parse_mode="Markdown")


async def reset_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /reset command - Clear conversation history."""
    user = update.effective_user
    conversation_history.pop(user.id, None)
    await update.message.reply_text("✅ Conversation history cleared.")


async def customers_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /customers command - List all test customers."""
    crm = get_mock_crm()
    customers = crm.get_all_customers()
    
    lines = ["*Available Test Customers:*\n"]
    for c in customers:
        emoji = {
            CustomerStatus.ACTIVE: "🟢",
            CustomerStatus.AT_RISK: "🟡",
            CustomerStatus.INACTIVE: "🔴",
            CustomerStatus.CHURNED: "⚫",
            CustomerStatus.LEAD: "🔵",
        }.get(c.status, "⚪")
        
        lines.append(
            f"{emoji} *{c.full_name}* - {c.status.value}\n"
            f"   Health: {c.health_score}/100 | "
            f"Last: {c.days_since_last_visit or 0}d ago"
        )
    
    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle regular text messages - Pass to AI agent."""
    user = update.effective_user
    message_text = update.message.text
    
    logger.info(f"Message from {user.id} ({user.first_name}): {message_text}")
    
    # Get or create customer
    customer = await agent.get_customer_by_telegram(user.id)
    if not customer:
        customer = await agent.create_test_customer(
            telegram_id=user.id,
            first_name=user.first_name or "User",
        )
    
    # Get conversation history
    history = conversation_history.get(user.id, [])
    
    try:
        # Show typing indicator
        await update.message.chat.send_action("typing")
        
        # Process through AI agent
        response = await agent.process_message(
            customer=customer,
            message=message_text,
            conversation_history=history,
        )
        
        # Update conversation history
        history.append({"role": "user", "content": message_text})
        history.append({"role": "assistant", "content": response.message})
        conversation_history[user.id] = history[-10:]  # Keep last 10 messages
        
        # Log intent and sentiment
        logger.info(
            f"Response - Intent: {response.intent}, "
            f"Sentiment: {response.sentiment:.2f}, "
            f"Escalate: {response.escalate}"
        )
        
        # Send response
        await update.message.reply_text(response.message)
        
        # If escalation needed, notify
        if response.escalate:
            await update.message.reply_text(
                f"⚠️ [DEBUG] Escalation triggered: {response.escalation_reason}"
            )
    
    except Exception as e:
        logger.error(f"Error processing message: {e}", exc_info=True)
        await update.message.reply_text(
            "Sorry, I encountered an error. Please try again. 🙏"
        )


def main() -> None:
    """Run the Telegram bot in polling mode."""
    if not settings.telegram_bot_token:
        raise ValueError(
            "TELEGRAM_BOT_TOKEN not set. "
            "Please set it in your .env file."
        )
    
    logger.info("Starting GymAI Telegram Bot...")
    logger.info(f"Environment: {settings.environment.value}")
    logger.info(f"Debug mode: {settings.debug}")
    
    # Create application
    app = Application.builder().token(settings.telegram_bot_token).build()
    
    # Add handlers
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("setcustomer", set_customer_command))
    app.add_handler(CommandHandler("simulate", simulate_command))
    app.add_handler(CommandHandler("status", status_command))
    app.add_handler(CommandHandler("reset", reset_command))
    app.add_handler(CommandHandler("customers", customers_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Run bot
    logger.info("Bot is running in polling mode. Press Ctrl+C to stop.")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
