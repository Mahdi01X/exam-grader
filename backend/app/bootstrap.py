"""Crée un compte admin initial si la table users est vide.

Le mot de passe est généré aléatoirement et imprimé une seule fois sur stdout.
À NE PAS conserver dans les logs persistants en production — utiliser un vault.
"""
import secrets
import string
import sys

from app.core.config import get_settings
from app.core.db import session_scope
from app.core.security import hash_password
from app.models.user import User, UserRole


def generate_password(length: int = 24) -> str:
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    return "".join(secrets.choice(alphabet) for _ in range(length))


def main() -> None:
    settings = get_settings()
    with session_scope() as db:
        if db.query(User).count() > 0:
            print("[bootstrap] users table not empty, skipping admin creation")
            return
        provided = bool(settings.bootstrap_admin_password)
        password = settings.bootstrap_admin_password or generate_password()
        admin = User(
            email=settings.bootstrap_admin_email,
            name="Administrateur",
            hashed_password=hash_password(password),
            role=UserRole.admin,
            is_active=True,
        )
        db.add(admin)
        print("=" * 60, file=sys.stderr)
        print(f"[bootstrap] admin user created: {settings.bootstrap_admin_email}", file=sys.stderr)
        if provided:
            print("[bootstrap] password: (set via BOOTSTRAP_ADMIN_PASSWORD)", file=sys.stderr)
        else:
            print(f"[bootstrap] one-time password: {password}", file=sys.stderr)
            print("[bootstrap] CHANGE THIS PASSWORD IMMEDIATELY", file=sys.stderr)
        print("=" * 60, file=sys.stderr)


if __name__ == "__main__":
    main()
