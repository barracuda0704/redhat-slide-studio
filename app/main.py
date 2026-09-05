import asyncio
import subprocess
from pathlib import Path
from urllib.parse import quote

import httpx
from fastapi import BackgroundTasks, Depends, FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from .config import settings, get_unsplash_key, save_unsplash_key, clear_unsplash_key
from .models import User, UserRole, UserStatus
from .projects import ProjectManager
from .users import UserManager

app = FastAPI(title="Slide Studio", version="1.0.0")

BASE_DIR = Path(__file__).resolve().parent.parent
WEB_DIR = BASE_DIR / "web"
ENGINE_DIR = Path(settings.ENGINE_DIR)

app.mount("/static", StaticFiles(directory=str(WEB_DIR / "static")), name="static")


@app.middleware("http")
async def no_cache_static(request: Request, call_next):
    response = await call_next(request)
    if request.url.path.startswith("/static/") or request.url.path.startswith("/projects/"):
        response.headers["Cache-Control"] = "no-cache"
    return response


user_manager = UserManager(
    settings.DATA_DIR,
    admin_email=settings.ADMIN_EMAIL,
    admin_initial_password=settings.ADMIN_INITIAL_PASSWORD,
    session_ttl_days=settings.SESSION_TTL_DAYS,
)

project_manager = ProjectManager(settings.ENGINE_DIR)

SERVICE_ACCOUNT_EMAIL = "service@slide-studio.local"

_SERVICE_USER = User(
    email=SERVICE_ACCOUNT_EMAIL,
    password_hash="",
    role=UserRole.USER,
    status=UserStatus.APPROVED,
)


def get_current_user(request: Request) -> User:
    if settings.LOGIN_DISABLED:
        return _SERVICE_USER
    token = request.cookies.get(settings.SESSION_COOKIE_NAME)
    user = user_manager.get_session_user(token) if token else None
    if not user:
        raise HTTPException(401, "로그인이 필요합니다.")
    return user


def require_admin(user: User = Depends(get_current_user)) -> User:
    # Single-tenant deployments (LOGIN_DISABLED) only ever have the synthetic
    # service account, which is role=USER — without this bypass every
    # admin-gated endpoint (e.g. Unsplash key registration) would be
    # permanently unreachable in the mode this app actually runs in.
    if not settings.LOGIN_DISABLED and user.role != UserRole.ADMIN:
        raise HTTPException(403, "관리자 권한이 필요합니다.")
    return user


def _logged_in_user(request: Request) -> User | None:
    if settings.LOGIN_DISABLED:
        return _SERVICE_USER
    token = request.cookies.get(settings.SESSION_COOKIE_NAME)
    return user_manager.get_session_user(token) if token else None


# ── Page routes ──

@app.get("/login", response_class=HTMLResponse)
async def login_page():
    if settings.LOGIN_DISABLED:
        return RedirectResponse("/")
    return (WEB_DIR / "login.html").read_text(encoding="utf-8")


@app.get("/register", response_class=HTMLResponse)
async def register_page():
    if settings.LOGIN_DISABLED:
        return RedirectResponse("/")
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


@app.get("/new", response_class=HTMLResponse)
async def new_project_page(request: Request):
    if not _logged_in_user(request):
        return RedirectResponse("/login")
    return (WEB_DIR / "new.html").read_text(encoding="utf-8")


@app.get("/projects/{name}", response_class=HTMLResponse)
async def project_page(name: str, request: Request):
    if not _logged_in_user(request):
        return RedirectResponse("/login")
    return (WEB_DIR / "project.html").read_text(encoding="utf-8")


