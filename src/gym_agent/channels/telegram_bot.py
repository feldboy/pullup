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
from gym_agent.models.conversation import Channel
from gym_agent.models.customer import CustomerStatus, MembershipType
from gym_agent.services.mongo_crm import get_mongo_crm
from gym_agent.services.database import get_database

# Set up logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO if not settings.debug else logging.DEBUG,
)
logger = logging.getLogger(__name__)

# Initialize the AI agent
# We use a factory function or global init to ensure async setup usually, 
# but for the bot script we can pass them directly.
# Note: Mongo dependencies are async, but creating the service instance is sync.
agent = GymAgent(
    gym_name="EloozFit - אילוזפיט",
    crm=get_mongo_crm(),
    db=get_database(),
)

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start command - Welcome message and help."""
    user = update.effective_user
    logger.info(f"Start command from user: {user.id} ({user.first_name})")
    
    welcome_message = (
        "🏋️ *GymAI Bot (Mongo DB)*\n\n"
        "שלום! אני העוזר הוירטואלי של הג'ים.\n"
        "Hi! I'm the gym's virtual assistant.\n\n"
        "*Commands:*\n"
        "/start - Show this help message\n"
        "/simulate <scenario> - Run test scenario\n"
        "/status - Show current customer status\n"
        "/customers - List all active customers\n"
    )
    
    await update.message.reply_text(welcome_message, parse_mode="Markdown")
    
    # Try to find or create customer
    customer = await agent.get_customer_by_telegram(user.id)
    if not customer:
        try:
           # For Mongo, we might not have a free-for-all create_test_customer.
           # But let's try.
            customer = await agent.create_test_customer(
                telegram_id=user.id,
                first_name=user.first_name or "User",
            )
            logger.info(f"Created new test customer for Telegram user {user.id}")
        except NotImplementedError:
             await update.message.reply_text("Note: Auto-creation not supported in Mongo mode yet. Please seed DB.")


async def set_customer_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /setcustomer command - Disabled in Mongo mode."""
    await update.message.reply_text("⚠️ /setcustomer is only available in Mock mode.")

# ... simulate_command remains ...


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle regular text messages - Pass to AI agent."""
    user = update.effective_user
    message_text = update.message.text
    
    # --- MANAGER REPLY LOGIC ---
    if user.id == settings.manager_telegram_id and update.message.reply_to_message:
        # (Keep existing logic)
        reply_target = update.message.reply_to_message
        try:
            import re
            match = re.search(r"ID: <code>(\d+)</code>", reply_target.text or reply_target.caption or "")
            
            if match:
                target_user_id = int(match.group(1))
                await context.bot.send_message(
                    chat_id=target_user_id,
                    text=f"📞 <b>Support Reply:</b>\n{message_text}",
                    parse_mode="HTML"
                )
                await update.message.reply_text(f"✅ Reply sent to user {target_user_id}.")
                
                # We should log this outbound message to DB too!
                # Using agent.db directly needed here? Or just skip log for manual replies for now.
                return
            else:
                await update.message.reply_text("❌ Could not extract User ID.")
                return
        except Exception as e:
            logger.error(f"Error sending reply: {e}")
            await update.message.reply_text(f"❌ Error: {e}")
            return
            
    # --- REGULAR USER MESSAGE HANDLING ---
    
    logger.info(f"Message from {user.id} ({user.first_name}): {message_text}")
    
    # Get customer
    customer = await agent.get_customer_by_telegram(user.id)
    if not customer:
        # Auto-create if not exists
        try:
            customer = await agent.create_test_customer(
                telegram_id=user.id,
                first_name=user.first_name or "User",
            )
            logger.info(f"Auto-created customer for {user.id}")
        except Exception as e:
            logger.error(f"Failed to auto-create customer: {e}")
            await update.message.reply_text("⛔ Error creating profile. Please contact Support.")
            return
    
    try:
        # Show typing indicator
        await update.message.chat.send_action("typing")
        
        # Process through AI agent (History handled by DB)
        response = await agent.process_message(
            customer=customer,
            message=message_text,
            channel=Channel.TELEGRAM, 
        )
        
        # Log intent
        logger.info(
            f"Response - Intent: {response.intent}, "
            f"Escalate: {response.escalate}"
        )
        
        # Send response
        await update.message.reply_text(response.message)
        
        # If escalation needed, notify MANAGER
        if response.escalate:
            await update.message.reply_text(
                "👨‍💼 העברתי את הפרטים למנהל, הוא יחזור אליך בהקדם."
            )
            
            if settings.manager_telegram_id:
                alert_text = (
                    f"🚨 <b>ESCALATION REQUIRED</b>\n"
                    f"User: {user.first_name} (ID: <code>{user.id}</code>)\n"
                    f"Reason: {response.escalation_reason}\n\n"
                    f"<i>Last Message:</i>\n{message_text}\n\n"
                    f"<i>Reply to this message to answer the customer directly.</i>"
                )
                await context.bot.send_message(
                    chat_id=settings.manager_telegram_id,
                    text=alert_text,
                    parse_mode="HTML"
                )
    
    except Exception as e:
        logger.error(f"Error processing message: {e}", exc_info=True)
        await update.message.reply_text("Sorry, error occurred. checked logs.")


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
    # Add handlers
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("setcustomer", set_customer_command))
    # Note: Other commands disabled in MongoDB mode refactor
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Run bot
    logger.info("Bot is running in polling mode. Press Ctrl+C to stop.")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
