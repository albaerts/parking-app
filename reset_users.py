#!/usr/bin/env python3

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import hashlib
from datetime import datetime
import uuid

async def reset_users():
    # MongoDB Verbindung
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    db = client.test_database
    users_collection = db.users
    
    print("🗑️  LÖSCHE ALLE BESTEHENDEN BENUTZER...")
    print("=" * 50)
    
    # Alle bestehenden Benutzer löschen
    delete_result = await users_collection.delete_many({})
    print(f"✅ {delete_result.deleted_count} Benutzer gelöscht")
    
    print("\n👥 ERSTELLE NEUE BENUTZER...")
    print("=" * 50)
    
    # Hash-Funktion wie im Backend
    def hash_password(password: str) -> str:
        return hashlib.sha256((password + "salt").encode()).hexdigest()
    
    # Neue Benutzer definieren
    new_users = [
        {
            "name": "Test User",
            "email": "user@test.com",
            "password": "password123",
            "role": "user"
        },
        {
            "name": "Test Owner",
            "email": "owner@test.com", 
            "password": "password123",
            "role": "owner"
        },
        {
            "name": "Test Admin",
            "email": "admin@test.com",
            "password": "password123", 
            "role": "admin"
        }
    ]
    
    # Benutzer erstellen
    created_users = []
    
    for user_data in new_users:
        # Passwort hashen (wie im Backend)
        hashed_password = hash_password(user_data["password"])
        
        # Benutzer-Dokument erstellen
        user_doc = {
            "id": str(uuid.uuid4()),
            "name": user_data["name"],
            "email": user_data["email"],
            "password_hash": hashed_password,
            "role": user_data["role"],
            "created_at": datetime.utcnow()
        }
        
        # In Datenbank einfügen
        await users_collection.insert_one(user_doc)
        
        created_users.append({
            "name": user_data["name"],
            "email": user_data["email"],
            "password": user_data["password"],
            "role": user_data["role"]
        })
        
        print(f"✅ {user_data['role'].upper()}: {user_data['email']} | {user_data['name']}")
    
    print(f"\n🎯 {len(created_users)} neue Benutzer erfolgreich erstellt!")
    
    print("\n📋 ZUSAMMENFASSUNG - NEUE ANMELDEDATEN:")
    print("=" * 60)
    
    for user in created_users:
        print(f"🎭 {user['role'].upper()}:")
        print(f"   📧 Email: {user['email']}")
        print(f"   🔑 Passwort: {user['password']}")
        print(f"   👤 Name: {user['name']}")
        print(f"   ---")
    
    # Verbindung schließen
    client.close()
    
    print("\n✅ DATENBANK-RESET ABGESCHLOSSEN!")
    print("Die App kann jetzt mit den neuen Anmeldedaten getestet werden.")

# Script ausführen
if __name__ == "__main__":
    asyncio.run(reset_users())
