#!/usr/bin/env python3
"""
Script to create test revenue data for the parking app.
This will generate parking sessions with revenue data for the owner account.
"""

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timedelta
import random
import os
from dotenv import load_dotenv
from pathlib import Path
import uuid

# Load environment from backend directory
ROOT_DIR = Path(__file__).parent
backend_env = ROOT_DIR / 'backend' / '.env'
load_dotenv(backend_env)

async def create_revenue_test_data():
    """Create test revenue data for demonstration purposes"""
    
    # Connect to MongoDB
    mongo_url = os.environ['MONGO_URL']
    client = AsyncIOMotorClient(mongo_url)
    db = client[os.environ['DB_NAME']]
    
    print("Creating test revenue data...")
    
    # Find owner user
    owner = await db.users.find_one({"email": "owner@test.com"})
    if not owner:
        print("❌ Owner user not found! Please run create_test_users.py first.")
        return
    
    print(f"✅ Found owner: {owner['email']}")
    
    # Find owner's parking spots
    owner_spots = await db.parking_spots.find({"owner_id": owner["id"]}).to_list(1000)
    if not owner_spots:
        print("❌ No parking spots found for owner! Please create some spots first.")
        return
    
    print(f"✅ Found {len(owner_spots)} parking spots")
    
    # Find test users for bookings
    users = await db.users.find({"role": "user"}).to_list(1000)
    if not users:
        print("❌ No users found for bookings!")
        return
    
    print(f"✅ Found {len(users)} users for bookings")
    
    # Generate test sessions over the last 6 months
    sessions_created = 0
    now = datetime.utcnow()
    
    for months_ago in range(6):  # Last 6 months
        month_start = now.replace(day=1) - timedelta(days=30 * months_ago)
        
        # Generate 5-15 sessions per month
        sessions_this_month = random.randint(5, 15)
        
        for _ in range(sessions_this_month):
            # Random spot and user
            spot = random.choice(owner_spots)
            user = random.choice(users)
            
            # Random start time within the month
            days_offset = random.randint(0, 29)
            hours_offset = random.randint(0, 23)
            start_time = month_start + timedelta(days=days_offset, hours=hours_offset)
            
            # Random session duration (1-8 hours)
            duration_hours = random.uniform(1, 8)
            end_time = start_time + timedelta(hours=duration_hours)
            
            # Calculate amount
            hourly_rate = spot["hourly_rate"]
            total_amount = duration_hours * hourly_rate
            
            # Create session
            session = {
                "id": str(uuid.uuid4()),
                "user_id": user["id"],
                "spot_id": spot["id"],
                "start_time": start_time,
                "end_time": end_time,
                "status": "ended",
                "hourly_rate": hourly_rate,
                "total_amount": round(total_amount, 2),
                "payment_session_id": None,
                "created_at": start_time
            }
            
            await db.parking_sessions.insert_one(session)
            sessions_created += 1
    
    print(f"✅ Created {sessions_created} test sessions with revenue data")
    
    # Calculate total revenue
    total_revenue = await db.parking_sessions.aggregate([
        {"$match": {
            "spot_id": {"$in": [spot["id"] for spot in owner_spots]},
            "status": "ended"
        }},
        {"$group": {
            "_id": None,
            "total": {"$sum": "$total_amount"}
        }}
    ]).to_list(1000)
    
    if total_revenue:
        print(f"💰 Total test revenue generated: CHF {total_revenue[0]['total']:.2f}")
    
    client.close()
    print("✅ Test data creation completed!")

if __name__ == "__main__":
    asyncio.run(create_revenue_test_data())
