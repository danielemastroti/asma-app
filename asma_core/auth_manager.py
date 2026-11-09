"""

ASMA Accordi Next Generation - Authentication & Role-Based Authorization

Conforms to SRS Cap. 3 (Architettura di Sicurezza) and Cap. 10.

Supports Google OAuth2 and local Band Member roles: ADMIN, BAND_MEMBER, VIEWER.

"""

from __future__ import annotations

import os

import json

from enum import Enum

from typing import Dict, Any, Optional, List

from dataclasses import dataclass, asdict

from pathlib import Path

class UserRole(str, Enum):

    ADMIN = "ADMIN"

    BAND_MEMBER = "BAND_MEMBER"

    VIEWER = "VIEWER"

@dataclass

class User:

    email: str

    name: str

    role: UserRole

    picture_url: str = ""

    is_active: bool = True

    provider: str = "google"  # "google" or "local"

    def can_edit(self) -> bool:

        """Only ADMIN and BAND_MEMBER can modify songs, setlists, and repertoires."""

        return self.is_active and self.role in [UserRole.ADMIN, UserRole.BAND_MEMBER]

    def can_admin(self) -> bool:

        """Only ADMIN can configure system, force-unlock, and purge data."""

        return self.is_active and self.role == UserRole.ADMIN

    def can_delete(self) -> bool:

        """ADMIN and BAND_MEMBER can soft-delete songs and items."""

        return self.is_active and self.role in [UserRole.ADMIN, UserRole.BAND_MEMBER]

    def can_force_unlock(self) -> bool:

        """Only ADMIN can break an active concurrency lock from another user."""

        return self.is_active and self.role == UserRole.ADMIN

    def to_dict(self) -> Dict[str, Any]:

        return {

            "email": self.email,

            "name": self.name,

            "role": self.role.value if isinstance(self.role, UserRole) else str(self.role),

            "picture_url": self.picture_url,

            "is_active": self.is_active,

            "provider": self.provider

        }

    @classmethod

    def from_dict(cls, d: Dict[str, Any]) -> User:

        return cls(

            email=d["email"],

            name=d.get("name", d["email"]),

            role=UserRole(d.get("role", "BAND_MEMBER")),

            picture_url=d.get("picture_url", ""),

            is_active=d.get("is_active", True),

            provider=d.get("provider", "google")

        )

