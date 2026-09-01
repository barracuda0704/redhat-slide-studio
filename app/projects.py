import re
import json
import os
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path


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
            pptx_path = self.projects_dir / name / version / "slides.pptx"
            if result.returncode != 0 or not pptx_path.exists():
                if meta:
                    meta["status"] = "failed"
                    self._save_meta(name, meta, version)
                raise RuntimeError(f"빌드 실패: {result.stderr or result.stdout}")
            if meta:
                meta["status"] = "completed"
                meta["updated"] = self._now_iso()
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
