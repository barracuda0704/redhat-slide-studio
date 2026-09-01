---
created: 2026-05-25
tags:
  - redhat-slide-skill
  - theme
  - generic
name: modern-minimal
description: Clean product/engineering minimal theme for tech seminars, product walkthroughs, and infrastructure explanation. System sans, pure white, blue accent.
brand_mode: generic
mode: light
---

# Theme: Modern Minimal

테크 세미나·제품 워크스루·인프라 설명을 위한 미니멀 라이트 테마. 시스템 sans 한 종류로 hierarchy를 만들고, 얇은 1pt 라인과 넉넉한 여백으로 시스템 다이어그램을 깔끔하게 받친다.

## 1. Identity

| 속성 | 값 |
|------|-----|
| 톤 | Clean, neutral, engineering-grade |
| 대상 | 개발자, 플랫폼 엔지니어, 제품 데모 청자 |
| 사용 시점 | 기술 세미나, product walkthrough, architecture/infra 설명 |
| 캔버스 | `720pt × 405pt` (16:9) |
| Mode | Light |

## 2. Color Tokens

```css
:root {
  --bg: #ffffff;
  --surface: #ffffff;
  --surface-alt: #fafafa;
  --text: #0a0a0a;
  --text-secondary: #525252;
  --text-muted: #a3a3a3;
  --accent: #0066ff;       /* engineering blue */
  --accent-soft: #e6efff;
  --line: #e5e5e5;          /* 1pt hairline */
  --line-strong: #0a0a0a;
}
```

**원칙**

- Solid backgrounds only. Gradient·mesh·noise 금지.
- 라인은 1pt `#e5e5e5` 기본, 강조 시 1pt `#0a0a0a`.
- `#0066ff`는 link·active state·diagram primary node에만.
- 카드는 fill 없이 border만. 그림자 금지.

## 3. Typography

| 항목 | 값 |
|------|-----|
| Display family | `-apple-system, BlinkMacSystemFont, "Inter", "Pretendard", "Noto Sans KR", sans-serif` |
| Body family | 동일 (single-stack) |
| Code family | `"JetBrains Mono", "D2Coding", "SF Mono", monospace` |
| Weights | 400 / 500 / 600 / 700 |

폰트는 한 종류. weight 차이로 hierarchy를 만든다.

### Type Scale (720×405pt 기준)

| 역할 | size | weight | line-height |
|------|------|--------|-------------|
| Eyebrow | 10pt | 600 | 1.2 |
| Section title | 32pt | 700 | 1.2 |
| Slide title | 24pt | 600 | 1.3 |
| Subtitle | 15pt | 400 | 1.4 |
| Body | 13pt | 400 | 1.5 |
| Caption / footer | 10pt | 400 | 1.3 |
| Code | 12pt | 400 | 1.45 |

한국어 본문 `line-height` 최소 1.5. `letter-spacing`은 본문 0, 제목 -0.01em.

## 4. Layout & Spacing

| Token | 값 |
|-------|-----|
| Outer padding (좌우) | `25pt` |
| Outer padding (상하) | `22pt` |
| Bottom safe area | `36pt` |
| Section gap | `16pt` |
| Card padding | `14pt` |
| Element gap | `8pt` |
| Diagram grid | 12pt baseline |

12pt baseline grid를 따른다. 모든 카드·라인·다이어그램 노드는 12의 배수 위치에 정렬.

## 5. Component Patterns

### 5.1 Title (cover / section opener)

```html
<section class="slide">
  <div class="eyebrow">PRODUCT · 2026</div>
  <h1 class="title">Edge Computing Platform</h1>
  <p class="subtitle">분산 인프라를 위한 차세대 컨테이너 런타임</p>
  <footer class="footer">
    <span>Engineering Showcase</span>
    <span>2026.05</span>
  </footer>
</section>

<style>
.slide {
  width: 720pt; height: 405pt;
  padding: 22pt 25pt;
  background: #ffffff;
  color: #0a0a0a;
  font-family: -apple-system, BlinkMacSystemFont, "Inter", "Pretendard", "Noto Sans KR", sans-serif;
  display: flex; flex-direction: column; justify-content: space-between;
}
.eyebrow {
  font-size: 10pt; font-weight: 600; letter-spacing: 0.08em;
  color: #0066ff; text-transform: uppercase;
  margin-bottom: 12pt;
}
.title { font-size: 32pt; font-weight: 700; line-height: 1.2; margin: 0 0 8pt; letter-spacing: -0.01em; }
.subtitle { font-size: 15pt; font-weight: 400; color: #525252; line-height: 1.4; }
</style>
```

### 5.2 Footer (every content slide)

```html
<footer class="footer">
  <span class="footer-meta">Engineering Showcase · 2026</span>
  <span class="footer-page">12 / 38</span>
</footer>

<style>
.footer {
  display: flex; justify-content: space-between;
  font-size: 10pt; color: #a3a3a3;
  font-family: -apple-system, BlinkMacSystemFont, "Inter", "Pretendard", "Noto Sans KR", sans-serif;
  border-top: 1pt solid #e5e5e5;
  padding-top: 6pt;
}
</style>
```

### 5.3 Eyebrow + Title block (content slide)

```html
<header class="slide-header">
  <div class="eyebrow">ARCHITECTURE</div>
  <h2 class="slide-title">Control plane와 data plane 분리</h2>
</header>

<style>
.slide-header { margin-bottom: 16pt; }
.eyebrow {
  font-size: 10pt; font-weight: 600; letter-spacing: 0.08em;
  color: #0066ff; text-transform: uppercase;
  margin-bottom: 6pt;
}
.slide-title {
  font-size: 22pt; font-weight: 600; line-height: 1.3;
  letter-spacing: -0.01em;
  margin: 0;
}
</style>
```

### 5.4 Diagram-friendly card

```html
<article class="card">
  <h3 class="card-title">API Gateway</h3>
  <p class="card-body">외부 트래픽을 받아 내부 서비스로 라우팅한다.</p>
</article>

<style>
.card {
  background: #ffffff;
  border: 1pt solid #e5e5e5;
  padding: 14pt;
}
.card-title { font-size: 13pt; font-weight: 600; margin: 0 0 4pt; }
.card-body  { font-size: 12pt; line-height: 1.5; color: #525252; }
</style>
```

## 6. Motion Philosophy

- 정밀하고 절제된 motion. 모든 전환 200ms `cubic-bezier(0.2, 0, 0, 1)`.
- Diagram의 노드가 순차 fade-in 가능 (50ms stagger).
- Bounce·elastic·rotate 금지.

## 7. Anti-Patterns

| ❌ 하지 말 것 | 이유 |
|--------------|------|
| Drop shadow on cards | 미니멀 톤 훼손 |
| 4종 이상 폰트 | single-stack 원칙 위배 |
| Pastel·neon 색 | 엔지니어링 톤 깨짐 |
| Border-radius > 4pt | 시스템 그래픽 톤 깨짐 |
| Gradient·glow | 평면성 위배 |

## 8. Acceptance

- 배경: `#ffffff` 단색
- 폰트: 단일 sans stack
- 캔버스: `720pt × 405pt`
- Padding default 유지 (`22pt/25pt`)
- Bottom safe area ≥ 36pt
- 12pt baseline grid 정렬
- 모든 content 슬라이드에 footer + page indicator
