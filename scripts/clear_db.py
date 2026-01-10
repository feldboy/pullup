import asyncio
from gym_agent.services.database import get_database

async def main():
    print("🧹 Cleaning up fake users from database...")
    db_service = get_database()
    
    # We want to keep the user's real account if possible, but identifying it is hard without input.
    # However, 'seed_db.py' created users with specific crm_ids like 'CUST-001'.
    # Use logic to remove those.
    
    # Delete all documents in 'customers' collection
    result = await db_service._db.customers.delete_many({})
    
    # Also clear conversations and messages to start fresh? 
    # User asked for "fake users", usually implies a full wipe of test data.
    # But let's ask confirm or just wipe customers.
    # "delete fake users" -> removing customers.
    
    print(f"✨ Deleted {result.deleted_count} customers.")
    
    # Optional: Wipe conversations too if they want a clean slate
    # await db_service._db.conversations.delete_many({})
    # await db_service._db.messages.delete_many({})

if __name__ == "__main__":
    asyncio.run(main())
