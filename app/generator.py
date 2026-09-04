import json
import re
import shutil
import subprocess
import tempfile
import time
from datetime import datetime
from pathlib import Path

from .config import settings


def _today_kr() -> str:
    return datetime.now().strftime("%Y년 %m월 %d일")


def _get_client():
    if settings.USE_VERTEX:
        from anthropic import AnthropicVertex
        return AnthropicVertex(project_id=settings.VERTEX_PROJECT_ID, region=settings.VERTEX_REGION)
    else:
        from anthropic import Anthropic
        return Anthropic(api_key=settings.ANTHROPIC_API_KEY)


def _create_message(client, **kwargs):
    # The SDK requires streaming once max_tokens is high enough that a
    # response could plausibly take >10 minutes — true for our
    # MAX_OUTPUT_TOKENS. Stream and collect the final message so callers
    # keep using response.content[0].text / response.stop_reason as before.
    with client.messages.stream(**kwargs) as stream:
        return stream.get_final_message()


def _is_retriable(detail: str) -> bool:
    return "resource_exhausted" in detail or "RetriableError" in detail


def _run_cursor_agent(model: str, instruction: str, cwd: str, output_path: Path, attempts: int) -> str | None:
    """Runs cursor-agent up to `attempts` times against one model. Returns
    None on success (output_path now holds the image), or the last failure
    detail string if every attempt failed."""
    last_detail = "no output"
    for attempt in range(attempts):
        if output_path.exists():
            output_path.unlink()
        result = subprocess.run(
            ["cursor-agent", "-p", "--force", "--model", model, "--output-format", "json", instruction],
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=settings.CURSOR_AGENT_TIMEOUT_SECONDS,
        )
        if output_path.exists():
            return None
        last_detail = (result.stdout.strip() or result.stderr.strip() or "no output")[:500]
        # Logged unconditionally (not just on final failure) so a real
        # occurrence — unlike ad-hoc reproduction attempts afterward, which
        # can easily land in a different, already-recovered window — is
        # actually diagnosable from logs/web.log instead of just showing up
        # to the user as an opaque 502.
        print(f"[generate_image] model={model} attempt={attempt + 1}/{attempts} failed: {last_detail}")
        if not _is_retriable(last_detail):
            break
        if attempt < attempts - 1:
            # A brief pause gives a transient resource_exhausted window an
            # actual chance to clear instead of hammering the same
            # overloaded endpoint again immediately.
            time.sleep(5)
    return last_detail


def generate_image(prompt: str, aspect_ratio: str = "16:9") -> bytes:
    """Generate a single image via the locally-installed `cursor-agent` CLI's
    native cursor.GenerateImage tool and return its raw bytes.

    Every Vertex AI image model (Gemini and Imagen) is blocked on this GCP
    project by the org's constraints/vertexai.allowedModels policy, so this
    shells out to Cursor's CLI instead — which only works because the app
    now runs natively on a machine with a logged-in cursor-agent session
    (its auth lives in the macOS Keychain, so it can't be mounted into a
    Docker container the way the Vertex ADC credentials are)."""
    tmpdir = tempfile.mkdtemp(prefix="cursor-imagegen-")
    try:
        output_path = Path(tmpdir) / "output.png"
        instruction = (
            "Do not ask for confirmation. Immediately call your native image "
            "generation tool right now to generate an image matching this "
            f"description: {prompt}\n"
            f"Use a {aspect_ratio} aspect ratio if the tool supports it. "
            f"Save the resulting image as a PNG file at exactly this absolute "
            f"path: {output_path}"
        )
        # Cursor's backend has shown both brief, retriable connection drops
        # and sustained resource_exhausted stretches on specific (usually
        # heavier-demand) models — retry the requested model a couple of
        # times, then fall back to a model that's held up reliably rather
        # than failing the whole request.
        detail = _run_cursor_agent(settings.CURSOR_AGENT_MODEL, instruction, tmpdir, output_path, attempts=2)
        if detail is None:
            return output_path.read_bytes()
        if _is_retriable(detail) and settings.CURSOR_AGENT_FALLBACK_MODEL != settings.CURSOR_AGENT_MODEL:
            detail = _run_cursor_agent(settings.CURSOR_AGENT_FALLBACK_MODEL, instruction, tmpdir, output_path, attempts=2)
            if detail is None:
                return output_path.read_bytes()
        raise RuntimeError(f"이미지 생성 결과 파일을 찾지 못했습니다: {detail}")
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


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


