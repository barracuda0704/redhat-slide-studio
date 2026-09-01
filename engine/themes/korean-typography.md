---
created: 2026-05-25
tags:
  - redhat-slide-skill
  - theme
  - typography
  - korean
---

# Theme: Korean Typography

Red Hat Korea 슬라이드의 한국어 타이포그래피 규칙. 한국어 지식 근로자와 개발자를 일차 독자로 가정하고, 줄바꿈/자간/행간을 안전하게 잡는다.

> 이 문서는 모든 `redhat-*` 테마에 상속되는 **공통 한글 타이포 기본기**다. 각 테마는 이 규칙을 위반하지 않는다.

## 1. 왜 별도 문서인가

라틴 타이포 디폴트를 그대로 쓰면 한국어 슬라이드에서 다음 문제가 발생한다:

- 단어 가운데에서 줄바꿈 ("OpenShift는 컨테이/너 플랫폼이다") → CJK에서 정상이지만 가독성 저하
- 영문/숫자가 섞인 문장에서 자간 들쭉날쭉
- `line-height: 1.2`로는 한글 받침 + 따옴표가 겹쳐 보임
- "꿰뚫다", "겹받침" 등 폰트 fallback이 깨지는 케이스

이 문서가 그 디폴트를 한국어 우선으로 재정의한다.

## 2. Font Stack

```css
:root {
  --font-ko: "Noto Sans KR", "Pretendard", "Apple SD Gothic Neo", "Malgun Gothic", system-ui, sans-serif;
  --font-mono: "JetBrains Mono", "D2Coding", "Pretendard", monospace;
}
body, .slide {
  font-family: var(--font-ko);
}
```

### 폰트 선택 근거

| 폰트 | 역할 | 비고 |
|------|------|------|
| `Noto Sans KR` | **1순위 (브랜드 요구사항 + Red Hat config 기본)** | `config.json`·엔진 기본, PPT 산출물에 적용 |
| `Pretendard` | 2순위 (HTML preview 보조) | 라틴+한글 통일감, 다양한 weight, 무료 |
| `Apple SD Gothic Neo` | macOS fallback | Keynote/PDF preview 호환 |
| `Malgun Gothic` | Windows fallback | PPT export 안전망 |
| `system-ui`, `sans-serif` | 마지막 안전망 | 환경 무관 fallback |

> `engine/html2pptx.js`와 `config.json`의 기본 폰트는 `Noto Sans KR`이다. HTML/CSS 우선순위도 `Noto Sans KR`을 1순위로 두어 HTML preview와 PPT 산출물의 시각 차이를 최소화한다.

## 3. 핵심 CSS 규칙 (NON-NEGOTIABLE)

```css
.slide, .slide * {
  /* 단어 단위로 줄바꿈 — 단어 중간을 자르지 않는다 */
  word-break: keep-all;

  /* 한 단어가 컨테이너보다 길면 어디서든 끊는다 (긴 URL, identifier 안전망) */
  overflow-wrap: anywhere;

  /* 자간: 한글은 기본 0, 라틴 섞이면 -0.005em ~ -0.01em */
  letter-spacing: -0.005em;

  /* 행간: 한글 받침을 위해 최소 1.35, 본문은 1.45 권장 */
  line-height: 1.35;
}

.slide p, .slide li {
  line-height: 1.45;
}

.slide h1, .slide h2, .slide h3, .slide .title {
  line-height: 1.3;
  letter-spacing: -0.015em; /* 큰 글자는 자간 조금 더 조임 */
}

/* 영문/숫자 강조 시 라틴 우선 폰트로 분리 */
.lat {
  font-family: "Inter", "Pretendard", sans-serif;
  letter-spacing: 0;
}
```

### 왜 `word-break: keep-all`인가

- 디폴트(`normal`)는 CJK 문자를 어디서든 끊어, "컨테이/너 플랫폼" 같은 분절이 발생.
- `keep-all`은 공백/문장부호에서만 줄바꿈 → 단어 보존.
- 단, 한 단어가 너무 길어 박스를 넘을 위험이 있어 `overflow-wrap: anywhere`로 안전망.

### 왜 `line-height: 1.35` 이상인가

- 한글은 받침(ᄀ, ᆨ, ᆪ 등) 때문에 글자 박스가 라틴보다 세로로 길다.
- `1.2`는 받침과 다음 줄 따옴표/괄호가 겹친다.
- 본문은 `1.45`, 제목/짧은 라벨은 `1.3` 정도가 안정적.

## 4. 줄바꿈 규칙

