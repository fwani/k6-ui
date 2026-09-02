# Performance Test UI — 디자인 가이드

> k6 + Playwright + InfluxDB + Grafana 기반 성능 테스트 플랫폼의 UI 디자인 시스템  
> **다크/라이트 테마 토글 지원 — CSS 변수 기반**

---

## 1. 디자인 방향

- **테마**: 다크/라이트 토글 지원. 기본값은 다크 (Grafana, k6 Web Dashboard와 일관성)
- **톤**: 산업용(industrial) — 화려함보다 데이터 가독성과 상태 인식 속도를 최우선
- **폰트**: 수치·코드는 monospace, 레이블·설명은 sans-serif 혼용
- **핵심 원칙**: 색상이 곧 의미다. 색을 장식에 쓰지 말 것
- **토글 방식**: `<html data-theme="dark|light">` 속성으로 전환

---

## 2. CSS 변수 시스템 (테마 통합)

모든 컴포넌트는 아래 CSS 변수만 참조한다. 하드코딩된 색상값은 액센트 색상(의미 고정)만 허용.

```css
/* ──────────────────────────────────────────
   다크 테마 (기본값)
────────────────────────────────────────── */
[data-theme="dark"] {
  /* 배경 레이어 */
  --bg-page:        #0d1117;   /* 전체 페이지 */
  --bg-surface:     #161b22;   /* 카드, 패널 */
  --bg-elevated:    #1c2128;   /* 모달, 드롭다운 */

  /* 테두리 */
  --border-default: rgba(255, 255, 255, 0.08);
  --border-emphasis:rgba(255, 255, 255, 0.14);

  /* 텍스트 */
  --text-primary:   #e6edf3;
  --text-secondary: #8b949e;
  --text-muted:     #484f58;

  /* 입력 필드 */
  --input-bg:       #161b22;
  --input-border:   rgba(255, 255, 255, 0.14);
  --input-text:     #e6edf3;

  /* 버튼 — Outline/Ghost */
  --btn-outline-text:   #e6edf3;
  --btn-ghost-text:     #8b949e;
  --btn-ghost-hover-bg: rgba(255, 255, 255, 0.06);

  /* 탭 스트립 */
  --tab-container-bg:   #161b22;
  --tab-active-bg:      #1c2128;
  --tab-active-border:  rgba(255, 255, 255, 0.08);

  /* 프로그레스 바 트랙 */
  --progress-track:     rgba(255, 255, 255, 0.08);

  /* 스파크라인 */
  --sparkline-opacity:  0.7;
}

/* ──────────────────────────────────────────
   라이트 테마
────────────────────────────────────────── */
[data-theme="light"] {
  /* 배경 레이어 */
  --bg-page:        #f4f6f8;   /* 전체 페이지 */
  --bg-surface:     #ffffff;   /* 카드, 패널 */
  --bg-elevated:    #f0f2f5;   /* 모달, 드롭다운 */

  /* 테두리 */
  --border-default: rgba(0, 0, 0, 0.08);
  --border-emphasis:rgba(0, 0, 0, 0.16);

  /* 텍스트 */
  --text-primary:   #1a1f2e;
  --text-secondary: #5a6272;
  --text-muted:     #9aa0ad;

  /* 입력 필드 */
  --input-bg:       #f4f6f8;
  --input-border:   rgba(0, 0, 0, 0.14);
  --input-text:     #1a1f2e;

  /* 버튼 — Outline/Ghost */
  --btn-outline-text:   #1a1f2e;
  --btn-ghost-text:     #5a6272;
  --btn-ghost-hover-bg: rgba(0, 0, 0, 0.05);

  /* 탭 스트립 */
  --tab-container-bg:   #e8eaed;
  --tab-active-bg:      #ffffff;
  --tab-active-border:  rgba(0, 0, 0, 0.08);

  /* 프로그레스 바 트랙 */
  --progress-track:     rgba(0, 0, 0, 0.08);

  /* 스파크라인 */
  --sparkline-opacity:  0.85;
}
```

---

## 3. 액센트 색상 (테마 무관 고정값)

의미가 고정된 색상이므로 CSS 변수로 분리하지 않고 직접 사용한다.  
단, 라이트 모드에서는 배경 opacity를 다크보다 낮게 조정한다.

| 이름 | Hex | 의미 / 사용처 |
|------|-----|---------------|
| `--accent-success` | `#00c97a` | 성공, k6 HTTP, "실행" 버튼 |
| `--accent-info`    | `#3b82f6` | 정보성 수치 (RPS, 연결 수 등) |
| `--accent-browser` | `#a855f7` | Playwright 브라우저 메트릭 |
| `--accent-warning` | `#f59e0b` | 경고, 임계값 초과 |
| `--accent-danger`  | `#ef4444` | 에러, 실패, "중단" 버튼 |

