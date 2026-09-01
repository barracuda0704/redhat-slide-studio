---
created: 2026-05-25
tags:
  - redhat-slide-skill
  - theme
  - generic
name: editorial-dark
description: Dark editorial/magazine theme for keynote talks, news/insight decks, and cinematic storytelling. Heavy display sans on near-black, coral accent.
brand_mode: generic
mode: dark
---

# Theme: Editorial Dark

키노트·뉴스/인사이트형 deck·시네마틱 스토리텔링을 위한 다크 에디토리얼 테마. 두꺼운 sans 헤드라인이 화면을 압도하고, 코랄 accent가 잡지 표지처럼 강조점을 만든다.

## 1. Identity

| 속성 | 값 |
|------|-----|
| 톤 | Bold, cinematic, editorial, confident |
| 대상 | 키노트 청중, 일반 대중, 미디어 청자 |
| 사용 시점 | Keynote talk, insight/trend report, brand storytelling |
| 캔버스 | `720pt × 405pt` (16:9) |
| Mode | Dark |

## 2. Color Tokens

```css
:root {
  --bg: #111111;
  --surface: #1a1a1a;
  --surface-alt: #222222;
  --text: #f5f5f5;
  --text-secondary: #b8b8b8;
  --text-muted: #6e6e6e;
  --accent: #ff5a5f;       /* coral */
  --accent-soft: #3a1f20;
  --line: #2e2e2e;
  --line-strong: #f5f5f5;
}
```

**원칙**

- Solid backgrounds only. Gradient·mesh·noise 금지 (build-contract).
- 풀블리드 헤더는 `#111111` 단색 위에 거대한 타이포로 구현. 사진 깔기 금지.
- `#ff5a5f`는 인용·강조 단어·핵심 숫자에만. UI line color 아님.
- 어두운 배경에서 본문은 `#f5f5f5`, 보조 텍스트는 `#b8b8b8` 이상으로 contrast 확보.

## 3. Typography

| 항목 | 값 |
|------|-----|
| Display family | `"Pretendard", "Noto Sans KR", system-ui, sans-serif` (heavy weight) |
| Body family | `"Pretendard", "Noto Sans KR", system-ui, sans-serif` |
| Code family | `"JetBrains Mono", "D2Coding", monospace` |
| Weights | 400 / 500 / 700 / 800 / 900 |

Heavy display weight(800~900)로 임팩트를 만든다. Italic은 인용에만.

### Type Scale (720×405pt 기준)

| 역할 | size | weight | line-height |
|------|------|--------|-------------|
| Hero headline | 64pt | 900 | 1.05 |
| Section title | 40pt | 800 | 1.15 |
| Slide title | 28pt | 700 | 1.25 |
| Eyebrow | 11pt | 600 | 1.2 |
| Subtitle | 16pt | 400 | 1.4 |
| Body | 14pt | 400 | 1.5 |
| Pull quote | 22pt | 500 italic | 1.4 |
| Caption / footer | 10pt | 400 | 1.3 |

한국어 본문 `line-height` 최소 1.5. Hero headline은 `letter-spacing` -0.02em.

## 4. Layout & Spacing

| Token | 값 |
|-------|-----|
| Outer padding (좌우) | `25pt` |
| Outer padding (상하) | `22pt` |
| Bottom safe area | `36pt` |
| Section gap | `20pt` |
| Card padding | `18pt` |
| Element gap | `10pt` |

`engine/html2pptx.js` 기본 padding(`22pt`/`25pt`) 유지. 헤드라인이 큰 만큼 본문 사이 간격은 넉넉히.

## 5. Component Patterns

### 5.1 Title (cover / section opener)

