"""
============================================
🔐 AUTH MODULE - Email/Password accounts
============================================
Passwords are hashed with bcrypt and stored in data/users.json
"""
import json
import bcrypt
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"
USERS_FILE = DATA_DIR / "users.json"


def _load_users():
    if not USERS_FILE.exists():
        return {}
    try:
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _save_users(users):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, indent=2, ensure_ascii=False)


def register_user(name, email, password):
    """Create a new account. Returns (success, message)"""
    users = _load_users()
    email = email.strip().lower()
    if email in users:
        return False, "An account with this email already exists."
    users[email] = {
        "name": name.strip(),
        "email": email,
        "password_hash": bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    }
    _save_users(users)
    return True, "Account created! You can log in now."


def login_user(email, password):
    """Verify login. Returns (user_dict or None, message)"""
    users = _load_users()
    email = email.strip().lower()
    user = users.get(email)
    if not user:
        return None, "No account found with this email."
    if bcrypt.checkpw(password.encode(), user["password_hash"].encode()):
        return user, "Login successful!"
    return None, "Incorrect password."