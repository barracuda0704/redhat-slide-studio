import json
import re
from pathlib import Path

from .config import settings


def _get_client():
    if settings.USE_VERTEX:
        from anthropic import AnthropicVertex
        return AnthropicVertex(project_id=settings.VERTEX_PROJECT_ID, region=settings.VERTEX_REGION)
    else:
        from anthropic import Anthropic
        return Anthropic(api_key=settings.ANTHROPIC_API_KEY)


def _load_theme_css(engine_dir: str) -> str:
    p = Path(engine_dir) / "redhat" / "theme.css"
    return p.read_text("utf-8") if p.exists() else ""


def _load_icon_list(engine_dir: str) -> str:
    icons_dir = Path(engine_dir) / "redhat" / "icons" / "official"
    if not icons_dir.exists():
        return ""
    icons = sorted([f.stem for f in icons_dir.glob("*.png") if not f.stem.endswith("-dark-theme")])
    return ", ".join(icons)


def _load_theme_guide(engine_dir: str, theme_id: str) -> str:
    p = Path(engine_dir) / "themes" / f"{theme_id}.md"
    return p.read_text("utf-8") if p.exists() else ""


CONTENT_SYSTEM = """당신은 Red Hat 기술 슬라이드 전문가입니다. 주어진 주제에 대해 슬라이드 콘텐츠(content.md)를 작성합니다.

작성 규칙:
- 한국어로 작성
- 각 슬라이드는 `## Slide N: 제목` 형식
- 슬라이드 1은 항상 타이틀 슬라이드
- 마지막 슬라이드는 CTA(Call to Action) 또는 Q&A
- 각 슬라이드에 핵심 메시지와 설명 포함
- 선택적으로 `**📝 Notes:**` 블록으로 발표자 노트 추가
- 슬라이드당 핵심 메시지는 하나만

출력 형식:
# [슬라이드 제목]

## Slide 1: [타이틀]
- [내용]

## Slide 2: [제목]
- [핵심 메시지]
- [세부 내용]

**📝 Notes:**
- [발표자 노트]

... (반복)
"""