```html
<section class="slide">
  <div class="eyebrow">KEYNOTE · 2026</div>
  <h1 class="title">우리는 왜 인프라를<br/>다시 짓는가</h1>
  <p class="subtitle">An editorial on platform reinvention</p>
  <footer class="footer">
    <span>OPENING SESSION</span>
    <span>01 / 24</span>
  </footer>
</section>

<style>
.slide {
  width: 720pt; height: 405pt;
  padding: 22pt 25pt;
  background: #111111;
  color: #f5f5f5;
  font-family: "Pretendard", "Noto Sans KR", system-ui, sans-serif;
  display: flex; flex-direction: column; justify-content: space-between;
}
.eyebrow {
  font-size: 11pt; font-weight: 600; letter-spacing: 0.14em;
  color: #ff5a5f; text-transform: uppercase;
  margin-bottom: 14pt;
}
.title {
  font-size: 56pt; font-weight: 900; line-height: 1.05;
  letter-spacing: -0.02em;
  margin: 0 0 10pt;
}
.subtitle {
  font-size: 16pt; font-weight: 400; color: #b8b8b8; line-height: 1.4;
  font-style: italic;
}
</style>
```

### 5.2 Footer (every content slide)

```html
<footer class="footer">
  <span class="footer-meta">KEYNOTE · OPENING</span>
  <span class="footer-page">12 / 24</span>
</footer>

<style>
.footer {
  display: flex; justify-content: space-between;
  font-size: 10pt; color: #6e6e6e;
  font-family: "Pretendard", "Noto Sans KR", system-ui, sans-serif;
  letter-spacing: 0.08em; text-transform: uppercase;
  border-top: 0.5pt solid #2e2e2e;
  padding-top: 6pt;
}
</style>
```

### 5.3 Eyebrow + Title block (content slide)

```html
<header class="slide-header">
  <div class="eyebrow">CHAPTER 02</div>
  <h2 class="slide-title">플랫폼은 <span class="hl">조직 구조</span>를 닮는다</h2>
</header>

<style>
.slide-header { margin-bottom: 18pt; }
.eyebrow {
  font-size: 11pt; font-weight: 600; letter-spacing: 0.14em;
  color: #ff5a5f; text-transform: uppercase;
  margin-bottom: 8pt;
}
.slide-title {
  font-size: 36pt; font-weight: 800; line-height: 1.15;
  letter-spacing: -0.015em;
  margin: 0;
}
.hl { color: #ff5a5f; }
</style>
```

### 5.4 Pull-quote card

```html
<article class="card">
  <blockquote class="quote">"인프라는 결국 팀이 일하는 방식의 기록이다."</blockquote>
  <p class="attribution">— Conway's Law revisited</p>
</article>

<style>
.card {
  background: #1a1a1a;
  border-left: 3pt solid #ff5a5f;
  padding: 18pt;
}
.quote {
  font-size: 22pt; font-weight: 500; font-style: italic;
  line-height: 1.4; color: #f5f5f5;
  margin: 0 0 8pt;
}
.attribution { font-size: 11pt; color: #b8b8b8; }
</style>
```

## 6. Motion Philosophy

- 시네마틱 fade. Headline은 250~400ms ease-out으로 등장.
- 인물·문장 단위 stagger 허용 (단어 단위는 과함).
- Cut transition으로 챕터를 강하게 끊는다. Push/wipe 금지.

## 7. Anti-Patterns

| ❌ 하지 말 것 | 이유 |
|--------------|------|
| 사진을 풀블리드로 배경 | solid bg 위배 (build-contract) |
| Drop shadow on text | 매거진 톤 깨짐 |
| Light weight 본문 (300 이하) | 다크 배경에서 가독성 저하 |
| Coral 색 남발 | accent의 임팩트 소실 |
| Rounded corners (>4pt) | 에디토리얼 톤 깨짐 |

## 8. Acceptance

- 배경: `#111111` 단색
- 본문 텍스트: `#f5f5f5`
- 폰트: Pretendard/Noto Sans KR heavy weight
- 캔버스: `720pt × 405pt`
- Padding default 유지 (`22pt/25pt`)
- Bottom safe area ≥ 36pt
- 모든 content 슬라이드에 footer + page indicator
