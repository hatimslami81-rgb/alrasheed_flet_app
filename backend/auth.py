\
import os, hashlib, secrets
from .db import get_conn

def _hash_password(password: str, salt: str) -> str:
    return hashlib.sha256( (salt + password).encode("utf-8") ).hexdigest()

def create_user(username: str, password: str, role: str, full_name: str = "", uni_id: str = None, level: str = None, gpa: float = None):
    salt = secrets.token_hex(16)
    pwd_hash = _hash_password(password, salt)
    with get_conn() as conn:
        c = conn.cursor()
        c.execute("""
            INSERT INTO users (username, password_hash, salt, role, full_name, uni_id, level, gpa)
            VALUES (?,?,?,?,?,?,?,?)
        """, (username, pwd_hash, salt, role, full_name, uni_id, level, gpa))
        conn.commit()
        return c.lastrowid

def verify_login(username: str, password: str):
    with get_conn() as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE username=?", (username,))
        row = c.fetchone()
        if not row:
            return None
        salt = row["salt"]
        if _hash_password(password, salt) == row["password_hash"]:
            # return dict row
            return dict(row)
        return None
