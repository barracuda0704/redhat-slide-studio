---
created: 2026-05-25
brand_mode: redhat
tags:
  - redhat-slide-skill
  - theme
  - dark
---

# Theme: Red Hat Modern Dark

기술 발표, 데모 무대, 키노트, 개발자 컨퍼런스용 어두운 변형. `redhat-enterprise.md`의 모든 규칙을 상속하되 surface만 다크로 뒤집는다.

## 1. Identity

| 속성 | 값 |
|------|-----|
| 톤 | Bold, technical, stage-ready |
| 대상 | 개발자 컨퍼런스, 데모 데이, AI/플랫폼 키노트 |
| 사용 시점 | Live demo, technical deep-dive, product launch |
| 캔버스 | `720pt × 405pt` (enterprise와 동일) |

## 2. Color Tokens

```css
:root {
  /* Brand (그대로 유지) */
  --brand-primary: #ee0000;
  --brand-secondary: #a60000;
  --brand-tertiary: #5f0000;

  /* Dark surface */
  --bg-base: #000000;
  --bg-elevated: #292929;   /* gray-80 */
  --bg-card: #1a1a1a;
  --border-dark: #4d4d4d;   /* gray-60 */

  /* Text on dark */
  --text-primary: #ffffff;
  --text-secondary: #e0e0e0; /* gray-20 */
  --text-muted: #a3a3a3;     /* gray-40 */

  /* Accents (대비 강한 톤 권장) */
  --accent-teal: #37a3a3;
  --accent-yellow: #ffe072;
  --accent-orange: #f5921b;
}
```

**Contrast 원칙**

- 본문 텍스트 vs 배경: WCAG AA (4.5:1) 이상. 다크에서는 `#ffffff` 또는 `#e0e0e0` 권장, `#a3a3a3`은 14pt 이상에만.
- `#ee0000`을 다크 배경(`#000000`)에 직접 올리면 chromatic aberration. 옆에 흰 텍스트나 라벨을 같이 두어 시각적 anchor 확보.
- Gradient 금지 원칙은 동일. Solid only.

## 3. Typography

`redhat-enterprise.md`와 동일. Font family: `Noto Sans KR`.

다크 배경에서는 weight를 한 단계 가볍게 운영해도 무방:

- Body 13pt: `400` → 가능하면 `400` 유지 (font-smoothing이 다크에서 더 굵게 보임)
- Slide title 26pt: `700` 유지

## 4. Layout & Spacing

`redhat-enterprise.md`와 완전히 동일. Padding `22pt/25pt`. `engine/html2pptx.js` default를 변경하지 않는다.

## 5. Component Patterns

### 5.1 Dark cover

```html
<section class="slide-dark">
  <div class="eyebrow">RED HAT SUMMIT KOREA · 2026</div>
  <h1 class="title">Agentic AI Platform</h1>
  <p class="subtitle">OpenShift AI와 함께하는 에이전트 개발 환경</p>
  <footer class="footer-dark">
    <span>Red Hat Korea</span><span>© Red Hat, Inc.</span>
  </footer>
</section>

<style>
.slide-dark {
  width: 720pt; height: 405pt;
  padding: 22pt 25pt;
  background: #000000;
  color: #ffffff;
  font-family: "Noto Sans KR", system-ui, sans-serif;
  display: flex; flex-direction: column; justify-content: space-between;
}
.slide-dark .eyebrow {
  color: #ee0000;
  font-size: 11pt; font-weight: 500; letter-spacing: 0.08em;
}
.slide-dark .title    { font-size: 32pt; font-weight: 700; line-height: 1.25; }
.slide-dark .subtitle { font-size: 16pt; font-weight: 400; color: #e0e0e0; line-height: 1.35; }
.footer-dark {
  display: flex; justify-content: space-between;
  font-size: 10pt; color: #a3a3a3;
  border-top: 0.5pt solid #4d4d4d; padding-top: 6pt;
}
</style>
```

### 5.2 Dark content card

```html
<article class="card-dark">
  <h3 class="card-title">에이전트 런타임</h3>
  <p class="card-body">OpenShift 위에서 agent harness를 정책 기반으로 격리한다.</p>
</article>

<style>
.card-dark {
  background: #1a1a1a;
  border: 0.75pt solid #4d4d4d;
  border-top: 2pt solid #ee0000;
  padding: 14pt;
  color: #ffffff;
}
.card-dark .card-title { font-size: 14pt; font-weight: 700; margin: 0 0 6pt; }
.card-dark .card-body  { font-size: 13pt; line-height: 1.45; color: #e0e0e0; }
</style>
```

### 5.3 Dark code block

```html
<pre class="code-dark"><code>oc apply -f agent-runtime.yaml
oc get pods -n agentic-ai</code></pre>

<style>
.code-dark {
  background: #292929;
  border: 0.5pt solid #4d4d4d;
  border-left: 2pt solid #ee0000;
  padding: 10pt 12pt;
  font-family: "JetBrains Mono", "Noto Sans KR", monospace;
  font-size: 12pt; line-height: 1.4;
  color: #e0e0e0;
}
</style>
```

## 6. Do / Don't

| ✅ Do | ❌ Don't |
|-------|---------|
| `#000000` 또는 `#5f0000`을 본문 배경으로 | `#ee0000`을 본문 전체 배경으로 |
| 흰 텍스트 + 빨강 강조 1~2개 | 빨강 텍스트를 검정 배경에 본문으로 |
| Code block은 `#292929` surface | 다크 위에 다크 카드 (대비 부족) |
| Footer 라인 색은 `#4d4d4d` | 흰색 라인으로 시선 분산 |

## 7. Acceptance

- `#ee0000` brand 일관성 유지 (라이트와 동일 hex)
- 배경 hex는 `#000000` / `#1a1a1a` / `#292929` / `#5f0000`만 허용
- 본문 텍스트 대비 4.5:1 이상
- 캔버스 `720pt × 405pt`, padding `22pt/25pt`
- Gradient 사용 금지
