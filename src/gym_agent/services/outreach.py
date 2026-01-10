"""
Proactive Outreach Service for GymAI Agent.

Handles automated customer outreach for:
- Absence check-ins (customers who haven't visited)
- Subscription expiry reminders
- Milestone celebrations
"""

from datetime import datetime
from typing import Any
from uuid import UUID

from gym_agent.models.customer import Customer, CustomerStatus
from gym_agent.models.conversation import Channel, MessageDirection
from gym_agent.services.mock_crm import MockCRMService, get_mock_crm
from gym_agent.services.database import DatabaseService, get_database
from gym_agent.config import settings


# Outreach message templates (Hebrew)
ABSENCE_CHECK_IN_TEMPLATES = [
    "היי {name}, הכל בסדר? לא ראינו אותך השבוע 💪",
    "היי {name}, מה קורה? חסר לנו פה 🏋️",
    "היי {name}, הכל טוב? לא היית אצלנו כבר כמה ימים",
]

SUBSCRIPTION_EXPIRY_TEMPLATES = [
    "היי {name}, רק להזכיר - המנוי שלך מסתיים בעוד {days} ימים. צריך עזרה עם החידוש?",
    "היי {name}, ראש השנה להזכיר שהמנוי שלך מסתיים ב-{date}. רוצה שנסדר את זה?",
]

MILESTONE_TEMPLATES = {
    10: "היי {name}! 🎉 סיימת 10 אימונים! כל הכבוד, ממשיכים!",
    50: "וואו {name}! 🏆 50 אימונים! אתה/את מכונה!",
    100: "{name}! 💯 100 אימונים! מדהים! אתה/את השראה לכולנו!",
    200: "{name}! 🌟 200 אימונים! אגדה חיה! 💪",
}


