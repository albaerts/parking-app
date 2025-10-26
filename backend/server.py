from fastapi import FastAPI, APIRouter, HTTPException, Request, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timedelta
import jwt
import hashlib
import json

# FastAPI App für gashis.ch
app = FastAPI(
    title="Gashis Parking API",
    description="Smart Parking System für die Schweiz",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS für gashis.ch
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://gashis.ch",
        "https://www.gashis.ch", 
        "https://parking.gashis.ch",
        "http://localhost:3000"  # Für lokale Entwicklung
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

"""
App initialization
- Keep a single FastAPI() instance (avoid reassigning app)
- Prepare database client placeholders so import does not fail
"""

# SQLite (unused currently) – keeping path for potential future use
import sqlite3
DATABASE_PATH = os.path.join(os.path.dirname(__file__), "parking.db")

# Initialize Mongo client lazily (won't connect until first operation)
MONGODB_URI = os.environ.get("MONGODB_URI", "mongodb://localhost:27017")
MONGODB_DB = os.environ.get("MONGODB_DB", "parking")
client = None
db = None
try:
    client = AsyncIOMotorClient(MONGODB_URI)
    db = client.get_database(MONGODB_DB)
except Exception:
    # If motor isn't available or initialization fails, keep db as None
    client = None
    db = None

# Simple in-memory fallback stores when MongoDB is not available
FORCE_MEMORY_MODE = os.environ.get("FORCE_MEMORY_MODE", "0") in ("1", "true", "True")
MEMORY_MODE = (db is None) or FORCE_MEMORY_MODE
memory_hardware_devices: Dict[str, Dict[str, Any]] = {}
memory_parking_spots: Dict[str, Dict[str, Any]] = {}
# In-memory command queue per hardware_id
memory_hardware_commands: Dict[str, List[Dict[str, Any]]] = {}
SIMPLE_COMMAND_SECRET = os.environ.get("SIMPLE_COMMAND_SECRET", "")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Security
security = HTTPBearer()
JWT_SECRET = os.environ.get('JWT_SECRET', 'your-secret-key-here')
JWT_ALGORITHM = 'HS256'

# Models
class User(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: str
    name: str
    password_hash: str
    role: str = "user"  # "user", "owner", or "admin"
    # Extended profile fields
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    zip_code: Optional[str] = None
    country: Optional[str] = None
    secondary_email: Optional[str] = None
    date_of_birth: Optional[datetime] = None
    profile_picture_url: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class UserCreate(BaseModel):
    email: str
    name: str
    password: str
    role: str = "user"

class UserLogin(BaseModel):
    email: str
    password: str

class UserProfileUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    zip_code: Optional[str] = None
    country: Optional[str] = None
    secondary_email: Optional[str] = None
    date_of_birth: Optional[datetime] = None

class EmailChangeRequest(BaseModel):
    new_email: str
    password: str

class PasswordChangeRequest(BaseModel):
    current_password: str
    new_password: str

class ParkingSpot(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    latitude: float
    longitude: float
    address: str
    hourly_rate: float
    is_available: bool = True
    owner_id: str
    hardware_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_updated: datetime = Field(default_factory=datetime.utcnow)

class ParkingSpotCreate(BaseModel):
    name: str
    latitude: float
    longitude: float
    address: str
    hourly_rate: float

class ParkingSession(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    spot_id: str
    start_time: datetime = Field(default_factory=datetime.utcnow)
    end_time: Optional[datetime] = None
    status: str = "active"  # "active", "ended", "paid"
    hourly_rate: float
    total_amount: float = 0.0
    payment_session_id: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

class PaymentTransaction(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str
    user_id: str
    parking_session_id: str
    amount: float
    currency: str = "usd"

class Review(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    owner_id: str
    parking_session_id: str
    rating: int  # 1-5
    comment: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None

class ReviewCreate(BaseModel):
    parking_session_id: str
    rating: int
    comment: Optional[str] = None

# Hardware Models
class HardwareDevice(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    hardware_id: str  # Unique device identifier
    spot_id: str
    device_type: str = "smart_barrier"  # "smart_barrier", "sensor_only"
    status: str = "online"  # "online", "offline", "maintenance"
    battery_level: float = 100.0  # Percentage
    solar_voltage: float = 0.0  # Solar panel voltage
    last_heartbeat: datetime = Field(default_factory=datetime.utcnow)
    firmware_version: str = "1.0.0"
    settings: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)

class HardwareStatus(BaseModel):
    hardware_id: str
    is_occupied: bool
    barrier_position: str  # "up", "down", "moving", "error"
    battery_level: float
    solar_voltage: float
    signal_strength: int  # dBm
    temperature: float
    last_motion: Optional[datetime] = None

class HardwareCommand(BaseModel):
    hardware_id: str
    command: str  # "raise_barrier", "lower_barrier", "reset", "update_settings"
    parameters: Dict[str, Any] = Field(default_factory=dict)
    issued_by: str  # user_id who issued the command
    created_at: datetime = Field(default_factory=datetime.utcnow)

class SensorReading(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    hardware_id: str
    sensor_type: str  # "ultrasonic", "magnetic", "motion"
    value: float
    unit: str  # "cm", "boolean", "lux"
    timestamp: datetime = Field(default_factory=datetime.utcnow)

# Utility functions
def hash_password(password: str) -> str:
    return hashlib.sha256((password + "salt").encode()).hexdigest()

def verify_password(password: str, hashed: str) -> bool:
    return hash_password(password) == hashed

def clean_mongo_doc(doc):
    """Remove MongoDB _id field from document"""
    if doc is None:
        return None
    if isinstance(doc, list):
        return [clean_mongo_doc(item) for item in doc]
    if isinstance(doc, dict):
        cleaned = {k: v for k, v in doc.items() if k != "_id"}
        return cleaned
    return doc

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(hours=24)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return encoded_jwt

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid authentication credentials")
        user = await db.users.find_one({"id": user_id})
        if user is None:
            raise HTTPException(status_code=401, detail="User not found")
        return User(**user)
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")

# Auth endpoints
@api_router.post("/auth/register")
async def register(user_data: UserCreate):
    # Check if user exists
    existing_user = await db.users.find_one({"email": user_data.email})
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create user
    user_dict = user_data.dict()
    user_dict["password_hash"] = hash_password(user_data.password)
    del user_dict["password"]
    user = User(**user_dict)
    
    await db.users.insert_one(user.dict())
    
    # Create token
    access_token = create_access_token(data={"sub": user.id})
    
    return {"access_token": access_token, "token_type": "bearer", "user": {"id": user.id, "email": user.email, "name": user.name, "role": user.role}}

@api_router.post("/auth/login")
async def login(login_data: UserLogin):
    user = await db.users.find_one({"email": login_data.email})
    if not user or not verify_password(login_data.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    access_token = create_access_token(data={"sub": user["id"]})
    return {"access_token": access_token, "token_type": "bearer", "user": {"id": user["id"], "email": user["email"], "name": user["name"], "role": user["role"]}}

# Parking spot endpoints
@api_router.get("/parking-spots")
async def get_parking_spots(lat: Optional[float] = None, lng: Optional[float] = None, radius: Optional[float] = 5.0):
    spots = await db.parking_spots.find().to_list(1000)
    return [ParkingSpot(**spot) for spot in spots]

@api_router.post("/parking-spots")
async def create_parking_spot(spot_data: ParkingSpotCreate, current_user: User = Depends(get_current_user)):
    if current_user.role != "owner":
        raise HTTPException(status_code=403, detail="Only parking lot owners can create spots")
    
    spot_dict = spot_data.dict()
    spot_dict["owner_id"] = current_user.id
    spot = ParkingSpot(**spot_dict)
    
    await db.parking_spots.insert_one(spot.dict())
    return spot

@api_router.get("/parking-spots/{spot_id}")
async def get_parking_spot(spot_id: str):
    spot = await db.parking_spots.find_one({"id": spot_id})
    if not spot:
        raise HTTPException(status_code=404, detail="Parking spot not found")
    return ParkingSpot(**spot)

@api_router.put("/parking-spots/{spot_id}")
async def update_parking_spot(spot_id: str, spot_data: ParkingSpotCreate, current_user: User = Depends(get_current_user)):
    if current_user.role != "owner":
        raise HTTPException(status_code=403, detail="Only parking lot owners can update spots")
    
    # Check if spot exists and belongs to the current user
    existing_spot = await db.parking_spots.find_one({"id": spot_id})
    if not existing_spot:
        raise HTTPException(status_code=404, detail="Parking spot not found")
    
    if existing_spot["owner_id"] != current_user.id:
        raise HTTPException(status_code=403, detail="You can only update your own parking spots")
    
    # Update the spot
    spot_dict = spot_data.dict()
    spot_dict["owner_id"] = current_user.id
    spot_dict["last_updated"] = datetime.utcnow()
    
    result = await db.parking_spots.update_one(
        {"id": spot_id},
        {"$set": spot_dict}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Parking spot not found")
    
    # Return updated spot
    updated_spot = await db.parking_spots.find_one({"id": spot_id})
    return ParkingSpot(**updated_spot)

@api_router.delete("/parking-spots/{spot_id}")
async def delete_parking_spot(spot_id: str, current_user: User = Depends(get_current_user)):
    if current_user.role != "owner":
        raise HTTPException(status_code=403, detail="Only parking lot owners can delete spots")
    
    # Check if spot exists and belongs to the current user
    existing_spot = await db.parking_spots.find_one({"id": spot_id})
    if not existing_spot:
        raise HTTPException(status_code=404, detail="Parking spot not found")
    
    if existing_spot["owner_id"] != current_user.id:
        raise HTTPException(status_code=403, detail="You can only delete your own parking spots")
    
    # Check if there are any active bookings for this spot
    active_bookings = await db.bookings.find({
        "spot_id": spot_id,
        "end_time": {"$gt": datetime.utcnow()}
    }).to_list(1)
    
    if active_bookings:
        raise HTTPException(status_code=400, detail="Cannot delete parking spot with active bookings")
    
    # Delete the spot
    result = await db.parking_spots.delete_one({"id": spot_id})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Parking spot not found")
    
    return {"message": "Parking spot deleted successfully"}

# Hardware simulation endpoints
@api_router.post("/hardware/{hardware_id}/status")
async def update_hardware_status(hardware_id: str, is_available: bool):
    """Simulates hardware updates from parking spot sensors"""
    result = await db.parking_spots.update_one(
        {"hardware_id": hardware_id},
        {"$set": {"is_available": is_available, "last_updated": datetime.utcnow()}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Hardware not found")
    return {"status": "updated"}

# Parking session endpoints
@api_router.post("/parking-sessions")
async def start_parking_session(spot_id: str, current_user: User = Depends(get_current_user)):
    # Check if spot exists and is available
    spot = await db.parking_spots.find_one({"id": spot_id})
    if not spot:
        raise HTTPException(status_code=404, detail="Parking spot not found")
    
    spot_obj = ParkingSpot(**spot)
    if not spot_obj.is_available:
        raise HTTPException(status_code=400, detail="Parking spot is not available")
    
    # Check if user already has an active session
    active_session = await db.parking_sessions.find_one({"user_id": current_user.id, "status": "active"})
    if active_session:
        raise HTTPException(status_code=400, detail="You already have an active parking session")
    
    # Create parking session
    session = ParkingSession(
        user_id=current_user.id,
        spot_id=spot_id,
        hourly_rate=spot_obj.hourly_rate
    )
    
    await db.parking_sessions.insert_one(session.dict())
    
    # Mark spot as unavailable
    await db.parking_spots.update_one(
        {"id": spot_id},
        {"$set": {"is_available": False, "last_updated": datetime.utcnow()}}
    )
    
    return session

@api_router.post("/parking-sessions/{session_id}/end")
async def end_parking_session(session_id: str, current_user: User = Depends(get_current_user)):
    session = await db.parking_sessions.find_one({"id": session_id, "user_id": current_user.id})
    if not session:
        raise HTTPException(status_code=404, detail="Parking session not found")
    
    session_obj = ParkingSession(**session)
    if session_obj.status != "active":
        raise HTTPException(status_code=400, detail="Session is not active")
    
    # Calculate total amount
    end_time = datetime.utcnow()
    duration_hours = (end_time - session_obj.start_time).total_seconds() / 3600
    total_amount = duration_hours * session_obj.hourly_rate
    
    # Update session
    await db.parking_sessions.update_one(
        {"id": session_id},
        {"$set": {
            "end_time": end_time,
            "total_amount": total_amount,
            "status": "ended"
        }}
    )
    
    # Mark spot as available
    await db.parking_spots.update_one(
        {"id": session_obj.spot_id},
        {"$set": {"is_available": True, "last_updated": datetime.utcnow()}}
    )
    
    return {"total_amount": total_amount, "duration_hours": duration_hours}

@api_router.get("/parking-sessions")
async def get_user_sessions(current_user: User = Depends(get_current_user)):
    sessions = await db.parking_sessions.find({"user_id": current_user.id}).sort([("start_time", -1)]).to_list(1000)
    return [ParkingSession(**session) for session in sessions]

@api_router.get("/parking-sessions/history")
async def get_user_booking_history(current_user: User = Depends(get_current_user)):
    """Get user's booking history with parking spot details"""
    sessions = await db.parking_sessions.find({
        "user_id": current_user.id,
        "status": "ended"
    }).sort([("end_time", -1)]).to_list(1000)
    
    # Enrich sessions with parking spot details
    enriched_sessions = []
    for session in sessions:
        session_obj = ParkingSession(**session)
        
        # Get parking spot details
        spot = await db.parking_spots.find_one({"id": session_obj.spot_id})
        if spot:
            spot_obj = ParkingSpot(**spot)
            session_dict = session_obj.dict()
            session_dict["parking_spot"] = {
                "name": spot_obj.name,
                "address": spot_obj.address,
                "latitude": spot_obj.latitude,
                "longitude": spot_obj.longitude
            }
            
            # Check if user has already reviewed this session
            review = await db.reviews.find_one({
                "user_id": current_user.id,
                "parking_session_id": session_obj.id
            })
            session_dict["has_review"] = review is not None
            session_dict["review"] = Review(**review).dict() if review else None
            
            enriched_sessions.append(session_dict)
    
    return enriched_sessions

@api_router.post("/reviews")
async def create_review(review_data: ReviewCreate, current_user: User = Depends(get_current_user)):
    """Create a review for a parking session"""
    # Verify the parking session exists and belongs to the user
    session = await db.parking_sessions.find_one({
        "id": review_data.parking_session_id,
        "user_id": current_user.id,
        "status": "ended"
    })
    
    if not session:
        raise HTTPException(status_code=404, detail="Parking session not found or not completed")
    
    # Check if user has already reviewed this session
    existing_review = await db.reviews.find_one({
        "user_id": current_user.id,
        "parking_session_id": review_data.parking_session_id
    })
    
    if existing_review:
        raise HTTPException(status_code=400, detail="You have already reviewed this parking session")
    
    # Get the parking spot to find the owner
    spot = await db.parking_spots.find_one({"id": session["parking_spot_id"]})
    if not spot:
        raise HTTPException(status_code=404, detail="Parking spot not found")
    
    # Validate rating
    if review_data.rating < 1 or review_data.rating > 5:
        raise HTTPException(status_code=400, detail="Rating must be between 1 and 5")
    
    # Create review
    review = Review(
        user_id=current_user.id,
        owner_id=spot["owner_id"],
        parking_session_id=review_data.parking_session_id,
        rating=review_data.rating,
        comment=review_data.comment
    )
    
    await db.reviews.insert_one(review.dict())
    
    # Mark the parking session as reviewed
    await db.parking_sessions.update_one(
        {"id": review_data.parking_session_id},
        {"$set": {"has_review": True}}
    )
    
    return review

@api_router.get("/reviews/owner/{owner_id}")
async def get_owner_reviews(owner_id: str):
    """Get all reviews for a specific owner"""
    reviews = await db.reviews.find({"owner_id": owner_id}).sort([("created_at", -1)]).to_list(1000)
    
    # Enrich reviews with user information (without sensitive data)
    enriched_reviews = []
    for review in reviews:
        review_obj = Review(**review)
        
        # Get user info (only username/email, no sensitive data)
        user = await db.users.find_one({"id": review_obj.user_id})
        if user:
            review_dict = review_obj.dict()
            review_dict["user"] = {
                "username": user.get("username", "Anonymous"),
                "email": user["email"][:3] + "***" + user["email"][-10:]  # Partially hide email
            }
            enriched_reviews.append(review_dict)
    
    return enriched_reviews

@api_router.get("/reviews/stats/{owner_id}")
async def get_owner_review_stats(owner_id: str):
    """Get review statistics for an owner"""
    reviews = await db.reviews.find({"owner_id": owner_id}).to_list(1000)
    
    if not reviews:
        return {
            "total_reviews": 0,
            "average_rating": 0,
            "rating_distribution": {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
        }
    
    total_reviews = len(reviews)
    total_rating = sum(review["rating"] for review in reviews)
    average_rating = total_rating / total_reviews
    
    # Calculate rating distribution
    rating_distribution = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
    for review in reviews:
        rating_distribution[review["rating"]] += 1
    
    return {
        "total_reviews": total_reviews,
        "average_rating": round(average_rating, 2),
        "rating_distribution": rating_distribution
    }

# User review endpoints
@api_router.get("/reviews/my-reviews")
async def get_my_reviews(current_user: User = Depends(get_current_user)):
    """Get all reviews by the current user"""
    reviews = await db.reviews.find({"user_id": current_user.id}).to_list(1000)
    
    enriched_reviews = []
    for review in reviews:
        review_dict = clean_mongo_doc(review)
        
        # Get parking spot details
        parking_session = await db.parking_sessions.find_one({"id": review["parking_session_id"]})
        if parking_session:
            parking_spot = await db.parking_spots.find_one({"id": parking_session["parking_spot_id"]})
            if parking_spot:
                review_dict["parking_spot"] = {
                    "name": parking_spot["name"],
                    "address": parking_spot["address"]
                }
        
        enriched_reviews.append(review_dict)
    
    return enriched_reviews

@api_router.get("/reviews/spot/{spot_id}")
async def get_spot_reviews(spot_id: str):
    """Get all reviews for a specific parking spot"""
    # Find all parking sessions for this spot
    sessions = await db.parking_sessions.find({"parking_spot_id": spot_id}).to_list(1000)
    session_ids = [session["id"] for session in sessions]
    
    # Find all reviews for these sessions
    reviews = await db.reviews.find({"parking_session_id": {"$in": session_ids}}).to_list(1000)
    
    enriched_reviews = []
    for review in reviews:
        review_dict = clean_mongo_doc(review)
        
        # Get user name (anonymized)
        user = await db.users.find_one({"id": review["user_id"]})
        if user:
            review_dict["user_name"] = user.get("name", "Anonymous")
        
        enriched_reviews.append(review_dict)
    
    return enriched_reviews

@api_router.put("/reviews/{review_id}")
async def update_review(review_id: str, rating: int = None, comment: str = None, current_user: User = Depends(get_current_user)):
    """Update a review (only by the author)"""
    review = await db.reviews.find_one({"id": review_id})
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    
    if review["user_id"] != current_user.id:
        raise HTTPException(status_code=403, detail="Can only update your own reviews")
    
    update_data = {}
    if rating is not None:
        if rating < 1 or rating > 5:
            raise HTTPException(status_code=400, detail="Rating must be between 1 and 5")
        update_data["rating"] = rating
    
    if comment is not None:
        update_data["comment"] = comment
    
    if update_data:
        update_data["updated_at"] = datetime.utcnow()
        await db.reviews.update_one({"id": review_id}, {"$set": update_data})
    
    return {"message": "Review updated successfully"}

@api_router.delete("/reviews/{review_id}")
async def delete_review(review_id: str, current_user: User = Depends(get_current_user)):
    """Delete a review (only by the author)"""
    review = await db.reviews.find_one({"id": review_id})
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    
    if review["user_id"] != current_user.id:
        raise HTTPException(status_code=403, detail="Can only delete your own reviews")
    
    await db.reviews.delete_one({"id": review_id})
    
    # Update the parking session to remove has_review flag
    await db.parking_sessions.update_one(
        {"id": review["parking_session_id"]}, 
        {"$unset": {"has_review": ""}}
    )
    
    return {"message": "Review deleted successfully"}

# Admin endpoints
@api_router.get("/admin/users")
async def get_all_users(current_user: User = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Only admins can access user data")
    
    users = await db.users.find().to_list(1000)
    # Remove password hashes from response and convert ObjectId to string
    for user in users:
        user.pop("password_hash", None)
        user["_id"] = str(user["_id"])
    return users

@api_router.get("/admin/parking-spots")
async def get_all_parking_spots_admin(current_user: User = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Only admins can access all parking spots")
    
    spots = await db.parking_spots.find().to_list(1000)
    return [ParkingSpot(**spot) for spot in spots]

@api_router.get("/admin/parking-sessions")
async def get_all_parking_sessions_admin(current_user: User = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Only admins can access all parking sessions")
    
    sessions = await db.parking_sessions.find().to_list(1000)
    return [ParkingSession(**session) for session in sessions]

@api_router.delete("/admin/users/{user_id}")
async def delete_user(user_id: str, current_user: User = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Only admins can delete users")
    
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot delete your own account")
    
    result = await db.users.delete_one({"id": user_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {"message": "User deleted successfully"}

@api_router.put("/admin/users/{user_id}/role")
async def update_user_role(user_id: str, new_role: str, current_user: User = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Only admins can update user roles")
    
    if new_role not in ["user", "owner", "admin"]:
        raise HTTPException(status_code=400, detail="Invalid role")
    
    result = await db.users.update_one(
        {"id": user_id},
        {"$set": {"role": new_role}}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {"message": f"User role updated to {new_role}"}

@api_router.get("/admin/statistics")
async def get_statistics(current_user: User = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Only admins can access statistics")
    
    total_users = await db.users.count_documents({})
    total_owners = await db.users.count_documents({"role": "owner"})
    total_admins = await db.users.count_documents({"role": "admin"})
    total_spots = await db.parking_spots.count_documents({})
    active_sessions = await db.parking_sessions.count_documents({"status": "active"})
    total_sessions = await db.parking_sessions.count_documents({})
    
    return {
        "total_users": total_users,
        "total_owners": total_owners,
        "total_admins": total_admins,
        "total_spots": total_spots,
        "active_sessions": active_sessions,
        "total_sessions": total_sessions
    }

# User Account Management endpoints
@api_router.get("/user/profile")
async def get_user_profile(current_user: User = Depends(get_current_user)):
    """Get current user's complete profile"""
    user_data = await db.users.find_one({"id": current_user.id})
    if not user_data:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Remove MongoDB _id and password hash from response
    user_data.pop("_id", None)
    user_data.pop("password_hash", None)
    return user_data

@api_router.put("/user/profile")
async def update_user_profile(profile_data: UserProfileUpdate, current_user: User = Depends(get_current_user)):
    """Update user profile information"""
    update_data = {k: v for k, v in profile_data.dict().items() if v is not None}
    
    if update_data:
        update_data["updated_at"] = datetime.utcnow()
        result = await db.users.update_one(
            {"id": current_user.id},
            {"$set": update_data}
        )
        
        if result.modified_count == 0:
            raise HTTPException(status_code=404, detail="User not found")
    
    # Return updated profile
    updated_user = await db.users.find_one({"id": current_user.id})
    cleaned_user = clean_mongo_doc(updated_user)
    cleaned_user.pop("password_hash", None)
    return {"message": "Profile updated successfully", "user": cleaned_user}

@api_router.put("/user/email")
async def change_email(email_request: EmailChangeRequest, current_user: User = Depends(get_current_user)):
    """Change user's primary email address"""
    # Verify current password
    user = await db.users.find_one({"id": current_user.id})
    if not verify_password(email_request.password, user["password_hash"]):
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    
    # Check if new email is already in use
    existing_user = await db.users.find_one({"email": email_request.new_email})
    if existing_user and existing_user["id"] != current_user.id:
        raise HTTPException(status_code=400, detail="Email address is already in use")
    
    # Update email
    result = await db.users.update_one(
        {"id": current_user.id},
        {"$set": {"email": email_request.new_email, "updated_at": datetime.utcnow()}}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Create new token with updated email
    access_token = create_access_token(data={"sub": current_user.id})
    
    return {
        "message": "Email updated successfully", 
        "access_token": access_token,
        "new_email": email_request.new_email
    }

@api_router.put("/user/password")
async def change_password(password_request: PasswordChangeRequest, current_user: User = Depends(get_current_user)):
    """Change user's password"""
    # Verify current password
    user = await db.users.find_one({"id": current_user.id})
    if not verify_password(password_request.current_password, user["password_hash"]):
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    
    # Validate new password (you can add more validation rules here)
    if len(password_request.new_password) < 6:
        raise HTTPException(status_code=400, detail="New password must be at least 6 characters long")
    
    # Hash new password and update
    new_password_hash = hash_password(password_request.new_password)
    result = await db.users.update_one(
        {"id": current_user.id},
        {"$set": {"password_hash": new_password_hash, "updated_at": datetime.utcnow()}}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {"message": "Password updated successfully"}

@api_router.delete("/user/account")
async def delete_user_account(password: str, current_user: User = Depends(get_current_user)):
    """Delete user's account (requires password confirmation)"""
    # Verify password
    user = await db.users.find_one({"id": current_user.id})
    if not verify_password(password, user["password_hash"]):
        raise HTTPException(status_code=400, detail="Password is incorrect")
    
    # Delete user's parking sessions
    await db.parking_sessions.delete_many({"user_id": current_user.id})
    
    # Delete user's reviews
    await db.reviews.delete_many({"user_id": current_user.id})
    
    # If user is an owner, delete their parking spots
    if current_user.role == "owner":
        await db.parking_spots.delete_many({"owner_id": current_user.id})
    
    # Delete user account
    result = await db.users.delete_one({"id": current_user.id})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {"message": "Account deleted successfully"}

@api_router.get("/user/account-summary")
async def get_account_summary(current_user: User = Depends(get_current_user)):
    """Get user's account summary with statistics"""
    # Count user's parking sessions
    total_sessions = await db.parking_sessions.count_documents({"user_id": current_user.id})
    active_sessions = await db.parking_sessions.count_documents({"user_id": current_user.id, "status": "active"})
    
    # Count user's reviews
    total_reviews = await db.reviews.count_documents({"user_id": current_user.id})
    
    # If user is an owner, count their parking spots
    owned_spots = 0
    if current_user.role == "owner":
        owned_spots = await db.parking_spots.count_documents({"owner_id": current_user.id})
    
    # Get user's recent activity (last 5 sessions)
    recent_sessions_cursor = await db.parking_sessions.find(
        {"user_id": current_user.id}
    ).sort("created_at", -1).limit(5).to_list(5)
    
    # Clean MongoDB documents
    recent_sessions = clean_mongo_doc(recent_sessions_cursor)
    
    return {
        "user_id": current_user.id,
        "email": current_user.email,
        "name": current_user.name,
        "role": current_user.role,
        "statistics": {
            "total_parking_sessions": total_sessions,
            "active_parking_sessions": active_sessions,
            "total_reviews": total_reviews,
            "owned_parking_spots": owned_spots
        },
        "recent_sessions": recent_sessions or []
    }

# Payment endpoints - temporarily disabled
@api_router.post("/payments/checkout")
async def create_checkout_session(request: Request, session_id: str, current_user: User = Depends(get_current_user)):
    return {"error": "Stripe integration temporarily disabled", "status": "disabled"}

@api_router.get("/payments/status/{stripe_session_id}")
async def get_payment_status(stripe_session_id: str, current_user: User = Depends(get_current_user)):
    return {"payment_status": "disabled", "status": "disabled"}

@api_router.post("/webhook/stripe")
async def stripe_webhook(request: Request):
    return {"status": "disabled"}

# Revenue endpoints for owners
@api_router.get("/owner/revenue/overview")
async def get_owner_revenue_overview(current_user: User = Depends(get_current_user)):
    """Get comprehensive revenue overview for owner"""
    if current_user.role != "owner":
        raise HTTPException(status_code=403, detail="Access denied. Owner role required.")
    
    # Get all parking spots owned by this user
    owner_spots = await db.parking_spots.find({"owner_id": current_user.id}).to_list(1000)
    spot_ids = [spot["id"] for spot in owner_spots]
    
    if not spot_ids:
        return {
            "total_revenue": 0.0,
            "total_sessions": 0,
            "average_session_value": 0.0,
            "spots_count": 0,
            "monthly_revenue": [],
            "daily_revenue": [],
            "weekly_revenue": [],
            "top_performing_spots": [],
            "recent_sessions": []
        }
    
    # Get all completed sessions for owner's spots
    completed_sessions = await db.parking_sessions.find({
        "spot_id": {"$in": spot_ids},
        "status": "ended",
        "total_amount": {"$gt": 0}
    }).sort([("end_time", -1)]).to_list(1000)
    
    # Calculate total revenue
    total_revenue = sum(session.get("total_amount", 0) for session in completed_sessions)
    total_sessions = len(completed_sessions)
    average_session_value = total_revenue / total_sessions if total_sessions > 0 else 0
    
    # Group by time periods
    now = datetime.utcnow()
    
    # Daily revenue (last 30 days)
    daily_revenue = {}
    for i in range(30):
        date = (now - timedelta(days=i)).strftime("%Y-%m-%d")
        daily_revenue[date] = 0.0
    
    # Weekly revenue (last 12 weeks)
    weekly_revenue = {}
    for i in range(12):
        week_start = now - timedelta(weeks=i)
        week_key = week_start.strftime("%Y-W%U")
        weekly_revenue[week_key] = 0.0
    
    # Monthly revenue (last 12 months)
    monthly_revenue = {}
    for i in range(12):
        date = now.replace(day=1) - timedelta(days=32*i)
        month_key = date.strftime("%Y-%m")
        monthly_revenue[month_key] = 0.0
    
    # Process sessions for time-based grouping
    spot_revenue = {}
    for session in completed_sessions:
        if session.get("end_time"):
            end_time = session["end_time"]
            amount = session.get("total_amount", 0)
            
            # Daily
            day_key = end_time.strftime("%Y-%m-%d")
            if day_key in daily_revenue:
                daily_revenue[day_key] += amount
            
            # Weekly
            week_key = end_time.strftime("%Y-W%U")
            if week_key in weekly_revenue:
                weekly_revenue[week_key] += amount
            
            # Monthly
            month_key = end_time.strftime("%Y-%m")
            if month_key in monthly_revenue:
                monthly_revenue[month_key] += amount
            
            # Spot performance
            spot_id = session["spot_id"]
            if spot_id not in spot_revenue:
                spot_revenue[spot_id] = {"revenue": 0, "sessions": 0}
            spot_revenue[spot_id]["revenue"] += amount
            spot_revenue[spot_id]["sessions"] += 1
    
    # Get top performing spots
    top_spots = []
    for spot in owner_spots:
        spot_id = spot["id"]
        if spot_id in spot_revenue:
            spot_data = spot_revenue[spot_id]
            top_spots.append({
                "spot_id": spot_id,
                "name": spot["name"],
                "address": spot["address"],
                "revenue": spot_data["revenue"],
                "sessions": spot_data["sessions"],
                "average_per_session": spot_data["revenue"] / spot_data["sessions"]
            })
    
    top_spots.sort(key=lambda x: x["revenue"], reverse=True)
    
    # Get recent sessions with spot details
    recent_sessions = []
    for session in completed_sessions[:10]:  # Last 10 sessions
        spot = next((s for s in owner_spots if s["id"] == session["spot_id"]), None)
        if spot:
            recent_sessions.append({
                "session_id": session["id"],
                "spot_name": spot["name"],
                "amount": session.get("total_amount", 0),
                "start_time": session.get("start_time"),
                "end_time": session.get("end_time"),
                "duration_hours": (session.get("end_time") - session.get("start_time")).total_seconds() / 3600 if session.get("end_time") and session.get("start_time") else 0
            })
    
    # Convert dictionaries to sorted lists
    daily_revenue_list = [{"date": k, "revenue": v} for k, v in sorted(daily_revenue.items())]
    weekly_revenue_list = [{"week": k, "revenue": v} for k, v in sorted(weekly_revenue.items())]
    monthly_revenue_list = [{"month": k, "revenue": v} for k, v in sorted(monthly_revenue.items())]
    
    return {
        "total_revenue": round(total_revenue, 2),
        "total_sessions": total_sessions,
        "average_session_value": round(average_session_value, 2),
        "spots_count": len(owner_spots),
        "daily_revenue": daily_revenue_list[-7:],  # Last 7 days
        "weekly_revenue": weekly_revenue_list[-4:],  # Last 4 weeks
        "monthly_revenue": monthly_revenue_list[-6:],  # Last 6 months
        "top_performing_spots": top_spots[:5],  # Top 5 spots
        "recent_sessions": recent_sessions
    }

@api_router.get("/owner/revenue/detailed/{period}")
async def get_detailed_revenue(period: str, current_user: User = Depends(get_current_user)):
    """Get detailed revenue for specific period (daily, weekly, monthly, yearly)"""
    if current_user.role != "owner":
        raise HTTPException(status_code=403, detail="Access denied. Owner role required.")
    
    if period not in ["daily", "weekly", "monthly", "yearly"]:
        raise HTTPException(status_code=400, detail="Invalid period. Use: daily, weekly, monthly, yearly")
    
    # Get all parking spots owned by this user
    owner_spots = await db.parking_spots.find({"owner_id": current_user.id}).to_list(1000)
    spot_ids = [spot["id"] for spot in owner_spots]
    
    if not spot_ids:
        return {"revenue_data": [], "total": 0.0}
    
    # Get all completed sessions
    completed_sessions = await db.parking_sessions.find({
        "spot_id": {"$in": spot_ids},
        "status": "ended",
        "total_amount": {"$gt": 0}
    }).sort([("end_time", -1)]).to_list(1000)
    
    # Group by period
    revenue_groups = {}
    now = datetime.utcnow()
    
    for session in completed_sessions:
        if session.get("end_time"):
            end_time = session["end_time"]
            amount = session.get("total_amount", 0)
            
            if period == "daily":
                key = end_time.strftime("%Y-%m-%d")
            elif period == "weekly":
                key = end_time.strftime("%Y-W%U")
            elif period == "monthly":
                key = end_time.strftime("%Y-%m")
            else:  # yearly
                key = end_time.strftime("%Y")
            
            if key not in revenue_groups:
                revenue_groups[key] = {
                    "period": key,
                    "revenue": 0.0,
                    "sessions": 0,
                    "unique_users": set()
                }
            
            revenue_groups[key]["revenue"] += amount
            revenue_groups[key]["sessions"] += 1
            revenue_groups[key]["unique_users"].add(session["user_id"])
    
    # Convert to list and clean up
    revenue_data = []
    for key, data in sorted(revenue_groups.items()):
        revenue_data.append({
            "period": data["period"],
            "revenue": round(data["revenue"], 2),
            "sessions": data["sessions"],
            "unique_users": len(data["unique_users"]),
            "average_per_session": round(data["revenue"] / data["sessions"], 2) if data["sessions"] > 0 else 0
        })
    
    total_revenue = sum(item["revenue"] for item in revenue_data)
    
    return {
        "revenue_data": revenue_data,
        "total": round(total_revenue, 2),
        "period_type": period
    }

# Hardware Management Endpoints
@api_router.post("/hardware/register")
async def register_hardware_device(device: HardwareDevice):
    """Register a new hardware device"""
    try:
        # In-memory fallback when DB is not available
        if MEMORY_MODE:
            device_dict = device.dict()
            # Accept registration even if spot doesn't exist; bind later via app
            memory_hardware_devices[device.hardware_id] = {
                **device_dict,
                "status": device_dict.get("status", "online"),
                "last_heartbeat": datetime.utcnow(),
            }
            # Optionally keep a placeholder spot mapping
            if device.spot_id:
                if device.spot_id not in memory_parking_spots:
                    memory_parking_spots[device.spot_id] = {
                        "id": device.spot_id,
                        "hardware_id": device.hardware_id,
                        "is_available": True,
                        "last_updated": datetime.utcnow(),
                    }
                else:
                    memory_parking_spots[device.spot_id]["hardware_id"] = device.hardware_id
                    memory_parking_spots[device.spot_id]["last_updated"] = datetime.utcnow()
            return {"message": "Hardware device registered (memory)", "device_id": device.id}

        # Check if hardware_id already exists
        existing = await db.hardware_devices.find_one({"hardware_id": device.hardware_id})
        if existing:
            raise HTTPException(status_code=400, detail="Hardware ID already registered")
        
        # Verify spot exists
        spot = await db.parking_spots.find_one({"id": device.spot_id})
        if not spot:
            raise HTTPException(status_code=404, detail="Parking spot not found")
        
        # Insert device
        device_dict = device.dict()
        await db.hardware_devices.insert_one(device_dict)
        
        # Update parking spot with hardware_id
        await db.parking_spots.update_one(
            {"id": device.spot_id},
            {"$set": {"hardware_id": device.hardware_id, "last_updated": datetime.utcnow()}}
        )
        
        return {"message": "Hardware device registered successfully", "device_id": device.id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/hardware/{hardware_id}/heartbeat")
async def hardware_heartbeat(hardware_id: str, status: HardwareStatus):
    """Receive heartbeat and status from hardware device"""
    try:
        # In-memory fallback when DB is not available
        if MEMORY_MODE:
            # Auto-register device if not present
            dev = memory_hardware_devices.get(hardware_id)
            if not dev:
                memory_hardware_devices[hardware_id] = {
                    "hardware_id": hardware_id,
                    "status": "online",
                    "battery_level": status.battery_level,
                    "solar_voltage": status.solar_voltage,
                    "last_heartbeat": datetime.utcnow(),
                }
            else:
                dev.update({
                    "status": "online",
                    "battery_level": status.battery_level,
                    "solar_voltage": status.solar_voltage,
                    "last_heartbeat": datetime.utcnow(),
                })

            # Update spot availability if we have a mapping
            for spot_id, spot in memory_parking_spots.items():
                if spot.get("hardware_id") == hardware_id:
                    spot["is_available"] = not status.is_occupied
                    spot["last_updated"] = datetime.utcnow()
                    break

            return {"message": "Heartbeat received (memory)", "command": "continue"}

        # Update device status
        update_data = {
            "last_heartbeat": datetime.utcnow(),
            "status": "online",
            "battery_level": status.battery_level,
            "solar_voltage": status.solar_voltage
        }
        
        result = await db.hardware_devices.update_one(
            {"hardware_id": hardware_id},
            {"$set": update_data}
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Hardware device not found")
        
        # Update parking spot availability
        spot_update = await db.parking_spots.update_one(
            {"hardware_id": hardware_id},
            {"$set": {
                "is_available": not status.is_occupied,
                "last_updated": datetime.utcnow()
            }}
        )
        
        # Store sensor reading
        sensor_reading = SensorReading(
            hardware_id=hardware_id,
            sensor_type="occupancy",
            value=1.0 if status.is_occupied else 0.0,
            unit="boolean"
        )
        await db.sensor_readings.insert_one(sensor_reading.dict())
        
        return {"message": "Heartbeat received", "command": "continue"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/hardware/{hardware_id}/command")
async def send_hardware_command(hardware_id: str, command: HardwareCommand, current_user: User = Depends(get_current_user)):
    """Send command to hardware device"""
    try:
        # Verify device exists and user has permission
        device = await db.hardware_devices.find_one({"hardware_id": hardware_id})
        if not device:
            raise HTTPException(status_code=404, detail="Hardware device not found")
        
        # Get associated parking spot
        spot = await db.parking_spots.find_one({"hardware_id": hardware_id})
        if not spot:
            raise HTTPException(status_code=404, detail="Associated parking spot not found")
        
        # Check permissions (owner or active session user)
        if current_user.role not in ["admin", "owner"] and spot["owner_id"] != current_user.id:
            # Check if user has active session for this spot
            active_session = await db.parking_sessions.find_one({
                "user_id": current_user.id,
                "spot_id": spot["id"],
                "status": "active"
            })
            if not active_session:
                raise HTTPException(status_code=403, detail="Access denied")
        
        # Store command
        command.issued_by = current_user.id
        command_dict = command.dict()
        await db.hardware_commands.insert_one(command_dict)
        
        return {"message": "Command queued", "command_id": command_dict["id"]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/hardware/{hardware_id}/commands")
async def get_pending_commands(hardware_id: str):
    """Get pending commands for hardware device"""
    try:
        if MEMORY_MODE:
            # Serve and clear in-memory commands for this hardware
            queued = memory_hardware_commands.get(hardware_id, [])
            # Convert to HardwareCommand-like objects
            cmds = []
            for cmd in queued:
                cmds.append(HardwareCommand(**{
                    "hardware_id": hardware_id,
                    "command": cmd.get("command"),
                    "parameters": cmd.get("parameters", {}),
                    "issued_by": cmd.get("issued_by", "memory"),
                    "created_at": cmd.get("created_at", datetime.utcnow())
                }))
            # Clear queue after serving
            memory_hardware_commands[hardware_id] = []
            return {"commands": cmds}
        # Get unprocessed commands
        commands = await db.hardware_commands.find({
            "hardware_id": hardware_id,
            "processed": {"$ne": True}
        }).sort([("created_at", 1)]).to_list(10)
        
        # Mark as processed
        if commands:
            command_ids = [cmd["_id"] for cmd in commands]
            await db.hardware_commands.update_many(
                {"_id": {"$in": command_ids}},
                {"$set": {"processed": True, "processed_at": datetime.utcnow()}}
            )
        
        return {"commands": [HardwareCommand(**cmd) for cmd in commands]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/hardware/{hardware_id}/commands/queue")
async def queue_command_simple(hardware_id: str, request: Request):
    """
    Lightweight dev endpoint to enqueue a command in MEMORY_MODE without auth.
    Body JSON: {"command": "raise_barrier"|"lower_barrier"|..., "parameters": {...}, "secret": "<optional>"}
    If SIMPLE_COMMAND_SECRET is set, it must match.
    """
    try:
        body = await request.json()
        cmd = body.get("command")
        params = body.get("parameters", {})
        secret = body.get("secret", "")
        if not MEMORY_MODE:
            raise HTTPException(status_code=400, detail="Not available when DB is enabled")
        if SIMPLE_COMMAND_SECRET and secret != SIMPLE_COMMAND_SECRET:
            raise HTTPException(status_code=401, detail="Invalid secret")
        if not cmd:
            raise HTTPException(status_code=400, detail="Missing 'command'")
        # Auto-register device in memory if needed
        if hardware_id not in memory_hardware_devices:
            memory_hardware_devices[hardware_id] = {
                "hardware_id": hardware_id,
                "status": "online",
                "last_heartbeat": datetime.utcnow(),
            }
        # Enqueue
        q = memory_hardware_commands.setdefault(hardware_id, [])
        q.append({
            "id": str(uuid.uuid4()),
            "hardware_id": hardware_id,
            "command": cmd,
            "parameters": params,
            "issued_by": "simple",
            "created_at": datetime.utcnow(),
        })
        return {"message": "Command queued (memory)", "hardware_id": hardware_id, "count": len(q)}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/owner/hardware")
async def get_owner_hardware(current_user: User = Depends(get_current_user)):
    """Get all hardware devices for owner's parking spots"""
    if current_user.role != "owner":
        raise HTTPException(status_code=403, detail="Access denied. Owner role required.")
    
    try:
        # Get owner's spots
        owner_spots = await db.parking_spots.find({"owner_id": current_user.id}).to_list(1000)
        spot_ids = [spot["id"] for spot in owner_spots]
        
        if not spot_ids:
            return {"devices": []}
        
        # Get hardware devices for these spots
        devices = await db.hardware_devices.find({
            "spot_id": {"$in": spot_ids}
        }).to_list(1000)
        
        # Enrich with spot information
        enriched_devices = []
        for device in devices:
            spot = next((s for s in owner_spots if s["id"] == device["spot_id"]), None)
            if spot:
                device_dict = device.copy()
                device_dict["spot_name"] = spot["name"]
                device_dict["spot_address"] = spot["address"]
                enriched_devices.append(device_dict)
        
        return {"devices": enriched_devices}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Log selected data mode for hardware endpoints
if MEMORY_MODE:
    logger.info("Hardware endpoints running in MEMORY_MODE (MongoDB disabled or FORCE_MEMORY_MODE=1)")
else:
    logger.info("Hardware endpoints using MongoDB (MEMORY_MODE disabled)")

@app.on_event("shutdown")
async def shutdown_db_client():
    try:
        if client is not None:
            client.close()
    except Exception:
        pass

# Health endpoints (no DB access required)
@app.get("/health")
async def health_root():
    return {"status": "ok"}

@api_router.get("/health")
async def api_health():
    return {"status": "ok"}