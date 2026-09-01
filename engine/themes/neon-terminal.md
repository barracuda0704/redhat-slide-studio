---
created: 2026-05-25
tags:
  - redhat-slide-skill
  - theme
  - generic
name: neon-terminal
description: Developer terminal style for CLI tutorials, demos, and code-heavy talks. Monospace everywhere, deep slate background, neon green accent.
brand_mode: generic
mode: dark
---

# Theme: Neon Terminal

CLI 튜토리얼·라이브 데모·코드 중심 톡을 위한 터미널 톤 다크 테마. 모든 텍스트는 모노스페이스, 모서리는 직각, 헤더는 프롬프트 형태. 코드가 1급 시민.

## 1. Identity

| 속성 | 값 |
|------|-----|
| 톤 | Technical, hacker, raw, terminal |
| 대상 | 개발자, DevOps/SRE, infra engineer |
| 사용 시점 | CLI tutorial, live coding, kubectl/podman demo, code-heavy talk |
| 캔버스 | `720pt × 405pt` (16:9) |
| Mode | Dark |

## 2. Color Tokens

```css
:root {
  --bg: #0a0e0f;          /* deep slate */
  --surface: #11171a;
  --surface-alt: #161d20;
  --text: #d4f1d4;        /* phosphor green tint */
  --text-secondary: #8fb88f;
  --text-muted: #5a7a5a;
  --accent: #00ff88;      /* neon green */
  --accent-soft: #003322;
  --accent-warn: #ffcc00;
  --accent-err: #ff5555;
  --line: #1f2a2e;
}
```

**원칙**

- Solid backgrounds only. Gradient·blur·glow filter 금지.
- 모든 모서리는 `border-radius: 0`. 직각 유지.
- `#00ff88`는 prompt sigil·success·강조 토큰에만.
- 빨강(`#ff5555`)은 error 표시 한정. 일반 강조 X.

## 3. Typography

| 항목 | 값 |
|------|-----|
| Display family | `"JetBrains Mono", "D2Coding", "Pretendard", monospace` |
| Body family | 동일 (mono-only) |
| Code family | 동일 |
| Weights | 400 / 500 / 700 |

전부 모노스페이스. 한글은 D2Coding 또는 Pretendard fallback이 받는다. Italic 금지(터미널에선 비표준).

### Type Scale (720×405pt 기준)

| 역할 | size | weight | line-height |
|------|------|--------|-------------|
| Prompt / eyebrow | 11pt | 500 | 1.3 |
| Section title | 26pt | 700 | 1.25 |
| Slide title | 20pt | 700 | 1.3 |
| Subtitle | 14pt | 400 | 1.4 |
| Body | 13pt | 400 | 1.5 |
| Code block | 13pt | 400 | 1.5 |
| Caption / footer | 10pt | 400 | 1.3 |

한국어 본문 `line-height` 최소 1.5. `letter-spacing` 0 (모노에선 조정 금지).

## 4. Layout & Spacing

| Token | 값 |
|-------|-----|
| Outer padding (좌우) | `25pt` |
| Outer padding (상하) | `22pt` |
| Bottom safe area | `36pt` |
| Section gap | `14pt` |
| Card padding | `14pt` |
| Element gap | `8pt` |

`engine/html2pptx.js` 기본 padding(`22pt`/`25pt`) 유지. 코드블록은 outer padding을 침범하지 않는다.

## 5. Component Patterns

### 5.1 Title (cover / section opener)

```html
<section class="slide">
  <div class="eyebrow">$ ./demo --chapter 01</div>
  <h1 class="title">kubectl, 한 줄씩 뜯어보기</h1>
  <p class="subtitle"># A hands-on tour of the Kubernetes CLI</p>
  <footer class="footer">
    <span>~/talks/kubectl-deep-dive</span>
    <span>2026.05</span>
  </footer>
</section>

<style>
.slide {
  width: 720pt; height: 405pt;
  padding: 22pt 25pt;
  background: #0a0e0f;
  color: #d4f1d4;
  font-family: "JetBrains Mono", "D2Coding", "Pretendard", monospace;
  display: flex; flex-direction: column; justify-content: space-between;
}
.eyebrow {
  font-size: 11pt; font-weight: 500;
  color: #00ff88;
  margin-bottom: 14pt;
}
.title { font-size: 26pt; font-weight: 700; line-height: 1.25; margin: 0 0 8pt; }
.subtitle { font-size: 14pt; font-weight: 400; color: #8fb88f; line-height: 1.4; }
</style>
```

### 5.2 Footer (every content slide)

```html
<footer class="footer">
  <span class="footer-meta">~/talks/kubectl-deep-dive</span>
  <span class="footer-page">[12/38]</span>
</footer>

<style>
.footer {
  display: flex; justify-content: space-between;
  font-size: 10pt; color: #5a7a5a;
  font-family: "JetBrains Mono", "D2Coding", "Pretendard", monospace;
  border-top: 0.5pt solid #1f2a2e;
  padding-top: 6pt;
}
</style>
```

### 5.3 Eyebrow + Title block (content slide)

```html
<header class="slide-header">
  <div class="eyebrow">$ kubectl get pods --all-namespaces</div>
  <h2 class="slide-title">Pod 상태 한눈에 보기</h2>
</header>

<style>
.slide-header { margin-bottom: 14pt; }
.eyebrow {
  font-size: 11pt; font-weight: 500;
  color: #00ff88;
  margin-bottom: 6pt;
}
.slide-title {
  font-size: 20pt; font-weight: 700; line-height: 1.3;
  margin: 0;
  border-left: 2pt solid #00ff88;
  padding-left: 10pt;
}
</style>
```

### 5.4 Terminal block

```html
<article class="terminal">
  <div class="prompt">$ kubectl describe pod nginx-7c8</div>
  <pre class="output">Name:         nginx-7c8
Namespace:    default
Status:       <span class="ok">Running</span>
IP:           10.244.0.12</pre>
</article>

<style>
.terminal {
  background: #11171a;
  border: 1pt solid #1f2a2e;
  padding: 14pt;
}
.prompt {
  font-size: 12pt; color: #00ff88;
  margin-bottom: 6pt;
}
.output {
  font-size: 13pt; line-height: 1.5; color: #d4f1d4;
  margin: 0; white-space: pre;
}
.ok { color: #00ff88; }
.err { color: #ff5555; }
.warn { color: #ffcc00; }
</style>
```

## 6. Motion Philosophy

- 터미널 출력 시퀀스를 모사. 100~150ms cut-in, 라인 단위 stagger.
- 커서 깜빡임(1Hz)은 cover 슬라이드 한정 허용.
- Fade·slide·zoom 모두 비권장. 즉각적인 cut.

## 7. Anti-Patterns

| ❌ 하지 말 것 | 이유 |
|--------------|------|
| Serif 폰트 | 터미널 톤 파괴 |
| 사진·일러스트 | 모노톤 코드 미학 깨짐 |
| Pastel·gradient | 터미널은 high-contrast |
| Border-radius > 0 | 직각 유지 원칙 |
| Drop shadow·glow | 평면 터미널 톤 |
| Italic 본문 | 모노 italic은 보통 깨짐 |

## 8. Acceptance

- 배경: `#0a0e0f` 단색
- 폰트: 전부 monospace stack
- 캔버스: `720pt × 405pt`
- Padding default 유지 (`22pt/25pt`)
- Bottom safe area ≥ 36pt
- 모서리 `border-radius: 0`
- 모든 content 슬라이드에 footer + page indicator