> 라이트 모드에서 `#00e5a0`은 배경이 밝아 대비가 부족하므로 `#00c97a`로 한 단계 어둡게 사용한다.

```css
:root {
  --accent-success: #00c97a;
  --accent-info:    #3b82f6;
  --accent-browser: #a855f7;
  --accent-warning: #f59e0b;
  --accent-danger:  #ef4444;
}
```

---

## 4. 테마 토글 구현

### HTML 설정
```html
<html data-theme="dark">
```

### 토글 버튼 JS
```js
function toggleTheme() {
  const html = document.documentElement;
  const next = html.dataset.theme === 'dark' ? 'light' : 'dark';
  html.dataset.theme = next;
  localStorage.setItem('theme', next);
}

// 초기 로드 시 저장값 복원
const saved = localStorage.getItem('theme') ?? 'dark';
document.documentElement.dataset.theme = saved;
```

### 시스템 설정 자동 감지 (선택)
```js
const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
const saved = localStorage.getItem('theme') ?? (prefersDark ? 'dark' : 'light');
document.documentElement.dataset.theme = saved;
```

---

## 5. 버튼 스타일

### 종류 및 용도

| 버튼 타입 | 배경 | 텍스트 색 | 사용 상황 |
|-----------|------|-----------|-----------|
| **Primary** | `var(--accent-success)` | `#ffffff` | 테스트 실행 등 주 액션 1개 |
| **Danger**  | `var(--accent-danger)`  | `#ffffff` | 테스트 중단, 삭제 |
| **Outline** | `transparent` | `var(--btn-outline-text)` | 보조 액션 |
| **Ghost**   | `transparent` | `var(--btn-ghost-text)`   | 이동 링크 |
| **Icon**    | `transparent` | `var(--btn-ghost-text)`   | 툴바 버튼 |

### CSS

```css
.btn {
  height: 36px;
  padding: 0 16px;
  border-radius: 7px;
  font-size: 13px;
  font-weight: 500;
  border: none;
  cursor: pointer;
  transition: all 0.15s;
  display: inline-flex;
  align-items: center;
  gap: 7px;
}
.btn:active { transform: scale(0.97); }

.btn-primary {
  background: var(--accent-success);
  color: #ffffff;
}
.btn-primary:hover { filter: brightness(1.1); }

.btn-danger {
  background: var(--accent-danger);
  color: #ffffff;
}
.btn-danger:hover { filter: brightness(1.1); }

.btn-outline {
  background: transparent;
  color: var(--btn-outline-text);
  border: 0.5px solid var(--border-emphasis);
}
.btn-outline:hover { background: var(--bg-elevated); }

.btn-ghost {
  background: transparent;
  color: var(--btn-ghost-text);
}
.btn-ghost:hover {
  background: var(--btn-ghost-hover-bg);
  color: var(--text-primary);
}

.btn-icon {
  width: 36px;
  padding: 0;
  justify-content: center;
  background: transparent;
  color: var(--btn-ghost-text);
  border: 0.5px solid var(--border-default);
}
.btn-icon:hover {
  color: var(--text-primary);
  border-color: var(--border-emphasis);
}
```

### 규칙
- 페이지당 Primary 버튼은 1개만
- Danger 버튼은 확인 다이얼로그 없이 단독 노출 금지
- 아이콘 버튼 크기는 36×36px 고정

---

## 6. 상태 표시 (Status Pills)

```
● Running   — var(--accent-success)  + 펄스 애니메이션 dot
● Idle      — var(--text-secondary)
● Failed    — var(--accent-danger)
● Warning   — var(--accent-warning)
● Browser   — var(--accent-browser)   (Playwright 전용)
● k6 Load   — var(--accent-info)      (k6 전용)
```

### CSS

```css
@keyframes pulse {
  0%, 100% { opacity: 1; }
  50%       { opacity: 0.4; }
}

.pill {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 3px 10px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 500;
}
.pill-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
}

/* Running */
.pill-running {
  background: rgba(0, 201, 122, 0.12);
  color: var(--accent-success);
}
.pill-running .pill-dot {
  background: var(--accent-success);
  box-shadow: 0 0 0 3px rgba(0, 201, 122, 0.2);
  animation: pulse 1.4s ease-in-out infinite;
}

/* Idle */
.pill-idle {
  background: rgba(90, 98, 114, 0.12);
  color: var(--text-secondary);
}
.pill-idle .pill-dot { background: var(--text-secondary); }

/* Failed */
.pill-error {
  background: rgba(239, 68, 68, 0.1);
  color: var(--accent-danger);
}
.pill-error .pill-dot { background: var(--accent-danger); }

/* Warning */
.pill-warning {
  background: rgba(245, 158, 11, 0.1);
  color: var(--accent-warning);
}
.pill-warning .pill-dot { background: var(--accent-warning); }
```

