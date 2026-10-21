import re
import bcrypt
from functools import wraps
from flask import session, redirect, url_for, flash, abort, request
from utils import get_connection

def hash_password(password: str) -> bytes:
    """Hashes a plaintext password using bcrypt."""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())

def check_password(password: str, hashed_password) -> bool:
    """Verifies a plaintext password against a stored bcrypt hash."""
    if not hashed_password:
        return False
    # Ensure hashed_password is bytes (MySQL VARBINARY returns bytes or bytearray)
    stored_bytes = bytes(hashed_password) if not isinstance(hashed_password, bytes) else hashed_password
    try:
        return bcrypt.checkpw(password.encode("utf-8"), stored_bytes)
    except Exception:
        return False

def validate_password_strength(password: str) -> tuple[bool, str]:
    """Enforces: Minimum 8 characters, at least 1 uppercase letter, at least 1 digit."""
    if len(password) < 8:
        return False, "Password must be at least 8 characters long."
    if not any(c.isupper() for c in password):
        return False, "Password must contain at least one uppercase letter (A-Z)."
    if not any(c.isdigit() for c in password):
        return False, "Password must contain at least one digit (0-9)."
    return True, ""

def log_history(username: str, action: str):
    """Logs an administrative activity into the existing MySQL history table."""
    con = None
    cur = None
    try:
        con = get_connection()
        if con:
            cur = con.cursor()
            cur.execute(
                "INSERT INTO history (USERNAME, ACTIONS) VALUES (%s, %s)",
                (username, action)
            )
            con.commit()
    except Exception as e:
        print("History Logging Error:", e)
    finally:
        if cur:
            cur.close()
        if con and con.is_connected():
            con.close()

def login_required(f):
    """Decorator to require user authentication for route access."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "username" not in session or "role" not in session:
            flash("Please sign in to access this page.", "warning")
            return redirect(url_for("login", next=request.path))
        return f(*args, **kwargs)
    return decorated_function

def role_required(allowed_roles):
    """Decorator to enforce role-based access control (RBAC)."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if "username" not in session or "role" not in session:
                flash("Please sign in to access this page.", "warning")
                return redirect(url_for("login"))
            user_role = session.get("role")
            if user_role not in allowed_roles:
                flash("Access Denied: You do not have permission to perform this action.", "danger")
                return redirect(url_for("dashboard"))
            return f(*args, **kwargs)
        return decorated_function
    return decorator
