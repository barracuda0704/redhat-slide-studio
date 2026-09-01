import json
from datetime import datetime, timedelta
from pathlib import Path

from .models import User, UserRole, UserStatus
from .security import hash_password, new_session_token, verify_password


class UserManager:
    def __init__(self, data_dir: str, admin_email: str, admin_initial_password: str, session_ttl_days: int):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.session_ttl_days = session_ttl_days
        self._users: dict[str, dict] = self._load(self._users_path())
        self._sessions: dict[str, dict] = self._load(self._sessions_path())
        self._bootstrap_admin(admin_email, admin_initial_password)

    def _users_path(self) -> Path:
        return self.data_dir / "users.json"

    def _sessions_path(self) -> Path:
        return self.data_dir / "sessions.json"

    @staticmethod
    def _load(path: Path) -> dict:
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
        return {}

    def _save_users(self):
        self._users_path().write_text(
            json.dumps(self._users, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    def _save_sessions(self):
        self._sessions_path().write_text(
            json.dumps(self._sessions, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    def _bootstrap_admin(self, admin_email: str, admin_initial_password: str):
        if admin_email in self._users:
            return
        now = datetime.now().isoformat()
        admin = User(
            email=admin_email,
            password_hash=hash_password(admin_initial_password),
            role=UserRole.ADMIN,
            status=UserStatus.APPROVED,
            created_at=now,
            approved_at=now,
            notify_email=admin_email,
        )
        self._users[admin_email] = admin.model_dump()
        self._save_users()

    def register(self, email: str, password: str) -> User:
        email = email.strip().lower()
        if email in self._users:
            raise ValueError("이미 가입된 이메일입니다.")
        now = datetime.now().isoformat()
        user = User(
            email=email,
            password_hash=hash_password(password),
            role=UserRole.USER,
            status=UserStatus.PENDING,
            created_at=now,
            notify_email=email,
        )
        self._users[email] = user.model_dump()
        self._save_users()
        return user

    def get_user(self, email: str) -> User | None:
        data = self._users.get(email.strip().lower())
        return User.model_validate(data) if data else None

    def authenticate(self, email: str, password: str) -> tuple[User | None, str | None]:
        user = self.get_user(email)
        if not user or not verify_password(password, user.password_hash):
            return None, "이메일 또는 비밀번호가 올바르지 않습니다."
        if user.status == UserStatus.PENDING:
            return None, "관리자 승인 대기 중입니다."
        if user.status == UserStatus.REJECTED:
            return None, "가입이 거부되었거나 접근이 차단된 계정입니다."
        return user, None

    def create_session(self, email: str) -> str:
        token = new_session_token()
        expires_at = (datetime.now() + timedelta(days=self.session_ttl_days)).isoformat()
        self._sessions[token] = {"email": email, "expires_at": expires_at}
        self._save_sessions()
        return token

    def get_session_user(self, token: str) -> User | None:
        session = self._sessions.get(token)
        if not session:
            return None
        if datetime.fromisoformat(session["expires_at"]) < datetime.now():
            self.delete_session(token)
            return None
        return self.get_user(session["email"])

    def delete_session(self, token: str):
        if token in self._sessions:
            del self._sessions[token]
            self._save_sessions()

    def list_users(self) -> list[User]:
        return sorted(
            (User.model_validate(u) for u in self._users.values()),
            key=lambda u: u.created_at,
            reverse=True,
        )

    def set_status(self, email: str, status: UserStatus) -> User:
        email = email.strip().lower()
        data = self._users.get(email)
        if not data:
            raise ValueError("사용자를 찾을 수 없습니다.")
        user = User.model_validate(data)
        user.status = status
        if status == UserStatus.APPROVED:
            user.approved_at = datetime.now().isoformat()
        self._users[email] = user.model_dump()
        self._save_users()
        return user

    def _invalidate_sessions_for(self, email: str):
        tokens = [t for t, s in self._sessions.items() if s.get("email") == email]
        for t in tokens:
            del self._sessions[t]
        if tokens:
            self._save_sessions()

    def delete_user(self, email: str):
        email = email.strip().lower()
        if email not in self._users:
            raise ValueError("사용자를 찾을 수 없습니다.")
        del self._users[email]
        self._save_users()
        self._invalidate_sessions_for(email)

    def update_email(self, old_email: str, new_email: str) -> User:
        old_email = old_email.strip().lower()
        new_email = new_email.strip().lower()
        if old_email not in self._users:
            raise ValueError("사용자를 찾을 수 없습니다.")
        if not new_email or "@" not in new_email:
            raise ValueError("올바른 이메일 형식이 아닙니다.")
        if new_email != old_email and new_email in self._users:
            raise ValueError("이미 사용 중인 이메일입니다.")

        data = self._users.pop(old_email)
        user = User.model_validate(data)
        if not user.notify_email or user.notify_email == user.email:
            user.notify_email = new_email
        user.email = new_email
        self._users[new_email] = user.model_dump()
        self._save_users()
        self._invalidate_sessions_for(old_email)
        return user

    def update_notify_email(self, email: str, notify_email: str) -> User:
        email = email.strip().lower()
        data = self._users.get(email)
        if not data:
            raise ValueError("사용자를 찾을 수 없습니다.")
        notify_email = notify_email.strip().lower()
        if not notify_email or "@" not in notify_email:
            raise ValueError("올바른 이메일 형식이 아닙니다.")

        user = User.model_validate(data)
        user.notify_email = notify_email
        self._users[email] = user.model_dump()
        self._save_users()
        return user
