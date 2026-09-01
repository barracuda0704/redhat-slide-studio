import re
import json
import os
import base64
import mimetypes
import shutil
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path

REDHAT_REL_RE = re.compile(r'(href|src)="\.\./\.\./\.\./\.\./redhat/([^"]+)"')
ASSET_REL_RE = re.compile(r'src="assets/([^"]+)"')


class ProjectManager:
    def __init__(self, engine_dir: str):
        self.engine_dir = Path(engine_dir)
        self.projects_dir = self.engine_dir / "projects"
        self.projects_dir.mkdir(parents=True, exist_ok=True)

    def _meta_path(self, name: str, version: str = "v1.0") -> Path:
        return self.projects_dir / name / version / "project.json"

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
        slug = name.strip().lower().replace(" ", "-")
        version_dir = self.projects_dir / slug / "v1.0"
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
            meta = self._load_meta(d.name)
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
        html_dir = self.projects_dir / name / version / "html"
        slides = sorted([f.name for f in html_dir.glob("slide*.html")]) if html_dir.exists() else []
        has_pptx = (self.projects_dir / name / version / "slides.pptx").exists()
        return {**meta, "name": name, "version": version, "slides": slides, "has_pptx": has_pptx}

    def delete_project(self, name: str) -> bool:
        project_dir = self.projects_dir / name
        if not project_dir.exists():
            raise ValueError(f"프로젝트 '{name}'을 찾을 수 없습니다.")
        shutil.rmtree(project_dir)
        return True

    def get_content(self, name: str, version: str = "v1.0") -> str:
        p = self.projects_dir / name / version / "content.md"
        if not p.exists():
            raise ValueError(f"content.md를 찾을 수 없습니다.")
        return p.read_text("utf-8")

    def save_content(self, name: str, content: str, version: str = "v1.0"):
        p = self.projects_dir / name / version / "content.md"
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, "utf-8")
        meta = self._load_meta(name, version)
        if meta:
            meta["updated"] = self._now_iso()
            self._save_meta(name, meta, version)

    def save_slide_html(self, name: str, filename: str, html: str, version: str = "v1.0"):
        html_dir = self.projects_dir / name / version / "html"
        html_dir.mkdir(parents=True, exist_ok=True)
        (html_dir / filename).write_text(html, "utf-8")
        meta = self._load_meta(name, version)
        if meta:
            meta["updated"] = self._now_iso()
            meta["slides"] = len(list(html_dir.glob("slide*.html")))
            self._save_meta(name, meta, version)

    def get_slide_html(self, name: str, filename: str, version: str = "v1.0") -> str:
        p = self.projects_dir / name / version / "html" / filename
        if not p.exists():
            raise ValueError(f"슬라이드 '{filename}'을 찾을 수 없습니다.")
        return p.read_text("utf-8")

    def list_slides(self, name: str, version: str = "v1.0") -> list[str]:
        html_dir = self.projects_dir / name / version / "html"
        if not html_dir.exists():
            return []
        return sorted([f.name for f in html_dir.glob("slide*.html")])

    def build_pptx(self, name: str, version: str = "v1.0") -> str:
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
            pptx_path = self.projects_dir / name / version / "slides.pptx"

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
        p = self.projects_dir / name / version / "slides.pptx"
        return str(p) if p.exists() else None

    def export_pdf(self, name: str, version: str = "v1.0") -> str:
        html_dir = self.projects_dir / name / version / "html"
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
            pdf_path = self.projects_dir / name / version / "slides.pdf"
            images[0].save(pdf_path, save_all=True, append_images=images[1:])
        return str(pdf_path)

    def get_pdf_path(self, name: str, version: str = "v1.0") -> str | None:
        p = self.projects_dir / name / version / "slides.pdf"
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

        html = REDHAT_REL_RE.sub(repl_redhat, html)
        html = ASSET_REL_RE.sub(repl_asset, html)
        return html

    def export_html(self, name: str, version: str = "v1.0") -> str:
        html_dir = self.projects_dir / name / version / "html"
        assets_dir = self.projects_dir / name / version / "assets"
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
        p = self.projects_dir / name / version / "assets" / filename
        return str(p) if p.exists() else None

    def list_themes(self) -> list[dict]:
        themes_dir = self.engine_dir / "themes"
        results = []
        if not themes_dir.exists():
            return results
        for f in sorted(themes_dir.glob("*.md")):
            name = f.stem
            text = f.read_text("utf-8")
            m = re.search(r'^#\s+(?:Theme:\s*)?(.+)', text, re.MULTILINE)
            label = m.group(1).strip() if m else name
            results.append({"id": name, "name": label})
        return results