def _content_system(current_date: str) -> str:
    return f"""당신은 Red Hat 기술 슬라이드 전문가입니다. 주어진 주제에 대해 슬라이드 콘텐츠(content.md)를 작성합니다.

오늘 날짜는 {current_date}입니다. "현재", "올해", "최신 동향" 등은 이 날짜 기준으로 작성하세요.
사용자가 주제/설명에서 특정 연도를 명시했다면 반드시 그 연도를 그대로 사용하세요.
통계나 사례를 인용할 때 원 자료에 실제로 명시된 연도(예: "2024년 보고서")는 바꾸지 말고 그대로 유지하세요.

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

오늘 날짜는 {_today_kr()}입니다. content.md에 이미 적힌 연도·통계 인용은 그대로 유지하고, 새로
연도를 표기해야 할 경우("현재", "최신" 등)에는 이 날짜를 기준으로 하세요.

## 캔버스 규격 (필수)
- 크기: 720pt × 405pt (16:9)
- 외부 패딩: body {{ padding: 25pt 35pt 45pt 35pt; }}
- **실제 콘텐츠에 쓸 수 있는 세로 공간은 335pt(405 - 25 - 45)뿐입니다.** 표/카드가 많거나
  "여백 없이 꽉 채워달라"는 요청이어도, 각 요소의 margin/padding/line-height을 합산해 이
  335pt를 절대 넘기지 마세요. 정확히 채우려다 1~2pt만 넘어도 해당 슬라이드는 PPTX 빌드에서
  통째로 누락됩니다. 표가 3개 이상이거나 행이 많으면 셀 padding·행간·섹션 간 margin을 미리
  줄여서 5~10pt 정도 안전 여백을 남기세요.
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
4. **글자·표·라벨을 이미지로 대체하지 마세요.** 단계/기간/절차표, 검정 배경 위 라벨, 강조를 위한
   붉은 글씨 등 텍스트로 표현 가능한 내용은 예외 없이 실제 `<p>`/`<h1>~<h6>`/`<ul>`/`<li>` +
   감싸는 `<div>`의 background-color로 구현하세요 (`<img>` 태그로 텍스트 내용을 대신하면 나중에
   글자를 수정할 방법이 없어집니다 — 사용자가 직접 편집할 수 있어야 하는 모든 콘텐츠는 실제
   텍스트여야 합니다). `<img>`는 공식 아이콘·사진처럼 정말 텍스트가 아닌 그래픽에만 사용하세요.
   - 한 줄 안에서 색상/굵기가 섞여야 할 때(예: "일반 검정 글씨 + 강조용 붉은 글씨", "일반 + 굵게")도
     이미지로 만들지 말고, 같은 `<p>` 안에 여러 개의 `<span>`을 넣어 각각 다르게 스타일링하세요.
   - 잘못된 예: `<img src="assets/table.png" alt="단계별 지원 내용 표">`
   - 올바른 예 (표/카드형 레이아웃): `<div class="stage-row"><div class="stage-cell"><p>1단계</p></div><div class="stage-cell"><p>3개월</p></div></div>`
   - 올바른 예 (한 줄 안 색상 혼합): `<p>일반 텍스트 <span style="color:#ee0000; font-weight:700;">강조 텍스트</span></p>`

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

    response = _create_message(client,
        model=settings.MODEL_NAME,
        max_tokens=settings.MAX_OUTPUT_TOKENS,
        system=_content_system(_today_kr()),
        messages=[{"role": "user", "content": user_msg}],
    )
    if response.stop_reason == "max_tokens":
        raise RuntimeError(
            f"content.md 생성이 출력 길이 제한({settings.MAX_OUTPUT_TOKENS} 토큰)에 걸려 중간에 잘렸습니다. "
            f"슬라이드 수를 줄이거나 다시 시도하세요."
        )
    return response.content[0].text


def _split_content_by_slide(content_md: str) -> tuple[str, list[str]]:
    """Split content.md into (preamble, [per-slide chunk, ...]) on '## Slide N:' boundaries."""
    parts = re.split(r'(?=^##\s*Slide\s+\d+:)', content_md, flags=re.MULTILINE)
    preamble = parts[0] if parts else ""
    slide_parts = [p for p in parts[1:] if p.strip()]
    if not slide_parts:
        # no recognizable slide headers — treat the whole thing as one batch
        return "", [content_md]
    return preamble, slide_parts


def generate_slides_html_batches(content_md: str, theme: str = "redhat-enterprise", batch_size: int = 6):
    """Yield (slides, truncated) per batch instead of one giant completion for
    the whole deck — a 20-slide request in one call risks running out of
    max_tokens mid-slide; each batch gets its own full token budget instead."""
    engine_dir = settings.ENGINE_DIR
    theme_css = _load_theme_css(engine_dir)
    icon_list = _load_icon_list(engine_dir)
    theme_guide = _load_theme_guide(engine_dir, theme)

    client = _get_client()
    system = _build_slide_system(theme_css, icon_list, theme_guide)

    preamble, slide_parts = _split_content_by_slide(content_md)
    slide_counter = 0  # authoritative numbering — never trust the model's own count

    for i in range(0, len(slide_parts), batch_size):
        batch = slide_parts[i:i + batch_size]
        batch_md = f"{preamble}\n\n{''.join(batch)}" if preamble else "".join(batch)
        response = _create_message(client,
            model=settings.MODEL_NAME,
            max_tokens=settings.MAX_OUTPUT_TOKENS,
            system=system,
            messages=[{
                "role": "user",
                "content": (
                    f"다음 content.md에 있는 슬라이드들의 HTML을 작성하세요 (이번 배치 {len(batch)}개 슬라이드):\n\n{batch_md}"
                ),
            }],
        )
        text = response.content[0].text
        raw_slides = _parse_slides(text)

        # Each batch is a stateless call with no memory of other batches' own
        # slide numbering, and the model can still miscount within a batch
        # (observed: two slides both named slide07-*). Renumber sequentially
        # here instead of trusting whatever number the model put in its own
        # "### slideNN-slug" header — only the descriptive slug is kept.
        slides = []
        for s in raw_slides:
            slide_counter += 1
            m = re.match(r'slide\d+-(.+)\.html$', s["filename"])
            slug = m.group(1) if m else "slide"
            slides.append({"filename": f"slide{slide_counter:02d}-{slug}.html", "html": s["html"]})

        truncated = response.stop_reason == "max_tokens"
        yield slides, truncated
        if truncated:
            return  # this batch already hit the limit; further batches would too


def _edit_system(theme_css: str) -> str:
    return f"""당신은 Red Hat 슬라이드 HTML 편집 전문가입니다. 사용자가 기존 슬라이드에 대해 요청한
