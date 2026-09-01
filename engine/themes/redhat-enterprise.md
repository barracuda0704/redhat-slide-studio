---
created: 2026-05-25
brand_mode: redhat
tags:
  - redhat-slide-skill
  - theme
  - enterprise
---

# Theme: Red Hat Enterprise

엔터프라이즈 고객 engagement, technical assessment 보고 발표, 공식 컨설팅 자료를 위한 기본 테마. Red Hat brand standards를 준수한 차분하고 신뢰감 있는 톤.

## 1. Identity

| 속성 | 값 |
|------|-----|
| 톤 | Confident, restrained, official |
| 대상 | 엔터프라이즈 IT 리더, 플랫폼 팀, 컨설팅 고객 |
| 사용 시점 | Discovery, assessment, executive briefing, formal proposal |
| 캔버스 | `720pt × 405pt` (16:9) |

## 2. Color Tokens

`config.json`을 single source of truth로 본다.

```css
:root {
  /* Primary brand */
  --brand-primary: #ee0000;   /* red-50, Red Hat Red */
  --brand-secondary: #a60000; /* red-60 */
  --brand-tertiary: #5f0000;  /* red-70 */

  /* Text & surface */
  --text-primary: #000000;
  --text-secondary: #4d4d4d; /* gray-60 */
  --text-muted: #a3a3a3;     /* gray-40 */
  --surface: #ffffff;
  --surface-alt: #f2f2f2;
  --border: #e0e0e0;         /* gray-20 */

  /* Accents (sparingly) */
  --accent-purple: #5e40be;
  --accent-teal: #37a3a3;
  --accent-orange: #f5921b;
  --accent-yellow: #ffe072;
}
```

**원칙**

- Solid backgrounds only. Gradient, mesh, noise 금지 (브랜드 표준 위배).
- `#ee0000`는 한 슬라이드에 1~2개 요소까지. 남발 금지.
- 어두운 배경이 필요하면 `#5f0000` 또는 `#000000` 사용, 절대 `#ee0000`을 본문 배경으로 쓰지 않는다.

## 3. Typography

| 항목 | 값 |
|------|-----|
| Font family | `Noto Sans KR`, system-ui, sans-serif |
| Weights | 300 / 400 / 500 / 700 / 900 |
| 로드 | `https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;500;700;900&display=swap` |

### Type Scale (캔버스 720×405pt 기준)

| 역할 | size | weight | line-height |
|------|------|--------|-------------|
| Eyebrow | 11pt | 500 | 1.2 |
| Section title | 32pt | 700 | 1.25 |
| Slide title | 26pt | 700 | 1.3 |
| Subtitle | 16pt | 500 | 1.35 |
| Body | 13pt | 400 | 1.45 |
| Caption / footer | 10pt | 400 | 1.3 |
| Code | 12pt monospace | 400 | 1.4 |

한국어 본문은 무조건 `line-height` 1.4 이상. `letter-spacing`은 -0.01em 정도만, 과도한 자간 조정 금지.

## 4. Layout & Spacing

| Token | 값 |
|-------|-----|
| Outer padding (좌우) | `25pt` |
| Outer padding (상하) | `22pt` |
| Section gap | `16pt` |
| Card padding | `14pt` |
| Element gap (기본) | `8pt` |

`engine/html2pptx.js`의 padding default 값(`22pt`/`25pt`)을 그대로 따른다. 테마에서 임의 변경하지 않는다.

```
+--------------------------------------------------+
|  22pt top                                        |
|  25pt   [ Eyebrow ]                       25pt   |
|  left   [ Title         ]                 right  |
|         [ Subtitle      ]                        |
|         [ Body / Cards  ]                        |
|         [ Footer (10pt) ]                        |
|  22pt bottom                                     |
+--------------------------------------------------+
```

## 5. Component Patterns

### 5.1 Title (cover / section opener)

```html
<section class="slide">
  <div class="eyebrow">RED HAT OPENSHIFT</div>
  <h1 class="title">컨테이너 플랫폼 도입 전략</h1>
  <p class="subtitle">엔터프라이즈 워크로드를 위한 modernization roadmap</p>
  <footer class="footer">
    <span>Red Hat Korea · 2026</span>
    <span>© Red Hat, Inc.</span>
  </footer>
</section>

<style>
.slide {
  width: 720pt; height: 405pt;
  padding: 22pt 25pt;
  background: #ffffff;
  color: #000000;
  font-family: "Noto Sans KR", system-ui, sans-serif;
  display: flex; flex-direction: column; justify-content: space-between;
}
.eyebrow {
  font-size: 11pt; font-weight: 500; letter-spacing: 0.08em;
  color: #ee0000; text-transform: uppercase;
  margin-bottom: 12pt;
}
.title { font-size: 26pt; font-weight: 700; line-height: 1.3; margin: 0 0 8pt; }
.subtitle { font-size: 16pt; font-weight: 500; color: #4d4d4d; line-height: 1.35; }
</style>
```

### 5.2 Footer (every content slide)

```html
<footer class="footer">
  <span class="footer-meta">Red Hat Korea · 2026 Architecture Review</span>
  <span class="footer-page">12 / 38</span>
</footer>

<style>
.footer {
  display: flex; justify-content: space-between;
  font-size: 10pt; color: #4d4d4d;
  border-top: 0.5pt solid #e0e0e0;
  padding-top: 6pt;
}
</style>
```

### 5.3 Eyebrow + Title block (content slide)

```html
<header class="slide-header">
  <div class="eyebrow">ASSESSMENT FINDINGS</div>
  <h2 class="slide-title">현행 아키텍처의 3가지 병목</h2>
</header>

<style>
.slide-header { margin-bottom: 14pt; }
.slide-title {
  font-size: 22pt; font-weight: 700; line-height: 1.3;
  border-left: 3pt solid #ee0000; padding-left: 10pt;
}
</style>
```

### 5.4 Card (information block)

```html
<article class="card">
  <h3 class="card-title">컨테이너 표준화</h3>
  <p class="card-body">레거시 VM 워크로드를 OpenShift 위로 단계적으로 이행한다.</p>
</article>

<style>
.card {
  background: #ffffff;
  border: 0.75pt solid #e0e0e0;
  border-top: 2pt solid #ee0000;
  padding: 14pt;
}
.card-title { font-size: 14pt; font-weight: 700; margin: 0 0 6pt; }
.card-body  { font-size: 13pt; line-height: 1.45; color: #292929; }
</style>
```

## 6. Do / Don't

| ✅ Do | ❌ Don't |
|-------|---------|
| `#ee0000`을 강조 1~2개에만 | 본문 전체를 빨강으로 칠하기 |
| Solid 배경 사용 | Gradient, mesh, 그림자 남용 |
| Noto Sans KR weight 차이로 hierarchy | 4종 이상의 폰트 혼합 |
| 슬라이드당 한 가지 핵심 메시지 | 한 슬라이드에 5개+ 카드 |
| `22pt/25pt` padding 유지 | 캔버스 끝까지 콘텐츠 붙이기 |

## 7. Acceptance

- 색상: `#ee0000`만 brand primary로 사용 (다른 빨강 hex 금지)
- 폰트: `Noto Sans KR` 명시
- 캔버스: `720pt × 405pt` (`16:9`)
- Padding default 미변경 (`22pt/25pt`)
- 모든 콘텐츠 슬라이드에 footer + page indicator