class AuthManager:

    """

    Handles user identities, roles, Google OAuth authentication flow,

    and role-based permission enforcement.

    """

    BAND_MEMBERS = {
        "danyposta@gmail.com": {"pseudonym": "Sentimental", "instrument": "Tastiera", "role": UserRole.ADMIN, "display_role": "Admin / Tastiera"},
        "acicchelli65@gmail.com": {"pseudonym": "Cico", "instrument": "Voce", "role": UserRole.BAND_MEMBER, "display_role": "Voce"},
        "maurobovolenta4@gmail.com": {"pseudonym": "Maurino", "instrument": "Chitarra ritmica", "role": UserRole.BAND_MEMBER, "display_role": "Chitarra ritmica"},
        "marcoerario2@gmail.com": {"pseudonym": "Red", "instrument": "Chitarra elettrica", "role": UserRole.BAND_MEMBER, "display_role": "Chitarra elettrica"},
        "gv.drummer69@gmail.com": {"pseudonym": "Mingo", "instrument": "Batteria", "role": UserRole.BAND_MEMBER, "display_role": "Batteria"},
        "titholola@gmail.com": {"pseudonym": "Puma", "instrument": "Basso", "role": UserRole.BAND_MEMBER, "display_role": "Basso"}
    }

    BAND_PSEUDONYMS = {
        "danyposta@gmail.com": "Sentimental",
        "maurobovolenta4@gmail.com": "Maurino",
        "marcoerario2@gmail.com": "Red",
        "gv.drummer69@gmail.com": "Mingo",
        "acicchelli65@gmail.com": "Cico",
        "titholola@gmail.com": "Puma"
    }

    DEFAULT_USERS = [
        User(
            email="danyposta@gmail.com",
            name="Sentimental",
            role=UserRole.ADMIN,
            picture_url="https://api.dicebear.com/7.x/bottts/svg?seed=Sentimental",
            provider="google"
        ),
        User(
            email="daniele@band.org",
            name="Daniele Rossi (Admin)",
            role=UserRole.ADMIN,
            picture_url="https://api.dicebear.com/7.x/bottts/svg?seed=Daniele",
            provider="google"
        ),
        User(
            email="maurobovolenta4@gmail.com",
            name="Maurino",
            role=UserRole.BAND_MEMBER,
            picture_url="https://api.dicebear.com/7.x/bottts/svg?seed=Maurino",
            provider="google"
        ),
        User(
            email="marcoerario2@gmail.com",
            name="Red",
            role=UserRole.BAND_MEMBER,
            picture_url="https://api.dicebear.com/7.x/bottts/svg?seed=Red",
            provider="google"
        ),
        User(
            email="gv.drummer69@gmail.com",
            name="Mingo",
            role=UserRole.BAND_MEMBER,
            picture_url="https://api.dicebear.com/7.x/bottts/svg?seed=Mingo",
            provider="google"
        ),
        User(
            email="acicchelli65@gmail.com",
            name="Cico",
            role=UserRole.BAND_MEMBER,
            picture_url="https://api.dicebear.com/7.x/bottts/svg?seed=Cico",
            provider="google"
        ),
        User(
            email="titholola@gmail.com",
            name="Puma",
            role=UserRole.BAND_MEMBER,
            picture_url="https://api.dicebear.com/7.x/bottts/svg?seed=Puma",
            provider="google"
        ),
        User(
            email="marco.chitarra@band.org",
            name="Marco Bassi (Chitarra / Band)",
            role=UserRole.BAND_MEMBER,
            picture_url="https://api.dicebear.com/7.x/bottts/svg?seed=Marco",
            provider="google"
        ),
        User(
            email="ospite@band.org",
            name="Ospite (Solo Lettura)",
            role=UserRole.VIEWER,
            picture_url="https://api.dicebear.com/7.x/bottts/svg?seed=Ospite",
            provider="google"
        )
    ]

    def __init__(self, data_dir: str = "data"):

        self.data_dir = Path(data_dir)

        self.users_file = self.data_dir / "users.json"

        self._users: Dict[str, User] = {}

        self._load_users()

    def _load_users(self):
        """Loads registered users from Turso Cloud, local JSON storage, or seeds default band members."""
        self.data_dir.mkdir(parents=True, exist_ok=True)
        default_data = os.path.abspath("data")
        is_default = (os.path.abspath(str(self.data_dir)) == default_data)

        # 1. Try loading from Turso Cloud if configured (production data directory only)
        if is_default:
            try:
                from asma_core.turso_client import TursoClient
                turso = TursoClient()
                if turso.is_configured:
                    turso_users = turso.fetch_users()
                    if turso_users:
                        for item in turso_users:
                            u = User.from_dict(item)
                            self._users[u.email.lower()] = u
                        # Refresh local cache file
                        data = [u.to_dict() for u in self._users.values()]
                        with open(self.users_file, "w", encoding="utf-8") as f:
                            json.dump(data, f, indent=2, ensure_ascii=False)
                        return
            except Exception:
                pass

        # 2. Fallback to local JSON storage
        if self.users_file.exists():
            try:
                with open(self.users_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for item in data:
                        u = User.from_dict(item)
                        self._users[u.email.lower()] = u
            except Exception:
                self._seed_default_users()
        else:
            self._seed_default_users()

    def _seed_default_users(self):
        """Initializes default band accounts."""
        self._users = {u.email.lower(): u for u in self.DEFAULT_USERS}
        self._save_users()

    def _save_users(self):
        """Persists registered users to disk and synchronizes with Turso Cloud."""
        data = [u.to_dict() for u in self._users.values()]
        with open(self.users_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        default_data = os.path.abspath("data")
        is_default = (os.path.abspath(str(self.data_dir)) == default_data)
        if is_default:
            # Synchronize with Turso Cloud
            try:
                from asma_core.turso_client import TursoClient
                turso = TursoClient()
                if turso.is_configured:
                    turso.push_users(data)
            except Exception:
                pass

    def list_users(self) -> List[User]:

        """Returns all configured users."""

        return list(self._users.values())

    def get_user_by_email(self, email: str) -> Optional[User]:

        """Looks up a user by email."""

        return self._users.get(email.lower())

    def authenticate_or_register_google(self, email: str, name: str = "", picture_url: str = "") -> User:

        """

        Authenticates a user after Google OAuth confirmation.

        If the user is new:

        - The first user or any @band.org address is created as BAND_MEMBER (or ADMIN if daniele).

        - Others are created as VIEWER for safety.

        """

        clean_email = email.strip().lower()

        if clean_email in self._users:

            user = self._users[clean_email]

            if name and user.name != name:

                user.name = name

            if picture_url:

                user.picture_url = picture_url

            self._save_users()

            return user

        # Auto-assign role and pseudonym from configured musicians

        pseudonym = self.BAND_PSEUDONYMS.get(clean_email)

        display_name = pseudonym or name or clean_email.split("@")[0].capitalize()

        if clean_email == "danyposta@gmail.com" or "admin" in clean_email or clean_email == "daniele@band.org":

            initial_role = UserRole.ADMIN

        elif clean_email in self.BAND_PSEUDONYMS or clean_email.endswith("@band.org"):

            initial_role = UserRole.BAND_MEMBER

        else:

            initial_role = UserRole.VIEWER

        new_user = User(

            email=clean_email,

            name=display_name,

            role=initial_role,

            picture_url=picture_url,

            is_active=True,

            provider="google"

        )

        self._users[clean_email] = new_user

        self._save_users()

        return new_user

    def update_user_role(self, target_email: str, new_role: UserRole, admin_email: str) -> bool:

        """Updates user role. Only allowed if admin_email has ADMIN role."""

        admin = self.get_user_by_email(admin_email)

        if not admin or not admin.can_admin():

            raise PermissionError("Solo un ADMIN può modificare i ruoli degli utenti.")

        target = self.get_user_by_email(target_email)

        if not target:

            return False

        target.role = new_role

        self._save_users()

        return True

    def delete_user(self, target_email: str, admin_email: str) -> bool:

        """Deletes a user account. Only permitted by an ADMIN."""

        admin = self.get_user_by_email(admin_email)

        if not admin or not admin.can_admin():

            raise PermissionError("Solo un ADMIN può eliminare gli utenti.")

        clean_target = target_email.strip().lower()

        if clean_target == admin_email.strip().lower():

            raise ValueError("Non puoi eliminare il tuo stesso account amministratore.")

        if clean_target not in self._users:

            return False

        # Protect against deleting the last admin

        target_user = self._users[clean_target]

        if target_user.role == UserRole.ADMIN:

            admin_count = sum(1 for u in self._users.values() if u.role == UserRole.ADMIN)

            if admin_count <= 1:

                raise ValueError("Impossibile eliminare l'unico account amministratore del sistema.")

        del self._users[clean_target]

        self._save_users()

        return True

    def build_google_oauth_url(self, client_id: str, redirect_uri: str, state: str = "asma_auth", login_hint: Optional[str] = None, **kwargs) -> str:

        """Generates Google OAuth2 authorization URL (SRS Cap. 3.2)."""

        import urllib.parse

        params = {

            "client_id": client_id,

            "redirect_uri": redirect_uri,

            "response_type": "code",

            "scope": "openid email profile",

            "access_type": "offline",

            "state": state,

            "prompt": "select_account"

        }

        hint = login_hint or kwargs.get("login_hint")
        if hint:
            params["login_hint"] = str(hint).strip().lower()

        return f"https://accounts.google.com/o/oauth2/v2/auth?{urllib.parse.urlencode(params)}"

    @classmethod
    def get_allowed_emails(cls) -> list:
        return list(cls.BAND_PSEUDONYMS.keys())

    @classmethod
    def is_email_allowed(cls, email: str) -> bool:
        clean = email.strip().lower()
        return clean in cls.BAND_PSEUDONYMS

    @classmethod
    def get_admin_emails(cls) -> list:
        return ["danyposta@gmail.com"]

    def exchange_google_code_for_user(self, code: str, client_id: str, client_secret: str, redirect_uri: str):
        import urllib.request
        import urllib.parse
        import json
        token_url = "https://oauth2.googleapis.com/token"
        data = urllib.parse.urlencode({
            "code": code,
            "client_id": client_id,
            "client_secret": client_secret,
            "redirect_uri": redirect_uri,
            "grant_type": "authorization_code"
        }).encode("utf-8")
        req = urllib.request.Request(token_url, data=data, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                token_data = json.loads(resp.read().decode("utf-8"))
            access_token = token_data.get("access_token")
            if not access_token:
                return None
            user_info_url = f"https://www.googleapis.com/oauth2/v2/userinfo?access_token={access_token}"
            with urllib.request.urlopen(user_info_url, timeout=10) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except Exception:
            return None
