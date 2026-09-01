---
created: 2026-05-25
tags:
  - redhat-slide-skill
  - theme
  - generic
name: paper-press
description: Print/cream paper style for long Korean lecture handouts and print-ready educational material. Serif display on cream, vermilion accent, dotted dividers, static motion.
brand_mode: generic
mode: light
---

# Theme: Paper Press

긴 한국어 강의 자료·교재·인쇄 배포물을 위한 활판 인쇄 톤 라이트 테마. 크림 종이 위에 검정에 가까운 본문, 주묵(朱墨) 같은 vermilion accent, 점선 구분선이 letterpress 질감을 만든다. 정적 매체(인쇄)를 가정한다.

## 1. Identity

| 속성 | 값 |
|------|-----|
| 톤 | Warm, scholarly, printed, calm |
| 대상 | 학생, 강의 수강생, 교재 독자 |
| 사용 시점 | 한국어 장문 강의 자료, 교재 챕터, 인쇄 핸드아웃 |
| 캔버스 | `720pt × 405pt` (16:9) |
| Mode | Light (print-friendly) |

## 2. Color Tokens

```css
:root {
  --bg: #f6f1e7;          /* cream paper */
  --surface: #fbf7ed;
  --surface-alt: #eee6d4;
  --text: #141210;        /* near-black, warm */
  --text-secondary: #4d463c;
  --text-muted: #8a8170;
  --accent: #c43a1d;      /* vermilion, 주묵 */
  --accent-soft: #f3dcd4;
  --line: #c8bca3;
}
```

**원칙**

- Solid backgrounds only. Gradient·noise 금지.
- 종이톤 위에서 본문은 진한 검정(`#141210`)이어야 인쇄 가독성 확보.
- `#c43a1d`는 도장·인용 부호·중요 표제어에만. 본문 색 아님.
- 점선(`dotted`) 구분선이 시그니처. 실선 구분 최소화.

## 3. Typography

| 항목 | 값 |
|------|-----|
| Display family | `"Times New Roman", "Source Serif Pro", serif` (weight 700) |
| Body family | `"Pretendard", "Noto Sans KR", "Inter", system-ui, sans-serif` |
| Code family | `"D2Coding", "JetBrains Mono", monospace` |
| Weights | 400 / 500 / 700 |

한국어가 메인. 본문은 Pretendard/Noto Sans KR 우선. 영문 표제어와 챕터 넘버만 serif가 받는다.

### Type Scale (720×405pt 기준)

| 역할 | size | weight | family | line-height |
|------|------|--------|--------|-------------|
| Chapter number | 11pt | 500 | sans (uppercase tracking 0.16em) | 1.2 |
| Chapter title | 28pt | 700 | serif | 1.3 |
| Slide title | 22pt | 700 | serif | 1.35 |
| Subtitle | 14pt | 500 | sans | 1.45 |
| Body | 13pt | 400 | sans | 1.6 |
| Pull quote | 16pt | 500 | serif italic | 1.5 |
| Caption / footer | 10pt | 400 | sans | 1.35 |

한국어 본문 `line-height` 최소 1.6 (교재용으로 넉넉히). `letter-spacing` 0.

## 4. Layout & Spacing

| Token | 값 |
|-------|-----|
| Outer padding (좌우) | `25pt` |
| Outer padding (상하) | `22pt` |
| Bottom safe area | `36pt` |
| Section gap | `18pt` |
| Card padding | `16pt` |
| Element gap | `10pt` |
| Marginalia | 좌측 70pt 띠 (선택) |

교재 톤을 살리려면 좌측에 70pt 정도의 marginalia(여백 주석) 영역을 비워두는 변형 레이아웃을 권장. 본 padding default(`22pt/25pt`)는 유지.

## 5. Component Patterns

### 5.1 Title (cover / chapter opener)

