import os
import hashlib
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy import Column, Integer, String, DateTime, create_engine, Boolean, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
"""Auth/Hilfsfunktionen mit Fallback für fehlendes bcrypt.

Wenn das native 'bcrypt' Modul im Container fehlt (z.B. Build-Probleme,
Volume-Mount überschreibt Layer), schalten wir auf passlib's bcrypt-Hash
um. Dadurch bleibt Login funktionsfähig und neue Passwörter werden mit
einem sicheren Bcrypt-Algorithmus gehasht – auch wenn das C-Modul fehlt.
"""
try:
    import bcrypt  # bevorzugt (C Implementierung)
    _BCRYPT_NATIVE = True
except ImportError:  # Fallback: passlib
    from passlib.hash import bcrypt as passlib_bcrypt
    bcrypt = None
    _BCRYPT_NATIVE = False
import jwt
import secrets

BASE_DIR = os.path.dirname(__file__)
DEFAULT_SQLITE = f"sqlite:///{os.path.join(BASE_DIR, 'parking.db')}"
DATABASE_URL = os.environ.get("DATABASE_URL", DEFAULT_SQLITE)

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {},
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

JWT_SECRET = os.environ.get("JWT_SECRET", "dev-secret-change-me")
JWT_ALGO = os.environ.get("JWT_ALGO", "HS256")
JWT_EXP_MINUTES = int(os.environ.get("JWT_EXP_MINUTES", "60"))


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    password_hash = Column(String, nullable=True)
    role = Column(String, default="user")
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)
    is_verified = Column(Boolean, default=False, nullable=False)
    verification_token = Column(String, unique=True, index=True, nullable=True)
    verification_token_expires = Column(DateTime, nullable=True)
    # Additional profile fields
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    address = Column(String, nullable=True)
    house_number = Column(String, nullable=True)
    city = Column(String, nullable=True)
    zip_code = Column(String, nullable=True)
    country = Column(String, nullable=True)
    secondary_email = Column(String, nullable=True)
    date_of_birth = Column(DateTime, nullable=True)


def init_db():
    Base.metadata.create_all(bind=engine)


def get_user_by_email(db, email: str) -> Optional[User]:
    return db.query(User).filter(User.email == email).first()

def get_user_by_verification_token(db, token: str) -> Optional[User]:
    return db.query(User).filter(User.verification_token == token).first()


def create_user(db, name: str, email: str, password: str, role: str = "user") -> User:
    """Erstellt einen neuen Benutzer und hasht Passwort mit Bcrypt.

    Nutzt native bcrypt wenn verfügbar, sonst passlib Fallback.
    """
    hashed = None
    if password:
        if len(password) > 72:
            password = password[:72]
        if _BCRYPT_NATIVE:
            hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        else:
            # passlib erzeugt direkt einen String mit Präfix $2b$/... kompatibel
            hashed = passlib_bcrypt.using(rounds=12).hash(password)

    verification_token = secrets.token_urlsafe(32)

    user = User(
        name=name, 
        email=email, 
        password_hash=hashed, 
        role=role,
        verification_token=verification_token
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _legacy_sha256(password: str) -> str:
    """Legacy hashing used by older code (sha256 + static 'salt')."""
    return hashlib.sha256((password + "salt").encode()).hexdigest()

def verify_password(plain: str, hashed: str) -> bool:
    """Support both bcrypt (current) and legacy sha256+salt hashes.

    Detect bcrypt by prefix ($2a$, $2b$, $2y$). If not bcrypt pattern, fall back
    to legacy sha256 check for backward compatibility.
    """
    if not plain or not hashed:
        return False
    try:
        # Bcrypt prefix detection
        if hashed.startswith("$2a$") or hashed.startswith("$2b$") or hashed.startswith("$2y$"):
            if len(plain) > 72:
                plain = plain[:72]
            if _BCRYPT_NATIVE:
                return bcrypt.checkpw(plain.encode('utf-8'), hashed.encode('utf-8'))
            else:
                # passlib verify
                return passlib_bcrypt.verify(plain, hashed)
        # Legacy fallback
        return _legacy_sha256(plain) == hashed
    except Exception:
        return False


def authenticate_user(db, email: str, password: str) -> Optional[User]:
    user = get_user_by_email(db, email)
    if not user:
        return None

    # Primary path: use password_hash when present
    if user.password_hash:
        if verify_password(password, user.password_hash):
            return user
        # If bcrypt hash exists but fails, do not try anything else
        return None

    # Fallback: legacy column named 'password' may exist in older DBs (PHP)
    try:
        result = db.execute(text("SELECT password FROM users WHERE email = :email"), {"email": email}).fetchone()
        legacy_hash = result[0] if result and len(result) > 0 else None
    except Exception:
        legacy_hash = None

    if not legacy_hash:
        return None

    # Support PHP's password_hash (bcrypt) or our older sha256+salt
    ok = False
    try:
        if legacy_hash.startswith("$2a$") or legacy_hash.startswith("$2b$") or legacy_hash.startswith("$2y$"):
            test_plain = password[:72] if len(password) > 72 else password
            if _BCRYPT_NATIVE:
                ok = bcrypt.checkpw(test_plain.encode("utf-8"), legacy_hash.encode("utf-8"))
            else:
                ok = passlib_bcrypt.verify(test_plain, legacy_hash)
        elif len(legacy_hash) == 64:
            ok = _legacy_sha256(password) == legacy_hash
    except Exception:
        ok = False

    if not ok:
        return None

    # Upgrade path: store a fresh bcrypt hash in password_hash for future logins
    try:
        upgrade_plain = password[:72] if len(password) > 72 else password
        if _BCRYPT_NATIVE:
            new_hash = bcrypt.hashpw(upgrade_plain.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        else:
            new_hash = passlib_bcrypt.using(rounds=12).hash(upgrade_plain)
        user.password_hash = new_hash
        db.add(user)
        db.commit()
    except Exception:
        db.rollback()

    return user


def create_access_token(subject: str, user_id: int, role: str, expires_delta: Optional[timedelta] = None) -> str:
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=JWT_EXP_MINUTES))
    to_encode = {"sub": subject, "user_id": user_id, "role": role, "exp": expire}
    return jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGO)


def decode_token(token: str):
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGO])
    except Exception:
        return None
