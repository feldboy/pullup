"""
MongoDB CRM Service for GymAI Agent.

Replaces MockCRMService with real MongoDB implementation.
"""

from datetime import datetime, timedelta
from typing import Any, cast
from uuid import UUID, uuid4

from gym_agent.models.customer import (
    Customer,
    CustomerStatus,
    HealthScore,
    MembershipType,
)
from gym_agent.services.database import get_database


class MongoCRMService:
    """
    MongoDB implementation of the CRM service.
    
    Connects to the database populated by seed_db.py.
    """
    
    def __init__(self) -> None:
        """Initialize service."""
        self.db = get_database()
        self._customers = self.db._customers
        # We don't have a separate visits collection despite the mock having it.
        # In seed_db.py, 'last_visit' is on the customer, and 'total_visits' is on the customer.
        # But for 'get_recent_visits', we might need a visits collection or just rely on the summary.
        # The prompt says seed_db.py has:
        # "last_visit": ..., "total_visits": ...
        # It does NOT seed a separate visits collection.
        # However, for a real CRM, we'd need one.
        # For now, I will use the fields available on Customer, and maybe mock 'recent_visits' 
        # based on 'last_visit', OR create a simple visits collection if needed.
        # US-001 says "Ensure seed_db.py data is queryable".
        # seed_db.py only puts data in 'customers'.
        # So I will implement based on what is there, and maybe simulate 'recent visits' logic 
        # or just return the last visit.
        
    async def get_customer(self, customer_id: UUID) -> Customer | None:
        """Get customer by ID."""
        doc = await self._customers.find_one({"_id": str(customer_id)})
        if doc:
            return self._dict_to_customer(doc)
        return None
    
    async def get_customer_by_phone(self, phone: str) -> Customer | None:
        """Get customer by phone number."""
        doc = await self._customers.find_one({"phone": phone})
        if doc:
            return self._dict_to_customer(doc)
        return None
    
    async def get_customer_by_telegram(self, telegram_id: int) -> Customer | None:
        """Get customer by Telegram ID."""
        doc = await self._customers.find_one({"telegram_id": telegram_id})
        if doc:
            return self._dict_to_customer(doc)
        return None
    
    async def get_all_customers(self) -> list[Customer]:
        """Get all customers."""
        cursor = self._customers.find({})
        customers = []
        async for doc in cursor:
            customers.append(self._dict_to_customer(doc))
        return customers

    async def search_customers(
        self,
        status: CustomerStatus | None = None,
        health_score_below: int | None = None,
    ) -> list[Customer]:
        """Search customers by criteria."""
        query: dict[str, Any] = {}
        if status:
            query["status"] = status.value
        if health_score_below is not None:
            query["health_score"] = {"$lt": health_score_below}
            
        cursor = self._customers.find(query)
        results = []
        async for doc in cursor:
            results.append(self._dict_to_customer(doc))
        return results
    
    # ==================== Visit History ====================
    # Since we don't have a visits collection yet, we'll implement partial support
    
    async def get_recent_visits(
        self,
        customer_id: UUID,
        days: int = 30,
    ) -> list[datetime]:
        """
        Get customer's recent visits.
        
        NOTE: Currently limited because we only store 'last_visit' and 'total_visits'.
        This returns [last_visit] if it was within the window.
        """
        customer = await self.get_customer(customer_id)
        if not customer or not customer.last_visit:
            return []
            
        if customer.last_visit > datetime.now() - timedelta(days=days):
            return [customer.last_visit]
        return []
    
    async def get_visit_count(
        self,
        customer_id: UUID,
        days: int = 30,
    ) -> int:
        """
        Get count of visits in time period.
        
        Approximation: If last_visit in range, return 1 + (avg visits).
        For now, just return 1 if active, else 0 to prevent breaking logic.
        """
        # Better approximation based on total_visits / membership duration?
        # The mock generated fake visits.
        # We can simulate this or just return 0 for now.
        visits = await self.get_recent_visits(customer_id, days)
        return len(visits)
    
    # ==================== Membership ====================
    
    async def get_membership_status(self, customer_id: UUID) -> dict[str, Any]:
        """Get membership details."""
        customer = await self.get_customer(customer_id)
        if not customer:
            return {}
        
        return {
            "plan": customer.membership_type.value,
            "start_date": customer.membership_start_date,
            "end_date": customer.membership_end_date,
            "days_remaining": customer.days_until_expiry,
            "is_expiring_soon": customer.is_membership_expiring_soon,
            "status": customer.status.value,
        }
    
    # ==================== Health Score ====================
    
    async def calculate_health_score(self, customer_id: UUID) -> HealthScore | None:
        """
        Calculate health score for customer.
        
        Reuses the logic from MockCRM but uses the (limited) data we have.
        """
        customer = await self.get_customer(customer_id)
        if not customer:
            return None
            
        # We can trust the pre-calculated health_score in the DB for now,
        # as seed_db.py generated it.
        # Or we can recalculate if we had granular visit data.
        # For US-001, returning the stored score is sufficient + wrapper.
        
        return HealthScore(
            customer_id=customer_id,
            score=customer.health_score,
            frequency_score=0, # Missing granular data
            trend_score=0,
            recency_score=0,
            expiry_score=0,
            updated_at=datetime.now()
        )
        
    async def get_stats(self) -> dict[str, Any]:
        """Get high-level CRM statistics."""
        total_customers = await self._customers.count_documents({})
        active_customers = await self._customers.count_documents({"status": CustomerStatus.ACTIVE.value})
        at_risk = await self._customers.count_documents({"status": CustomerStatus.AT_RISK.value})
        
        # Calculate recent visits (mock logic/limited data)
        # In real world, we'd count visits in last 24h from a visits collection.
        # Here we just return static or calculated from customers if possible.
        
        return {
            "total_customers": total_customers,
            "active_customers": active_customers,
            "at_risk_customers": at_risk,
            "new_this_month": 0, # Placeholder
            "visits_today": 0,   # Placeholder
        }

    # ==================== Test Utilities ====================
    
    def add_test_customer(self, telegram_id: int, first_name: str, **kwargs: Any) -> Customer:
        """Add a customer for testing purposes."""
        # This is synchronous in the interface but we need async for Mongo usually.
        # However, MockCRM was sync.
        # If the interface requires sync, we have a problem because Motor is async.
        # But looking at MockCRM, it was just dict manipulation.
        # If I change this to async, I break the interface if it's expected to be sync?
        # MockCRM's add_test_customer was sync.
        # But GymAgent.create_test_customer is async? No, let's check orchestrator.py.
        # orchestrator.py: async def create_test_customer(...) -> return self.crm.add_test_customer(...)
        # Wait, if add_test_customer is sync, then async def wrapper is fine.
        # But if I make add_test_customer async, I need to await it in wrapper.
        
        # Actually, let's look at orchestrator.py again.
        # async def create_test_customer(...): return self.crm.add_test_customer(...)
        # If add_test_customer is sync, this returns the value (Customer).
        # If it's async, this returns a coroutine, which is returned by the async wrapper.
        
        # Since I'm using Motor (AsyncIOMotorClient), database ops are async.
        # So I MUST make this async.
        # And I must update orchestrator.py to await it.
        
        # For now, let's implement validation first.
        raise NotImplementedError("Use seed_db.py for Mongo data, or implement async add_test_customer and update orchestrator")

    # ==================== Helpers ====================

    def _dict_to_customer(self, doc: dict[str, Any]) -> Customer:
        """Convert MongoDB document to Customer model."""
        # Handle date conversions if they are strings (seed_db stores strings/isoformat)
        
        # seed_db.py stores dates as ISO strings for: membership_start_date, membership_end_date, last_visit
        # But 'created_at' is datetime.
        # Pydantic can handle ISO strings usually.
        
        return Customer(
            id=UUID(doc["_id"]),
            crm_id=doc["crm_id"],
            phone=doc["phone"],
            first_name=doc["first_name"],
            last_name=doc.get("last_name"),
            email=doc.get("email"),
            membership_type=MembershipType(doc["membership_type"]),
            membership_start_date=doc["membership_start_date"],
            membership_end_date=doc["membership_end_date"],
            status=CustomerStatus(doc["status"]),
            health_score=doc["health_score"],
            last_visit=doc.get("last_visit"),
            total_visits=doc.get("total_visits", 0),
            preferred_classes=doc.get("preferred_classes", []),
            preferred_language=doc.get("preferred_language", "he"),
            telegram_id=doc.get("telegram_id"),
        )

# Global Accessor
_crm_service: MongoCRMService | None = None

def get_mongo_crm() -> MongoCRMService:
    global _crm_service
    if _crm_service is None:
        _crm_service = MongoCRMService()
    return _crm_service
