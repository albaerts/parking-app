from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import sqlite3
import json
import os
from datetime import datetime

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

class LoginRequest(BaseModel):
    email: str
    password: str

class RegisterRequest(BaseModel):
    name: str
    email: str
    password: str
    role: Optional[str] = "user"

# Bekannte Test-User (nur lokal!)
TEST_USERS = {
    "user@test.com": {"password": "user123", "role": "user", "name": "Test User"},
    "owner@test.com": {"password": "owner123", "role": "owner", "name": "Test Owner"},
    "admin@test.com": {"password": "admin123", "role": "admin", "name": "Test Admin"},
}

@app.post("/login.php")
async def login_local(payload: LoginRequest):
    """Lokaler Demo-Login zur Unterstützung des Frontends in der Entwicklung.

    Nutzt die Standard-Zugangsdaten:
    - user@test.com / user123
    - owner@test.com / owner123
    - admin@test.com / admin123
    """
    user = TEST_USERS.get(payload.email)
    if not user or user["password"] != payload.password:
        raise HTTPException(status_code=401, detail="Invalid email or password")

    # Dummy-Token (nur lokal!)
    token = f"dev-token-{user['role']}"

    # Response-Form an das bestehende Frontend angepasst
    return {
        "token": token,
        "user": {
            "id": 1,
            "email": payload.email,
            "name": user["name"],
            "role": user["role"],
        },
    }

@app.post("/register.php")
async def register_local(payload: RegisterRequest):
    """Lokale Demo-Registrierung: legt keinen echten User an,
    gibt aber direkt einen gültigen Token zurück, damit das Frontend weiterarbeiten kann.
    """
    # Wenn E-Mail schon als Test-User existiert, so tun als ob Login
    existing = TEST_USERS.get(payload.email)
    role = payload.role or (existing["role"] if existing else "user")
    name = payload.name or (existing["name"] if existing else "New User")

    token = f"dev-token-{role}"

    return {
        "token": token,
        "user": {
            "id": 2,
            "email": payload.email,
            "name": name,
            "role": role,
        },
    }

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

    # Parse role from demo token
    role = None
    token = None
    if authorization:
        if authorization.startswith("Bearer "):
            token = authorization.split(" ", 1)[1]
        else:
            token = authorization

    if token and token.startswith("dev-token-"):
        role = token.replace("dev-token-", "")

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


@app.get('/api/owner/devices')
async def list_owner_devices(authorization: str = Header(None)):
    """Return devices assigned to the owner (by demo token role)."""
    # parse token -> owner email from token if possible
    owner_email = None
    token = None
    if authorization:
        if authorization.startswith('Bearer '):
            token = authorization.split(' ',1)[1]
        else:
            token = authorization
    # For demo tokens, token does not contain email; fallback to query all devices
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        cursor.execute('''SELECT hardware_id, owner_email, parking_spot_id, created_at FROM hardware_devices''')
        rows = cursor.fetchall()
        devices = []
        for r in rows:
            devices.append({"hardware_id": r[0], "owner_email": r[1], "parking_spot_id": r[2], "created_at": r[3]})
        conn.close()
        return {"devices": devices}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post('/api/owner/devices/assign')
async def assign_device_to_spot(payload: dict, authorization: str = Header(None)):
    """Assign a hardware_id to a parking_spot_id. Requires owner/admin role in demo token."""
    hardware_id = payload.get('hardware_id')
    spot_id = payload.get('spot_id')
    if not hardware_id or not spot_id:
        raise HTTPException(status_code=400, detail='hardware_id and spot_id required')

    # simple role check
    role = None
    token = None
    if authorization:
        if authorization.startswith('Bearer '):
            token = authorization.split(' ',1)[1]
        else:
            token = authorization
    if token and token.startswith('dev-token-'):
        role = token.replace('dev-token-','')
    if role not in ('owner','admin'):
        raise HTTPException(status_code=403, detail='Forbidden')

    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        # upsert hardware device
        cursor.execute('''SELECT id FROM hardware_devices WHERE hardware_id = ?''', (hardware_id,))
        row = cursor.fetchone()
        if row:
            cursor.execute('''UPDATE hardware_devices SET parking_spot_id = ?, owner_email = ? WHERE hardware_id = ?''', (spot_id, None, hardware_id))
        else:
            cursor.execute('''INSERT INTO hardware_devices (hardware_id, owner_email, parking_spot_id) VALUES (?, ?, ?)''', (hardware_id, None, spot_id))
        conn.commit()
        conn.close()
        return {'status':'assigned','hardware_id':hardware_id,'spot_id':spot_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# User endpoints (simple)
@app.post("/users", response_model=User)
async def create_user(user: User):
    """Create new user"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO users (email, name)
            VALUES (?, ?)
        ''', (user.email, user.name))
        
        user_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        user.id = user_id
        return user
        
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=400, detail="User with this email already exists")
    except sqlite3.Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8001)