def _build_slide_system(theme_css: str, icon_list: str, theme_guide: str) -> str:
    return f"""당신은 Red Hat 슬라이드 HTML 작성 전문가입니다.

## 캔버스 규격 (필수)
- 크기: 720pt × 405pt (16:9)
- 외부 패딩: body {{ padding: 25pt 35pt 45pt 35pt; }}
- 폰트: Noto Sans KR
- 배경: 단색만 허용 (그라디언트, 사진 배경 금지)
- word-break: keep-all (한글 텍스트)

## 기본 theme.css
```css
{theme_css}
```

## 사용 가능한 아이콘 (경로: ../../../../redhat/icons/official/<name>.png)
{icon_list}

## 테마 가이드
{theme_guide}

## HTML 슬라이드 작성 규칙
1. 각 슬라이드는 독립적인 완전한 HTML 문서
2. theme.css를 `<link rel="stylesheet" href="../../../../redhat/theme.css">`로 참조
3. 슬라이드별 스타일은 `<style>` 태그에 인라인으로 작성
4. 아이콘 사용 시 `<img>` 태그로 공식 아이콘 참조
5. 한글 텍스트에 `word-break: keep-all` 필수
6. 레이아웃은 CSS Grid 또는 Flexbox 사용
7. 절대 위치(absolute positioning) 최소화
8. 타이틀 슬라이드: 큰 제목 + 부제 + 로고/장식
9. 콘텐츠 슬라이드: 카드 그리드, 리스트, 스택 등 다양한 레이아웃
10. 각 카드/항목에 아이콘을 적극 활용

## PPTX 변환 필수 규칙 (위반하면 해당 슬라이드가 PPTX 빌드에서 통째로 누락됩니다)
이 HTML은 headless 브라우저로 렌더링된 후 DOM을 분석해 PPTX 도형/텍스트박스로 변환됩니다.
아래 두 규칙을 슬라이드 전체에서 예외 없이 지키세요.

1. **모든 글자는 반드시 `<p>`, `<h1>~<h6>`, `<ul>`, `<ol>` 태그 안에만 있어야 합니다.**
   `<div>`, `<span>` 바로 밑에 텍스트를 직접 두면 안 됩니다 (뱃지, 라벨, 숫자, 코드 한 줄짜리도 예외 없음).
   - 잘못된 예: `<div class="badge">NEW</div>`, `<div class="stat-num">44.8%</div>`
   - 올바른 예: `<div class="badge"><p>NEW</p></div>`, `<div class="stat-num"><p>44.8%</p></div>`
2. **`<h1>`, `<h2>`, `<h3>`, `<h4>`, `<h5>`, `<h6>`, `<p>`, `<ul>`, `<ol>`, `<li>` 태그 자체에는 background, border, box-shadow 스타일을 어떤 경우에도 직접 적용하지 마세요.**
   제목 밑에 빨간 밑줄 같은 강조선을 넣고 싶을 때도 예외 없이 감싸는 `<div>`에 border를 적용하세요.
   - 잘못된 예: `<h1 style="border-bottom:2pt solid red;">제목</h1>`, `<h2 class="underline">제목</h2>` (underline 클래스가 border-bottom을 h2에 직접 줌)
   - 올바른 예: `<div style="border-bottom:2pt solid red; padding-bottom:6pt;"><h2>제목</h2></div>`
3. `<div>`에 `background-image`나 `linear-gradient`/`radial-gradient`를 쓰지 마세요 (단색 `background-color`만 가능). 이미지는 `<img>` 태그로 배치하세요.

## 출력 형식
각 슬라이드를 다음 형식으로 출력하세요:

### slide01-title
```html
<!DOCTYPE html>
<html lang="ko">
... (완전한 HTML)
</html>
```

### slide02-agenda
```html
... (완전한 HTML)
```
"""


def generate_content(topic: str, num_slides: int = 8, description: str = "") -> str:
    client = _get_client()
    user_msg = f"주제: {topic}\n슬라이드 수: {num_slides}장"
    if description:
        user_msg += f"\n추가 설명: {description}"

    response = client.messages.create(
        model=settings.MODEL_NAME,
        max_tokens=settings.MAX_OUTPUT_TOKENS,
        system=CONTENT_SYSTEM,
        messages=[{"role": "user", "content": user_msg}],
    )
    return response.content[0].text


def generate_slides_html(content_md: str, theme: str = "redhat-enterprise") -> list[dict]:
    engine_dir = settings.ENGINE_DIR
    theme_css = _load_theme_css(engine_dir)
    icon_list = _load_icon_list(engine_dir)
    theme_guide = _load_theme_guide(engine_dir, theme)

    client = _get_client()
    system = _build_slide_system(theme_css, icon_list, theme_guide)

    response = client.messages.create(
        model=settings.MODEL_NAME,
        max_tokens=settings.MAX_OUTPUT_TOKENS,
        system=system,
        messages=[{"role": "user", "content": f"다음 content.md를 기반으로 각 슬라이드의 HTML을 작성하세요:\n\n{content_md}"}],
    )
    text = response.content[0].text
    return _parse_slides(text)


def _parse_slides(text: str) -> list[dict]:
    pattern = r'###\s+(slide\d+-[a-z0-9-]+)\s*\n```html\s*\n(.*?)```'
    matches = re.findall(pattern, text, re.DOTALL)
    results = []
    for filename, html in matches:
        html = html.strip()
        if not filename.endswith(".html"):
            filename += ".html"
        results.append({"filename": filename, "html": html})

    if not results:
        # ponytail: fallback — try splitting by ```html blocks without headers
        html_blocks = re.findall(r'```html\s*\n(.*?)```', text, re.DOTALL)
        for i, html in enumerate(html_blocks, 1):
            num = str(i).zfill(2)
            results.append({"filename": f"slide{num}-section.html", "html": html.strip()})
    return results