### 4.1 자동 줄바꿈 (CSS에 위임)

대부분의 경우 위 CSS만 적용하면 한국어 자동 줄바꿈은 문제가 없다.

### 4.2 수동 줄바꿈

긴 제목/카피는 의미 단위로 직접 끊는다. `<br>` 또는 줄바꿈을 의미 단위로 둔다.

```html
<!-- ❌ 어색 -->
<h1>엔터프라이즈를 위한 컨테이너 플랫폼 도입 전략과 거버넌스 가이드</h1>

<!-- ✅ 의미 단위 끊기 -->
<h1>엔터프라이즈를 위한<br>컨테이너 플랫폼 도입 전략</h1>
<p class="subtitle">거버넌스와 운영 가이드</p>
```

### 4.3 끊지 말아야 할 위치

- 조사 앞 ("플랫폼<br>은" ❌)
- 숫자 + 단위 사이 ("3<br>개월" ❌)
- 영문 product name 중간 ("Open<br>Shift" ❌)

이런 케이스는 `<span style="white-space: nowrap">3개월</span>` 또는 `<span class="lat">OpenShift</span>`로 묶는다.

## 5. 자간 (letter-spacing)

| 상황 | 값 |
|------|-----|
| 한글 본문 (13pt) | `0` 또는 `-0.005em` |
| 한글 큰 제목 (24pt+) | `-0.015em` ~ `-0.02em` |
| 라틴/숫자 본문 | `0` |
| Eyebrow (대문자 라틴) | `0.08em` |
| 한글 + 라틴 혼용 | 한글 기준 `-0.005em` |

**금지 패턴**

- 한글 본문에 양수 자간 (`letter-spacing: 0.05em`) — 한글 가독성 망친다
- `letter-spacing: -0.05em` 같은 과도한 조임 — 받침 충돌

## 6. 한·영 혼용

영문 product name, 코드 식별자, 약어가 자주 섞인다. 다음 패턴을 권장:

```html
<p>
  <span class="lat">OpenShift</span>의 <span class="lat">GitOps</span> 기능은
  <span class="lat">ArgoCD</span> 기반으로 동작한다.
</p>
```

```css
.lat {
  font-family: "Inter", "Pretendard", "JetBrains Mono", sans-serif;
  font-feature-settings: "tnum" 1;
  letter-spacing: 0;
}
```

- 영문 단어는 라틴 폰트로 분리해 자간/베이스라인을 정돈.
- 약어/숫자 비중이 높은 카드는 카드 전체를 `.lat`로 둘 수도 있다.

## 7. 따옴표·구두점

- 한국어 본문에는 한글 따옴표("…", '…') 또는 한국어 인용부호 사용 권장.
- 코드/명령어는 `<code>`로 감싸 `monospace`로 격리 → 따옴표 혼란 방지.
- 마침표 다음 줄바꿈 후 공백은 1칸으로 충분 (markdown 기본 동작 신뢰).

## 8. Do / Don't

| ✅ Do | ❌ Don't |
|-------|---------|
| `word-break: keep-all` 전역 적용 | `word-break: break-all`로 단어 가운데 자르기 |
| `overflow-wrap: anywhere` 안전망 | 긴 URL이 박스 밖으로 흐르게 두기 |
| 본문 `line-height: 1.45` | 본문 `line-height: 1.2` (받침 겹침) |
| 한글 자간 0 ~ `-0.015em` | 한글 자간 `+0.05em` |
| 영문은 `.lat` 클래스로 분리 | 한 폰트로 한·영 강제 처리 |
| 의미 단위로 `<br>` 수동 줄바꿈 | 조사·단위·약어 중간에 줄바꿈 |
| 폰트 stack에 `Noto Sans KR` 1순위 | `Arial`, `Helvetica` 단독 사용 |

## 9. Acceptance

- 모든 슬라이드 컨테이너에 `word-break: keep-all`
- `overflow-wrap: anywhere` 폴백
- 본문 `line-height` ≥ `1.35` (권장 `1.45`)
- Font stack 1순위: `"Noto Sans KR"` (브랜드 요구사항 + PPT 산출물 기본)
- 한·영 혼용 시 라틴 부분은 `.lat`로 분리 가능

## 10. 참고

- Pretendard: https://github.com/orioncactus/pretendard
- Noto Sans KR: https://fonts.google.com/noto/specimen/Noto+Sans+KR
- CSS `word-break` 명세: https://developer.mozilla.org/en-US/docs/Web/CSS/word-break
- 한국어 타이포 가이드 (네이버 D2): https://d2.naver.com/helloworld
