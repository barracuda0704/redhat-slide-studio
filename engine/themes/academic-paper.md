---
created: 2026-05-25
tags:
  - redhat-slide-skill
  - theme
  - generic
name: academic-paper
description: Light academic style for lectures, research presentations, and analytical decks. Restrained serif display with sans body, warm off-white surface, violet accent.
brand_mode: generic
mode: light
---

# Theme: Academic Paper

논문·세미나·강의·분석 보고용 라이트 테마. 따뜻한 종이톤 배경에 정제된 serif 제목과 깔끔한 sans 본문을 결합해 학술적 신뢰감과 가독성을 동시에 잡는다. Generic mode의 기본값.

## 1. Identity

| 속성 | 값 |
|------|-----|
| 톤 | Analytical, restrained, scholarly |
| 대상 | 연구자, 강의 참석자, 분석 리포트 청자 |
| 사용 시점 | 학술 발표, 연구 결과 공유, 강의 자료, 분석 deck |
| 캔버스 | `720pt × 405pt` (16:9) |
| Mode | Light |

## 2. Color Tokens

```css
:root {
  --bg: #f7f5f0;          /* warm off-white, paper feel */
  --surface: #ffffff;     /* card / inset */
  --surface-alt: #efece5;
  --text: #1a1814;        /* near-black, warm */
  --text-secondary: #4a4640;
  --text-muted: #8a857c;
  --accent: #6d4cff;      /* violet, scholarly accent */
  --accent-soft: #ece6ff;
  --line: #d8d3c7;        /* hairline rule */
}
```

**원칙**

