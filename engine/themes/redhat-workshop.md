---
created: 2026-05-25
brand_mode: redhat
tags:
  - redhat-slide-skill
  - theme
  - workshop
---

# Theme: Red Hat Workshop

핸즈온 워크숍, enablement 세션, lab guide 발표용 테마. 단계 번호, 코드, facilitator note에 최적화.

## 1. Identity

| 속성 | 값 |
|------|-----|
| 톤 | Instructional, hands-on, scannable |
| 대상 | 파트너 엔지니어, 내부 SA enablement, 고객 워크숍 참가자 |
| 사용 시점 | Lab walkthrough, hands-on session, train-the-trainer |
| 캔버스 | `720pt × 405pt` |
| 베이스 | `redhat-enterprise.md` 상속, step/code 패턴 추가 |

## 2. Color Tokens

`redhat-enterprise.md`와 동일. 추가로:

```css
:root {
  --step-number-bg: #ee0000;
  --step-number-fg: #ffffff;
  --code-bg: #f2f2f2;       /* gray surface alt */
  --code-border: #e0e0e0;
  --note-bg: #fff4cc;       /* yellow-10, facilitator note */
  --note-border: #ffe072;   /* yellow-30 */
  --note-fg: #5f0000;
}
```

## 3. Typography

`redhat-enterprise.md` 베이스. Code block만 monospace로 분리:

| 역할 | size | weight | line-height |
|------|------|--------|-------------|
| Step number | 18pt | 900 | 1.0 |
| Step title | 18pt | 700 | 1.3 |
| Step body | 13pt | 400 | 1.45 |
| Code block | 12pt | 400 | 1.4 |
| Inline code | 12pt | 500 | inherit |
| Facilitator note | 11pt | 400 | 1.4 |

Code font stack: `"JetBrains Mono", "Fira Code", "D2Coding", "Noto Sans KR", monospace`.

## 4. Step Layout

핵심은 **"한 슬라이드 = 한 step"** 또는 **"한 슬라이드 = 2~3 sub-step"**. 절대 5개 이상 step을 한 슬라이드에 넣지 않는다.

### 4.1 단일 step layout

```html
<section class="slide">
  <header class="slide-header">
    <div class="eyebrow">LAB 03 · OPENSHIFT GITOPS</div>
    <h2 class="slide-title">ArgoCD Application 등록</h2>
  </header>

  <div class="step">
    <div class="step-num">04</div>
    <div class="step-body">
      <h3 class="step-title">Application 매니페스트 생성</h3>
      <p>대상 클러스터에 ArgoCD Application 리소스를 적용한다.</p>
      <pre class="code"><code>oc apply -f apps/demo-app.yaml
oc get applications -n openshift-gitops</code></pre>
    </div>
  </div>

  <aside class="note">
    <strong>Facilitator:</strong> 적용 후 ArgoCD UI에서 sync 상태를 확인시킨다.
    오류가 나면 RBAC 권한부터 점검.
  </aside>
</section>
```

```css
.step { display: grid; grid-template-columns: 44pt 1fr; gap: 14pt; }
.step-num {
  background: #ee0000; color: #ffffff;
  font-size: 18pt; font-weight: 900;
  width: 44pt; height: 44pt;
  display: flex; align-items: center; justify-content: center;
  border-radius: 4pt;
}
.step-title { font-size: 18pt; font-weight: 700; margin: 0 0 4pt; }
.code {
  background: #f2f2f2; border: 0.5pt solid #e0e0e0;
  border-left: 2pt solid #ee0000;
  padding: 10pt 12pt; margin: 8pt 0 0;
  font-family: "JetBrains Mono", "Noto Sans KR", monospace;
  font-size: 12pt; line-height: 1.4;
}
```

### 4.2 다단계 (2~3 step) layout