수정사항을 반영한 완성된 HTML을 출력합니다.

오늘 날짜는 {_today_kr()}입니다.

## 규칙
- 기존 슬라이드의 전체 구조·스타일·클래스명을 최대한 유지하고, 요청된 부분만 정확히 수정하세요.
- 요청과 무관한 내용은 임의로 바꾸지 마세요.
- word-break: keep-all (한글 텍스트) 유지.

## PPTX 변환 필수 규칙 (위반하면 이 슬라이드가 PPTX 빌드에서 통째로 누락됩니다)
1. 모든 글자는 반드시 `<p>`, `<h1>~<h6>`, `<ul>`, `<ol>` 태그 안에만 있어야 합니다. `<div>`, `<span>`
   바로 밑에 텍스트를 직접 두지 마세요.
2. `<h1>~<h6>`, `<p>`, `<ul>`, `<ol>`, `<li>` 태그 자체에는 background, border, box-shadow를 적용하지
   마세요 — 감싸는 `<div>`에 적용하세요.
3. `<div>`에 background-image나 그라디언트를 쓰지 마세요.
4. 본문이 720×405pt 캔버스(패딩 제외 실사용 335pt 세로)를 넘지 않도록 하세요.
5. 글자·표·라벨을 이미지로 대체하지 마세요 — 실제 텍스트 태그와 감싸는 `<div>`의
   background-color로 구현하세요. 한 줄 안에서 색상/굵기가 섞여야 할 때도 이미지 대신 같은
   `<p>` 안에 여러 `<span>`을 넣어 각각 스타일링하세요.

## 참고 theme.css
```css
{theme_css}
```

## 출력 형식
설명 없이 완성된 HTML 전체만 아래처럼 코드 블록 하나로 출력하세요.
```html
<!DOCTYPE html>
...
```
"""


def apply_edit_instruction(html: str, instruction: str, target_html: str | None = None) -> str:
    theme_css = _load_theme_css(settings.ENGINE_DIR)
    client = _get_client()
    user_msg = ""
    if target_html:
        # Comes from the WYSIWYG overlay: the user clicked one specific
        # element in the rendered preview, so scope the edit to it instead
        # of leaving the model to guess which part of the slide "제목"/"이
        # 부분" etc. refers to.
        user_msg += (
            "특히 아래 요소를 대상으로 수정하세요 (이 요소의 위치·구조는 최대한 유지):\n"
            f"```html\n{target_html}\n```\n\n"
        )
    user_msg += f"현재 슬라이드 전체 HTML:\n```html\n{html}\n```\n\n수정 요청: {instruction}"

    response = _create_message(client,
        model=settings.MODEL_NAME,
        max_tokens=settings.MAX_OUTPUT_TOKENS,
        system=_edit_system(theme_css),
        messages=[{"role": "user", "content": user_msg}],
    )
    text = response.content[0].text
    m = re.search(r'```html\s*\n(.*?)```', text, re.DOTALL)
    return m.group(1).strip() if m else text.strip()


def _consistency_system(theme_css: str) -> str:
    return f"""당신은 Red Hat 슬라이드 디자인 감수자입니다. 아래 "비교 대상 슬라이드"들과
