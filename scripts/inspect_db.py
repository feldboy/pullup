
import asyncio
import sys
import os
from pprint import pprint

# Add src to path
sys.path.insert(0, os.path.join(os.getcwd(), 'src'))

from motor.motor_asyncio import AsyncIOMotorClient

async def inspect_db():
    print("🔌 Connecting to MongoDB...")
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    db = client["gym_ai"]
    
    print("\n📨 Recent Messages (Last 5):")
    cursor = db.messages.find().sort("created_at", -1).limit(5)
    async for msg in cursor:
        print("-" * 50)
        print(f"Time: {msg.get('created_at')}")
        print(f"Direction: {msg.get('direction')}")
        print(f"Intent: {msg.get('intent')}")
        print(f"Content: {msg.get('content')}")
        print(f"Agent: {msg.get('agent_type')}")
        if msg.get('metadata'):
            print(f"Metadata: {msg.get('metadata')}")

    print("\n🚨 Pending Escalations:")
    cursor = db.escalations.find({"status": "pending"})
    async for esc in cursor:
        pprint(esc)

if __name__ == "__main__":
    asyncio.run(inspect_db())
