#!/usr/bin/env python3
import asyncio
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from motor.motor_asyncio import AsyncIOMotorClient
import hashlib
import uuid
from datetime import datetime

# Database connection
MONGODB_URL = "mongodb://localhost:27017"
DATABASE_NAME = "test_database"

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

async def create_test_users():
    client = AsyncIOMotorClient(MONGODB_URL)
    db = client[DATABASE_NAME]
    
    # Test users to create
    test_users = [
        {
            "id": str(uuid.uuid4()),
            "name": "Test User",
            "email": "user@test.com", 
            "password_hash": hash_password("password123"),
            "role": "user",
            "created_at": datetime.utcnow(),
            "last_login": None
        },
        {
            "id": str(uuid.uuid4()),
            "name": "Parking Owner",
            "email": "owner@test.com",
            "password_hash": hash_password("password123"), 
            "role": "owner",
            "created_at": datetime.utcnow(),
            "last_login": None
        },
        {
            "id": str(uuid.uuid4()),
            "name": "System Admin",
            "email": "admin@test.com",
            "password_hash": hash_password("password123"),
            "role": "admin", 
            "created_at": datetime.utcnow(),
            "last_login": None
        }
    ]
    
    print("🚀 Creating test users...")
    
    for user in test_users:
        # Check if user already exists
        existing = await db.users.find_one({"email": user["email"]})
        if existing:
            print(f"✅ User {user['email']} already exists")
        else:
            await db.users.insert_one(user)
            print(f"✅ Created user: {user['email']} ({user['role']})")
    
    print("\n📋 ALL TEST USERS:")
    print("=" * 50)
    
    all_users = await db.users.find({}).to_list(length=None)
    for user in all_users:
        print(f"👤 Name: {user['name']}")
        print(f"📧 Email: {user['email']}")
        print(f"🔑 Password: password123")
        print(f"🎭 Role: {user['role']}")
        print(f"🆔 ID: {user['id']}")
        print(f"📅 Created: {user['created_at']}")
        print("-" * 30)
    
    print(f"\n🎯 Total users in database: {len(all_users)}")
    client.close()

if __name__ == "__main__":
    asyncio.run(create_test_users())
