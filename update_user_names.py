#!/usr/bin/env python3
import asyncio
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from motor.motor_asyncio import AsyncIOMotorClient

# Database connection
MONGODB_URL = "mongodb://localhost:27017"
DATABASE_NAME = "test_database"

async def update_user_names():
    client = AsyncIOMotorClient(MONGODB_URL)
    db = client[DATABASE_NAME]
    
    # Update names to have proper first names
    name_updates = [
        {"email": "user@test.com", "new_name": "Max Mustermann"},
        {"email": "owner@test.com", "new_name": "Anna Schmidt"}, 
        {"email": "admin@test.com", "new_name": "Tom Weber"}
    ]
    
    print("🔄 Updating user names...")
    
    for update in name_updates:
        result = await db.users.update_one(
            {"email": update["email"]},
            {"$set": {"name": update["new_name"]}}
        )
        if result.modified_count > 0:
            print(f"✅ Updated user {update['email']}: {update['new_name']}")
        else:
            print(f"❌ Failed to update user {update['email']}")
    
    print("\n📋 Updated user list:")
    print("=" * 50)
    
    all_users = await db.users.find({}).to_list(length=None)
    for user in all_users:
        print(f"👤 Name: {user['name']}")
        print(f"📧 Email: {user['email']}")
        print(f"🎭 Role: {user['role']}")
        print("-" * 30)
    
    client.close()

if __name__ == "__main__":
    asyncio.run(update_user_names())
