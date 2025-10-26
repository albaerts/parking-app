#!/usr/bin/env python3
"""
Script to create an admin user for the parking app
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

async def create_admin_user():
    # MongoDB connection
    mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
    db_name = os.environ.get('DB_NAME', 'parking_app')
    
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]
    
    admin_email = "admin@test.com"
    admin_password = "admin123"  # Change this to a secure password
    
    # Check if admin already exists
    existing_admin = await db.users.find_one({"email": admin_email})
    if existing_admin:
        print(f"Admin user with email {admin_email} already exists!")
        return
    
    # Create admin user
    admin_user = {
        "id": str(uuid.uuid4()),
        "email": admin_email,
        "name": "System Administrator",
        "password_hash": hash_password(admin_password),
        "role": "admin",
        "created_at": datetime.utcnow()
    }
    
    await db.users.insert_one(admin_user)
    print(f"Admin user created successfully!")
    print(f"Email: {admin_email}")
    print(f"Password: {admin_password}")
    print("Please change the password after first login!")
    
    await client.close()

if __name__ == "__main__":
    asyncio.run(create_admin_user())
