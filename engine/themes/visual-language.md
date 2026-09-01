---
created: 2026-05-25
tags:
  - redhat-slide-skill
  - theme
  - visual-language
  - spec
  - backlog
---

# Visual Language Spec (Web UI · Phase 2 Backlog)

> **이 문서는 spec / guideline / reference다. 실행 코드가 아니다.**
> 여기 정의된 buttons, cards, panels, motion, spacing tokens는 **Web UI 폴리시 단계용 reference design language**이며,
> 실제 Web UI 구현은 **Phase 2 backlog로 deferred** 되어 있다. PPT 생성 파이프라인(`engine/html2pptx.js`)은 이 spec에 영향을 받지 않는다.

## 0. Scope & Status

| 항목 | 상태 |
|------|------|
| PPT 슬라이드 테마 (enterprise/dark/workshop) | ✅ 활성, `themes/*.md` 별도 문서로 정의됨 |
| Korean typography 규칙 | ✅ 활성, `themes/korean-typography.md` |
| **Web UI visual language** (이 문서) | 🟡 **spec only, deferred to Phase 2** |
| Web UI 실제 구현 (React/Vue/CSS framework) | 🔴 backlog, 미정 |

**현재 단계에서 하지 않는 것:**

- 이 문서를 보고 React 컴포넌트 라이브러리를 만들지 않는다.
- `engine/html2pptx.js`의 padding/스타일 default를 변경하지 않는다.
- 새로운 CSS framework (Tailwind config, design tokens 패키지 등)을 도입하지 않는다.

**이 문서가 존재하는 이유:**

- Phase 2에서 Web UI 폴리시 작업 시 일관된 reference로 사용.
- 외부 디자이너/협업자에게 보여줄 visual language guideline.
- 슬라이드 테마와 Web UI 사이의 brand consistency 유지 근거.

## 1. Foundation

### 1.1 Color Tokens (reference)

`config.json` 색상을 Web UI 토큰으로 매핑한 reference. 실제 구현 시 토큰 이름은 채택하는 시스템(Tailwind, CSS variables, design-tokens.json)에 맞게 조정.

```css
:root {
  /* Brand */
  --color-brand: #ee0000;
  --color-brand-hover: #a60000;
  --color-brand-pressed: #5f0000;
  --color-brand-subtle: #fce3e3;

  /* Surface — light */
  --surface-base: #ffffff;
  --surface-raised: #ffffff;
  --surface-sunken: #f2f2f2;
  --surface-overlay: rgba(0,0,0,0.04);

  /* Surface — dark */
  --surface-base-dark: #000000;
  --surface-raised-dark: #1a1a1a;
  --surface-elevated-dark: #292929;

  /* Border */
  --border-subtle: #e0e0e0;
  --border-default: #a3a3a3;
  --border-strong: #4d4d4d;

  /* Text */
  --text-primary: #000000;
  --text-secondary: #4d4d4d;
  --text-muted: #a3a3a3;
  --text-inverse: #ffffff;

  /* Semantic */
  --color-success: #37a3a3;   /* teal-50 */
  --color-warning: #f5921b;   /* orange-50 */
  --color-danger:  #ee0000;   /* red-50 */
  --color-info:    #5e40be;   /* purple-50 */
}
```

### 1.2 Spacing Scale (reference)

8pt grid 기반. 슬라이드(`22pt/25pt`)와 별개로 Web UI는 8/12/16/24/32/48/64pt scale 권장.

| Token | px / pt |
|-------|---------|
| `--space-1` | 4 |
| `--space-2` | 8 |
| `--space-3` | 12 |
| `--space-4` | 16 |
| `--space-5` | 24 |
| `--space-6` | 32 |
| `--space-7` | 48 |
| `--space-8` | 64 |

### 1.3 Typography Scale (reference)

Web UI는 슬라이드보다 1~2pt 큰 size로 운영 권장 (모니터/스크롤 가독성).

| 역할 | size | weight | line-height |
|------|------|--------|-------------|
| Display | 40 | 700 | 1.2 |
| H1 | 32 | 700 | 1.25 |
| H2 | 24 | 700 | 1.3 |
| H3 | 20 | 600 | 1.35 |
| Body | 16 | 400 | 1.5 |
| Body sm | 14 | 400 | 1.5 |
| Caption | 12 | 400 | 1.4 |

Font stack은 `themes/korean-typography.md` 따라 `Pretendard` 1순위 유지.

### 1.4 Radius & Elevation (reference)

| Token | 값 |
|-------|-----|
| `--radius-sm` | 4px |
| `--radius-md` | 8px |
| `--radius-lg` | 12px |
| `--radius-pill` | 999px |
| `--shadow-1` | `0 1px 2px rgba(0,0,0,0.06)` |
| `--shadow-2` | `0 4px 12px rgba(0,0,0,0.08)` |
| `--shadow-3` | `0 12px 32px rgba(0,0,0,0.12)` |

> 슬라이드 테마에서는 shadow 사용을 자제하지만(인쇄 깨짐), Web UI에서는 elevation 표현을 위해 허용.

## 2. Components (Spec Only)

### 2.1 Button

| 상태 | 스타일 |
|------|-------|
| Default | bg `--color-brand`, text `--text-inverse`, radius `--radius-md`, padding `12px 20px` |
| Hover | bg `--color-brand-hover` |
| Focus | outline `2px solid --color-brand`, outline-offset `2px` |
| Pressed | bg `--color-brand-pressed`, translateY(1px) |
| Disabled | opacity 0.4, cursor not-allowed |