---

## 7. 메트릭 카드

```css
.metric-card {
  background: var(--bg-surface);
  border: 0.5px solid var(--border-default);
  border-radius: 10px;
  padding: 14px;
}
.metric-name  { font-size: 11px; color: var(--text-muted); }
.metric-value { font-size: 22px; font-weight: 500; font-family: monospace; }
.metric-sub   { font-size: 11px; color: var(--text-muted); margin-top: 4px; }

.metric-trend-up   { font-size: 11px; color: var(--accent-success); }
.metric-trend-down { font-size: 11px; color: var(--accent-danger); }
```

### 수치 색상 매핑

| 메트릭 | CSS 변수 |
|--------|----------|
| Response time, Latency | `var(--accent-success)` |
| RPS, Throughput | `var(--accent-info)` |
| Error rate | `var(--accent-danger)` |
| FCP, LCP, CLS (브라우저) | `var(--accent-browser)` |

### 스파크라인

```html
<svg width="100%" height="28" viewBox="0 0 100 28" preserveAspectRatio="none">
  <polyline
    points="0,22 20,16 40,12 60,8 80,6 100,4"
    fill="none"
    stroke="var(--accent-success)"
    stroke-width="1.5"
    opacity="var(--sparkline-opacity)"
  />
</svg>
```

---

## 8. 테스트 설정 폼

### 탭 스트립

```css
.tab-strip {
  display: flex;
  gap: 2px;
  background: var(--tab-container-bg);
  border-radius: 8px;
  padding: 3px;
}
.tab {
  padding: 5px 14px;
  border-radius: 6px;
  font-size: 12px;
  color: var(--text-secondary);
  background: none;
  border: none;
  cursor: pointer;
  transition: all 0.15s;
}
.tab.active {
  background: var(--tab-active-bg);
  border: 0.5px solid var(--tab-active-border);
  color: var(--text-primary);
  font-weight: 500;
}
.tab:hover:not(.active) { color: var(--text-primary); }
```

### 입력 필드

```css
.field input,
.field select {
  height: 32px;
  padding: 0 10px;
  border-radius: 6px;
  background: var(--input-bg);
  border: 0.5px solid var(--input-border);
  color: var(--input-text);
  font-size: 13px;
  font-family: monospace;
  width: 100%;
}
.field input:focus,
.field select:focus {
  outline: none;
  border-color: var(--accent-success);
}
```

### 프로그레스 바

```css
.progress-track {
  height: 4px;
  background: var(--progress-track);
  border-radius: 2px;
  overflow: hidden;
}
.progress-bar {
  height: 100%;
  background: linear-gradient(90deg, var(--accent-success), var(--accent-info));
  border-radius: 2px;
  transition: width 0.3s;
}
```

---

## 9. 레이아웃 원칙

1. **메트릭 카드 그리드**: `grid-template-columns: repeat(4, 1fr)` — 모바일은 2열
2. **설정 폼**: `grid-template-columns: 1fr 1fr` — 2열 배치
3. **간격**: 컴포넌트 간 `gap: 10~12px`, 섹션 간 `gap: 24px`
4. **패널 내부 패딩**: `padding: 20px 24px`
5. **구분선**: `border: 0.5px solid var(--border-default)` — 두꺼운 구분선 사용 금지

---

## 10. 컴포넌트 위계 요약

```
[data-theme="dark|light"]
  └─ 페이지 (var(--bg-page))
       └─ 섹션 패널 (var(--bg-surface), border 0.5px)
            ├─ 탭 스트립
            ├─ 메트릭 카드 그리드
            ├─ 설정 폼 (input/select)
            └─ 액션 바
                 ├─ [▶ 실행] Primary — var(--accent-success)
                 ├─ [■ 중단] Danger  — var(--accent-danger)
                 └─ 프로그레스 바   — success → info 그라디언트
```

---

## 11. 다크/라이트 색상 비교표