```html
<section class="slide">
  <div class="chapter-no">CHAPTER 04 · 한국어 교본</div>
  <h1 class="title">시스템 사고의 다섯 가지 원리</h1>
  <p class="subtitle">생각의 도구로서 시스템을 다시 보다</p>
  <footer class="footer">
    <span>2026 봄학기 · 인문공학 강의</span>
    <span>04 / 12</span>
  </footer>
</section>

<style>
.slide {
  width: 720pt; height: 405pt;
  padding: 22pt 25pt;
  background: #f6f1e7;
  color: #141210;
  font-family: "Pretendard", "Noto Sans KR", "Inter", system-ui, sans-serif;
  display: flex; flex-direction: column; justify-content: space-between;
}
.chapter-no {
  font-size: 11pt; font-weight: 500; letter-spacing: 0.16em;
  color: #c43a1d; text-transform: uppercase;
  margin-bottom: 14pt;
}
.title {
  font-family: "Times New Roman", "Source Serif Pro", serif;
  font-size: 28pt; font-weight: 700; line-height: 1.3;
  margin: 0 0 10pt;
}
.subtitle {
  font-size: 14pt; font-weight: 500; color: #4d463c; line-height: 1.45;
}
</style>
```

### 5.2 Footer (every content slide)

```html
<footer class="footer">
  <span class="footer-meta">시스템 사고 입문 · 2026 봄</span>
  <span class="footer-page">— 12 —</span>
</footer>

<style>
.footer {
  display: flex; justify-content: space-between;
  font-size: 10pt; color: #8a8170;
  font-family: "Pretendard", "Noto Sans KR", "Inter", system-ui, sans-serif;
  border-top: 0.75pt dotted #c8bca3;
  padding-top: 6pt;
}
</style>
```

### 5.3 Eyebrow + Title block (content slide)

```html
<header class="slide-header">
  <div class="chapter-no">§ 4.2</div>
  <h2 class="slide-title">피드백 루프와 지연</h2>
  <hr class="rule" />
</header>

<style>
.slide-header { margin-bottom: 16pt; }
.chapter-no {
  font-size: 11pt; font-weight: 500; letter-spacing: 0.16em;
  color: #c43a1d;
  margin-bottom: 6pt;
}
.slide-title {
  font-family: "Times New Roman", "Source Serif Pro", serif;
  font-size: 22pt; font-weight: 700; line-height: 1.35;
  margin: 0 0 10pt;
}
.rule { border: 0; border-top: 0.75pt dotted #c8bca3; margin: 0; }
</style>
```

### 5.4 Letterpress card

```html
<article class="card">
  <div class="stamp">원리 1</div>
  <h3 class="card-title">지연된 피드백은 진동을 만든다</h3>
  <p class="card-body">시스템의 반응이 늦게 돌아올수록 결정은 과잉 보정으로 흐른다.</p>
</article>

<style>
.card {
  background: #fbf7ed;
  border: 0.5pt solid #c8bca3;
  border-left: 3pt solid #c43a1d;
  padding: 16pt;
}
.stamp {
  display: inline-block;
  border: 1pt solid #c43a1d; color: #c43a1d;
  font-size: 10pt; font-weight: 700; letter-spacing: 0.12em;
  padding: 2pt 6pt;
  margin-bottom: 8pt;
}
.card-title {
  font-family: "Times New Roman", "Source Serif Pro", serif;
  font-size: 14pt; font-weight: 700;
  margin: 0 0 6pt;
}
.card-body { font-size: 13pt; line-height: 1.6; color: #141210; }
</style>
```

## 6. Motion Philosophy

- 정적. 애니메이션 없음. 인쇄물을 그대로 옮긴 듯 다뤄야 한다.
- Slide transition도 instant cut.
- 동영상·라이브 코드도 권장 안 함. 필요하면 정지 이미지 캡처로 대체.

## 7. Anti-Patterns

| ❌ 하지 말 것 | 이유 |
|--------------|------|
| 애니메이션·motion 효과 | 인쇄 정합성 위배 |
| 한글에 serif 강제 | 가독성·인쇄 톤 저하 |
| 형광·neon 색 | 종이톤과 충돌 |
| Drop shadow·glow | 활판 인쇄 톤 깨짐 |
| Gradient 배경 | build-contract 위배 |
| 실선 두꺼운 구분선 | 점선 시그니처 훼손 |

## 8. Acceptance

- 배경: `#f6f1e7` 단색
- 본문 색: `#141210`
- Display: serif 명시 (Times/Source Serif)
- 본문: Pretendard/Noto Sans KR 명시
- 캔버스: `720pt × 405pt`
- Padding default 유지 (`22pt/25pt`)
- Bottom safe area ≥ 36pt
- 구분선은 dotted 우선
- 애니메이션 없음
- 모든 content 슬라이드에 footer + page indicator
