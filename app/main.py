from pathlib import Path

from fastapi import Depends, FastAPI, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from fastapi.staticfiles import StaticFiles

from .config import settings
from .models import User, UserRole, UserStatus
from .users import UserManager

app = FastAPI(title="Slide Studio", version="1.0.0")

BASE_DIR = Path(__file__).resolve().parent.parent
WEB_DIR = BASE_DIR / "web"

app.mount("/static", StaticFiles(directory=str(WEB_DIR / "static")), name="static")


@app.middleware("http")
async def no_cache_static(request: Request, call_next):
    response = await call_next(request)
    if request.url.path.startswith("/static/"):
        response.headers["Cache-Control"] = "no-cache"
    return response


user_manager = UserManager(
    settings.DATA_DIR,
    admin_email=settings.ADMIN_EMAIL,
    admin_initial_password=settings.ADMIN_INITIAL_PASSWORD,
    session_ttl_days=settings.SESSION_TTL_DAYS,
)


def get_current_user(request: Request) -> User:
    token = request.cookies.get(settings.SESSION_COOKIE_NAME)
    user = user_manager.get_session_user(token) if token else None
    if not user:
        raise HTTPException(401, "로그인이 필요합니다.")
    return user


def require_admin(user: User = Depends(get_current_user)) -> User:
    if user.role != UserRole.ADMIN:
        raise HTTPException(403, "관리자 권한이 필요합니다.")
    return user


def _logged_in_user(request: Request) -> User | None:
    token = request.cookies.get(settings.SESSION_COOKIE_NAME)
    return user_manager.get_session_user(token) if token else None


@app.get("/login", response_class=HTMLResponse)
async def login_page():
    return (WEB_DIR / "login.html").read_text(encoding="utf-8")


@app.get("/register", response_class=HTMLResponse)
async def register_page():
    return (WEB_DIR / "register.html").read_text(encoding="utf-8")


@app.get("/admin", response_class=HTMLResponse)
async def admin_page(request: Request):
    user = _logged_in_user(request)
    if not user or user.role != UserRole.ADMIN:
        return RedirectResponse("/")
    return (WEB_DIR / "admin.html").read_text(encoding="utf-8")


@app.get("/", response_class=HTMLResponse)
async def index_page(request: Request):
    if not _logged_in_user(request):
        return RedirectResponse("/login")
    return (WEB_DIR / "index.html").read_text(encoding="utf-8")


@app.post("/api/register")
async def api_register(email: str = Form(...), password: str = Form(...)):
    email = email.strip().lower()
    if not email or "@" not in email:
        raise HTTPException(400, "올바른 이메일 형식이 아닙니다.")
    if len(password) < 8:
        raise HTTPException(400, "비밀번호는 8자 이상이어야 합니다.")
    try:
        user_manager.register(email, password)
    except ValueError as e:
        raise HTTPException(400, str(e))
    return {"status": "pending", "message": "가입 신청이 접수되었습니다. 관리자 승인 후 로그인할 수 있습니다."}


@app.post("/api/login")
async def api_login(response: Response, email: str = Form(...), password: str = Form(...)):
    user, error = user_manager.authenticate(email, password)
    if not user:
        raise HTTPException(401, error)
    token = user_manager.create_session(user.email)
    response.set_cookie(
        settings.SESSION_COOKIE_NAME,
        token,
        httponly=True,
        samesite="lax",
        secure=settings.SESSION_COOKIE_SECURE,
        max_age=settings.SESSION_TTL_DAYS * 24 * 3600,
    )
    return {"status": "ok", "email": user.email, "role": user.role.value}


@app.post("/api/logout")
async def api_logout(request: Request, response: Response):
    token = request.cookies.get(settings.SESSION_COOKIE_NAME)
    if token:
        user_manager.delete_session(token)
    response.delete_cookie(settings.SESSION_COOKIE_NAME)
    return {"status": "ok"}


@app.get("/api/me")
async def api_me(user: User = Depends(get_current_user)):
    return {"email": user.email, "role": user.role.value}


@app.get("/api/admin/users")
async def api_admin_list_users(_: User = Depends(require_admin)):
    return [
        {
            "email": u.email,
            "notify_email": u.notify_email or u.email,
            "role": u.role.value,
            "status": u.status.value,
            "created_at": u.created_at,
            "approved_at": u.approved_at,
        }
        for u in user_manager.list_users()
    ]


@app.post("/api/admin/users/{email}/approve")
async def api_admin_approve_user(email: str, _: User = Depends(require_admin)):
    try:
        user_manager.set_status(email, UserStatus.APPROVED)
    except ValueError as e:
        raise HTTPException(404, str(e))
    return {"status": "approved"}


@app.post("/api/admin/users/{email}/reject")
async def api_admin_reject_user(email: str, _: User = Depends(require_admin)):
    try:
        user_manager.set_status(email, UserStatus.REJECTED)
    except ValueError as e:
        raise HTTPException(404, str(e))
    return {"status": "rejected"}


@app.delete("/api/admin/users/{email}")
async def api_admin_delete_user(email: str, admin: User = Depends(require_admin)):
    email = email.strip().lower()
    if email == admin.email:
        raise HTTPException(400, "본인 계정은 삭제할 수 없습니다.")
    if email == settings.ADMIN_EMAIL:
        raise HTTPException(400, "최초 관리자 계정은 삭제할 수 없습니다.")
    try:
        user_manager.delete_user(email)
    except ValueError as e:
        raise HTTPException(404, str(e))
    return {"status": "deleted"}


@app.post("/api/admin/users/{email}/edit")
async def api_admin_edit_user(
    email: str,
    new_email: str = Form(None),
    notify_email: str = Form(None),
    _: User = Depends(require_admin),
):
    try:
        current = email.strip().lower()
        if new_email and new_email.strip().lower() != current:
            updated = user_manager.update_email(current, new_email)
            current = updated.email
        if notify_email:
            user_manager.update_notify_email(current, notify_email)
    except ValueError as e:
        raise HTTPException(400, str(e))
    return {"status": "updated"}


@app.get("/api/health")
async def health():
    return {"status": "ok"}
