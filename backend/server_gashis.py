from fastapi import FastAPI, HTTPException, Depends, Form, Request, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr, SecretStr
from typing import List, Optional
import sqlite3
import json
import os
from datetime import datetime, timedelta
from backend import auth
"""Optional import of graph_mailer.
If dependencies (httpx/msal) are missing or the module errors at import time,
we degrade gracefully so the API can still start and /health works.
"""
try:
    from backend import graph_mailer  # type: ignore
except Exception as e:  # broad: any import/init failure
    class _GraphMailerStub:
        async def send_verification_email(self, recipient_email: str, verification_link: str):
            print(f"[graph_mailer:stub] Email disabled (import failed: {e}); would send to {recipient_email} link={verification_link}")

    graph_mailer = _GraphMailerStub()  # type: ignore
import secrets
from starlette.responses import RedirectResponse
from sqlalchemy.orm import Session
from dotenv import load_dotenv
import pathlib
import asyncio
import time
import requests
from collections import defaultdict, deque

# Load environment variables from .env file in parent directory
env_path = pathlib.Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

# Dependency to get DB session
def get_db():
    db = auth.SessionLocal()
    try:
        yield db
    finally:
        db.close()

# FastAPI App für gashis.ch
app = FastAPI(
    title="Gashis Parking API",
    description="Smart Parking System für die Schweiz",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Simple health & version endpoint (used by docker-compose healthcheck)
@app.get("/health")
async def health():
    commit = os.environ.get("BACKEND_COMMIT_SHA") or _read_version_file()
    return {"status": "ok", "commit": commit, "time": datetime.utcnow().isoformat(timespec='seconds')}

def _read_version_file():
    try:
        vf = pathlib.Path(__file__).parent / 'version.txt'
        if vf.exists():
            return vf.read_text().strip()[:64]
    except Exception:
        pass
    return "unknown"

# CORS für gashis.ch
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://gashis.ch",
        "https://www.gashis.ch", 
        "https://parking.gashis.ch",
        "http://localhost:3000",  # Für lokale Entwicklung
        "http://127.0.0.1:3000",   # Alternative localhost
        "http://192.168.1.110:3000"  # On-your-network Dev-Link (Beispiel)
    ],
    # Erlaube zusätzlich alle 192.168.X.X:3000 Origins in Dev via Regex
    allow_origin_regex=r"http://(localhost|127\\.0\\.0\\.1|192\\.168\\.\\d{1,3}\\.\\d{1,3}):3000",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database Setup
DATABASE_PATH = os.path.join(os.path.dirname(__file__), "parking.db")