class ProactiveOutreachService:
    """
    Service for handling proactive customer outreach.
    
    Features:
    - Identify absent customers (7+ days)
    - Send personalized check-in messages
    - Track outreach attempts
    - Respect rate limits
    """
    
    def __init__(
        self,
        crm: MockCRMService | None = None,
        db: DatabaseService | None = None,
    ) -> None:
        """
        Initialize outreach service.
        
        Args:
            crm: CRM service for customer data
            db: Database service for tracking outreach
        """
        self.crm = crm or get_mock_crm()
        self.db = db or get_database()
        
        # Rate limiting settings
        self.max_unanswered_messages = settings.max_unanswered_messages
        self.followup_wait_hours = settings.followup_wait_hours
    
    async def get_absent_customers(
        self,
        days_absent: int = 7,
    ) -> list[Customer]:
        """
        Get customers who haven't visited in specified days.
        
        Args:
            days_absent: Minimum days since last visit (default: 7)
            
        Returns:
            List of absent customers eligible for outreach
        """
        all_customers = self.crm.get_all_customers()
        absent_customers = []
        
        for customer in all_customers:
            # Check if customer is active
            if customer.status not in [CustomerStatus.ACTIVE, CustomerStatus.AT_RISK]:
                continue
            
            # Check days since visit
            days_since = customer.days_since_last_visit
            if days_since is None or days_since < days_absent:
                continue
            
            # Check if we haven't sent too many unanswered messages
            conversation = await self.db.get_active_conversation(
                customer_id=customer.id,
                channel=Channel.TELEGRAM,
            )
            
            if conversation:
                # Skip if we've sent max unanswered messages
                if conversation.unanswered_count >= self.max_unanswered_messages:
                    continue
                
                # Skip if we sent a message recently
                if conversation.last_message_at:
                    hours_since = (datetime.now() - conversation.last_message_at).total_seconds() / 3600
                    if hours_since < self.followup_wait_hours:
                        continue
            
            absent_customers.append(customer)
        
        return absent_customers
    
    async def get_expiring_subscriptions(
        self,
        days_until_expiry: int = 14,
    ) -> list[Customer]:
        """
        Get customers with subscriptions expiring soon.
        
        Args:
            days_until_expiry: Days until expiry threshold (default: 14)
            
        Returns:
            List of customers with expiring subscriptions
        """
        all_customers = self.crm.get_all_customers()
        expiring = []
        
        for customer in all_customers:
            days_left = customer.days_until_expiry
            if days_left is not None and 0 < days_left <= days_until_expiry:
                expiring.append(customer)
        
        return expiring
    
    def generate_absence_message(self, customer: Customer) -> str:
        """
        Generate a personalized absence check-in message.
        
        Args:
            customer: Customer to message
            
        Returns:
            Personalized message string
        """
        import random
        template = random.choice(ABSENCE_CHECK_IN_TEMPLATES)
        return template.format(name=customer.first_name)
    
    def generate_expiry_message(self, customer: Customer) -> str:
        """
        Generate a subscription expiry reminder message.
        
        Args:
            customer: Customer to message
            
        Returns:
            Personalized message string
        """
        import random
        template = random.choice(SUBSCRIPTION_EXPIRY_TEMPLATES)
        
        days_left = customer.days_until_expiry or 0
        expiry_date = customer.membership_end_date
        
        return template.format(
            name=customer.first_name,
            days=days_left,
            date=expiry_date.strftime("%d/%m") if expiry_date else "בקרוב",
        )
    
    def generate_milestone_message(
        self,
        customer: Customer,
        milestone: int,
    ) -> str | None:
        """
        Generate a milestone celebration message.
        
        Args:
            customer: Customer to celebrate
            milestone: Milestone number (10, 50, 100, 200)
            
        Returns:
            Personalized message string or None if not a valid milestone
        """
        template = MILESTONE_TEMPLATES.get(milestone)
        if not template:
            return None
        return template.format(name=customer.first_name)
    
    async def send_absence_check_ins(
        self,
        days_absent: int = 7,
        dry_run: bool = False,
    ) -> list[dict[str, Any]]:
        """
        Send absence check-in messages to eligible customers.
        
        Args:
            days_absent: Minimum days since last visit
            dry_run: If True, generate but don't send messages
            
        Returns:
            List of outreach results
        """
        customers = await self.get_absent_customers(days_absent)
        results = []
        
        for customer in customers:
            message = self.generate_absence_message(customer)
            
            result = {
                "customer_id": str(customer.id),
                "customer_name": customer.full_name,
                "days_absent": customer.days_since_last_visit,
                "message": message,
                "sent": False,
            }
            
            if not dry_run:
                # Get or create conversation
                conversation = await self.db.get_or_create_conversation(
                    customer_id=customer.id,
                    channel=Channel.TELEGRAM,
                )
                
                # Store outgoing message
                await self.db.add_message(
                    conversation_id=conversation.id,
                    direction=MessageDirection.OUTBOUND,
                    content=message,
                    agent_type="proactive_outreach",
                    metadata={"outreach_type": "absence_check_in"},
                )
                
                # Track event
                await self.db.track_event(
                    event_type="retention.outreach_sent",
                    customer_id=customer.id,
                    conversation_id=conversation.id,
                    properties={
                        "outreach_type": "absence_check_in",
                        "days_absent": customer.days_since_last_visit,
                    },
                )
                
                result["sent"] = True
                print(f"📤 Sent check-in to {customer.full_name}: {message}")
            
            results.append(result)
        
        return results
    
    async def send_subscription_reminders(
        self,
        days_until_expiry: int = 14,
        dry_run: bool = False,
    ) -> list[dict[str, Any]]:
        """
        Send subscription expiry reminders to eligible customers.
        
        Args:
            days_until_expiry: Days threshold for expiry
            dry_run: If True, generate but don't send messages
            
        Returns:
            List of outreach results
        """
        customers = await self.get_expiring_subscriptions(days_until_expiry)
        results = []
        
        for customer in customers:
            message = self.generate_expiry_message(customer)
            
            result = {
                "customer_id": str(customer.id),
                "customer_name": customer.full_name,
                "days_until_expiry": customer.days_until_expiry,
                "message": message,
                "sent": False,
            }
            
            if not dry_run:
                conversation = await self.db.get_or_create_conversation(
                    customer_id=customer.id,
                    channel=Channel.TELEGRAM,
                )
                
                await self.db.add_message(
                    conversation_id=conversation.id,
                    direction=MessageDirection.OUTBOUND,
                    content=message,
                    agent_type="proactive_outreach",
                    metadata={"outreach_type": "subscription_reminder"},
                )
                
                await self.db.track_event(
                    event_type="retention.outreach_sent",
                    customer_id=customer.id,
                    conversation_id=conversation.id,
                    properties={
                        "outreach_type": "subscription_reminder",
                        "days_until_expiry": customer.days_until_expiry,
                    },
                )
                
                result["sent"] = True
                print(f"📤 Sent expiry reminder to {customer.full_name}: {message}")
            
            results.append(result)
        
        return results
    
    def get_milestone_for_visits(self, total_visits: int) -> int | None:
        """
        Get the highest milestone reached for a given visit count.
        
        Args:
            total_visits: Customer's total visit count
            
        Returns:
            Milestone number (10, 50, 100, 200) or None
        """
        milestones = sorted(MILESTONE_TEMPLATES.keys(), reverse=True)
        for milestone in milestones:
            if total_visits >= milestone:
                return milestone
        return None
    
    async def get_milestone_candidates(self) -> list[tuple[Customer, int]]:
        """
        Get customers who have reached new milestones.
        
        Returns:
            List of (customer, milestone) tuples
        """
        all_customers = self.crm.get_all_customers()
        candidates = []
        
        for customer in all_customers:
            if customer.status != CustomerStatus.ACTIVE:
                continue
            
            total = customer.total_visits
            milestone = self.get_milestone_for_visits(total)
            
            if milestone is None:
                continue
            
            # Check if we already celebrated this milestone
            already_sent = await self._milestone_already_sent(customer.id, milestone)
            if already_sent:
                continue
            
            candidates.append((customer, milestone))
        
        return candidates
    
    async def _milestone_already_sent(self, customer_id: UUID, milestone: int) -> bool:
        """Check if milestone celebration was already sent."""
        # Check analytics events for this milestone
        event = await self.db._analytics_events.find_one({
            "customer_id": str(customer_id),
            "event_type": "retention.milestone_celebration",
            "properties.milestone": milestone,
        })
        return event is not None
    
    async def send_milestone_celebrations(
        self,
        dry_run: bool = False,
    ) -> list[dict[str, Any]]:
        """
        Send milestone celebration messages to eligible customers.
        
        Args:
            dry_run: If True, generate but don't send messages
            
        Returns:
            List of celebration results
        """
        candidates = await self.get_milestone_candidates()
        results = []
        
        for customer, milestone in candidates:
            message = self.generate_milestone_message(customer, milestone)
            if not message:
                continue
            
            result = {
                "customer_id": str(customer.id),
                "customer_name": customer.full_name,
                "milestone": milestone,
                "total_visits": customer.total_visits,
                "message": message,
                "sent": False,
            }
            
            if not dry_run:
                conversation = await self.db.get_or_create_conversation(
                    customer_id=customer.id,
                    channel=Channel.TELEGRAM,
                )
                
                await self.db.add_message(
                    conversation_id=conversation.id,
                    direction=MessageDirection.OUTBOUND,
                    content=message,
                    agent_type="proactive_outreach",
                    metadata={
                        "outreach_type": "milestone_celebration",
                        "milestone": milestone,
                    },
                )
                
                await self.db.track_event(
                    event_type="retention.milestone_celebration",
                    customer_id=customer.id,
                    conversation_id=conversation.id,
                    properties={
                        "milestone": milestone,
                        "total_visits": customer.total_visits,
                    },
                )
                
                result["sent"] = True
                print(f"🎉 Sent milestone to {customer.full_name}: {message}")
            
            results.append(result)
        
        return results

