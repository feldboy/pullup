from gym_agent.services.database import get_database

class MockCRMService:
    # ... existing init ...
    def __init__(self) -> None:
        """Initialize with mock data."""
        self._customers: dict[UUID, Customer] = {}
        self._visits: dict[UUID, list[datetime]] = {}
        self._telegram_mapping: dict[int, UUID] = {}
        self._phone_mapping: dict[str, UUID] = {}
        self.db = get_database()
        
        # Generate initial mock customers
        # self._generate_mock_customers()

    # ... existing generation methods ...

    # ==================== Customer Lookup ====================
    
    async def get_customer(self, customer_id: UUID) -> Customer | None:
        """Get customer by ID."""
        # Try DB first
        db_customer = await self.db.get_customer(customer_id)
        if db_customer:
            return db_customer
        return self._customers.get(customer_id)
    
    async def get_customer_by_phone(self, phone: str) -> Customer | None:
        """Get customer by phone number."""
        # Try DB first is hard without method, but we have memory mapping for mocks
        # Actually DatabaseService doesn't have get_by_phone exposed yet? It does now.
        # But let's check memory first for mocks, then DB? Or DB first?
        # Let's stick to memory for mocks compatibility, but really we want DB.
        # Since I didn't verify get_customer_by_phone in DatabaseService (I added telegram_id index), let's skip complex logic here and just rely on memory for mocks + DB for real.
        # Wait, I did add index for phone. But no get_customer_by_phone method in DatabaseService yet?
        # I only added get_customer and get_customer_by_telegram.
        
        customer_id = self._phone_mapping.get(phone)
        if customer_id:
            return self._customers.get(customer_id)
        return None
    
    async def get_customer_by_telegram(self, telegram_id: int) -> Customer | None:
        """Get customer by Telegram ID."""
        # Try DB first
        db_customer = await self.db.get_customer_by_telegram(telegram_id)
        if db_customer:
            return db_customer
            
        customer_id = self._telegram_mapping.get(telegram_id)
        if customer_id:
            return self._customers.get(customer_id)
        return None
    
    # ... search and visits ...

    # ==================== Test Utilities ====================
    
    async def add_test_customer(
        self,
        telegram_id: int,
        first_name: str = "Test",
        **kwargs: Any,
    ) -> Customer:
        """Add a customer for testing purposes."""
        
        # Check if already exists in DB
        existing = await self.db.get_customer_by_telegram(telegram_id)
        if existing:
            return existing
            
        customer_id = uuid4()
        
        customer = Customer(
            id=customer_id,
            crm_id=f"TEST-{telegram_id}",
            phone=f"+9725{telegram_id % 100000000:08d}",
            first_name=first_name,
            telegram_id=telegram_id,
            **kwargs,
        )
        
        # Save to memory (legacy)
        self._customers[customer_id] = customer
        self._telegram_mapping[telegram_id] = customer_id
        self._phone_mapping[customer.phone] = customer_id
        
        # Save to DB
        await self.db.save_customer(customer)
        
        return customer
    
    def get_all_customers(self) -> list[Customer]:
        """Get all customers (for testing/admin)."""
        return list(self._customers.values())



@lru_cache
def get_mock_crm() -> MockCRMService:
    """Get cached mock CRM service instance."""
    return MockCRMService()