Variants: `primary` (위 default), `secondary` (border + text brand), `ghost` (text only), `danger` (brand 그대로).

### 2.2 Card

- Surface `--surface-base`, border `0.5px solid --border-subtle`, radius `--radius-lg`, padding `--space-5`.
- Optional top accent: `border-top: 2px solid --color-brand` (slide의 card 패턴과 일치).
- Hover: `--shadow-2`, `transform: translateY(-2px)`.

### 2.3 Panel / Section

- Surface `--surface-sunken` 또는 `--surface-base`.
- Heading + body grid: `grid-template-columns: 240px 1fr` (desktop), stack (mobile).
- Section divider: `0.5px solid --border-subtle`, `--space-6` 위아래 여백.

### 2.4 Code Block (Web)

- Light: bg `--surface-sunken`, border-left `2px solid --color-brand`, font `JetBrains Mono`, size 14, line-height 1.55.
- Dark: bg `#292929`, text `#e0e0e0`, border-left 동일.
- Inline code: padding `2px 6px`, radius `--radius-sm`, bg `--surface-sunken`.

### 2.5 Form Inputs (spec sketch)

- Height 40px, padding `0 12px`, radius `--radius-md`, border `1px solid --border-default`.
- Focus: border `--color-brand`, outline `2px rgba(238,0,0,0.2)`.
- Error: border `--color-danger`, helper text `--color-danger`.

## 3. Motion (Spec)

| 토큰 | 값 | 용도 |
|------|-----|------|
| `--motion-duration-fast` | 120ms | hover, focus ring |
| `--motion-duration-base` | 200ms | button press, card lift |
| `--motion-duration-slow` | 320ms | panel slide, dialog |
| `--motion-ease-standard` | `cubic-bezier(0.2, 0, 0, 1)` | 기본 |
| `--motion-ease-emphasized` | `cubic-bezier(0.3, 0, 0, 1)` | 강조 |

**원칙**

- 의미 있는 변화에만 motion (단순 장식 금지).
- `prefers-reduced-motion: reduce` 사용자에게는 duration 0 fallback.
- 슬라이드 산출물(PPT)에는 적용하지 않는다 — Web UI 한정.

## 4. States — Hover / Focus / Pressed / Disabled (Spec)

| 상태 | 처리 |
|------|------|
| Hover | 색상 1단계 어둡게 또는 elevation 1단계 상승 |
| Focus | 항상 visible. 2px outline + 2px offset. Keyboard 접근성 필수 |
| Pressed | 색상 2단계 어둡게 + translateY(1px) |
| Disabled | opacity 0.4, pointer-events none |
| Loading | spinner 또는 skeleton, 텍스트 라벨 유지 |
| Error | `--color-danger` border + helper text |

## 5. Accessibility (Spec)

- WCAG 2.1 AA 이상.
- 텍스트 대비 4.5:1 이상, 큰 텍스트(18pt+) 3:1 이상.
- 모든 인터랙티브 요소 keyboard 접근 가능, focus ring 가시.
- 색상에만 의존하지 않는 상태 표시 (아이콘/텍스트 병행).
- Touch target ≥ 44×44 px.

## 6. Backlog & Deferral

이 visual language를 **실제 코드로 구현하는 작업은 Phase 2 backlog**다. 우선순위와 의존성:

| 항목 | 우선순위 | 상태 | 비고 |
|------|----------|------|------|
| Web UI design token 패키지 (`design-tokens.json`) | P1 | deferred | 색/spacing/typography 토큰화 |
| 컴포넌트 라이브러리 선정 (Pat­ternFly / shadcn / 자체) | P1 | deferred | Red Hat은 PatternFly 가능성 검토 |
| Button / Card / Panel 1차 구현 | P2 | deferred | 토큰 패키지 선행 |
| Form / Input 컴포넌트 | P2 | deferred | |
| Motion 토큰 + 적용 | P3 | deferred | |
| Dark mode 토글 | P3 | deferred | 슬라이드 dark theme과 일관성 유지 |
| A11y audit (Axe / WAVE) | P2 | deferred | 구현과 병행 |

**Phase 2 진입 조건 (제안):**

1. 현재 PPT 파이프라인(`engine/html2pptx.js`)이 안정화되어 변경 빈도가 낮을 것.
2. Web UI를 두는 명확한 use case 확정 (예: 슬라이드 갤러리 web viewer, 에이전트 입력 UI 등).
3. 컴포넌트 라이브러리 정책(PatternFly 채택 여부 등) 결정.

## 7. Cross-Reference

- 슬라이드 색/폰트 single source of truth: `config.json`
- 한글 타이포 규칙: `themes/korean-typography.md` (Web UI도 이 규칙 상속)
- 슬라이드 라이트 테마: `themes/redhat-enterprise.md`
- 슬라이드 다크 테마: `themes/redhat-modern-dark.md`
- 워크숍 테마: `themes/redhat-workshop.md`

## 8. Acceptance (for this spec)

- 이 문서는 **spec / guideline / reference**임을 명시 ✅
- Web UI 구현이 **Phase 2 backlog로 deferred** 됨을 명시 ✅
- 색/spacing/typography/motion 토큰 정의 ✅
- Button / Card / Panel / 상태 spec 정의 ✅
- `config.json` 및 다른 theme 문서와의 cross-reference ✅
- PPT 파이프라인(`engine/html2pptx.js`)을 건드리지 않음 ✅