async def run_absence_check_in(days: int = 7, dry_run: bool = False) -> None:
    """CLI helper to run absence check-in batch."""
    service = ProactiveOutreachService()
    
    print(f"\n🔍 Looking for customers absent for {days}+ days...")
    results = await service.send_absence_check_ins(days_absent=days, dry_run=dry_run)
    
    if not results:
        print("✅ No customers need absence check-in")
    else:
        print(f"\n📊 Results: {len(results)} customers")
        for r in results:
            status = "✅ Sent" if r["sent"] else "⏳ Would send (dry run)"
            print(f"  {status}: {r['customer_name']} ({r['days_absent']} days)")


async def run_subscription_reminders(days: int = 14, dry_run: bool = False) -> None:
    """CLI helper to run subscription reminder batch."""
    service = ProactiveOutreachService()
    
    print(f"\n🔍 Looking for subscriptions expiring in {days} days...")
    results = await service.send_subscription_reminders(days_until_expiry=days, dry_run=dry_run)
    
    if not results:
        print("✅ No subscriptions expiring soon")
    else:
        print(f"\n📊 Results: {len(results)} customers")
        for r in results:
            status = "✅ Sent" if r["sent"] else "⏳ Would send (dry run)"
            print(f"  {status}: {r['customer_name']} (expires in {r['days_until_expiry']} days)")


async def run_milestone_celebrations(dry_run: bool = False) -> None:
    """CLI helper to run milestone celebration batch."""
    service = ProactiveOutreachService()
    
    print("\n🔍 Looking for milestone achievements...")
    results = await service.send_milestone_celebrations(dry_run=dry_run)
    
    if not results:
        print("✅ No new milestones reached")
    else:
        print(f"\n📊 Results: {len(results)} milestones")
        for r in results:
            status = "✅ Sent" if r["sent"] else "⏳ Would send (dry run)"
            print(f"  {status}: {r['customer_name']} - {r['milestone']} workouts!")


# Export
__all__ = [
    "ProactiveOutreachService",
    "run_absence_check_in",
    "run_subscription_reminders",
    "run_milestone_celebrations",
    "MILESTONE_TEMPLATES",
]

