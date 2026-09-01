from pydantic import BaseModel
from enum import Enum


class UserRole(str, Enum):
    ADMIN = "admin"
    USER = "user"


class UserStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class User(BaseModel):
    email: str
    password_hash: str
    role: UserRole = UserRole.USER
    status: UserStatus = UserStatus.PENDING
    created_at: str = ""
    approved_at: str | None = None
    notify_email: str | None = None


class ProjectStatus(str, Enum):
    DRAFT = "draft"
    GENERATING = "generating"
    COMPLETED = "completed"
    FAILED = "failed"
