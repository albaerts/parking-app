#!/usr/bin/env python3
"""
Restore original parking app users with correct credentials
"""
import asyncio
import os
import sys
import hashlib
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime
import uuid

# MongoDB connection
mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ.get('DB_NAME', 'parkingdb')]

def hash_password(password: str) -> str:
    """Hash password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

async def restore_original_users():
    """Restore the original parking app users"""
    
    print("🔄 RESTORING ORIGINAL PARKING APP USERS")
    print("="*50)
    
    # Clear existing users
    await db.users.delete_many({})
    print("🗑️ Cleared existing users")
    
    # Original users with correct credentials
    original_users = [
        {
            "id": str(uuid.uuid4()),
            "email": "user@parking.com",
            "name": "Regular User",
            "password_hash": hash_password("user123"),
            "role": "user",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        },
        {
            "id": str(uuid.uuid4()),
            "email": "owner@parking.com", 
            "name": "Parking Owner",
            "password_hash": hash_password("owner123"),
            "role": "owner",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        },
        {
            "id": str(uuid.uuid4()),
            "email": "admin@parking.com",
            "name": "System Admin", 
            "password_hash": hash_password("admin123"),
            "role": "admin",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
    ]
    
    # Insert original users
    for user in original_users:
        await db.users.insert_one(user)
        print(f"✅ Created: {user['email']} ({user['role']})")
    
    print("\n🎉 ORIGINAL USERS RESTORED!")
    print("="*50)
    print("🔑 LOGIN CREDENTIALS:")
    print("👤 USER: user@parking.com / user123")
    print("🏢 OWNER: owner@parking.com / owner123") 
    print("👑 ADMIN: admin@parking.com / admin123")
    print("="*50)

if __name__ == "__main__":
    asyncio.run(restore_original_users())
