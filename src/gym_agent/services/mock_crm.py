"""
Mock CRM Service for GymAI Agent.

Provides realistic mock data for development and testing
without requiring actual CRM (Arbox) integration.
"""

from datetime import date, datetime, timedelta
from functools import lru_cache
from typing import Any
from uuid import UUID, uuid4
import random

from gym_agent.models.customer import (
    Customer,
    CustomerStatus,
    HealthScore,
    MembershipType,
)


class MockCRMService:
    """
    Mock CRM service simulating Arbox-like functionality.
    
    Provides:
    - Customer data lookup
    - Attendance records
    - Membership information
    - Visit history
    """
    
    def __init__(self):
        """Initialize with mock data."""
        self._customers: dict[UUID, Customer] = {}
        self._visits: dict[UUID, list[datetime]] = {}
        self._telegram_mapping: dict[int, UUID] = {}
        self._phone_mapping: dict[str, UUID] = {}
        
        # Generate initial mock customers
        self._generate_mock_customers()
    
    def _generate_mock_customers(self) -> None:
        """Generate diverse mock customers for testing."""
        
        mock_customers = [
            # Active, healthy customer
            {
                "first_name": "דניאל",
                "last_name": "כהן",
                "phone": "+972501234567",
                "status": CustomerStatus.ACTIVE,
                "health_score": 85,
                "membership_type": MembershipType.YEARLY,
                "total_visits": 120,
                "days_since_visit": 2,
                "preferred_classes": ["CrossFit", "HIIT"],
            },
            # At-risk customer (hasn't visited in 2 weeks)
            {
                "first_name": "שרה",
                "last_name": "לוי",
                "phone": "+972502345678",
                "status": CustomerStatus.AT_RISK,
                "health_score": 45,
                "membership_type": MembershipType.MONTHLY,
                "total_visits": 24,
                "days_since_visit": 14,
                "preferred_classes": ["Yoga", "Pilates"],
            },
            # Inactive customer
            {
                "first_name": "מיכאל",
                "last_name": "ברק",
                "phone": "+972503456789",
                "status": CustomerStatus.INACTIVE,
                "health_score": 25,
                "membership_type": MembershipType.MONTHLY,
                "total_visits": 8,
                "days_since_visit": 30,
                "preferred_classes": ["Spinning"],
            },
            # New member (trial)
            {
                "first_name": "רחל",
                "last_name": "אברהם",
                "phone": "+972504567890",
                "status": CustomerStatus.ACTIVE,
                "health_score": 70,
                "membership_type": MembershipType.TRIAL,
                "total_visits": 3,
                "days_since_visit": 1,
                "preferred_classes": [],
            },
            # Customer with expiring membership
            {
                "first_name": "יוסי",
                "last_name": "גולן",
                "phone": "+972505678901",
                "status": CustomerStatus.ACTIVE,
                "health_score": 60,
                "membership_type": MembershipType.QUARTERLY,
                "total_visits": 25,
                "days_since_visit": 5,
                "days_until_expiry": 7,
                "preferred_classes": ["Kickboxing", "TRX"],
            },
            # English-speaking customer
            {
                "first_name": "John",
                "last_name": "Smith",
                "phone": "+972506789012",
                "status": CustomerStatus.ACTIVE,
                "health_score": 75,
                "membership_type": MembershipType.MONTHLY,
                "total_visits": 15,
                "days_since_visit": 3,
                "preferred_classes": ["Weights", "Cardio"],
                "preferred_language": "en",
            },
        ]
        
        for i, data in enumerate(mock_customers):
            customer_id = uuid4()
            
            # Calculate dates
            days_since_visit = data.pop("days_since_visit", 0)
            days_until_expiry = data.pop("days_until_expiry", 90)
            preferred_language = data.pop("preferred_language", "he")
            preferred_classes = data.pop("preferred_classes", [])
            
            customer = Customer(
                id=customer_id,
                crm_id=f"ARBOX-{1000 + i}",
                phone=data["phone"],
                first_name=data["first_name"],
                last_name=data.get("last_name"),
                email=f"{data['first_name'].lower()}@example.com",
                membership_type=data["membership_type"],
                membership_start_date=date.today() - timedelta(days=180),
                membership_end_date=date.today() + timedelta(days=days_until_expiry),
                status=data["status"],
                health_score=data["health_score"],
                last_visit=datetime.now() - timedelta(days=days_since_visit) if days_since_visit else None,
                total_visits=data["total_visits"],
                preferred_classes=preferred_classes,
                preferred_language=preferred_language,
                telegram_id=1000000 + i,  # Mock telegram ID
            )
            
            self._customers[customer_id] = customer
            self._phone_mapping[customer.phone] = customer_id
            if customer.telegram_id:
                self._telegram_mapping[customer.telegram_id] = customer_id
            
            # Generate visit history
            self._generate_visit_history(customer_id, customer.total_visits)
    
    def _generate_visit_history(self, customer_id: UUID, total_visits: int) -> None:
        """Generate mock visit history for a customer."""
        visits = []
        for i in range(total_visits):
            # Distribute visits over the past 6 months
            days_ago = random.randint(1, 180)
            visit_time = datetime.now() - timedelta(days=days_ago)
            visits.append(visit_time)
        
        visits.sort(reverse=True)  # Most recent first
        self._visits[customer_id] = visits
    
    # ==================== Customer Lookup ====================
    
    async def get_customer(self, customer_id: UUID) -> Customer | None:
        """Get customer by ID."""
        return self._customers.get(customer_id)
    
    async def get_customer_by_phone(self, phone: str) -> Customer | None:
        """Get customer by phone number."""
        customer_id = self._phone_mapping.get(phone)
        if customer_id:
            return self._customers.get(customer_id)
        return None
    
    async def get_customer_by_telegram(self, telegram_id: int) -> Customer | None:
        """Get customer by Telegram ID."""
        customer_id = self._telegram_mapping.get(telegram_id)
        if customer_id:
            return self._customers.get(customer_id)
        return None
    
    async def search_customers(
        self,
        status: CustomerStatus | None = None,
        health_score_below: int | None = None,
    ) -> list[Customer]:
        """Search customers by criteria."""
        results = []
        for customer in self._customers.values():
            if status and customer.status != status:
                continue
            if health_score_below and customer.health_score >= health_score_below:
                continue
            results.append(customer)
        return results
    
    # ==================== Visit History ====================
    
    async def get_recent_visits(
        self,
        customer_id: UUID,
        days: int = 30,
    ) -> list[datetime]:
        """Get customer's recent visits."""
        all_visits = self._visits.get(customer_id, [])
        cutoff = datetime.now() - timedelta(days=days)
        return [v for v in all_visits if v > cutoff]
    
    async def get_visit_count(
        self,
        customer_id: UUID,
        days: int = 30,
    ) -> int:
        """Get count of visits in time period."""
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
        """Calculate health score for customer."""
        customer = await self.get_customer(customer_id)
        if not customer:
            return None
        
        # Frequency score (visits per week vs expected)
        recent_visits = await self.get_visit_count(customer_id, days=30)
        expected_visits = 12  # ~3 per week
        frequency_score = min(100, int((recent_visits / expected_visits) * 100))
        
        # Trend score (comparing recent to previous period)
        older_visits = await self.get_visit_count(customer_id, days=60)
        older_visits -= recent_visits  # Previous 30 days only
        if older_visits > 0:
            trend_ratio = recent_visits / max(1, older_visits)
            trend_score = min(100, int(trend_ratio * 50 + 25))
        else:
            trend_score = 50 if recent_visits > 0 else 0
        
        # Recency score
        days_since = customer.days_since_last_visit or 30
        if days_since <= 3:
            recency_score = 100
        elif days_since <= 7:
            recency_score = 80
        elif days_since <= 14:
            recency_score = 50
        elif days_since <= 30:
            recency_score = 25
        else:
            recency_score = 0
        
        # Expiry score
        days_until = customer.days_until_expiry or 0
        if days_until > 60:
            expiry_score = 100
        elif days_until > 30:
            expiry_score = 80
        elif days_until > 14:
            expiry_score = 50
        elif days_until > 0:
            expiry_score = 25
        else:
            expiry_score = 0
        
        return HealthScore.calculate(
            customer_id=customer_id,
            frequency_score=frequency_score,
            trend_score=trend_score,
            recency_score=recency_score,
            expiry_score=expiry_score,
        )
    
    # ==================== Test Utilities ====================
    
    def add_test_customer(
        self,
        telegram_id: int,
        first_name: str = "Test",
        **kwargs: Any,
    ) -> Customer:
        """Add a customer for testing purposes."""
        customer_id = uuid4()
        
        customer = Customer(
            id=customer_id,
            crm_id=f"TEST-{telegram_id}",
            phone=f"+9725{telegram_id % 100000000:08d}",
            first_name=first_name,
            telegram_id=telegram_id,
            **kwargs,
        )
        
        self._customers[customer_id] = customer
        self._telegram_mapping[telegram_id] = customer_id
        self._phone_mapping[customer.phone] = customer_id
        
        return customer
    
    def get_all_customers(self) -> list[Customer]:
        """Get all customers (for testing/admin)."""
        return list(self._customers.values())


@lru_cache
def get_mock_crm() -> MockCRMService:
    """Get cached mock CRM service instance."""
    return MockCRMService()