```html
<ol class="step-list">
  <li>
    <span class="step-num-sm">01</span>
    <div>
      <h4>Namespace 생성</h4>
      <code class="inline">oc new-project demo</code>
    </div>
  </li>
  <li>
    <span class="step-num-sm">02</span>
    <div>
      <h4>SCC 권한 부여</h4>
      <code class="inline">oc adm policy add-scc-to-user anyuid -z default</code>
    </div>
  </li>
</ol>
```

```css
.step-list { list-style: none; padding: 0; margin: 0; display: grid; gap: 10pt; }
.step-list li { display: grid; grid-template-columns: 28pt 1fr; gap: 10pt; align-items: start; }
.step-num-sm {
  background: #ee0000; color: #ffffff;
  font-size: 12pt; font-weight: 700;
  width: 28pt; height: 28pt;
  display: flex; align-items: center; justify-content: center;
  border-radius: 50%;
}
.inline {
  font-family: "JetBrains Mono", "Noto Sans KR", monospace;
  background: #f2f2f2; padding: 1pt 5pt; border-radius: 2pt; font-size: 12pt;
}
```

## 5. Code Block Handling

| 원칙 | 설명 |
|------|------|
| 라인 수 제한 | 한 슬라이드 code block 합쳐 **8라인 이하** |
| 한 줄 길이 | 약 **70자 이하** (`720pt - 50pt padding ≈ 670pt`에서 12pt monospace) |
| Long command | 백슬래시 `\\` 줄바꿈 또는 별도 슬라이드 분리 |
| 색 강조 | 키 부분만 `<mark>`로 `#ee0000` underline, 전체 syntax highlight는 지양 (PPT 변환에서 깨짐) |
| 출력 결과 | 별도 `.output` 박스로 분리 |

```html
<pre class="code"><code>oc create -f <mark>secret.yaml</mark> -n openshift-gitops</code></pre>
<div class="output">secret/git-creds created</div>
```

```css
.code mark { background: transparent; color: #ee0000; border-bottom: 1pt dashed #ee0000; }
.output {
  margin-top: 4pt;
  font-family: "JetBrains Mono", monospace; font-size: 11pt;
  color: #4d4d4d; padding: 6pt 12pt;
  border-left: 2pt solid #a3a3a3;
}
```

## 6. Facilitator Notes

발표 슬라이드에서 진행자가 봐야 할 hint, timing, troubleshooting을 별도 영역에 둔다. 학습자용 PDF에서는 제외할 수 있도록 클래스 `note`로 분리.

```html
<aside class="note">
  <strong>Facilitator:</strong> 이 단계에서 약 5분 소요.
  실패 시 <code>oc describe</code>로 이벤트 확인을 안내한다.
</aside>

<style>
.note {
  background: #fff4cc; border-left: 3pt solid #ffe072;
  color: #5f0000;
  padding: 8pt 10pt; font-size: 11pt; line-height: 1.4;
  margin-top: 10pt;
}
.note code { font-family: "JetBrains Mono", monospace; }
</style>
```

학습자 배포본 빌드 시 `display: none` 또는 `print` 제외 옵션을 둔다 (실행은 Phase 2 backlog).

## 7. Do / Don't

| ✅ Do | ❌ Don't |
|-------|---------|
| 슬라이드당 1 step 또는 sub-step 묶음 | 5개 이상 step을 한 슬라이드에 |
| Code 8라인 이하 | 한 슬라이드에 전체 yaml 붙여넣기 |
| Facilitator note는 `.note`로 분리 | 본문 안에 "(강사: ...)" 인라인 코멘트 |
| Long command는 줄바꿈 또는 분리 | 한 줄 100자 넘는 코드 |
| Step number `#ee0000` 강조 | 모든 step에 다른 색 사용 |

## 8. Acceptance

- 각 step에 번호 (`step-num` 또는 `step-num-sm`)
- Code block은 monospace + `#ee0000` left border
- Facilitator note는 `.note` 클래스 분리
- 캔버스 `720pt × 405pt`, padding `22pt/25pt`
- Solid 배경, gradient 금지
