#!/usr/bin/env python3
"""
Script to create test users for the parking app
"""
import asyncio
import os
from pathlib import Path
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient
import hashlib
import uuid
from datetime import datetime

# Load environment variables
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

def hash_password(password: str) -> str:
    return hashlib.sha256((password + "salt").encode()).hexdigest()

async def create_test_users():
    # MongoDB connection
    mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
    db_name = os.environ.get('DB_NAME', 'test_database')  # Using existing DB_NAME from .env
    
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]
    
    # Test users to create
    test_users = [
        {
            "email": "user@test.com",
            "name": "Test User",
            "password": "user123",
            "role": "user"
        },
        {
            "email": "owner@test.com", 
            "name": "Test Owner",
            "password": "owner123",
            "role": "owner"
        },
        {
            "email": "admin@test.com",
            "name": "Test Admin", 
            "password": "admin123",
            "role": "admin"
        }
    ]
    
    print("Creating test users...")
    created_users = []
    
    for user_data in test_users:
        # Check if user already exists
        existing_user = await db.users.find_one({"email": user_data["email"]})
        if existing_user:
            print(f"❌ User {user_data['email']} already exists!")
            continue
        
        # Create user
        user = {
            "id": str(uuid.uuid4()),
            "email": user_data["email"],
            "name": user_data["name"],
            "password_hash": hash_password(user_data["password"]),
            "role": user_data["role"],
            "created_at": datetime.utcnow()
        }
        
        await db.users.insert_one(user)
        created_users.append(user_data)
        print(f"✅ Created {user_data['role']}: {user_data['email']} / {user_data['password']}")
    
    client.close()
    
    # Show existing users if none were created
    if not created_users:
        print("\n💡 All test users already exist!")
        print("\n📋 EXISTING LOGIN CREDENTIALS:")
        print("="*50)
        
        # Display the standard test credentials
        standard_users = [
            {"role": "USER", "email": "user@test.com", "password": "user123"},
            {"role": "OWNER", "email": "owner@test.com", "password": "owner123"}, 
            {"role": "ADMIN", "email": "admin@test.com", "password": "admin123"}
        ]
        
        for user in standard_users:
            print(f"Role: {user['role']}")
            print(f"Email: {user['email']}")
            print(f"Password: {user['password']}")
            print("-" * 30)
    else:
        print("\n🎉 Test users created successfully!")
        print("\n📋 LOGIN CREDENTIALS:")
        print("="*50)
        for user in created_users:
            print(f"Role: {user['role'].upper()}")
            print(f"Email: {user['email']}")
            print(f"Password: {user['password']}")
            print("-" * 30)

if __name__ == "__main__":
    asyncio.run(create_test_users())
