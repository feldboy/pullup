#!/usr/bin/env python3
"""
Seed MongoDB with mock customer data.

Run: python scripts/seed_db.py
"""

import asyncio
from datetime import date, datetime, timedelta
from uuid import uuid4
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from motor.motor_asyncio import AsyncIOMotorClient

from gym_agent.models.customer import CustomerStatus, MembershipType


MOCK_CUSTOMERS = [
    # Active, healthy customer
    {
        "first_name": "דניאל",
        "last_name": "כהן",
        "phone": "+972501234567",
        "email": "daniel@example.com",
        "status": CustomerStatus.ACTIVE.value,
        "health_score": 85,
        "membership_type": MembershipType.YEARLY.value,
        "total_visits": 120,
        "days_since_visit": 2,
        "preferred_classes": ["CrossFit", "HIIT"],
        "preferred_language": "he",
    },
    # At-risk customer (hasn't visited in 2 weeks)
    {
        "first_name": "שרה",
        "last_name": "לוי",
        "phone": "+972502345678",
        "email": "sarah@example.com",
        "status": CustomerStatus.AT_RISK.value,
        "health_score": 45,
        "membership_type": MembershipType.MONTHLY.value,
        "total_visits": 24,
        "days_since_visit": 14,
        "preferred_classes": ["Yoga", "Pilates"],
        "preferred_language": "he",
    },
    # Inactive customer
    {
        "first_name": "מיכאל",
        "last_name": "ברק",
        "phone": "+972503456789",
        "email": "michael@example.com",
        "status": CustomerStatus.INACTIVE.value,
        "health_score": 25,
        "membership_type": MembershipType.MONTHLY.value,
        "total_visits": 8,
        "days_since_visit": 30,
        "preferred_classes": ["Spinning"],
        "preferred_language": "he",
    },
    # New member (trial)
    {
        "first_name": "רחל",
        "last_name": "אברהם",
        "phone": "+972504567890",
        "email": "rachel@example.com",
        "status": CustomerStatus.ACTIVE.value,
        "health_score": 70,
        "membership_type": MembershipType.TRIAL.value,
        "total_visits": 3,
        "days_since_visit": 1,
        "preferred_classes": [],
        "preferred_language": "he",
    },
    # Customer with expiring membership
    {
        "first_name": "יוסי",
        "last_name": "גולן",
        "phone": "+972505678901",
        "email": "yossi@example.com",
        "status": CustomerStatus.ACTIVE.value,
        "health_score": 60,
        "membership_type": MembershipType.QUARTERLY.value,
        "total_visits": 25,
        "days_since_visit": 5,
        "days_until_expiry": 7,
        "preferred_classes": ["Kickboxing", "TRX"],
        "preferred_language": "he",
    },
    # English-speaking customer
    {
        "first_name": "John",
        "last_name": "Smith",
        "phone": "+972506789012",
        "email": "john@example.com",
        "status": CustomerStatus.ACTIVE.value,
        "health_score": 75,
        "membership_type": MembershipType.MONTHLY.value,
        "total_visits": 15,
        "days_since_visit": 3,
        "preferred_classes": ["Weights", "Cardio"],
        "preferred_language": "en",
    },
]


async def seed_customers():
    """Seed the database with mock customers."""
    
    print("🔌 Connecting to MongoDB...")
    client: AsyncIOMotorClient = AsyncIOMotorClient("mongodb://localhost:27017")
    db = client["gym_ai"]
    customers_collection = db.customers
    
    # Check if already seeded
    existing = await customers_collection.count_documents({})
    if existing > 0:
        print(f"⚠️  Database already has {existing} customers.")
        response = input("Clear and reseed? (y/N): ")
        if response.lower() != 'y':
            print("Skipping seed.")
            client.close()
            return
        # Clear existing customers
        await customers_collection.delete_many({})
        print("🗑️  Cleared existing customers.")
    
    print(f"\n📝 Seeding {len(MOCK_CUSTOMERS)} customers...")
    
    for i, data in enumerate(MOCK_CUSTOMERS):
        customer_id = uuid4()
        days_since_visit = data.pop("days_since_visit", 0)
        days_until_expiry = data.pop("days_until_expiry", 90)
        
        customer_doc = {
            "_id": str(customer_id),
            "crm_id": f"ARBOX-{1000 + i}",
            "telegram_id": 1000000 + i,
            "membership_start_date": (date.today() - timedelta(days=180)).isoformat(),
            "membership_end_date": (date.today() + timedelta(days=days_until_expiry)).isoformat(),
            "last_visit": (datetime.now() - timedelta(days=days_since_visit)).isoformat() if days_since_visit else None,
            "created_at": datetime.now(),
            **data,
        }
        
        await customers_collection.insert_one(customer_doc)
        status_emoji = {
            CustomerStatus.ACTIVE.value: "🟢",
            CustomerStatus.AT_RISK.value: "🟡",
            CustomerStatus.INACTIVE.value: "🔴",
        }.get(data["status"], "⚪")
        
        print(f"  {status_emoji} {data['first_name']} {data['last_name']} - {data['status']} (Health: {data['health_score']})")
    
    # Create indexes
    print("\n📊 Creating indexes...")
    await customers_collection.create_index("phone")
    await customers_collection.create_index("telegram_id")
    await customers_collection.create_index("status")
    await customers_collection.create_index("health_score")
    
    print("\n✅ Database seeded successfully!")
    print(f"\nMongoCompass Connection: mongodb://localhost:27017")
    print(f"Database: gym_ai")
    print(f"Collections: customers, conversations, messages, analytics_events")
    
    client.close()


if __name__ == "__main__":
    asyncio.run(seed_customers())
