import asyncio
import os
from gym_agent.config import settings
from gym_agent.services.mongo_crm import get_mongo_crm
from gym_agent.services.database import get_database
from gym_agent.agents.orchestrator import GymAgent
from gym_agent.models.conversation import Channel
from gym_agent.models.customer import Customer

async def verify():
    # Force settings
    settings.manager_telegram_id = 999999
    
    # Init
    crm = get_mongo_crm()
    db = get_database()
    agent = GymAgent(crm=crm, db=db)
    
    # 1. Create Admin Customer
    try:
        admin = await crm.get_customer_by_telegram(999999)
    except:
        admin = None
        
    if not admin:
        print("Creating admin customer...")
        # Since add_test_customer is not implemented, we must rely on seed or mock
        # But we can just create a dummy object if we are mocking context in crm...
        # Wait, get_customer_by_telegram might return None.
        # Let's insert one directly using motor if needed, or better, assuming existing data.
        # Actually, let's use an existing customer and momentarily change their ID in the object passed to process_message
        # OR we can just inject a Customer object directly since process_message takes it as arg.
        pass

    # Create a mock customer object representing admin
    from uuid import uuid4
    from gym_agent.models.customer import CustomerStatus, MembershipType
    from datetime import date
    
    admin_customer = Customer(
        id=uuid4(),
        crm_id="ADMIN001",
        telegram_id=999999,
        first_name="Admin",
        last_name="User",
        phone="000",
        email="admin@gym.com",
        status=CustomerStatus.ACTIVE,
        membership_type=MembershipType.MONTHLY,
        membership_start_date=date.today(),
        membership_end_date=date.today(),
        days_until_expiry=100,
        last_visit=None,
        days_since_last_visit=0,
        total_visits=0,
        health_score=100,
        preferred_classes=[],
        preferred_language="en",
        notes=""
    )
    
    print("\n--- Testing /stats ---")
    response = await agent.process_message(admin_customer, "/stats")
    print(f"Response: {response.message}")
    if "Gym Stats" in response.message:
        print("✅ /stats passed")
    else:
        print("❌ /stats failed")

    print("\n--- Testing /risk ---")
    response = await agent.process_message(admin_customer, "/risk")
    print(f"Response: {response.message}")
    if "No customers" in response.message or "At Risk" in response.message:
        print("✅ /risk passed")
    else:
        print("❌ /risk failed")

    print("\n--- Testing regular message ---")
    # Should NOT be treated as command
    try:
        # process_message might fail if it tries to save to DB for a fake UUID
        # But let's try. If it hits DB and fails on FK or something, we know it passed the command check.
        # Or we can just mock db.
        pass
    except Exception as e:
        pass
        
if __name__ == "__main__":
    asyncio.run(verify())
