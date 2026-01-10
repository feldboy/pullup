
import asyncio
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from gym_agent.services.mongo_crm import get_mongo_crm

async def verify():
    print("Verifying MongoCRMService...")
    crm = get_mongo_crm()
    customers = await crm.get_all_customers()
    print(f"Found {len(customers)} customers.")
    
    if len(customers) > 0:
        c = customers[0]
        print(f"Sample customer: {c.full_name} ({c.id})")
        
        # Test methods
        print("Testing get_customer...")
        c2 = await crm.get_customer(c.id)
        assert c2 is not None and c2.id == c.id
        print("✅ get_customer passed")
        
        print("Testing health score...")
        hs = await crm.calculate_health_score(c.id)
        print(f"Health score: {hs.score if hs else 'None'}")
        
        print("✅ US-001 Verification Complete!")
    else:
        print("❌ No customers found. Did you run seed_db.py?")

if __name__ == "__main__":
    asyncio.run(verify())
