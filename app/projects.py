import re
import json
import os
import base64
import mimetypes
import shutil
import subprocess
import tempfile
import threading
from datetime import datetime, timezone
from pathlib import Path

REDHAT_REL_RE = re.compile(r'(href|src)="\.\./\.\./\.\./\.\./redhat/([^"]+)"')
ASSET_REL_RE = re.compile(r'src="assets/([^"]+)"')
REDHAT_URL_RE = re.compile(r"url\(\s*['\"]?\.\./\.\./\.\./\.\./redhat/([^'\")]+)['\"]?\s*\)")
ASSET_URL_RE = re.compile(r"url\(\s*['\"]?assets/([^'\")]+)['\"]?\s*\)")
def _blank_slide_html(deck_title: str, page_num: int, total: int) -> str:
    """A blank slide that already follows the deck's standard anatomy
    (eyebrow + title-wrap + footer) so it doesn't stand out as a different
    theme once the user fills it in via AI edit."""
    return f"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<link rel="stylesheet" href="../../../../redhat/theme.css">
<style>
body {{ display: flex; flex-direction: column; word-break: keep-all; }}
.eyebrow {{
  font-size: 11pt; font-weight: 500; letter-spacing: 0.08em; color: #ee0000;
  text-transform: uppercase; margin: 0 0 6pt 0;
}}
.title-wrap {{ border-left: 3pt solid #ee0000; padding-left: 10pt; margin-bottom: 14pt; }}
.title-wrap h2 {{ font-size: 20pt; font-weight: 700; line-height: 1.3; color: #151515; margin: 0; }}
.placeholder {{ color: #4d4d4d; font-size: 12pt; margin: 0; }}
.footer {{
  margin-top: auto; display: flex; justify-content: space-between;
  border-top: 0.5pt solid #e0e0e0; padding-top: 6pt;
}}
.footer p {{ font-size: 10pt; color: #4d4d4d; margin: 0; }}
</style>
</head>
<body>
<div class="header-area">
  <p class="eyebrow">새 슬라이드</p>
  <div class="title-wrap"><h2>제목을 입력하세요</h2></div>
</div>
<p class="placeholder">여기에 내용을 입력하세요.</p>
<footer class="footer">
  <p>{deck_title}</p>
  <p>{page_num} / {total}</p>
</footer>
</body>
</html>
"""

# Project/version/filename come straight from URL path params — never trust
# them as path components without validation (e.g. name="..") reaches
# shutil.rmtree(projects_dir / "..") == delete the whole engine dir).
NAME_RE = re.compile(r'^[a-z0-9]+(-[a-z0-9]+)*$')
VERSION_RE = re.compile(r'^v\d+\.\d+$')
FILENAME_RE = re.compile(r'^[A-Za-z0-9][A-Za-z0-9_.-]*$')


def _validate_name(name: str) -> str:
    if not name or not NAME_RE.match(name):
        raise ValueError(f"올바르지 않은 프로젝트 이름입니다: {name}")
    return name


def _validate_version(version: str) -> str:
    if not version or not VERSION_RE.match(version):
        raise ValueError(f"올바르지 않은 버전입니다: {version}")
    return version


def _validate_filename(filename: str) -> str:
    if not filename or not FILENAME_RE.match(filename):
        raise ValueError(f"올바르지 않은 파일명입니다: {filename}")
    return filename


def _sanitize_asset_filename(original: str) -> str:
    """Uploaded filenames are real-world (screenshots, phone photos): spaces,
    Korean text, parentheses — all rejected by FILENAME_RE, which is meant
    for internal slideNN-*.html names, not user file uploads. An upload
    always creates a brand-new file, so sanitize instead of rejecting:
    strip to a basename, drop anything unsafe, keep the extension."""
    base = os.path.basename((original or "").strip()) or "upload"
    stem, ext = os.path.splitext(base)
    stem = re.sub(r'[^A-Za-z0-9_-]+', '-', stem).strip('-') or "asset"
    ext = re.sub(r'[^A-Za-z0-9.]', '', ext)[:10]
    return f"{stem}{ext}"


def _validate_asset_filename(filename: str) -> str:
    if not filename or filename.startswith("/") or ".." in filename or "\\" in filename:
        raise ValueError(f"올바르지 않은 파일명입니다: {filename}")
    for part in filename.split("/"):
        _validate_filename(part)
    return filename


class ProjectManager:
    def __init__(self, engine_dir: str):
        self.engine_dir = Path(engine_dir)
        self.projects_dir = self.engine_dir / "projects"
        self.projects_dir.mkdir(parents=True, exist_ok=True)
        self._locks: dict[str, threading.Lock] = {}
        self._locks_guard = threading.Lock()

    def _lock_for(self, name: str) -> threading.Lock:
        # Per-project lock so a double-clicked build/save/generate can't
        # interleave its project.json read-modify-write with another request
        # for the same project (separate projects never contend).
        with self._locks_guard:
            lock = self._locks.get(name)
            if lock is None:
                lock = threading.Lock()
                self._locks[name] = lock
            return lock

    def _project_dir(self, name: str) -> Path:
        return self.projects_dir / _validate_name(name)

    def _version_dir(self, name: str, version: str = "v1.0") -> Path:
        return self._project_dir(name) / _validate_version(version)

    def _meta_path(self, name: str, version: str = "v1.0") -> Path:
        return self._version_dir(name, version) / "project.json"

    def _load_meta(self, name: str, version: str = "v1.0") -> dict | None:
        p = self._meta_path(name, version)
        if p.exists():
            return json.loads(p.read_text("utf-8"))
        return None

    def _save_meta(self, name: str, meta: dict, version: str = "v1.0"):
        p = self._meta_path(name, version)
        p.write_text(json.dumps(meta, ensure_ascii=False, indent=2) + "\n", "utf-8")

    def _now_iso(self) -> str:
        return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    def create_project(self, name: str, title: str, owner_email: str, theme: str = "redhat-enterprise", description: str = "", num_slides: int = 8) -> dict:
        slug = _validate_name(name.strip().lower().replace(" ", "-"))
        version_dir = self._version_dir(slug)
        if version_dir.exists():
            raise ValueError(f"프로젝트 '{slug}'가 이미 존재합니다.")
        version_dir.mkdir(parents=True)
        (version_dir / "html").mkdir()
        (version_dir / "assets").mkdir()
        (version_dir / "content.md").write_text("", "utf-8")
        meta = {
            "title": title,
            "description": description,
            "author": "Red Hat Korea",
            "owner": owner_email,
            "theme": theme,
            "num_slides": num_slides,
            "status": "draft",
            "slides": 0,
            "created": self._now_iso(),
            "updated": self._now_iso(),
        }
        self._save_meta(slug, meta)
        return {"name": slug, **meta}

    def list_projects(self, owner_email: str | None = None) -> list[dict]:
        results = []
        if not self.projects_dir.exists():
            return results
        for d in sorted(self.projects_dir.iterdir()):
            if not d.is_dir() or d.name.startswith("."):
                continue
            try:
                meta = self._load_meta(d.name)
            except ValueError:
                continue  # directory name doesn't match the slug format — skip, don't 500 the whole list
            if not meta:
                continue
            if owner_email and meta.get("owner") != owner_email:
                continue
            html_dir = d / "v1.0" / "html"
            slide_count = len([f for f in html_dir.glob("slide*.html")]) if html_dir.exists() else 0
            has_pptx = (d / "v1.0" / "slides.pptx").exists()
            results.append({
                "name": d.name,
                "title": meta.get("title", d.name),
                "description": meta.get("description", ""),
                "owner": meta.get("owner", ""),
                "theme": meta.get("theme", "redhat-enterprise"),
                "status": meta.get("status", "draft"),
                "slides": slide_count,
                "has_pptx": has_pptx,
                "created": meta.get("created", ""),
                "updated": meta.get("updated", ""),
            })
        return results

    def get_project(self, name: str, version: str = "v1.0") -> dict:
        meta = self._load_meta(name, version)
        if not meta:
            raise ValueError(f"프로젝트 '{name}'을 찾을 수 없습니다.")
        html_dir = self._version_dir(name, version) / "html"
        slides = sorted([f.name for f in html_dir.glob("slide*.html")]) if html_dir.exists() else []
        has_pptx = (self._version_dir(name, version) / "slides.pptx").exists()
        return {**meta, "name": name, "version": version, "slides": slides, "has_pptx": has_pptx}

    def delete_project(self, name: str) -> bool:
        project_dir = self._project_dir(name)
        if not project_dir.exists():
            raise ValueError(f"프로젝트 '{name}'을 찾을 수 없습니다.")
        shutil.rmtree(project_dir)
        return True

    def get_content(self, name: str, version: str = "v1.0") -> str:
        p = self._version_dir(name, version) / "content.md"
        if not p.exists():
            raise ValueError(f"content.md를 찾을 수 없습니다.")
        return p.read_text("utf-8")

    def save_content(self, name: str, content: str, version: str = "v1.0"):
        with self._lock_for(name):
            p = self._version_dir(name, version) / "content.md"
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(content, "utf-8")
            meta = self._load_meta(name, version)
            if meta:
                meta["updated"] = self._now_iso()
                self._save_meta(name, meta, version)

    def _backup_dir(self, name: str, version: str = "v1.0") -> Path:
        d = self._version_dir(name, version) / ".backups"
        d.mkdir(parents=True, exist_ok=True)
        return d

    def save_slide_html(self, name: str, filename: str, html: str, version: str = "v1.0"):
        filename = _validate_filename(filename)
        with self._lock_for(name):
            html_dir = self._version_dir(name, version) / "html"
            html_dir.mkdir(parents=True, exist_ok=True)
            target = html_dir / filename
            backup_path = self._backup_dir(name, version) / filename
            if target.exists() and not backup_path.exists():
                # Snapshot only the very first time this slide is ever
                # overwritten (presumably its as-generated original) — NOT
                # on every save. A backup that gets replaced by every save
                # only ever lets "되돌리기" undo the single most recent
                # save, silently baking in every earlier WYSIWYG edit that
                # happened to get saved along the way (e.g. font-size
                # reverting but an earlier color/bold change not, depending
                # purely on save order) instead of reverting to the true
                # original. Stored in a sibling .backups/ dir — NOT html/,
                # so build.js's own slide*.html glob (also used by
                # list_slides()) can never pick a backup up as a real slide.
                backup_path.write_text(target.read_text("utf-8"), "utf-8")
            target.write_text(html, "utf-8")
            self._sync_content_md_slide(name, filename, html, version)
            meta = self._load_meta(name, version)
            if meta:
                meta["updated"] = self._now_iso()
                meta["slides"] = len(list(html_dir.glob("slide*.html")))
                self._save_meta(name, meta, version)

    _TAG_RE = re.compile(r'<[^>]+>')

    def _extract_slide_summary(self, html: str) -> tuple[str, list[str]]:
        """Rough text extraction from a slide's HTML for content.md sync —
        not a real HTML parser, just enough to keep the outline readable."""
        title_m = re.search(r'<h[1-3][^>]*>(.*?)</h[1-3]>', html, re.DOTALL | re.IGNORECASE)
        title = self._TAG_RE.sub('', title_m.group(1)).strip() if title_m else "제목 없음"
        bullets = []
        for tag in ('p', 'li'):
            for m in re.finditer(rf'<{tag}[^>]*>(.*?)</{tag}>', html, re.DOTALL | re.IGNORECASE):
                text = self._TAG_RE.sub('', m.group(1)).strip()
                if text and text != title and text not in bullets:
                    bullets.append(text)
        return title or "제목 없음", bullets[:6]

    def _sync_content_md_slide(self, name: str, filename: str, html: str, version: str = "v1.0"):
        """A slide added via "새 슬라이드" starts as a blank template with no
        content.md entry at all. Once the user fills it in and saves, add a
        matching "## Slide N:" section so content.md doesn't silently miss
        it. Only ever ADDS a missing section — never overwrites one that
        already exists, since AI-generated slides already have a much
        richer content.md entry than this regex-based extraction could
        reproduce, and every save (including ones during AI generation
        itself) goes through this same path."""
        m = re.match(r'slide(\d+)-', filename)
        if not m:
            return
        slide_num = int(m.group(1))
        content_path = self._version_dir(name, version) / "content.md"
        if not content_path.exists():
            return
        content = content_path.read_text("utf-8")
        if re.search(rf'^##\s*Slide\s+{slide_num}:', content, re.MULTILINE):
            return  # already has an entry (AI-generated or previously synced) — leave it alone

        title, bullets = self._extract_slide_summary(html)
        bullet_block = "\n".join(f"- {b}" for b in bullets) if bullets else "- (내용 없음)"
        new_section = f"## Slide {slide_num}: {title}\n{bullet_block}\n"
        content_path.write_text(content.rstrip("\n") + "\n\n" + new_section, "utf-8")

    def get_slide_html(self, name: str, filename: str, version: str = "v1.0") -> str:
        p = self._version_dir(name, version) / "html" / _validate_filename(filename)
        if not p.exists():
            raise ValueError(f"슬라이드 '{filename}'을 찾을 수 없습니다.")
        return p.read_text("utf-8")

    def has_slide_backup(self, name: str, filename: str, version: str = "v1.0") -> bool:
        return (self._backup_dir(name, version) / _validate_filename(filename)).exists()

    def restore_slide_backup(self, name: str, filename: str, version: str = "v1.0") -> str:
        backup_path = self._backup_dir(name, version) / _validate_filename(filename)
        if not backup_path.exists():
            raise ValueError("되돌릴 이전 버전이 없습니다.")
        html = backup_path.read_text("utf-8")
        self.save_slide_html(name, filename, html, version)  # snapshots current (bad) state, restores the good one
        return html

    def list_slides(self, name: str, version: str = "v1.0") -> list[str]:
        html_dir = self._version_dir(name, version) / "html"
        if not html_dir.exists():
            return []
        return sorted([f.name for f in html_dir.glob("slide*.html")])

    def delete_slide(self, name: str, filename: str, version: str = "v1.0"):
        filename = _validate_filename(filename)
        with self._lock_for(name):
            html_dir = self._version_dir(name, version) / "html"
            p = html_dir / filename
            if not p.exists():
                raise ValueError(f"슬라이드 '{filename}'을 찾을 수 없습니다.")
            p.unlink()
            meta = self._load_meta(name, version)
            if meta:
                meta["updated"] = self._now_iso()
                meta["slides"] = len(list(html_dir.glob("slide*.html")))
                self._save_meta(name, meta, version)

    def add_blank_slide(self, name: str, version: str = "v1.0") -> str:
        with self._lock_for(name):
            html_dir = self._version_dir(name, version) / "html"
            html_dir.mkdir(parents=True, exist_ok=True)
            nums = [int(m.group(1)) for f in html_dir.glob("slide*.html") if (m := re.match(r'slide(\d+)', f.name))]
            next_num = (max(nums) + 1) if nums else 1
            filename = f"slide{next_num:02d}-new.html"
            meta = self._load_meta(name, version)
            deck_title = meta.get("title", name) if meta else name
            total = len(list(html_dir.glob("slide*.html"))) + 1
            (html_dir / filename).write_text(_blank_slide_html(deck_title, next_num, total), "utf-8")
            if meta:
                meta["updated"] = self._now_iso()
                meta["slides"] = len(list(html_dir.glob("slide*.html")))
                self._save_meta(name, meta, version)
            return filename

    def reorder_slides(self, name: str, order: list[str], version: str = "v1.0") -> list[str]:
        order = [_validate_filename(f) for f in order]
        with self._lock_for(name):
            html_dir = self._version_dir(name, version) / "html"
            existing = {f.name for f in html_dir.glob("slide*.html")}
            if set(order) != existing:
                raise ValueError("전달된 슬라이드 목록이 현재 슬라이드 목록과 일치하지 않습니다.")

            # Two-pass rename so renumbering never overwrites a file that
            # hasn't been moved out of the way yet.
            temp_pairs = []
            for i, old_name in enumerate(order):
                tmp = html_dir / f".reorder-tmp-{i}.html"
                (html_dir / old_name).rename(tmp)
                temp_pairs.append((tmp, old_name))

            new_order = []
            for i, (tmp, old_name) in enumerate(temp_pairs):
                m = re.match(r'slide\d+-(.+)\.html$', old_name)
                slug = m.group(1) if m else "slide"
                new_name = f"slide{i + 1:02d}-{slug}.html"
                tmp.rename(html_dir / new_name)
                new_order.append(new_name)

            meta = self._load_meta(name, version)
            if meta:
                meta["updated"] = self._now_iso()
                self._save_meta(name, meta, version)
            return new_order

    def save_asset(self, name: str, filename: str, data: bytes, version: str = "v1.0") -> str:
        safe_name = _sanitize_asset_filename(filename)
        assets_dir = self._version_dir(name, version) / "assets"
        assets_dir.mkdir(parents=True, exist_ok=True)
        target = assets_dir / safe_name
        if target.exists():
            # Different uploads can sanitize to the same name (e.g. two
            # "스크린샷....png" screenshots) — don't silently clobber the
            # earlier one.
            stem, ext = os.path.splitext(safe_name)
            safe_name = f"{stem}-{int(datetime.now().timestamp() * 1000)}{ext}"
            target = assets_dir / safe_name
        target.write_bytes(data)
        return safe_name

    def list_assets(self, name: str, version: str = "v1.0") -> list[dict]:
        assets_dir = self._version_dir(name, version) / "assets"
        if not assets_dir.exists():
            return []
        items = []
        for f in sorted(assets_dir.iterdir()):
            if f.is_file():
                stat = f.stat()
                items.append({
                    "name": f.name,
                    "size": stat.st_size,
                    "modified": datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat(),
                })
        return items

    def rename_asset(self, name: str, old_filename: str, new_filename: str, version: str = "v1.0") -> str:
        assets_dir = self._version_dir(name, version) / "assets"
        old_path = assets_dir / _validate_asset_filename(old_filename)
        if not old_path.exists():
            raise ValueError(f"자산을 찾을 수 없습니다: {old_filename}")
        new_safe = _sanitize_asset_filename(new_filename)
        if not os.path.splitext(new_safe)[1]:
            new_safe += os.path.splitext(old_filename)[1]
        new_path = assets_dir / new_safe
        if new_path != old_path and new_path.exists():
            raise ValueError(f"이미 존재하는 파일명입니다: {new_safe}")
        old_path.rename(new_path)
        return new_safe

    def delete_asset(self, name: str, filename: str, version: str = "v1.0") -> None:
        path = self._version_dir(name, version) / "assets" / _validate_asset_filename(filename)
        if path.exists():
            path.unlink()

    def build_pptx(self, name: str, version: str = "v1.0") -> str:
        _validate_name(name)
        _validate_version(version)
        with self._lock_for(name):
            meta = self._load_meta(name, version)
            if meta:
                meta["status"] = "building"
                self._save_meta(name, meta, version)
        try:
            result = subprocess.run(
                ["node", str(self.engine_dir / "scripts" / "build.js"), name, version],
                cwd=str(self.engine_dir),
                capture_output=True, text=True, timeout=120
            )
            output = f"{result.stdout or ''}\n{result.stderr or ''}"
            pptx_path = self._version_dir(name, version) / "slides.pptx"

            if result.returncode != 0 or not pptx_path.exists():
                if meta:
                    meta["status"] = "failed"
                    meta.pop("build_warning", None)
                    self._save_meta(name, meta, version)
                raise RuntimeError(f"빌드 실패: {result.stderr or result.stdout}")

            # build.js swallows per-slide conversion errors and always exits 0,
            # so a "successful" run can still produce a PPTX with zero slides —
            # parse its own summary line to catch that instead of trusting returncode.
            m = re.search(r"Build complete: (\d+) success, (\d+) errors", output)
            success_count = int(m.group(1)) if m else None
            error_count = int(m.group(2)) if m else 0

            if success_count == 0:
                if meta:
                    meta["status"] = "failed"
                    self._save_meta(name, meta, version)
                raise RuntimeError(f"빌드 실패: 모든 슬라이드가 PPTX 변환 규칙을 위반해 누락되었습니다.\n{output.strip()[-3000:]}")

            if meta:
                meta["status"] = "completed"
                meta["updated"] = self._now_iso()
                if error_count:
                    meta["build_warning"] = (
                        f"{error_count}개 슬라이드가 PPTX 변환에 실패해 누락되었습니다 "
                        f"(성공 {success_count} / 실패 {error_count}). HTML 편집기에서 텍스트가 "
                        f"<p>/<h1>~<h6>/<ul>/<ol> 태그로 감싸져 있는지, 텍스트 태그에 배경·테두리가 "
                        f"적용되어 있지 않은지 확인하세요."
                    )
                else:
                    meta.pop("build_warning", None)
                self._save_meta(name, meta, version)
            return str(pptx_path)
        except subprocess.TimeoutExpired:
            if meta:
                meta["status"] = "failed"
                self._save_meta(name, meta, version)
            raise RuntimeError("빌드 타임아웃 (120초)")

    def get_pptx_path(self, name: str, version: str = "v1.0") -> str | None:
        p = self._version_dir(name, version) / "slides.pptx"
        return str(p) if p.exists() else None

    def export_pdf(self, name: str, version: str = "v1.0") -> str:
        _validate_name(name)
        _validate_version(version)
        html_dir = self._version_dir(name, version) / "html"
        if not html_dir.exists():
            raise ValueError(f"프로젝트 '{name}'을 찾을 수 없습니다.")

        with tempfile.TemporaryDirectory() as tmp:
            result = subprocess.run(
                ["node", str(self.engine_dir / "scripts" / "export-slides-png.js"), name, version, tmp],
                cwd=str(self.engine_dir),
                capture_output=True, text=True, timeout=180,
            )
            png_files = sorted(Path(tmp).glob("*.png"))
            if result.returncode != 0 or not png_files:
                raise RuntimeError(f"PDF 생성 실패: {result.stderr or result.stdout}")

            from PIL import Image
            images = [Image.open(p).convert("RGB") for p in png_files]
            pdf_path = self._version_dir(name, version) / "slides.pdf"
            images[0].save(pdf_path, save_all=True, append_images=images[1:])
        return str(pdf_path)

    def get_pdf_path(self, name: str, version: str = "v1.0") -> str | None:
        p = self._version_dir(name, version) / "slides.pdf"
        return str(p) if p.exists() else None

    def _file_to_data_uri(self, path: Path) -> str:
        mime = mimetypes.guess_type(str(path))[0] or "application/octet-stream"
        data = base64.b64encode(path.read_bytes()).decode("ascii")
        return f"data:{mime};base64,{data}"

    def _inline_slide_assets(self, html: str, assets_dir: Path) -> str:
        def repl_redhat(m):
            attr, rel = m.group(1), m.group(2)
            p = self.engine_dir / "redhat" / rel
            return f'{attr}="{self._file_to_data_uri(p)}"' if p.exists() else m.group(0)

        def repl_asset(m):
            p = assets_dir / m.group(1)
            return f'src="{self._file_to_data_uri(p)}"' if p.exists() else m.group(0)

        def repl_redhat_url(m):
            p = self.engine_dir / "redhat" / m.group(1)
            return f"url('{self._file_to_data_uri(p)}')" if p.exists() else m.group(0)

        def repl_asset_url(m):
            p = assets_dir / m.group(1)
            return f"url('{self._file_to_data_uri(p)}')" if p.exists() else m.group(0)

        html = REDHAT_REL_RE.sub(repl_redhat, html)
        html = ASSET_REL_RE.sub(repl_asset, html)
        # Also catch background-image: url('assets/...') / url('../../../../redhat/...')
        # inside a slide's own <style> block, not just href/src attributes.
        html = REDHAT_URL_RE.sub(repl_redhat_url, html)
        html = ASSET_URL_RE.sub(repl_asset_url, html)
        return html

    def export_html(self, name: str, version: str = "v1.0") -> str:
        html_dir = self._version_dir(name, version) / "html"
        assets_dir = self._version_dir(name, version) / "assets"
        if not html_dir.exists():
            raise ValueError(f"프로젝트 '{name}'을 찾을 수 없습니다.")
        files = sorted(html_dir.glob("slide*.html"))
        if not files:
            raise ValueError("슬라이드가 없습니다.")

        slide_htmls = [self._inline_slide_assets(f.read_text("utf-8"), assets_dir) for f in files]
        meta = self._load_meta(name, version) or {}
        return self._build_standalone_player(slide_htmls, meta.get("title", name))

    def _build_standalone_player(self, slide_htmls: list[str], title: str) -> str:
        slides_json = json.dumps(slide_htmls)
        title_html = title.replace("<", "&lt;").replace(">", "&gt;")
        return f"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<title>{title_html}</title>
<style>
  html, body {{ margin:0; padding:0; height:100%; background:#151515; overflow:hidden; }}
  #stage {{ position:fixed; inset:0; display:flex; align-items:center; justify-content:center; }}
  #frame {{ width:960px; height:540px; border:none; background:#fff; box-shadow:0 8px 40px rgba(0,0,0,.5); }}
  #counter {{ position:fixed; bottom:16px; right:20px; color:#9aa0a6; font:12px -apple-system,sans-serif; z-index:10; }}
  .zone {{ position:fixed; top:0; bottom:0; width:20%; cursor:pointer; z-index:5; }}
  #zone-prev {{ left:0; }}
  #zone-next {{ right:0; }}
</style>
</head>
<body>
<div id="stage"><iframe id="frame" scrolling="no"></iframe></div>
<div class="zone" id="zone-prev"></div>
<div class="zone" id="zone-next"></div>
<div id="counter"></div>
<script>
const SLIDES = {slides_json};
let idx = 0;
const frame = document.getElementById('frame');
const counter = document.getElementById('counter');
function render() {{
  frame.srcdoc = SLIDES[idx];
  counter.textContent = (idx + 1) + ' / ' + SLIDES.length;
  fit();
}}
function fit() {{
  const scale = Math.min(window.innerWidth / 960, window.innerHeight / 540) * 0.92;
  frame.style.transform = 'scale(' + scale + ')';
}}
function go(delta) {{
  idx = Math.max(0, Math.min(SLIDES.length - 1, idx + delta));
  render();
}}
document.getElementById('zone-prev').onclick = () => go(-1);
document.getElementById('zone-next').onclick = () => go(1);
window.addEventListener('keydown', (e) => {{
  if (e.key === 'ArrowRight' || e.key === ' ') go(1);
  else if (e.key === 'ArrowLeft') go(-1);
  else if (e.key === 'Home') {{ idx = 0; render(); }}
  else if (e.key === 'End') {{ idx = SLIDES.length - 1; render(); }}
}});
window.addEventListener('resize', fit);
render();
</script>
</body>
</html>"""

    def get_asset_path(self, name: str, filename: str, version: str = "v1.0") -> str | None:
        p = self._version_dir(name, version) / "assets" / _validate_asset_filename(filename)
        return str(p) if p.exists() else None

    # Not selectable visual themes: shared typography rules inherited by every
    # redhat-* theme, and an unrelated Web UI design spec that happens to live
    # in the same folder — both say so explicitly in their own doc bodies.
    NON_THEME_DOCS = {"korean-typography", "visual-language"}

    def list_themes(self) -> list[dict]:
        themes_dir = self.engine_dir / "themes"
        results = []
        if not themes_dir.exists():
            return results
        for f in sorted(themes_dir.glob("*.md")):
            name = f.stem
            if name in self.NON_THEME_DOCS:
                continue
            text = f.read_text("utf-8")
            m = re.search(r'^#\s+(?:Theme:\s*)?(.+)', text, re.MULTILINE)
            label = m.group(1).strip() if m else name
            results.append({"id": name, "name": label})
        return results
