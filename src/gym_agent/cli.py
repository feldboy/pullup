#!/usr/bin/env python3
"""
CLI for GymAI Agent operations.

Commands:
- outreach: Run proactive outreach campaigns
- check: Check system status
"""

import asyncio
import argparse
import sys


def main() -> None:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="GymAI Agent CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Outreach command
    outreach_parser = subparsers.add_parser(
        "outreach",
        help="Run proactive outreach campaigns",
    )
    outreach_parser.add_argument(
        "type",
        choices=["absence", "expiry", "all"],
        help="Type of outreach to run",
    )
    outreach_parser.add_argument(
        "--days",
        type=int,
        default=7,
        help="Days threshold (default: 7 for absence, 14 for expiry)",
    )
    outreach_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview without sending messages",
    )
    
    # Check command
    check_parser = subparsers.add_parser(
        "check",
        help="Check system status",
    )
    check_parser.add_argument(
        "target",
        choices=["db", "customers", "conversations"],
        help="What to check",
    )
    
    args = parser.parse_args()
    
    if args.command == "outreach":
        asyncio.run(run_outreach(args))
    elif args.command == "check":
        asyncio.run(run_check(args))
    else:
        parser.print_help()
        sys.exit(1)


async def run_outreach(args: argparse.Namespace) -> None:
    """Run outreach campaigns."""
    from gym_agent.services.outreach import (
        run_absence_check_in,
        run_subscription_reminders,
    )
    
    print("🏋️ GymAI Agent - Proactive Outreach")
    print("=" * 40)
    
    if args.type in ["absence", "all"]:
        await run_absence_check_in(
            days=args.days,
            dry_run=args.dry_run,
        )
    
    if args.type in ["expiry", "all"]:
        expiry_days = 14 if args.type == "all" else args.days
        await run_subscription_reminders(
            days=expiry_days,
            dry_run=args.dry_run,
        )
    
    print("\n✅ Done!")


async def run_check(args: argparse.Namespace) -> None:
    """Run status checks."""
    print("🏋️ GymAI Agent - System Check")
    print("=" * 40)
    
    if args.target == "db":
        await check_database()
    elif args.target == "customers":
        await check_customers()
    elif args.target == "conversations":
        await check_conversations()


async def check_database() -> None:
    """Check database connectivity."""
    from gym_agent.services.database import get_database
    
    print("\n📊 Database Status:")
    try:
        db = get_database()
        await db.initialize()
        
        # Count documents
        conv_count = await db._conversations.count_documents({})
        msg_count = await db._messages.count_documents({})
        esc_count = await db._escalations.count_documents({})
        event_count = await db._analytics_events.count_documents({})
        
        print(f"  ✅ MongoDB connected")
        print(f"  📁 Conversations: {conv_count}")
        print(f"  💬 Messages: {msg_count}")
        print(f"  🚨 Escalations: {esc_count}")
        print(f"  📈 Events: {event_count}")
    except Exception as e:
        print(f"  ❌ Connection failed: {e}")


async def check_customers() -> None:
    """Check customer data."""
    from gym_agent.services.mock_crm import get_mock_crm
    
    print("\n👥 Customer Status:")
    crm = get_mock_crm()
    customers = crm.get_all_customers()
    
    print(f"  📊 Total customers: {len(customers)}")
    
    by_status: dict[str, int] = {}
    for c in customers:
        status = c.status.value
        by_status[status] = by_status.get(status, 0) + 1
    
    for status, count in by_status.items():
        print(f"  • {status}: {count}")
    
    # Health score distribution
    critical = sum(1 for c in customers if c.health_score < 50)
    at_risk = sum(1 for c in customers if 50 <= c.health_score < 70)
    healthy = sum(1 for c in customers if c.health_score >= 70)
    
    print(f"\n  🩺 Health Scores:")
    print(f"  • Critical (<50): {critical}")
    print(f"  • At-risk (50-70): {at_risk}")
    print(f"  • Healthy (>70): {healthy}")


async def check_conversations() -> None:
    """Check conversation status."""
    from gym_agent.services.database import get_database
    
    print("\n💬 Conversation Status:")
    try:
        db = get_database()
        
        # Get all conversations
        cursor = db._conversations.find({})
        conversations = await cursor.to_list(length=100)
        
        if not conversations:
            print("  📭 No conversations yet")
            return
        
        print(f"  📊 Total: {len(conversations)}")
        
        by_status: dict[str, int] = {}
        for c in conversations:
            status = c.get("status", "unknown")
            by_status[status] = by_status.get(status, 0) + 1
        
        for status, count in by_status.items():
            print(f"  • {status}: {count}")
    except Exception as e:
        print(f"  ❌ Error: {e}")


if __name__ == "__main__":
    main()