| 토큰 | 다크 | 라이트 |
|------|------|--------|
| `--bg-page` | `#0d1117` | `#f4f6f8` |
| `--bg-surface` | `#161b22` | `#ffffff` |
| `--bg-elevated` | `#1c2128` | `#f0f2f5` |
| `--text-primary` | `#e6edf3` | `#1a1f2e` |
| `--text-secondary` | `#8b949e` | `#5a6272` |
| `--text-muted` | `#484f58` | `#9aa0ad` |
| `--border-default` | `rgba(255,255,255,0.08)` | `rgba(0,0,0,0.08)` |
| `--border-emphasis` | `rgba(255,255,255,0.14)` | `rgba(0,0,0,0.16)` |
| `--accent-success` | `#00c97a` | `#00c97a` (동일) |

---

## 12. 금지 사항

- CSS 변수를 우회해 색상 하드코딩 금지 (액센트 색 제외)
- 3가지 이상 액센트 색을 한 화면에 동시 사용 금지
- Primary 버튼 2개 이상 동일 화면 배치 금지
- 테두리 두께 1px 초과 금지 (0.5px 원칙)
- 장식 목적의 그라디언트/그림자 금지 (프로그레스 바 제외)
- 라이트 모드에서 `#00e5a0` 직접 사용 금지 → `#00c97a` 사용

---

## 13. Vuetify 적용 가이드

> 이 프로젝트는 Vuetify 3를 사용한다. Vuetify는 자체 테마 시스템을 가지므로,  
> 위의 CSS 변수와 **Vuetify 테마를 연동**해야 디자인이 일관되게 적용된다.

### 13-1. Vuetify 테마 설정 (`plugins/vuetify.js`)

Vuetify의 `colors`를 디자인 가이드의 액센트 색으로 덮어씌운다.  
`primary` → success(초록), `error` → danger(빨강)로 매핑해 기존 `color="primary"` 코드를 그대로 유지한다.

```js
// plugins/vuetify.js
import { createVuetify } from 'vuetify'

const darkTheme = {
  dark: true,
  colors: {
    background:  '#0d1117',   // --bg-page
    surface:     '#161b22',   // --bg-surface
    primary:     '#00c97a',   // --accent-success  (실행 버튼)
    error:       '#ef4444',   // --accent-danger   (중단·삭제)
    warning:     '#f59e0b',   // --accent-warning
    info:        '#3b82f6',   // --accent-info
    secondary:   '#8b949e',   // --text-secondary  (복제 등 보조 버튼)
    'on-background': '#e6edf3',
    'on-surface':    '#e6edf3',
    'on-primary':    '#ffffff',
    'on-error':      '#ffffff',
  },
}

const lightTheme = {
  dark: false,
  colors: {
    background:  '#f4f6f8',
    surface:     '#ffffff',
    primary:     '#00c97a',
    error:       '#ef4444',
    warning:     '#f59e0b',
    info:        '#3b82f6',
    secondary:   '#5a6272',
    'on-background': '#1a1f2e',
    'on-surface':    '#1a1f2e',
    'on-primary':    '#ffffff',
    'on-error':      '#ffffff',
  },
}

export default createVuetify({
  theme: {
    defaultTheme: 'darkTheme',
    themes: { darkTheme, lightTheme },
  },
})
```

### 13-2. 테마 토글 (Vue 컴포넌트)

```vue
<script setup>
import { useTheme } from 'vuetify'

const theme = useTheme()

function toggleTheme() {
  theme.global.name.value =
    theme.global.name.value === 'darkTheme' ? 'lightTheme' : 'darkTheme'
  localStorage.setItem('theme', theme.global.name.value)
}

// 초기 로드 시 복원
const saved = localStorage.getItem('theme') ?? 'darkTheme'
theme.global.name.value = saved
</script>
```

### 13-3. 컴포넌트별 Vuetify prop 규칙

Vuetify 컴포넌트에 `color=`, `variant=` prop을 직접 쓸 때 아래 규칙을 따른다.  
임의의 hex를 `color`에 직접 넣지 말 것 — 테마 토글이 깨진다.

#### `v-btn`

| 용도 | color | variant | size |
|------|-------|---------|------|
| 테스트 실행 (Primary) | `primary` | `flat` | `small` |
| 테스트 중단·선택 삭제 | `error` | `flat` | `small` |
| 보조 액션 (새 시나리오 등) | 없음 | `outlined` | `small` |
| 텍스트 링크 (수정·실행·복제) | `primary` | `text` | `small` |
| 아이콘 버튼 (삭제 행) | 없음 | `text` | `small` |
| 위험도 낮은 보조 (모두 지우기) | 없음 | `text` | `small` |