# ── Auth API ──

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
    if settings.LOGIN_DISABLED:
        # This endpoint used to accept real credentials regardless of
        # LOGIN_DISABLED — get_current_user() bypasses auth entirely in this
        # mode, but /api/login itself stayed live, so a real admin password
        # still worked here even in a deployment meant to have no login at
        # all. Closing it off entirely rather than just hiding the login UI.
        raise HTTPException(403, "로그인이 비활성화된 배포입니다.")
    user, error = user_manager.authenticate(email, password)
    if not user:
        raise HTTPException(401, error)
    token = user_manager.create_session(user.email)
    response.set_cookie(
        settings.SESSION_COOKIE_NAME, token,
        httponly=True, samesite="lax",
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
    return {"email": user.email, "role": user.role.value, "login_disabled": settings.LOGIN_DISABLED}


# ── Admin API ──

@app.get("/api/admin/users")
async def api_admin_list_users(_: User = Depends(require_admin)):
    return [
        {"email": u.email, "notify_email": u.notify_email or u.email, "role": u.role.value,
         "status": u.status.value, "created_at": u.created_at, "approved_at": u.approved_at}
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
async def api_admin_edit_user(email: str, new_email: str = Form(None), notify_email: str = Form(None), _: User = Depends(require_admin)):
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


# ── Project API ──

class ProjectCreate(BaseModel):
    name: str
    title: str
    description: str = ""
    theme: str = "redhat-enterprise"
    num_slides: int = 8


@app.post("/api/projects")
async def api_create_project(body: ProjectCreate, user: User = Depends(get_current_user)):
    try:
        project = project_manager.create_project(
            body.name, body.title, user.email, body.theme, body.description, body.num_slides
        )
    except ValueError as e:
        raise HTTPException(400, str(e))
    return project


@app.get("/api/projects")
async def api_list_projects(user: User = Depends(get_current_user)):
    if user.role == UserRole.ADMIN or settings.LOGIN_DISABLED:
        return project_manager.list_projects()
    return project_manager.list_projects(user.email)


@app.get("/api/projects/{name}")
async def api_get_project(name: str, user: User = Depends(get_current_user)):
    try:
        return project_manager.get_project(name)
    except ValueError as e:
        raise HTTPException(404, str(e))


@app.delete("/api/projects/{name}")
async def api_delete_project(name: str, user: User = Depends(get_current_user)):
    try:
        project = project_manager.get_project(name)
        if user.role != UserRole.ADMIN and not settings.LOGIN_DISABLED and project.get("owner") != user.email:
            raise HTTPException(403, "본인의 프로젝트만 삭제할 수 있습니다.")
        project_manager.delete_project(name)
    except ValueError as e:
        raise HTTPException(404, str(e))
    return {"status": "deleted"}



# ── Generate API (AI) ──

class GenerateRequest(BaseModel):
    topic: str = ""
    description: str = ""
    num_slides: int = 8
    theme: str = "redhat-enterprise"
    content_md: str | None = None  # skip AI outline generation, use this markdown as-is


def _run_post_generation_qa(name: str, theme: str, max_rounds: int = 3) -> str | None:
    """Runs right after generation, before the deck is marked 'completed':
    rebuilds to catch PPTX-conversion-breaking structural issues (overflow,
    unwrapped text, etc. — reuses build_pptx()'s own per-slide failure
    detail) and reviews each slide against the theme's actual guide document
    for brand/typography drift, auto-fixing flagged slides through the same
    AI-edit pipeline the UI's "AI 수정" button uses. Capped at max_rounds
    (mirrors the reference skill bundle's own 3-attempt auto-fix limit) so a
    stubborn slide can't loop forever. Returns a warning string describing
    anything still unresolved, or None if the deck came out clean."""
    from . import generator
    filenames_to_check: list[str] | None = None
    remaining_issues: dict[str, str] = {}
    for _round in range(max_rounds):
        try:
            project_manager.build_pptx(name)
        except RuntimeError:
            break  # unbuildable in a way per-slide auto-fix can't generically address
        meta = project_manager._load_meta(name)
        structural = {f["filename"]: f["reason"] for f in ((meta or {}).get("build_failures") or [])}

        check_list = filenames_to_check if filenames_to_check is not None else project_manager.list_slides(name)
        brand_results: dict[str, dict] = {}
        for filename in check_list:
            try:
                html = project_manager.get_slide_html(name, filename)
                result = generator.review_slide_consistency(html, [], theme_id=theme)
            except Exception:
                continue  # one slide's review failing shouldn't block the whole QA pass
            if not result["matches"]:
                brand_results[filename] = result

        remaining_issues = dict(structural)
        for filename, result in brand_results.items():
            remaining_issues[filename] = (remaining_issues.get(filename, "") + " " + result["reason"]).strip()

        if not remaining_issues:
            return None  # clean — the build_pptx() call above already reflects this

        fixed_filenames = []
        for filename, issue in remaining_issues.items():
            try:
                html = project_manager.get_slide_html(name, filename)
            except ValueError:
                continue
            # Prefer the brand review's own fixed_html only when that's the
            # sole problem — it doesn't know the specific structural defect
            # (e.g. "overflows by 0.8pt"), so a slide with both issues goes
            # through apply_edit_instruction with the concrete description
            # instead of a fix aimed only at the style drift.
            fixed_html = None if filename in structural else brand_results.get(filename, {}).get("fixed_html")
            if not fixed_html:
                try:
                    fixed_html = generator.apply_edit_instruction(html, f"다음 문제를 해결하세요: {issue}")
                except Exception:
                    continue
            project_manager.save_slide_html(name, filename, fixed_html)
            fixed_filenames.append(filename)
        filenames_to_check = fixed_filenames

    # Loop exhausted max_rounds still with issues (or broke out early, e.g.
    # a timeout on a large deck) — rebuild once more and check its ACTUAL
    # result, rather than trusting remaining_issues from the loop above.
    # That loop-local state goes stale the moment a round breaks early
    # (build_pptx() timing out on a big deck was silently exiting the loop
    # with remaining_issues still {} from initialization, so this used to
    # report "clean" while the real, just-built PPTX was missing slides).
    try:
        project_manager.build_pptx(name)
    except RuntimeError:
        return "자동 품질 검토 중 최종 PPTX 빌드 자체가 실패했습니다. '빌드' 버튼으로 직접 다시 시도해주세요."
    meta = project_manager._load_meta(name)
    final_structural = {f["filename"] for f in ((meta or {}).get("build_failures") or [])}
    still_broken = final_structural | set(remaining_issues.keys())
    if not still_broken:
        return None
    return (
        f"자동 품질 검토를 시도했지만 다음 슬라이드에 문제가 남아있습니다: "
        + ", ".join(sorted(still_broken)) + ". AI 수정 기능으로 직접 확인해주세요."
    )


def _run_generation(name: str, topic: str, description: str, num_slides: int, theme: str, content_md: str | None = None):
    from . import generator
    meta = project_manager._load_meta(name)
    if meta:
        meta["status"] = "generating"
        project_manager._save_meta(name, meta)
    try:
        content = content_md if content_md else generator.generate_content(topic, num_slides, description)
        project_manager.save_content(name, content)

        total_saved = 0
        any_truncated = False
        # Generated (and saved) in batches rather than one giant completion —
        # each batch gets its own full max_tokens budget, so a 20-slide deck
        # can't run out of output length mid-slide the way a single call could.
        for batch_slides, truncated in generator.generate_slides_html_batches(content, theme):
            for s in batch_slides:
                project_manager.save_slide_html(name, s["filename"], s["html"])
                total_saved += 1
            any_truncated = any_truncated or truncated
            meta = project_manager._load_meta(name)
            if meta:
                meta["slides"] = total_saved
                project_manager._save_meta(name, meta)

        warnings = []
        if any_truncated:
            warnings.append(
                f"AI 응답이 출력 길이 제한에 걸려 요청한 {num_slides}장 중 {total_saved}장만 "
                f"생성되었습니다. 슬라이드 수를 줄여 다시 생성하거나, 나머지는 직접 추가하세요."
            )

        # Auto QA/fix pass — status stays "generating" through this so the
        # frontend keeps polling instead of showing the deck as done while
        # slides are still being rewritten underneath the user.
        if total_saved > 0:
            qa_warning = _run_post_generation_qa(name, theme)
            if qa_warning:
                warnings.append(qa_warning)

        meta = project_manager._load_meta(name)
        if meta:
            meta["status"] = "completed"
            meta["slides"] = total_saved
            if warnings:
                meta["generation_warning"] = "\n\n".join(warnings)
            else:
                meta.pop("generation_warning", None)
            project_manager._save_meta(name, meta)
    except Exception as e:
        meta = project_manager._load_meta(name)
        if meta:
            meta["status"] = "failed"
            meta["error"] = str(e)
            project_manager._save_meta(name, meta)


@app.post("/api/projects/{name}/generate")
async def api_generate(name: str, body: GenerateRequest, bg: BackgroundTasks, user: User = Depends(get_current_user)):
    try:
        project = project_manager.get_project(name)
    except ValueError as e:
        raise HTTPException(404, str(e))
    topic = body.topic or project.get("title", name)
    bg.add_task(
        _run_generation, name, topic, body.description or project.get("description", ""),
        body.num_slides, body.theme or project.get("theme", "redhat-enterprise"), body.content_md,
    )
    return {"status": "generating", "message": "AI가 슬라이드를 생성하고 있습니다."}


# ── Slides API ──

@app.get("/api/projects/{name}/slides")
async def api_list_slides(name: str, _: User = Depends(get_current_user)):
    return project_manager.list_slides(name)


@app.get("/api/projects/{name}/slides/{filename}")
async def api_get_slide(name: str, filename: str, _: User = Depends(get_current_user)):
    try:
        return {"html": project_manager.get_slide_html(name, filename)}
    except ValueError as e:
        raise HTTPException(404, str(e))


class SlideUpdate(BaseModel):
    html: str


@app.put("/api/projects/{name}/slides/{filename}")
async def api_save_slide(name: str, filename: str, body: SlideUpdate, _: User = Depends(get_current_user)):
    try:
        project_manager.save_slide_html(name, filename, body.html)
    except ValueError as e:
        raise HTTPException(400, str(e))
    return {"status": "saved"}


@app.delete("/api/projects/{name}/slides/{filename}")
async def api_delete_slide(name: str, filename: str, _: User = Depends(get_current_user)):
    try:
        project_manager.delete_slide(name, filename)
    except ValueError as e:
        raise HTTPException(404, str(e))
    return {"status": "deleted"}


@app.post("/api/projects/{name}/slides")
async def api_add_blank_slide(name: str, _: User = Depends(get_current_user)):
    try:
        filename = project_manager.add_blank_slide(name)
    except ValueError as e:
        raise HTTPException(404, str(e))
    return {"filename": filename}


class ReorderRequest(BaseModel):
    order: list[str]


@app.post("/api/projects/{name}/slides/reorder")
async def api_reorder_slides(name: str, body: ReorderRequest, _: User = Depends(get_current_user)):
    try:
        new_order = project_manager.reorder_slides(name, body.order)
    except ValueError as e:
        raise HTTPException(400, str(e))
    return {"order": new_order}


@app.get("/api/projects/{name}/slides/{filename}/backup")
async def api_has_slide_backup(name: str, filename: str, _: User = Depends(get_current_user)):
    try:
        return {"has_backup": project_manager.has_slide_backup(name, filename)}
    except ValueError as e:
        raise HTTPException(400, str(e))


@app.post("/api/projects/{name}/slides/{filename}/restore")
async def api_restore_slide(name: str, filename: str, _: User = Depends(get_current_user)):
    try:
        html = project_manager.restore_slide_backup(name, filename)
    except ValueError as e:
        raise HTTPException(404, str(e))
    return {"html": html}


class AiEditRequest(BaseModel):
    instruction: str
    target_html: str | None = None  # outerHTML of one element, if the request came from a WYSIWYG click-to-select
    current_html: str | None = None  # editor's live (possibly unsaved) HTML, if different from the saved file


@app.post("/api/projects/{name}/slides/{filename}/ai-edit")
async def api_ai_edit_slide(name: str, filename: str, body: AiEditRequest, _: User = Depends(get_current_user)):
    from . import generator
    if body.current_html:
        # Prefer the editor's live content over disk — otherwise unsaved
        # WYSIWYG changes (font size/color/drag, or a newly-inserted text
        # box) are invisible to the model, and target_html may not even
        # exist yet in the saved file.
        html = body.current_html
    else:
        try:
            html = project_manager.get_slide_html(name, filename)
        except ValueError as e:
            raise HTTPException(404, str(e))
    if not body.instruction.strip():
        raise HTTPException(400, "수정 요청 내용을 입력하세요.")
    new_html = await asyncio.to_thread(generator.apply_edit_instruction, html, body.instruction, body.target_html)
    return {"html": new_html}


@app.post("/api/projects/{name}/review-consistency")
async def api_review_consistency(name: str, _: User = Depends(get_current_user)):
    from . import generator
    filenames = project_manager.list_slides(name)
    if len(filenames) < 2:
        return {"results": []}  # nothing to compare a lone slide against
    htmls = {f: project_manager.get_slide_html(name, f) for f in filenames}
    # Was comparing slides only to each other — if the whole deck (or the
    # anchor slides themselves) already drifted from the theme, everything
    # looks "consistent" and nothing gets flagged. theme_id makes the actual
    # theme guide document (engine/themes/{theme}.md) the primary reference,
    # same as the automatic post-generation QA pass already does.
    try:
        project = project_manager.get_project(name)
    except ValueError:
        project = {}
    theme = project.get("theme", "redhat-enterprise")

    sem = asyncio.Semaphore(3)  # bound concurrent Claude calls per review run
    n = len(filenames)
    # Anchor each slide's comparison against a fixed {first, middle, last}
    # sample of the deck rather than its immediate neighbors. Neighbor-based
    # sampling has no way to tell which of two adjacent slides is the actual
    # outlier — a single off-theme slide sandwiched between two normal ones
    # gets ALL THREE flagged, since each only ever sees the others as "not
    # matching its neighbor". A fixed anchor sample gives every slide the
    # same reference frame, so one bad slide can corrupt at most one anchor
    # instead of appearing symmetrically "wrong" to everyone next to it.
    anchor_indices = sorted({0, n // 2, n - 1})

    async def review_one(i: int, filename: str) -> dict | None:
        sibling_indices = [j for j in anchor_indices if j != i] or [j for j in range(n) if j != i][:2]
        siblings = [htmls[filenames[j]] for j in sibling_indices]
        async with sem:
            try:
                result = await asyncio.to_thread(
                    generator.review_slide_consistency, htmls[filename], siblings, theme
                )
            except Exception:
                return None  # one slide's review failing shouldn't fail the whole batch
        if result["matches"]:
            return None
        return {"filename": filename, "reason": result["reason"], "fixed_html": result["fixed_html"]}

    results = await asyncio.gather(*(review_one(i, f) for i, f in enumerate(filenames)))
    return {"results": [r for r in results if r]}


@app.get("/api/projects/{name}/slides/{filename}/preview", response_class=HTMLResponse)
async def api_slide_preview(name: str, filename: str):
    try:
        html = project_manager.get_slide_html(name, filename)
        html = html.replace("../../../../redhat/", "/engine/redhat/")
        html = html.replace('src="assets/', f'src="/api/projects/{name}/assets/')
        return html
    except ValueError as e:
        raise HTTPException(404, str(e))


# ── Build API ──

@app.post("/api/projects/{name}/build")
async def api_build(name: str, _: User = Depends(get_current_user)):
    try:
        pptx_path = await asyncio.to_thread(project_manager.build_pptx, name)
        return {"status": "completed", "path": pptx_path}
    except (ValueError, RuntimeError) as e:
        raise HTTPException(400, str(e))


@app.get("/api/projects/{name}/download")
async def api_download(name: str, _: User = Depends(get_current_user)):
    pptx_path = project_manager.get_pptx_path(name)
    if not pptx_path:
        raise HTTPException(404, "PPTX 파일이 없습니다. 먼저 빌드하세요.")
    project = project_manager.get_project(name)
    dl_name = f"{project.get('title', name)}.pptx"
    return FileResponse(pptx_path, filename=dl_name, media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation")


@app.get("/api/projects/{name}/export/html")
async def api_export_html(name: str, _: User = Depends(get_current_user)):
    try:
        html = project_manager.export_html(name)
    except ValueError as e:
        raise HTTPException(404, str(e))
    project = project_manager.get_project(name)
    dl_name = f"{project.get('title', name)}.html"
    return Response(
        html, media_type="text/html",
        headers={"Content-Disposition": f"attachment; filename*=UTF-8''{quote(dl_name)}"},
    )


@app.post("/api/projects/{name}/export/pdf")
async def api_export_pdf(name: str, _: User = Depends(get_current_user)):
    try:
        pdf_path = await asyncio.to_thread(project_manager.export_pdf, name)
        return {"status": "completed", "path": pdf_path}
    except (ValueError, RuntimeError) as e:
        raise HTTPException(400, str(e))


@app.get("/api/projects/{name}/export/pdf/download")
async def api_export_pdf_download(name: str, _: User = Depends(get_current_user)):
    pdf_path = project_manager.get_pdf_path(name)
    if not pdf_path:
        raise HTTPException(404, "PDF 파일이 없습니다. 먼저 생성하세요.")
    project = project_manager.get_project(name)
    dl_name = f"{project.get('title', name)}.pdf"
    return FileResponse(pdf_path, filename=dl_name, media_type="application/pdf")


# ── Assets API ──

class RenameAssetRequest(BaseModel):
    old_filename: str
    new_filename: str


@app.get("/api/projects/{name}/assets")
async def api_list_assets(name: str, _: User = Depends(get_current_user)):
    try:
        return project_manager.list_assets(name)
    except ValueError as e:
        raise HTTPException(404, str(e))


@app.get("/api/projects/{name}/assets/{filename:path}")
async def api_asset(name: str, filename: str):
    try:
        asset_path = project_manager.get_asset_path(name, filename)
    except ValueError:
        raise HTTPException(404)
    if not asset_path:
        raise HTTPException(404)
    return FileResponse(asset_path)


@app.post("/api/projects/{name}/assets")
async def api_upload_asset(name: str, file: UploadFile = File(...), _: User = Depends(get_current_user)):
    data = await file.read()
    try:
        saved_name = project_manager.save_asset(name, file.filename or "upload.png", data)
    except ValueError as e:
        raise HTTPException(400, str(e))
    return {"filename": saved_name}


@app.post("/api/projects/{name}/assets/rename")
async def api_rename_asset(name: str, body: RenameAssetRequest, _: User = Depends(get_current_user)):
    try:
        new_name = project_manager.rename_asset(name, body.old_filename, body.new_filename)
    except ValueError as e:
        raise HTTPException(400, str(e))
    return {"filename": new_name}


@app.delete("/api/projects/{name}/assets/{filename:path}")
async def api_delete_asset(name: str, filename: str, _: User = Depends(get_current_user)):
    try:
        project_manager.delete_asset(name, filename)
    except ValueError as e:
        raise HTTPException(400, str(e))
    return {"status": "deleted"}



class ImportAssetUrlRequest(BaseModel):
    url: str
    filename: str


@app.post("/api/projects/{name}/assets/import-url")
async def api_import_asset_url(name: str, body: ImportAssetUrlRequest, _: User = Depends(get_current_user)):
    # Fetches server-side (not from the browser) so logo/stock-photo imports
    # never hit CORS, and the result flows through the same save_asset()
    # path as a manual upload.
    try:
        async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
            res = await client.get(body.url)
        res.raise_for_status()
    except httpx.HTTPError as e:
        raise HTTPException(400, f"이미지를 가져오지 못했습니다: {e}")
    try:
        saved_name = project_manager.save_asset(name, body.filename, res.content)
    except ValueError as e:
        raise HTTPException(400, str(e))
    return {"filename": saved_name}


class GenerateImageRequest(BaseModel):
    prompt: str
    aspect_ratio: str = "16:9"


@app.post("/api/projects/{name}/generate-image")
async def api_generate_image(name: str, body: GenerateImageRequest, _: User = Depends(get_current_user)):
    from . import generator
    if not body.prompt.strip():
        raise HTTPException(400, "프롬프트를 입력하세요.")
    try:
        image_bytes = await asyncio.to_thread(generator.generate_image, body.prompt.strip(), body.aspect_ratio)
    except subprocess.TimeoutExpired:
        raise HTTPException(504, "이미지 생성 시간이 초과되었습니다.")
    except Exception as e:
        raise HTTPException(502, f"이미지 생성 실패: {e}")
    try:
        saved_name = project_manager.save_asset(name, "generated.png", image_bytes)
    except ValueError as e:
        raise HTTPException(400, str(e))
    return {"filename": saved_name}


# ── Logo/icon search (SVGL — free public API, no key required) ──

@app.get("/api/logos/search")
async def api_logo_search(q: str, _: User = Depends(get_current_user)):
    if not q.strip():
        return []
    try:
        async with httpx.AsyncClient(timeout=8) as client:
            res = await client.get("https://api.svgl.app", params={"search": q})
        res.raise_for_status()
        items = res.json()
    except httpx.HTTPError:
        return []
    results = []
    for item in items:
        route = item.get("route")
        url = route.get("light") if isinstance(route, dict) else route
        if url:
            results.append({"name": item.get("title", q), "url": url})
    return results[:30]


# ── Unsplash stock photo search ──
# The access key is registered later by the user (Settings 화면), not baked
# in here — see config.get_unsplash_key()/save_unsplash_key().

@app.get("/api/unsplash/status")
async def api_unsplash_status(_: User = Depends(get_current_user)):
    return {"configured": bool(get_unsplash_key())}


class UnsplashKeyRequest(BaseModel):
    api_key: str


@app.post("/api/unsplash/key")
async def api_unsplash_save_key(body: UnsplashKeyRequest, _: User = Depends(require_admin)):
    if not body.api_key.strip():
        raise HTTPException(400, "API 키를 입력하세요.")
    save_unsplash_key(body.api_key)
    return {"status": "ok"}


@app.delete("/api/unsplash/key")
async def api_unsplash_clear_key(_: User = Depends(require_admin)):
    clear_unsplash_key()
    return {"status": "ok"}


@app.get("/api/unsplash/search")
async def api_unsplash_search(q: str, page: int = 1, per_page: int = 20, _: User = Depends(get_current_user)):
    key = get_unsplash_key()
    if not key:
        raise HTTPException(400, "Unsplash API 키가 등록되지 않았습니다. 설정에서 먼저 등록하세요.")
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            res = await client.get(
                "https://api.unsplash.com/search/photos",
                params={"query": q, "page": page, "per_page": per_page},
                headers={"Authorization": f"Client-ID {key}"},
            )
        res.raise_for_status()
    except httpx.HTTPError as e:
        raise HTTPException(502, f"Unsplash 검색 실패: {e}")
    data = res.json()
    results = [
        {
            "id": r["id"],
            "thumb": r["urls"]["thumb"],
            "regular": r["urls"]["regular"],
            "download_location": r["links"]["download_location"],
            "author": r["user"]["name"],
        }
        for r in data.get("results", [])
    ]
    return {"results": results, "total_pages": data.get("total_pages", 0)}


class UnsplashTrackRequest(BaseModel):
    download_location: str


@app.post("/api/unsplash/track-download")
async def api_unsplash_track_download(body: UnsplashTrackRequest, _: User = Depends(get_current_user)):
    # Required by Unsplash's API terms whenever a photo is actually used,
    # separate from the search call itself.
    key = get_unsplash_key()
    if not key:
        return {"status": "skipped"}
    try:
        async with httpx.AsyncClient(timeout=8) as client:
            await client.get(body.download_location, headers={"Authorization": f"Client-ID {key}"})
    except httpx.HTTPError:
        pass
    return {"status": "ok"}


# ── Themes API ──

@app.get("/api/themes")
async def api_themes():
    return project_manager.list_themes()


# ── Engine static (for slide preview) ──

@app.get("/engine/redhat/theme.css")
async def engine_theme_css():
    p = ENGINE_DIR / "redhat" / "theme.css"
    if not p.exists():
        raise HTTPException(404)
    return Response(p.read_text("utf-8"), media_type="text/css")


@app.get("/engine/redhat/icons/official/{filename}")
async def engine_icon(filename: str):
    p = ENGINE_DIR / "redhat" / "icons" / "official" / filename
    if not p.exists():
        raise HTTPException(404)
    return FileResponse(str(p), media_type="image/png")


@app.get("/engine/redhat/logos/{filename:path}")
async def engine_logo(filename: str):
    p = ENGINE_DIR / "redhat" / "logos" / filename
    if not p.exists():
        raise HTTPException(404)
    return FileResponse(str(p))


# ── Health ──

@app.get("/api/health")
async def health():
    return {"status": "ok"}