비교했을 때, "검토할 슬라이드"가 같은 덱의 일부라고 느껴지지 않을 정도로 톤앤매너(색상
사용, 타이포그래피 크기/굵기 위계, 여백·레이아웃 패턴, 아이콘/이미지 스타일, 어투)가
어긋나는지 판단합니다.

## 규칙
- 비교 대상 슬라이드가 여러 장이면, 그중 다수가 공유하는 스타일을 그 덱의 기준(theme.css를
  따르는 표준)으로 보세요. "검토할 슬라이드"가 그 다수 기준과 다르면 어긋난 것이고, 반대로
  비교 대상 쪽이 소수/특이 사례이고 "검토할 슬라이드"가 오히려 theme.css 표준에 더 가깝다면
  어긋나지 않은 것입니다 — 단순히 서로 다르다는 이유만으로 "검토할 슬라이드"를 고치지 마세요.
- 내용(사실관계·문구)은 절대 바꾸지 마세요. 오직 시각적 톤앤매너·구조적 관례만 봅니다.
- 사소한 차이(슬라이드마다 당연히 다를 수 있는 레이아웃, 예: 표 vs 카드형 등 콘텐츠 특성상
  불가피한 차이)는 어긋남으로 보지 마세요. 명백히 이질적인 경우만 표시하세요.
- 어긋난다고 판단되면, 다수 기준에 맞춰 스타일만 고친 완성된 HTML을 주세요 (구조·클래스명은
  최대한 유지, 내용은 그대로).
- word-break: keep-all (한글 텍스트) 유지.

## PPTX 변환 필수 규칙 (수정본에도 반드시 지켜야 함)
1. 모든 글자는 반드시 `<p>`, `<h1>~<h6>`, `<ul>`, `<ol>` 태그 안에만 있어야 합니다.
2. `<h1>~<h6>`, `<p>`, `<ul>`, `<ol>`, `<li>` 태그 자체에는 background, border, box-shadow를
   적용하지 마세요 — 감싸는 `<div>`에 적용하세요.
3. 본문이 720×405pt 캔버스(패딩 제외 실사용 335pt 세로)를 넘지 않도록 하세요.

## 참고 theme.css
```css
{theme_css}
```

## 출력 형식
설명 없이 아래 JSON 하나만 출력하세요 (fixed_html은 matches가 false일 때만 포함):
```json
{{"matches": true|false, "reason": "판단 이유 한두 문장", "fixed_html": "<!DOCTYPE html>..."}}
```
"""


def review_slide_consistency(slide_html: str, sibling_htmls: list[str]) -> dict:
    theme_css = _load_theme_css(settings.ENGINE_DIR)
    client = _get_client()
    siblings_block = "\n\n".join(
        f"### 비교 대상 슬라이드 {i + 1}\n```html\n{h}\n```" for i, h in enumerate(sibling_htmls)
    )
    user_msg = (
        f"{siblings_block}\n\n### 검토할 슬라이드\n```html\n{slide_html}\n```"
        if siblings_block else f"### 검토할 슬라이드\n```html\n{slide_html}\n```"
    )
    response = _create_message(client,
        model=settings.MODEL_NAME,
        max_tokens=settings.MAX_OUTPUT_TOKENS,
        system=_consistency_system(theme_css),
        messages=[{"role": "user", "content": user_msg}],
    )
    text = response.content[0].text
    m = re.search(r'```json\s*\n(.*?)```', text, re.DOTALL)
    raw = m.group(1).strip() if m else text.strip()
    try:
        result = json.loads(raw)
    except json.JSONDecodeError:
        return {"matches": True, "reason": "검토 결과를 해석하지 못해 건너뜀", "fixed_html": None}
    if not isinstance(result, dict) or "matches" not in result:
        return {"matches": True, "reason": "검토 결과를 해석하지 못해 건너뜀", "fixed_html": None}
    return {
        "matches": bool(result.get("matches")),
        "reason": str(result.get("reason") or ""),
        "fixed_html": result.get("fixed_html") if not result.get("matches") else None,
    }


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