- Solid backgrounds only. Gradient·mesh·noise 금지.
- `#6d4cff`는 강조 hairline·인용 표시·중요 데이터 highlight에만. 본문 색 아님.
- 카드는 surface(#ffffff)와 얇은 line으로 분리, 그림자 남용 금지.

## 3. Typography

| 항목 | 값 |
|------|-----|
| Display family | `"Times New Roman", "Georgia", serif` |
| Body family | `"Pretendard", "Noto Sans KR", system-ui, sans-serif` |
| Code family | `"JetBrains Mono", "D2Coding", monospace` |
| Weights | 400 / 500 / 700 |

한국어 본문은 Pretendard/Noto Sans KR이 우선이고, 영문 제목은 serif가 받는다. 혼용 시에도 한글은 sans 유지.

### Type Scale (720×405pt 기준)

| 역할 | size | weight | family | line-height |
|------|------|--------|--------|-------------|
| Eyebrow | 10pt | 500 | sans (uppercase, letter-spacing 0.12em) | 1.2 |
| Section title | 30pt | 700 | serif | 1.25 |
| Slide title | 24pt | 700 | serif | 1.3 |
| Subtitle | 15pt | 400 italic | serif | 1.4 |
| Body | 13pt | 400 | sans | 1.5 |
| Caption / footer | 10pt | 400 | sans | 1.35 |
| Code | 12pt | 400 | mono | 1.4 |

한국어 본문 `line-height` 최소 1.5. `letter-spacing` 0 또는 -0.005em.

## 4. Layout & Spacing

| Token | 값 |
|-------|-----|
| Outer padding (좌우) | `25pt` |
| Outer padding (상하) | `22pt` |
| Bottom safe area | `36pt` |
| Section gap | `18pt` |
| Card padding | `16pt` |
| Element gap | `8pt` |

`engine/html2pptx.js` 기본 padding(`22pt`/`25pt`) 유지. Footer 위로 최소 36pt 여백을 비워둔다.

## 5. Component Patterns

### 5.1 Title (cover / section opener)

```html
<section class="slide">
  <div class="eyebrow">RESEARCH · 2026</div>
  <h1 class="title">분산 시스템에서의 일관성 모델</h1>
  <p class="subtitle">An empirical study of CAP trade-offs</p>
  <footer class="footer">
    <span>KAIST CS Colloquium</span>
    <span>2026.05</span>
  </footer>
</section>

<style>
.slide {
  width: 720pt; height: 405pt;
  padding: 22pt 25pt;
  background: #f7f5f0;
  color: #1a1814;
  font-family: "Pretendard", "Noto Sans KR", system-ui, sans-serif;
  display: flex; flex-direction: column; justify-content: space-between;
}
.eyebrow {
  font-size: 10pt; font-weight: 500; letter-spacing: 0.12em;
  color: #6d4cff; text-transform: uppercase;
  margin-bottom: 14pt;
}
.title {
  font-family: "Times New Roman", "Georgia", serif;
  font-size: 30pt; font-weight: 700; line-height: 1.25;
  margin: 0 0 10pt;
}
.subtitle {
  font-family: "Times New Roman", "Georgia", serif;
  font-style: italic;
  font-size: 15pt; color: #4a4640; line-height: 1.4;
}
</style>
```

### 5.2 Footer (every content slide)

```html
<footer class="footer">
  <span class="footer-meta">분산 시스템 · 2026 Spring Lecture 07</span>
  <span class="footer-page">12 / 38</span>
</footer>

<style>
.footer {
  display: flex; justify-content: space-between;
  font-size: 10pt; color: #8a857c;
  font-family: "Pretendard", "Noto Sans KR", system-ui, sans-serif;
  border-top: 0.5pt solid #d8d3c7;
  padding-top: 6pt;
}
</style>
```

### 5.3 Eyebrow + Title block (content slide)

```html
<header class="slide-header">
  <div class="eyebrow">SECTION 03</div>
  <h2 class="slide-title">Consistency vs. Availability</h2>
  <hr class="rule" />
</header>

<style>
.slide-header { margin-bottom: 14pt; }
.eyebrow {
  font-size: 10pt; font-weight: 500; letter-spacing: 0.12em;
  color: #6d4cff; text-transform: uppercase;
  margin-bottom: 6pt;
}
.slide-title {
  font-family: "Times New Roman", "Georgia", serif;
  font-size: 22pt; font-weight: 700; line-height: 1.3;
  margin: 0 0 8pt;
}
.rule { border: 0; border-top: 0.5pt solid #d8d3c7; margin: 0; }
</style>
```

### 5.4 Card (restrained information block)

```html
<article class="card">
  <h3 class="card-title">Strong Consistency</h3>
  <p class="card-body">모든 노드가 동일한 시점에 같은 값을 본다. 가용성을 희생한다.</p>
</article>

<style>
.card {
  background: #ffffff;
  border: 0.5pt solid #d8d3c7;
  border-left: 2pt solid #6d4cff;
  padding: 16pt;
}
.card-title {
  font-family: "Times New Roman", "Georgia", serif;
  font-size: 14pt; font-weight: 700; margin: 0 0 6pt;
}
.card-body { font-size: 13pt; line-height: 1.5; color: #1a1814; }
</style>
```

## 6. Motion Philosophy

- 거의 정적. Fade-in 200~300ms만 허용.
- Slide transition은 단순 cut 또는 fade. Push/zoom 금지.
- 강조는 색이 아닌 weight 변화로 처리.

## 7. Anti-Patterns

| ❌ 하지 말 것 | 이유 |
|--------------|------|
| Gradient·neon·sticker | 학술 톤 훼손 |
| 본문에 violet 사용 | accent는 강조 용도 한정 |
| 한글에 serif 강제 적용 | 가독성 저하 |
| 4종 이상 폰트 혼합 | 인쇄물의 절제 원칙 위배 |
| 그림자 큰 카드 | 종이톤과 충돌 |

## 8. Acceptance

- 배경: `#f7f5f0` 단색
- 제목 폰트: serif 명시
- 본문 폰트: Pretendard/Noto Sans KR 명시
- 캔버스: `720pt × 405pt`
- Padding default 유지 (`22pt/25pt`)
- Bottom safe area ≥ 36pt
- 모든 content 슬라이드에 footer + page indicator