```vue
<!-- 실행 버튼 -->
<v-btn color="primary" variant="flat" size="small" prepend-icon="mdi-play">
  테스트 실행
</v-btn>

<!-- 중단·삭제 버튼 — :disabled로 비활성 처리 -->
<v-btn color="error" variant="flat" size="small" :disabled="selectedIds.length === 0">
  선택 삭제 ({{ selectedIds.length }})
</v-btn>

<!-- 보조 액션 -->
<v-btn variant="outlined" size="small" prepend-icon="mdi-plus">
  새 테스트
</v-btn>

<!-- 행 내 텍스트 링크 -->
<v-btn :to="`/tests/${t.id}/edit`" variant="text" size="small" color="primary">수정</v-btn>
<v-btn :to="`/tests/${t.id}/run`"  variant="text" size="small" color="primary">실행</v-btn>
<v-btn variant="text" size="small" @click="cloneTest(t)">복제</v-btn>
```

#### `v-text-field` / `v-select`

```vue
<!-- 모든 입력 필드 공통 prop -->
density="compact"
variant="outlined"
hide-details="auto"
```

- `variant="outlined"` 고정 — `filled`·`underlined` 사용 금지 (배경 오염)
- `color="primary"` 추가 시 focus 링 색상이 `--accent-success`로 자동 적용됨

```vue
<v-text-field
  v-model="runHdr.bearer"
  label="Bearer 토큰 (선택)"
  type="password"
  density="compact"
  variant="outlined"
  color="primary"
  hide-details="auto"
/>

<v-select
  v-model="tagFilter"
  :items="tagOptions"
  label="태그"
  density="compact"
  variant="outlined"
  color="primary"
  hide-details
  clearable
  placeholder="전체"
  style="max-width: 220px; min-width: 160px"
/>
```

#### `v-chip` (태그)

```vue
<!-- outlined 대신 tonal로 변경 — 배경이 생겨 가독성 향상 -->
<v-chip
  v-for="tag in tagList(t).slice(0, 4)"
  :key="tag"
  size="x-small"
  variant="tonal"
  color="primary"
  label
>
  {{ tag }}
</v-chip>
```

#### `v-expansion-panels` (헤더 패널)

```vue
<!-- accordion + 테두리 제거로 깔끔하게 -->
<v-expansion-panels variant="accordion" elevation="0">
  <v-expansion-panel
    bg-color="surface"
    :rounded="true"
    style="border: 0.5px solid rgba(255,255,255,0.08)"
  >
```

#### `v-table` (테스트 목록)

Vuetify `v-table`은 자체 배경색을 가지므로 `bg-color="surface"`로 고정한다.

```vue
<v-table bg-color="surface" class="compact-table">
```

```css
/* scoped style — 헤더 강조 및 행 호버 */
.compact-table :deep(th) {
  font-size: 11px !important;
  color: var(--v-theme-on-surface) !important;
  opacity: 0.5;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  padding: 6px 10px !important;
  border-bottom: 0.5px solid rgba(255, 255, 255, 0.08) !important;
}
.compact-table :deep(td) {
  padding: 6px 10px !important;
  font-size: 13px;
  border-bottom: 0.5px solid rgba(255, 255, 255, 0.05) !important;
}
.compact-table :deep(tbody tr:hover td) {
  background: rgba(255, 255, 255, 0.03);
}
```

### 13-4. `code-chip` 스타일 개선

기존 `background: rgba(0,0,0,0.07)`은 다크 모드에서 거의 안 보인다.

```css
/* scoped style */
.code-chip {
  font-size: 0.82em;
  padding: 1px 6px;
  border-radius: 4px;
  font-family: ui-monospace, monospace;
  background: rgba(0, 201, 122, 0.1);   /* --accent-success tint */
  color: #00c97a;
  border: 0.5px solid rgba(0, 201, 122, 0.25);
}
```

### 13-5. TestList.vue 수정 체크리스트

파일을 수정할 때 아래 항목을 순서대로 확인한다.

- [ ] `plugins/vuetify.js`에 `darkTheme` / `lightTheme` 추가
- [ ] `v-btn color="error" variant="outlined"` → `variant="flat"` 으로 변경
- [ ] `v-btn color="primary" to="/tests/new"` → `variant="flat"` 추가
- [ ] `v-btn color="secondary"` (복제) → `color` 제거, `variant="text"` 유지
- [ ] 모든 `v-text-field` / `v-select`에 `variant="outlined" color="primary"` 추가
- [ ] `v-chip variant="outlined"` → `variant="tonal" color="primary"` 로 변경
- [ ] `v-table` → `bg-color="surface"` 추가
- [ ] `v-expansion-panels`에 `elevation="0"` 추가, 패널에 border 인라인 스타일 적용
- [ ] `.code-chip` 스타일 교체
- [ ] `.compact-table` scoped CSS에 헤더·행 스타일 추가