def init_database():
    """Initialize SQLite database with tables and demo data"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    # Create parking_spots table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS parking_spots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            address TEXT,
            latitude REAL NOT NULL,
            longitude REAL NOT NULL,
            status TEXT DEFAULT 'free',
            price_per_hour REAL DEFAULT 0.0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create users table (simple)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Create hardware devices table: maps hardware_id -> owner_email and parking_spot
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS hardware_devices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            hardware_id TEXT UNIQUE NOT NULL,
            owner_email TEXT,
            parking_spot_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    # Add telemetry columns if they don't exist (nullable)
    try:
        cursor.execute("ALTER TABLE hardware_devices ADD COLUMN last_heartbeat TIMESTAMP")
    except Exception:
        pass
    try:
        cursor.execute("ALTER TABLE hardware_devices ADD COLUMN battery_level REAL")
    except Exception:
        pass
    try:
        cursor.execute("ALTER TABLE hardware_devices ADD COLUMN rssi INTEGER")
    except Exception:
        pass
    try:
        cursor.execute("ALTER TABLE hardware_devices ADD COLUMN occupancy TEXT")
    except Exception:
        pass
    try:
        cursor.execute("ALTER TABLE hardware_devices ADD COLUMN last_mag JSON")
    except Exception:
        pass

    # Create persistent hardware commands queue
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS hardware_commands (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            hardware_id TEXT NOT NULL,
            command TEXT NOT NULL,
            parameters TEXT,
            status TEXT DEFAULT 'queued', -- queued | sent | done | failed
            issued_by TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            claimed_at TIMESTAMP,
            executed_at TIMESTAMP
        )
    ''')
    
    # Check if we have demo data
    cursor.execute('SELECT COUNT(*) FROM parking_spots')
    if cursor.fetchone()[0] == 0:
        # Insert Swiss demo data
        demo_spots = [
            ("Zürich HB Parkhaus Sihlquai", "Sihlquai 41, 8005 Zürich", 47.3769, 8.5417, "free", 4.50),
            ("Basel SBB Centralbahnplatz", "Centralbahnpl. 20, 4051 Basel", 47.5474, 7.5892, "occupied", 3.80),
            ("Bern Bahnhof Parking", "Bahnhofplatz 10A, 3011 Bern", 46.9481, 7.4474, "free", 4.20),
            ("Genève Aéroport P51", "Route de l'Aéroport 21, 1215 Genève", 46.2044, 6.1432, "free", 5.00),
            ("Luzern Parkhaus Bahnhof", "Bahnhofstrasse 3, 6003 Luzern", 47.0502, 8.3093, "occupied", 3.90),
            ("St. Gallen Bahnhof", "Bahnhofplatz 1A, 9001 St. Gallen", 47.4245, 9.3767, "free", 3.50),
            ("Winterthur Zentrum", "Stadthausstrasse 1, 8400 Winterthur", 47.4979, 8.7211, "free", 3.20),
            ("Lausanne Gare CFF", "Place de la Gare 9, 1003 Lausanne", 46.5197, 6.6323, "occupied", 4.00)
        ]
        
        for spot in demo_spots:
            cursor.execute('''
                INSERT INTO parking_spots (name, address, latitude, longitude, status, price_per_hour)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', spot)
    
    conn.commit()
    conn.close()
    print("✅ Database initialized with Swiss demo data!")

# Initialize database on startup
init_database()
# Initialize auth DB (SQLAlchemy models)
try:
    auth.init_db()
except Exception:
    # If SQLAlchemy or DB libs are not installed yet, init_db will fail during dev; ignore for now
    pass

# Pydantic Models
class ParkingSpot(BaseModel):
    id: Optional[int] = None
    name: str
    address: Optional[str] = None
    latitude: float
    longitude: float
    status: str = "free"  # free, occupied, reserved
    price_per_hour: float = 0.0

class User(BaseModel):
    id: Optional[int] = None
    email: str
    name: str

    # Optional: simple role field for demo auth
    # (nicht Teil der SQLite-Users-Tabelle, nur für Response)
    # Werte: "user" | "owner" | "admin"
    # Wird im Login-Endpoint gesetzt
    # Hinweis: Für produktive Nutzung bitte echtes Auth-Backend verwenden
    # (z.B. PHP-API oder vollwertiges FastAPI-Auth)
    

# Telemetry model for hardware devices
class HardwareTelemetry(BaseModel):
    battery_level: Optional[float] = None
    rssi: Optional[int] = None
    occupancy: Optional[str] = None
    last_mag: Optional[dict] = None  # e.g. {"x":...,"y":...,"z":...}
    timestamp: Optional[datetime] = None

# API Routes
@app.get("/")
async def root():
    return {
        "message": "Gashis Parking API ist online! 🚗",
        "domain": "gashis.ch",
        "version": "1.0.0",
        "docs": "/docs",
        "status": "active"
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now()}

@app.get("/parking-spots", response_model=List[ParkingSpot])
async def get_parking_spots():
    """Get all parking spots"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, name, address, latitude, longitude, status, price_per_hour
            FROM parking_spots
            ORDER BY name
        ''')
        
        spots = []
        for row in cursor.fetchall():
            spots.append({
                "id": row[0],
                "name": row[1],
                "address": row[2],
                "latitude": row[3],
                "longitude": row[4], 
                "status": row[5],
                "price_per_hour": row[6]
            })
        
        conn.close()
        return spots
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.get("/parking-spots/{spot_id}", response_model=ParkingSpot)
async def get_parking_spot(spot_id: int):
    """Get specific parking spot"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, name, address, latitude, longitude, status, price_per_hour
            FROM parking_spots WHERE id = ?
        ''', (spot_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            raise HTTPException(status_code=404, detail="Parking spot not found")
        
        return {
            "id": row[0],
            "name": row[1],
            "address": row[2],
            "latitude": row[3],
            "longitude": row[4],
            "status": row[5],
            "price_per_hour": row[6]
        }
        
    except sqlite3.Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

# =====================
#  Einfaches Local-Auth
# =====================

# Pydantic Models for request bodies
class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str
    role: str = "user"

# Dependency to parse form data into UserCreate model
async def get_user_create_form(
    name: str = Form(...),
    email: EmailStr = Form(...),
    password: str = Form(...),
    role: str = Form("user")
) -> UserCreate:
    return UserCreate(name=name, email=email, password=password, role=role)


@app.post("/login.php")
async def login_php_mock(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Handles user login, checking for verification status.
    """
    # Try to parse as JSON first, then fall back to form data
    content_type = request.headers.get("content-type", "")
    
    if "application/json" in content_type:
        body = await request.json()
        email = body.get("email")
        password = body.get("password")
    else:
        # Parse form data
        form = await request.form()
        email = form.get("email")
        password = form.get("password")
    
    user = auth.authenticate_user(db, email, password)

    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password")

    # Allow optional bypass for testing if env set
    allow_unverified = os.environ.get("ALLOW_UNVERIFIED_LOGIN", "false").lower() == "true"
    if not user.is_verified and not allow_unverified:
        raise HTTPException(status_code=403, detail="Account not verified. Please check your email.")
    elif not user.is_verified and allow_unverified:
        # Mark verified on first successful login if bypass enabled
        user.is_verified = True
        db.commit()

    token = auth.create_access_token(user.email, user.id, user.role)
    
    # Update last_login
    user.last_login = datetime.utcnow()
    db.commit()

    return {
        "token": token,
        "user": {"id": user.id, "email": user.email, "name": user.name, "role": user.role},
    }

@app.get("/user/profile")
async def get_user_profile(
    request: Request,
    db: Session = Depends(get_db)
):
    """Get current user's profile"""
    # Extract user from JWT token
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    token = auth_header.replace("Bearer ", "")
    try:
        user_data = auth.decode_token(token)
        if not user_data:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        user_id = user_data.get("user_id")
        
        user = db.query(auth.User).filter(auth.User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        return {
            "id": user.id,
            "email": user.email,
            "name": user.name,
            "role": user.role,
            "created_at": user.created_at.isoformat() if user.created_at else None,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "phone": user.phone,
            "address": user.address,
            "house_number": user.house_number,
            "city": user.city,
            "zip_code": user.zip_code,
            "country": user.country,
            "secondary_email": user.secondary_email,
            "date_of_birth": user.date_of_birth.isoformat() if user.date_of_birth else None
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")

@app.put("/user/profile")
async def update_user_profile(
    request: Request,
    db: Session = Depends(get_db)
):
    """Update current user's profile"""
    # Extract user from JWT token
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    token = auth_header.replace("Bearer ", "")
    try:
        user_data = auth.decode_token(token)
        if not user_data:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        user_id = user_data.get("user_id")
        
        user = db.query(auth.User).filter(auth.User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Get update data
        body = await request.json()
        
        # Update allowed fields
        if "name" in body:
            user.name = body["name"]
        if "email" in body:
            # Check if email is already taken by another user
            existing_user = db.query(auth.User).filter(
                auth.User.email == body["email"],
                auth.User.id != user_id
            ).first()
            if existing_user:
                raise HTTPException(status_code=409, detail="Email already in use")
            user.email = body["email"]
        
        # Update additional profile fields
        if "first_name" in body:
            user.first_name = body["first_name"]
        if "last_name" in body:
            user.last_name = body["last_name"]
        if "phone" in body:
            user.phone = body["phone"]
        if "address" in body:
            user.address = body["address"]
        if "house_number" in body:
            user.house_number = body["house_number"]
        if "city" in body:
            user.city = body["city"]
        if "zip_code" in body:
            user.zip_code = body["zip_code"]
        if "country" in body:
            user.country = body["country"]
        if "secondary_email" in body:
            user.secondary_email = body["secondary_email"]
        if "date_of_birth" in body and body["date_of_birth"]:
            # Parse date string to datetime
            from datetime import datetime
            try:
                user.date_of_birth = datetime.fromisoformat(body["date_of_birth"].replace('Z', '+00:00'))
            except:
                # If it's just a date (YYYY-MM-DD), parse it
                user.date_of_birth = datetime.strptime(body["date_of_birth"], "%Y-%m-%d")
        
        db.commit()
        db.refresh(user)
        
        return {
            "id": user.id,
            "email": user.email,
            "name": user.name,
            "role": user.role,
            "created_at": user.created_at.isoformat() if user.created_at else None,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "phone": user.phone,
            "address": user.address,
            "house_number": user.house_number,
            "city": user.city,
            "zip_code": user.zip_code,
            "country": user.country,
            "secondary_email": user.secondary_email,
            "date_of_birth": user.date_of_birth.isoformat() if user.date_of_birth else None
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating profile: {str(e)}")

# Owner Parking Spots Management
@app.get("/owner/parking-spots")
async def get_owner_parking_spots(
    request: Request,
    db: Session = Depends(get_db)
):
    """Get all parking spots owned by the current user"""
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    token = auth_header.replace("Bearer ", "")
    try:
        user_data = auth.decode_token(token)
        if not user_data:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        user_id = user_data.get("user_id")
        role = user_data.get("role")
        
        if role != "owner":
            raise HTTPException(status_code=403, detail="Only owners can access this endpoint")
        
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, name, address, latitude, longitude, status, price_per_hour, owner_id
            FROM parking_spots
            WHERE owner_id = ?
            ORDER BY name
        ''', (user_id,))
        
        spots = []
        for row in cursor.fetchall():
            spots.append({
                "id": row[0],
                "name": row[1],
                "address": row[2],
                "latitude": row[3],
                "longitude": row[4],
                "status": row[5],
                "price_per_hour": row[6],
                "owner_id": row[7]
            })
        
        conn.close()
        return spots
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@app.post("/owner/parking-spots")
async def create_parking_spot(
    request: Request,
    db: Session = Depends(get_db)
):
    """Create a new parking spot (owner only)"""
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    token = auth_header.replace("Bearer ", "")
    try:
        user_data = auth.decode_token(token)
        if not user_data:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        user_id = user_data.get("user_id")
        role = user_data.get("role")
        
        if role != "owner":
            raise HTTPException(status_code=403, detail="Only owners can create parking spots")
        
        body = await request.json()
        
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO parking_spots (name, address, latitude, longitude, status, price_per_hour, owner_id)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            body.get('name'),
            body.get('address'),
            body.get('latitude'),
            body.get('longitude'),
            body.get('status', 'free'),
            body.get('price_per_hour', 0.0),
            user_id
        ))
        
        spot_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return {"id": spot_id, "message": "Parking spot created successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@app.put("/owner/parking-spots/{spot_id}")
async def update_parking_spot(
    spot_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    """Update a parking spot (owner only)"""
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    token = auth_header.replace("Bearer ", "")
    try:
        user_data = auth.decode_token(token)
        if not user_data:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        user_id = user_data.get("user_id")
        role = user_data.get("role")
        
        if role != "owner":
            raise HTTPException(status_code=403, detail="Only owners can update parking spots")
        
        body = await request.json()
        
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        # Check if user owns this spot
        cursor.execute('SELECT owner_id FROM parking_spots WHERE id = ?', (spot_id,))
        result = cursor.fetchone()
        
        if not result:
            conn.close()
            raise HTTPException(status_code=404, detail="Parking spot not found")
        
        if result[0] != user_id:
            conn.close()
            raise HTTPException(status_code=403, detail="You don't own this parking spot")
        
        # Update the spot
        updates = []
        params = []
        
        if 'name' in body:
            updates.append('name = ?')
            params.append(body['name'])
        if 'address' in body:
            updates.append('address = ?')
            params.append(body['address'])
        if 'latitude' in body:
            updates.append('latitude = ?')
            params.append(body['latitude'])
        if 'longitude' in body:
            updates.append('longitude = ?')
            params.append(body['longitude'])
        if 'status' in body:
            updates.append('status = ?')
            params.append(body['status'])
        if 'price_per_hour' in body:
            updates.append('price_per_hour = ?')
            params.append(body['price_per_hour'])
        
        params.append(spot_id)
        
        if updates:
            cursor.execute(f'''
                UPDATE parking_spots 
                SET {', '.join(updates)}
                WHERE id = ?
            ''', params)
        
        conn.commit()
        conn.close()
        
        return {"message": "Parking spot updated successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@app.delete("/owner/parking-spots/{spot_id}")
async def delete_parking_spot(
    spot_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    """Delete a parking spot (owner only)"""
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    token = auth_header.replace("Bearer ", "")
    try:
        user_data = auth.decode_token(token)
        if not user_data:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        user_id = user_data.get("user_id")
        role = user_data.get("role")
        
        if role != "owner":
            raise HTTPException(status_code=403, detail="Only owners can delete parking spots")
        
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        # Check if user owns this spot
        cursor.execute('SELECT owner_id FROM parking_spots WHERE id = ?', (spot_id,))
        result = cursor.fetchone()
        
        if not result:
            conn.close()
            raise HTTPException(status_code=404, detail="Parking spot not found")
        
        if result[0] != user_id:
            conn.close()
            raise HTTPException(status_code=403, detail="You don't own this parking spot")
        
        cursor.execute('DELETE FROM parking_spots WHERE id = ?', (spot_id,))
        conn.commit()
        conn.close()
        
        return {"message": "Parking spot deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@app.post("/register.php", response_model=dict)
async def register_php_mock(
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    print("--- REGISTER ENDPOINT HIT ---")
    try:
        # Try to parse as JSON first, then fall back to form data
        content_type = request.headers.get("content-type", "")
        
        if "application/json" in content_type:
            body = await request.json()
            user_data = UserCreate(**body)
        else:
            # Parse form data
            form = await request.form()
            user_data = UserCreate(
                name=form.get("name"),
                email=form.get("email"),
                password=form.get("password"),
                role=form.get("role", "user")
            )
        
        print(f"Registering user: {user_data.email} with role: {user_data.role}")
        
        # Check if user already exists
        db_user = db.query(auth.User).filter(auth.User.email == user_data.email).first()
        if db_user:
            raise HTTPException(status_code=409, detail="Email already registered")

        # Create user but mark as unverified
        new_user = auth.create_user(db, name=user_data.name, email=user_data.email, password=user_data.password, role=user_data.role)

        # Optional auto-verify if email service not configured and AUTO_VERIFY_ON_EMAIL_FAILURE=true
        auto_verify = os.environ.get("AUTO_VERIFY_ON_EMAIL_FAILURE", "false").lower() == "true"
        
        # Der Token wird jetzt direkt in create_user gesetzt und muss hier nicht mehr manuell hinzugefügt werden.
        # Wir müssen nur committen, um die ID zu bekommen und den Token abrufen zu können.
        db.commit()
        db.refresh(new_user)

        # Build verification link using the correct endpoint name
        verification_link = request.url_for('verify_email', token=new_user.verification_token)

        # Send email in the background
        try:
            background_tasks.add_task(
                graph_mailer.send_verification_email,
                recipient_email=new_user.email,
                verification_link=str(verification_link)
            )
            print(f"✅ Verification email task for {new_user.email} queued.")
            print(f"📧 Verification link: {verification_link}")
        except Exception as mail_err:
            print(f"⚠️ Email sending failed: {mail_err}")
            if auto_verify:
                new_user.is_verified = True
                db.commit()
                db.refresh(new_user)
                print("Auto-verified user due to email failure and AUTO_VERIFY_ON_EMAIL_FAILURE=true")

        return {"message": "Registration successful. Please check your email to verify your account."}
    except HTTPException as e:
        # Re-raise HTTPException to preserve status code and detail
        raise e
    except Exception as e:
        # Log the unexpected error for debugging
        print(f"An unexpected error occurred during registration: {e}")
        # Return a generic error to the user
        raise HTTPException(status_code=500, detail="An unexpected internal error occurred.")
    finally:
        db.close()


@app.post("/parking-spots", response_model=ParkingSpot)
async def create_parking_spot(spot: ParkingSpot):
    """Create new parking spot"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO parking_spots (name, address, latitude, longitude, status, price_per_hour)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (spot.name, spot.address, spot.latitude, spot.longitude, spot.status, spot.price_per_hour))
        
        spot_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        spot.id = spot_id
        return spot
        
    except sqlite3.Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.put("/parking-spots/{spot_id}/status")
async def update_spot_status(spot_id: int, status: dict):
    """Update parking spot status"""
    try:
        new_status = status.get("status")
        if new_status not in ["free", "occupied", "reserved"]:
            raise HTTPException(status_code=400, detail="Invalid status")
        
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE parking_spots SET status = ?
            WHERE id = ?
        ''', (new_status, spot_id))
        
        if cursor.rowcount == 0:
            conn.close()
            raise HTTPException(status_code=404, detail="Parking spot not found")
        
        conn.commit()
        conn.close()
        
        return {"message": "Status updated successfully", "spot_id": spot_id, "new_status": new_status}
        
    except sqlite3.Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.post("/parking-spots/{spot_id}/status")
async def update_spot_status_post(spot_id: int, status: dict):
    """POST-Alias für Status-Update (für Modems, die PUT schwer unterstützen)."""
    try:
        new_status = status.get("status")
        if new_status not in ["free", "occupied", "reserved"]:
            raise HTTPException(status_code=400, detail="Invalid status")

        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()

        cursor.execute('''
            UPDATE parking_spots SET status = ?
            WHERE id = ?
        ''', (new_status, spot_id))

        if cursor.rowcount == 0:
            conn.close()
            raise HTTPException(status_code=404, detail="Parking spot not found")

        conn.commit()
        conn.close()

        return {"message": "Status updated successfully (POST)", "spot_id": spot_id, "new_status": new_status}
        
    except sqlite3.Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.get("/stats")
async def get_stats():
    """Get parking statistics"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        # Count spots by status
        cursor.execute('''
            SELECT status, COUNT(*) 
            FROM parking_spots 
            GROUP BY status
        ''')
        
        stats = {"total": 0, "free": 0, "occupied": 0, "reserved": 0}
        for row in cursor.fetchall():
            status, count = row
            stats[status] = count
            stats["total"] += count
        
        conn.close()
        return stats
        
    except sqlite3.Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    
@app.get("/parking-sessions")
async def get_parking_sessions():
    """Stub: returns an empty list to satisfy frontend calls during local dev"""
    return []

@app.get("/parking-sessions/history")
async def get_parking_sessions_history():
    """Stub: returns an empty history list for local dev"""
    return []


# -----------------------------
# Geo search proxy (Nominatim)
# -----------------------------

# Simple in-memory cache for geo queries
_GEO_CACHE: dict = {}
_GEO_CACHE_TTL_SECONDS = 60
_GEO_RATE_LOCK = asyncio.Lock()
_GEO_LAST_CALL_TS = 0.0


def _geo_cache_key(q: str, limit: int, countrycodes: str) -> str:
    return f"q={q.strip().lower()}|limit={limit}|country={countrycodes}"


def _geo_cache_get(key: str):
    entry = _GEO_CACHE.get(key)
    if not entry:
        return None
    ts, data = entry
    if (time.time() - ts) <= _GEO_CACHE_TTL_SECONDS:
        return data
    # expired
    try:
        del _GEO_CACHE[key]
    except Exception:
        pass
    return None


def _geo_cache_put(key: str, data):
    _GEO_CACHE[key] = (time.time(), data)


@app.get("/geo/search")
async def geo_search(q: str, limit: int = 8, countrycodes: str = "ch"):
    """Proxy endpoint to query Nominatim for address/business suggestions.

    - Enforces a minimal query length (>= 2)
    - Adds User-Agent as required by Nominatim usage policy
    - Caches responses briefly and applies a simple global rate-limit
    - Normalizes the response for the frontend
    """
    query = (q or "").strip()
    # Log incoming request (lightweight for debugging)
    try:
        print(f"[GEO] incoming query='{query}' limit={limit} countrycodes={countrycodes}")
    except Exception:
        pass
    if len(query) < 1:
        return []

    # Check cache
    cache_key = _geo_cache_key(query, limit, countrycodes)
    cached = _geo_cache_get(cache_key)
    if cached is not None:
        return cached

    # Simple global rate-limit: max ~1 request/sec
    global _GEO_LAST_CALL_TS
    async with _GEO_RATE_LOCK:
        now = time.time()
        delta = now - _GEO_LAST_CALL_TS
        if delta < 1.0:
            await asyncio.sleep(1.0 - delta)
        _GEO_LAST_CALL_TS = time.time()

    # Build Nominatim query
    base_url = "https://nominatim.openstreetmap.org/search"
    params = {
        "format": "json",
        "addressdetails": 1,
        "limit": max(1, min(int(limit), 10)),  # be gentle
        "countrycodes": countrycodes,
        "q": query,
    }
    headers = {
        # Provide a UA per Nominatim policy (replace with your proper contact email/domain)
        "User-Agent": "gashis-parking/1.0 (contact: info@gashis.ch)",
    }

    try:
        # Perform request in thread executor to avoid blocking the event loop
        loop = asyncio.get_event_loop()
        resp = await loop.run_in_executor(
            None,
            lambda: requests.get(base_url, params=params, headers=headers, timeout=8)
        )
        if resp.status_code != 200:
            # graceful degrade
            return []
        data = resp.json()
        results = []
        for item in data:
            try:
                # classify as business if typical POI properties exist
                poi_fields = (item.get("amenity") or item.get("shop") or item.get("tourism") or item.get("office") or item.get("leisure") or item.get("craft"))
                source = "business" if poi_fields else "address"
                results.append({
                    "display_name": item.get("display_name"),
                    "lat": float(item.get("lat")),
                    "lon": float(item.get("lon")),
                    "type": item.get("type"),
                    "address": (item.get("display_name") or "").split(',')[0],
                    "source": source
                })
            except Exception:
                continue

        # Deduplicate by lat/lon
        seen = set()
        unique = []
        for r in results:
            key = f"{r['lat']},{r['lon']}"
            if key not in seen:
                seen.add(key)
                unique.append(r)

        _geo_cache_put(cache_key, unique)
        try:
            print(f"[GEO] results={len(unique)} for query='{query}'")
        except Exception:
            pass
        return unique
    except Exception:
        # On error, return empty to allow frontend fallback
        return []


# -----------------------------
# Hardware command queue (dev-mode)
# -----------------------------
from fastapi import Header, Request


@app.post("/api/hardware/{hardware_id}/commands/queue")
async def queue_hardware_command(hardware_id: str, request: Request, authorization: str = Header(None)):
    """Development-only endpoint: accept hardware commands from the frontend and respond with a queued status.

    Authorization: expects the demo token format `Bearer dev-token-<role>` where role is user/owner/admin.
    Only `owner` and `admin` are allowed to queue hardware commands in this dev shim.
    """
    try:
        body = await request.json()
    except Exception:
        body = {}

    # Parse role from demo token or real JWT
    role = None
    token = None
    if authorization:
        if authorization.startswith("Bearer "):
            token = authorization.split(" ", 1)[1]
        else:
            token = authorization

    if token and token.startswith("dev-token-"):
        role = token.replace("dev-token-", "")
    elif token:
        # Try to decode real JWT token
        payload = auth.decode_token(token)
        if payload:
            role = payload.get('role')

    if role not in ("owner", "admin"):
        raise HTTPException(status_code=403, detail="Forbidden: insufficient role to control hardware")

    cmd = body.get("command") if isinstance(body, dict) else None
    params = body.get("parameters") if isinstance(body, dict) else None

    # Persist command to DB
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO hardware_commands (hardware_id, command, parameters, issued_by)
            VALUES (?, ?, ?, ?)
        """, (hardware_id, cmd, json.dumps(params) if params is not None else None, authorization))
        cmd_id = cursor.lastrowid
        conn.commit()
        conn.close()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to queue command: {e}")

    print(f"[HARDWARE-QUEUE] id={cmd_id} hardware={hardware_id} cmd={cmd} by={role}")
    return {"status": "queued", "id": cmd_id, "hardware_id": hardware_id, "command": cmd, "parameters": params}


@app.get("/api/hardware/{hardware_id}/commands")
async def poll_hardware_commands(hardware_id: str):
    """Device polling endpoint: returns queued commands for the hardware and marks them as sent."""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, command, parameters, created_at FROM hardware_commands
            WHERE hardware_id = ? AND status = 'queued'
            ORDER BY created_at ASC
        ''', (hardware_id,))
        rows = cursor.fetchall()
        cmds = []
        now = datetime.now()
        for row in rows:
            cmd_id, command, parameters, created_at = row
            params = None
            if parameters:
                try:
                    params = json.loads(parameters)
                except Exception:
                    params = parameters
            cmds.append({"id": cmd_id, "command": command, "parameters": params, "created_at": created_at})

        # mark them as sent
        if rows:
            ids = [str(r[0]) for r in rows]
            cursor.execute(f"UPDATE hardware_commands SET status = 'sent', claimed_at = ? WHERE id IN ({','.join(['?']*len(ids))})", tuple([now.isoformat()]+ids))
            conn.commit()

        conn.close()
        return {"commands": cmds}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Polling error: {e}")


@app.post("/api/hardware/{hardware_id}/commands/{cmd_id}/ack")
async def ack_hardware_command(hardware_id: str, cmd_id: int, payload: dict = None):
    """Device acknowledges execution of a command (sets status=done)."""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE hardware_commands SET status = 'done', executed_at = ? WHERE id = ? AND hardware_id = ?
        ''', (datetime.now(), cmd_id, hardware_id))
        conn.commit()
        conn.close()
        return {"status": "acknowledged", "id": cmd_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ack error: {e}")


 


# -------------------------------------------------
# Unified Autocomplete Endpoint (Photon + Nominatim)
# -------------------------------------------------
# In-Memory cache + rate limiting (simple best-effort, resets on restart)
_AC_CACHE: dict = {}
_AC_CACHE_TTL_SECONDS = 300  # 5 minutes

_AC_RATE_BUCKETS = defaultdict(deque)  # ip -> deque[timestamps]
_AC_RATE_LIMIT_MAX = 30  # max requests per window per IP
_AC_RATE_LIMIT_WINDOW = 60  # seconds


def _ac_cache_key(q: str, limit: int, countrycodes: str, lat: float, lon: float) -> str:
    return f"q={q.lower().strip()}|limit={limit}|cc={countrycodes}|lat={lat:.4f}|lon={lon:.4f}"


def _ac_cache_get(key: str):
    entry = _AC_CACHE.get(key)
    if not entry:
        return None
    ts, data = entry
    if (time.time() - ts) <= _AC_CACHE_TTL_SECONDS:
        return data
    try:
        del _AC_CACHE[key]
    except Exception:
        pass
    return None


def _ac_cache_put(key: str, data):
    _AC_CACHE[key] = (time.time(), data)


async def _fetch_nominatim(query: str, limit: int, countrycodes: str, lat: Optional[float], lon: Optional[float], no_viewbox: bool = False):
    base_url = "https://nominatim.openstreetmap.org/search"
    params = {
        "q": query,
        "format": "jsonv2",
        "addressdetails": 1,
        "limit": min(max(limit, 1), 15),
        "dedupe": 1,
        "autocomplete": 1,
        "accept-language": "de",
        "countrycodes": countrycodes.replace(" ", "") if countrycodes else ""
    }
    # Optional viewbox bias (rough ~25km square) if coordinates available and not disabled
    if lat is not None and lon is not None and not no_viewbox:
        d_lat = 0.225
        d_lng = 0.35
        west = lon - d_lng
        south = lat - d_lat
        east = lon + d_lng
        north = lat + d_lat
        params["viewbox"] = f"{west},{north},{east},{south}"

    headers = {"User-Agent": "gashis-parking/1.0 (contact: info@gashis.ch)"}
    loop = asyncio.get_event_loop()
    try:
        resp = await loop.run_in_executor(None, lambda: requests.get(base_url, params=params, headers=headers, timeout=8))
        if resp.status_code != 200:
            return []
        data = resp.json()
        out = []
        for r in data:
            try:
                primary = r.get("name") or (r.get("display_name") or "").split(',')[0]
                addr = r.get("display_name")
                postcode = r.get('address', {}).get('postcode') if isinstance(r.get('address'), dict) else None
                city = None
                if isinstance(r.get('address'), dict):
                    city = r['address'].get('city') or r['address'].get('town') or r['address'].get('village')
                secondary = " ".join([p for p in [postcode, city] if p])
                out.append({
                    "id": f"osm_{r.get('place_id')}",
                    "source": "osm",
                    "primary": primary,
                    "secondary": secondary,
                    "address": addr,
                    "lat": float(r.get("lat")),
                    "lng": float(r.get("lon"))
                })
            except Exception:
                continue
        return out
    except Exception:
        return []


async def _fetch_photon(query: str, limit: int, lat: Optional[float], lon: Optional[float]):
    base_url = "https://photon.komoot.io/api/"
    params = {
        "q": query,
        "limit": min(max(limit, 1), 15),
        "lang": "de"
    }
    if lat is not None and lon is not None:
        params["lat"] = f"{lat:.6f}"
        params["lon"] = f"{lon:.6f}"
        params["location_bias_scale"] = "2"
    headers = {"Accept": "application/json"}
    loop = asyncio.get_event_loop()
    try:
        resp = await loop.run_in_executor(None, lambda: requests.get(base_url, params=params, headers=headers, timeout=8))
        if resp.status_code != 200:
            return []
        data = resp.json()
        feats = (data or {}).get("features") or []
        out = []
        for i, f in enumerate(feats):
            try:
                p = f.get("properties") or {}
                coords = (f.get("geometry") or {}).get("coordinates") or []
                if len(coords) < 2:
                    continue
                primary = p.get("name") or p.get("street") or p.get("city") or p.get("country") or "Ort"
                postcode = p.get("postcode")
                city = p.get("city")
                housenumber = p.get("housenumber")
                street = p.get("street")
                secondary_parts = []
                if street:
                    secondary_parts.append(street + (f" {housenumber}" if housenumber else ""))
                if postcode:
                    secondary_parts.append(postcode)
                if city:
                    secondary_parts.append(city)
                secondary = " ".join(secondary_parts)
                address_parts = [p.get("name"), street and (street + (f" {housenumber}" if housenumber else "")), postcode, city, p.get("country")]
                address = ", ".join([x for x in address_parts if x])
                out.append({
                    "id": f"ph_{f.get('id') or primary}_{i}",
                    "source": "photon",
                    "primary": primary,
                    "secondary": secondary,
                    "address": address,
                    "lat": coords[1],
                    "lng": coords[0]
                })
            except Exception:
                continue
        return out
    except Exception:
        return []


def _dedupe_suggestions(items: list):
    seen = set()
    out = []
    for it in items:
        key = (it.get("primary"), it.get("secondary"))
        if key not in seen:
            seen.add(key)
            out.append(it)
    return out


@app.get("/api/autocomplete")
async def unified_autocomplete(q: str, request: Request, limit: int = 12, countrycodes: str = "ch,de,at", lat: Optional[float] = None, lon: Optional[float] = None):
    """Unified autocomplete endpoint combining Nominatim + Photon.

    Query Params:
      q: Benutzer-Eingabe (>=1 Zeichen)
      limit: Max result count (default 12, capped 15)
      countrycodes: Komma-separierte Länder (für Nominatim bias)
      lat/lon: Optional user location for bias

    Features:
      - Per-IP rate limiting (30 req / 60s)
      - Caching (5m TTL)
      - Provider merge + dedupe (Nominatim first, then Photon)
      - Automatic deep fallback (Nominatim ohne viewbox + Photon retry) if no results
    """
    query = (q or "").strip()
    if len(query) < 1:
        return []

    # Per-IP rate limit
    ip = request.client.host if request.client else "unknown"
    bucket = _AC_RATE_BUCKETS[ip]
    now = time.time()
    # purge old
    while bucket and (now - bucket[0]) > _AC_RATE_LIMIT_WINDOW:
        bucket.popleft()
    if len(bucket) >= _AC_RATE_LIMIT_MAX:
        raise HTTPException(status_code=429, detail="Rate limit exceeded. Please slow down.")
    bucket.append(now)

    # Cache check (include coords so biased searches are distinct)
    ck = _ac_cache_key(query, limit, countrycodes, lat or 0.0, lon or 0.0)
    cached = _ac_cache_get(ck)
    if cached is not None:
        return cached

    # Parallel fetch primary pass
    nom_task = _fetch_nominatim(query, limit, countrycodes, lat, lon, no_viewbox=False)
    ph_task = _fetch_photon(query, limit, lat, lon)
    nom, ph = await asyncio.gather(nom_task, ph_task)
    merged = _dedupe_suggestions([*nom, *ph])

    # Deep fallback if empty: broaden Nominatim (no viewbox) and retry Photon
    if not merged:
        nom2, ph2 = await asyncio.gather(
            _fetch_nominatim(query, limit, countrycodes, lat, lon, no_viewbox=True),
            _fetch_photon(query, limit, lat, lon)
        )
        merged = _dedupe_suggestions([*nom2, *ph2])

    # Trim & cache
    final = merged[:limit]
    _ac_cache_put(ck, final)
    try:
        print(f"[AC] q='{query}' ip={ip} results={len(final)}")
    except Exception:
        pass
    return final


@app.post('/api/hardware/{hardware_id}/telemetry')
async def receive_hardware_telemetry(hardware_id: str, payload: HardwareTelemetry):
    """Receive telemetry/heartbeat from hardware devices.

    Example payload: { battery_level: 3.7, rssi: -72, occupancy: 'occupied', last_mag: {x:..,y:..,z:..}, timestamp: '2025-11-02T12:34:56' }
    """
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()

        # Upsert device entry and update telemetry columns
        cursor.execute('SELECT id FROM hardware_devices WHERE hardware_id = ?', (hardware_id,))
        row = cursor.fetchone()
        now = payload.timestamp.isoformat() if payload.timestamp else datetime.now().isoformat()
        last_mag_json = json.dumps(payload.last_mag) if payload.last_mag is not None else None

        if row:
            cursor.execute('''
                UPDATE hardware_devices SET last_heartbeat = ?, battery_level = ?, rssi = ?, occupancy = ?, last_mag = ?
                WHERE hardware_id = ?
            ''', (now, payload.battery_level, payload.rssi, payload.occupancy, last_mag_json, hardware_id))
        else:
            cursor.execute('''
                INSERT INTO hardware_devices (hardware_id, owner_email, parking_spot_id, created_at, last_heartbeat, battery_level, rssi, occupancy, last_mag)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (hardware_id, None, None, datetime.now().isoformat(), now, payload.battery_level, payload.rssi, payload.occupancy, last_mag_json))

        conn.commit()
        conn.close()
        return {"status": "ok", "hardware_id": hardware_id, "last_heartbeat": now}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Telemetry error: {e}")


@app.get('/api/owner/devices')
async def list_owner_devices(authorization: str = Header(None)):
    """Return devices assigned to the owner.

    Sicherheits-Note: In der Dev-Umgebung gibt es einfache Demo-Tokens
    im Format `dev-token-<role>`. Dieses Endpoint darf nur von Admins
    verwendet werden. Nicht-Admin-Requests liefern 403.
    """
    # Parse token and determine role + owner_email. Support dev-token- fallback and real JWTs via auth.decode_token
    token = None
    role = None
    owner_email = None
    if authorization:
        if authorization.startswith('Bearer '):
            token = authorization.split(' ', 1)[1]
        else:
            token = authorization

    if token:
        if token.startswith('dev-token-'):
            role = token.replace('dev-token-', '')
            # map dev owner token to demo email for convenience
            if role == 'owner':
                owner_email = 'owner@test.com'
        else:
            payload = auth.decode_token(token)
            if payload:
                role = payload.get('role')
                owner_email = payload.get('sub') or payload.get('email')

    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()

        # If admin, return all devices. If owner, return only devices owned by that owner's email.
        if role == 'admin':
            cursor.execute('''SELECT hardware_id, owner_email, parking_spot_id, created_at, last_heartbeat, battery_level, rssi, occupancy, last_mag FROM hardware_devices''')
            rows = cursor.fetchall()
        elif role == 'owner' and owner_email:
            cursor.execute('''SELECT hardware_id, owner_email, parking_spot_id, created_at, last_heartbeat, battery_level, rssi, occupancy, last_mag FROM hardware_devices WHERE owner_email = ?''', (owner_email,))
            rows = cursor.fetchall()
        else:
            # Forbidden for other roles or unauthenticated requests
            raise HTTPException(status_code=403, detail='Forbidden: admin or owner role required')

        devices = []
        for r in rows:
            hardware_id = r[0]
            owner_email = r[1]
            parking_spot_id = r[2]
            created_at = r[3]
            # telemetry columns
            last_heartbeat = r[4]
            battery_level = r[5]
            rssi = r[6]
            occupancy = r[7]
            last_mag = json.loads(r[8]) if r[8] else None

            telemetry = {
                'last_heartbeat': last_heartbeat,
                'battery_level': battery_level,
                'rssi': rssi,
                'occupancy': occupancy,
                'last_mag': last_mag
            }

            devices.append({
                "hardware_id": hardware_id,
                "owner_email": owner_email,
                "parking_spot_id": parking_spot_id,
                "created_at": created_at,
                "telemetry": telemetry
            })

        conn.close()
        return {"devices": devices}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post('/api/owner/devices/assign')
async def assign_device_to_spot(payload: dict, authorization: str = Header(None)):
    """Assign a hardware_id to a parking_spot_id. Requires owner/admin role in demo token."""
    hardware_id = payload.get('hardware_id')
    spot_id = payload.get('spot_id')
    if not hardware_id or not spot_id:
        raise HTTPException(status_code=400, detail='hardware_id and spot_id required')

    # Determine role and owner email from token (supports dev-token- fallback and real JWT)
    role = None
    token = None
    owner_email = None
    if authorization:
        if authorization.startswith('Bearer '):
            token = authorization.split(' ',1)[1]
        else:
            token = authorization

    # Dev-token fallback (simple demo tokens)
    if token and token.startswith('dev-token-'):
        role = token.replace('dev-token-','')
        # Map the demo owner token to the demo email for convenience
        if role == 'owner':
            owner_email = 'owner@test.com'

    # If we have a JWT or real token, try to decode and extract role/email
    if token and not token.startswith('dev-token-'):
        payload = auth.decode_token(token)
        if payload:
            role = payload.get('role')
            owner_email = payload.get('sub') or payload.get('email')

    if role not in ('owner','admin'):
        raise HTTPException(status_code=403, detail='Forbidden')

    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        # upsert hardware device and set owner_email when assigning
        cursor.execute('''SELECT id FROM hardware_devices WHERE hardware_id = ?''', (hardware_id,))
        row = cursor.fetchone()
        if row:
            cursor.execute('''UPDATE hardware_devices SET parking_spot_id = ?, owner_email = ? WHERE hardware_id = ?''', (spot_id, owner_email, hardware_id))
        else:
            cursor.execute('''INSERT INTO hardware_devices (hardware_id, owner_email, parking_spot_id) VALUES (?, ?, ?)''', (hardware_id, owner_email, spot_id))
        conn.commit()
        conn.close()
        return {'status':'assigned','hardware_id':hardware_id,'spot_id':spot_id, 'owner_email': owner_email}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# User endpoints (simple)
@app.get("/verify-email/{token}", name="verify_email")
async def verify_email(token: str, db: Session = Depends(get_db)):
    try:
        user = auth.get_user_by_verification_token(db, token)
        if not user:
            raise HTTPException(status_code=400, detail="Invalid or expired verification token.")
        
        user.is_verified = True
        user.verification_token = None # Token nach Gebrauch entfernen
        db.commit()
        
        # Redirect to a confirmation page on the frontend
        return RedirectResponse(url="http://localhost:3000/email-verified")
    finally:
        db.close()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8001)
