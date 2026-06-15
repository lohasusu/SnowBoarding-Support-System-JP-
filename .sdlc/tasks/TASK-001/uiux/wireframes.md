---
document_id: "WF-TASK-001-v1.0"
title: "線框圖反向追溯 — snowboarding_support brownfield"
version: "1.0"
date: "2026-06-15"
author: "UIUX"
status: "Draft"
task_id: "TASK-001"
phase: "uiux"
mode: "brownfield-document"
source_documents:
  - "REQ-TASK-001-v1.0"
  - "FUNC-TASK-001-v1.0"
  - "web/templates/base.html"
  - "web/templates/index.html"
  - "web/templates/ski.html"
  - "web/templates/flight.html"
  - "web/templates/plan.html"
  - "web/templates/profile.html"
  - "web/templates/auth/login.html"
  - "web/templates/auth/register.html"
  - "web/static/js/ski.js"
  - "web/static/js/flight.js"
  - "web/static/js/plan.js"
  - "web/static/js/auth.js"
change_history:
  - version: "1.0"
    date: "2026-06-15"
    changes: "初始版本 — brownfield 反向追溯 7 個 PAGE + 1 個 LAYOUT。來源: 既有 HTML/JS。Pencil MCP 停用"
    author: "UIUX"
approval:
  reviewer: "PM"
  date: ""
  result: "Pending"
notes:
  - "**來源: 既有 HTML 反向追溯**（非新設計）"
  - "ASCII wireframe 為簡化示意，**權威來源為 templates/*.html 與對應 JS 動態片段**"
  - "Pencil MCP 停用（config.json.project.pencilMcp=false）— 不畫新視覺稿"
---

# 線框圖反向追溯 — snowboarding_support brownfield

> **模式**: brownfield-document — 從既有 Jinja2 templates + JS 動態片段反向萃取
> **權威來源**: `web/templates/` HTML 是真相基線；本文件只是文字化描述，**HTML 為準**
> **設計風格**: Bootstrap 5.3.3 default + custom.css 微調（藍色 brand + 地區 badge 色碼）
> **語系**: zh-TW（繁體中文，硬編碼）

---

## 1. 頁面清單

| PAGE-ID | 頁面名稱 | 路由 | 對應 FUNC | 模板 | 動態 JS | 登入要求 |
|---------|---------|------|-----------|------|---------|---------|
| LAYOUT-001 | AppLayout（共用佈局） | （所有頁繼承） | — | `base.html` | inline `<script>` (navbar user check) | — |
| PAGE-001 | 首頁 | `/` | （導航入口）| `index.html` | — | 否 |
| PAGE-002 | 雪票查詢 | `/ski` | FUNC-001..014 | `ski.html` | `ski.js` (SSE) | 是 |
| PAGE-003 | 機票查詢 | `/flight` | FUNC-015..019 | `flight.html` | `flight.js` (fetch + 篩選) | 是 |
| PAGE-004 | 整合查詢 | `/plan` | FUNC-020..021 | `plan.html` | `plan.js` (Promise.all) | 是 |
| PAGE-005 | 個人 / 收藏 | `/profile` | FUNC-041, 043..045 | `profile.html` | inline `<script>` | 是 |
| PAGE-006 | 登入 | `/login` | FUNC-028..030, 034, 036..040 | `auth/login.html` | `auth.js` + inline | 否 |
| PAGE-007 | 註冊 | `/register` | FUNC-022..027 | `auth/register.html` | `auth.js` | 否 |

---

## 2. LAYOUT-001: AppLayout（共用佈局）

**來源**: `web/templates/base.html`（190 行）

### 結構（區塊佈局）

```
┌──────────────────────────────────────────────────────────────┐
│ Skip Link（無障礙，焦點時顯示「跳到主要內容」）                  │
├──────────────────────────────────────────────────────────────┤
│ <header>                                                      │
│   <nav class="navbar navbar-dark bg-primary shadow-sm">       │
│     [🌨 SnowTrip Japan]                                       │
│     │ 雪票查詢  ✈ 機票查詢  ⊞ 整合查詢          [👤 登入]  │
│     │ (active 高亮 = 當前路由)                              │
│   </nav>                                                      │
├──────────────────────────────────────────────────────────────┤
│ <main id="main-content">                                      │
│   {% block content %}{% endblock %}                           │
│   ← 各頁面注入自己的 Content                                  │
│ </main>                                                       │
├──────────────────────────────────────────────────────────────┤
│ <footer class="bg-dark text-white">                           │
│   ┌─ SnowTrip Japan ─┬─ 功能 ─────┬─ 熱門地區 ────┐         │
│   │ logo + 簡介      │ 雪票       │ 北海道         │         │
│   │                  │ 機票       │ 長野           │         │
│   │                  │            │ 新潟           │         │
│   │                  │            │ 山形           │         │
│   └──────────────────┴────────────┴────────────────┘         │
│   © 2026 SnowTrip Japan．票價資料僅供參考...                 │
│ </footer>                                                     │
└──────────────────────────────────────────────────────────────┘
```

### Navbar 元件（COMP-001 候選）
- 來源: `base.html:79-126`
- 結構: Bootstrap `.navbar.navbar-expand-lg.navbar-dark.bg-primary.shadow-sm`
- Brand: `<a class="navbar-brand">` 含 `bi-snow` icon + "SnowTrip Japan"
- 主導航（左）: 3 個 `<li class="nav-item">`：雪票/機票/整合（每個帶 icon）
- 用戶選單（右）: 1 個 `<li>` 含 `<a id="nav-login-btn">`，預設 `href="/login"` 文字「登入」
- **動態行為**（`base.html:175-185` inline script）:
  - 載入時 `fetch('/api/auth/me')`，若 `ok=true` → `nav-user-label` 改為 username + `nav-login-btn.href` 改為 `/profile`
  - 失敗時靜默忽略（無提示）
- Active 狀態: Jinja2 條件 `{% if request.url.path == '/ski' %}active fw-semibold{% endif %}` + `aria-current="page"`
- Mobile: `navbar-toggler` 漢堡按鈕 + `<div class="collapse navbar-collapse" id="mainNav">`

### Footer 元件（COMP-002 候選）
- 來源: `base.html:134-168`
- 結構: `<footer class="bg-dark text-white pt-5 pb-4 mt-5">`
- 3 欄 grid (`col-md-4`): 品牌 / 功能列表 / 熱門地區列表
- 連結均用 `.text-white-50` 淡色 + `.footer-link:hover` → `#fff`（custom.css:78）
- 版權聲明: 置中小字

### Skip Link 元件（COMP-003 候選）
- 來源: `base.html:76` + `custom.css:2-14`
- 行為: 預設 `left: -9999px`；焦點時 `left: 0` 顯示
- 文字: 「跳到主要內容」（zh-TW 硬編碼）

### SEO 與 metadata（非 UI 元件，但影響 head）
- `<title>`、`<meta name="description">`、`<meta name="keywords">`、Open Graph、Twitter Card、JSON-LD schema.org/WebSite
- canonical / robots 由 Jinja2 block 控制
- 各頁面可 override `{% block title %}`、`{% block og_title %}` 等

---

## 3. PAGE-001: 首頁

**來源**: `web/templates/index.html`（178 行） | **路由**: `/`（無登入要求）

### Layer 1 — 結構

```
┌──────────────────────────────────────────────────────────────┐
│ [LAYOUT-001 Header / Navbar]                                  │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  HERO SECTION (gradient blue, snow pattern overlay)          │
│  ┌─────────────────────────────────────────┐               │
│  │           🌨️ SnowTrip Japan              │               │
│  │   一站式日本滑雪行程規劃                   │               │
│  │   查早鳥雪票  ・  找最便宜機票             │               │
│  │   [ 🏷  查雪票 ]  [ ✈ 找機票 ]              │               │
│  └─────────────────────────────────────────┘               │
│                                                              │
├──────────────────────────────────────────────────────────────┤
│  STATS BAR (bg-primary, 3 cols)                              │
│   40+ 日本雪場  │  6 主要地區  │  每日 資料更新              │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  FEATURES (container py-5, 3 cards)                          │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐                   │
│  │ 🏷 icon  │ │ ✈ icon  │ │ ⊞ icon   │                   │
│  │ 雪票查詢  │ │ 機票查詢 │ │ 整合查詢  │                   │
│  │ 介紹文字  │ │ 介紹文字 │ │ (即將推出 │                   │
│  │ [開始查詢]│ │ [搜尋機票]│ │  badge)  │                   │
│  └──────────┘ └──────────┘ └──────────┘                   │
│                                                              │
├──────────────────────────────────────────────────────────────┤
│  HOW TO USE (bg-light)                                       │
│  ① 選擇查詢類型 ② 輸入條件 ③ 查看結果 ④ 下載 Excel        │
├──────────────────────────────────────────────────────────────┤
│  HOT REGIONS (container py-5)                                │
│  ┌─北海道─┐ ┌─長野─┐ ┌─新潟─┐                            │
│  │🏔️ 富良野│ │⛷️ 白馬│ │🌨️ 苗場│                            │
│  └────────┘ └──────┘ └──────┘                            │
│  ┌─山形─┐ ┌─青森─┐ ┌─福島─┐                              │
│  │❄️ 藏王│ │🦌 八甲田│ │🌲 Alts│                            │
│  └──────┘ └──────┘ └──────┘                              │
├──────────────────────────────────────────────────────────────┤
│ [LAYOUT-001 Footer]                                           │
└──────────────────────────────────────────────────────────────┘
```

### Layer 2 — 元件配置

| 區塊 | 元件 | 來源 line | 說明 |
|------|------|----------|------|
| Hero | HeroSection (COMP-004) | `index.html:24-42` | gradient 背景 + h1 + lead + 雙 CTA |
| Stats | StatsBar (COMP-005) | `index.html:45-62` | bg-primary + 3 等分 col + 數字大字 |
| Features | FeatureCard (COMP-006) | `index.html:69-122` | 3 個 card-hover，第 3 個 `opacity-65` + disabled |
| How-To | StepGrid (inline) | `index.html:127-148` | Jinja2 for-loop 4 步驟 |
| Regions | RegionCard (COMP-007) | `index.html:151-175` | Jinja2 for-loop 6 地區 |

### Layer 3 — 互動與 UI 文字

| 元件 | 互動 | UI 文字 (zh-TW) |
|------|------|----------------|
| Hero CTA「查雪票」| click → `/ski`（未登入 → 302 /login）| 「🏷 查雪票」 |
| Hero CTA「找機票」| click → `/flight` | 「✈ 找機票」 |
| FeatureCard hover | card 上浮 4px + 陰影增強（custom.css:32-37）| - |
| FeatureCard 第 3 張 | disabled state（`opacity-65` + `<button disabled>`）| 標題後 badge「即將推出」、按鈕「敬請期待」|
| RegionCard click | → `/ski?region={region}` | 6 地區: 北海道/長野/新潟/山形/青森/福島 |

### Layer 4 — 響應式

| 斷點 | 行為 | 來源 |
|------|------|------|
| `<576px` | hero `.display-4` 縮為 `2rem`、`.lead` 縮為 `1rem` | custom.css:96-99 |
| `<768px` | features card stack 為 1 欄（`col-md-4` → 全寬）| Bootstrap |
| `<768px` | hot regions 從 3 欄變 2 欄（`col-6 col-md-4`）| `index.html:162` |
| navbar `<lg` | 漢堡選單摺疊 | Bootstrap |

### Layer 5 — 多狀態

| 狀態 | 描述 | 觸發 |
|------|------|------|
| default | 上述完整佈局 | 預設 |
| navbar 已登入 | navbar 右側「登入」改為 username（JS 改 nav-user-label）| `/api/auth/me` 回 ok=true |
| 第 3 張 card disabled | 視覺淡化 + 按鈕 disabled + badge「即將推出」 | 永久狀態（DESIGN.md 已說明，**註**: 實際 `/plan` 路由已上線，此 disabled card 與真相不符，是既有 brownfield 不一致）|

> **[BROWNFIELD-INCONSISTENCY: 首頁第 3 張 features card 仍標「即將推出」+ disabled，但 `/plan` 路由 production 已運作。屬於既有 brownfield 不一致，留後續 TASK 修正]**

---

## 4. PAGE-002: 雪票查詢

**來源**: `web/templates/ski.html`（98 行）+ `web/static/js/ski.js`（181 行） | **路由**: `/ski`（須登入）

### Layer 1 — 結構（靜態 HTML 部分）

```
┌──────────────────────────────────────────────────────────────┐
│ [LAYOUT-001 Header / Navbar (active=雪票)]                    │
├──────────────────────────────────────────────────────────────┤
│ container py-4                                                │
│   <nav 麵包屑> 首頁 / 雪票查詢                                │
│                                                              │
│   <h1>雪票查詢</h1>                                          │
│   <p text-muted>查詢日本各雪場早鳥票、一般票價格（資料每日更新）│
│                                                              │
│  ┌─ Card: 搜尋條件 ─────────────────────────────────────┐ │
│  │ 🔻 搜尋條件                                            │ │
│  │ ┌─地區────┐ ┌─雪場名稱(選填)──┐ ┌─[查詢]─[Excel]──┐ │ │
│  │ │ 全部地區▾│ │ 例: Furano、白馬│ │   按鈕區          │ │
│  │ └─────────┘ └─────────────────┘ └─────────────────┘ │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                              │
│  ┌─ Results container（動態填入）──────────────────────┐  │
│  │ (預設空狀態 — 詳見 Layer 5)                          │  │
│  └────────────────────────────────────────────────────┘  │
├──────────────────────────────────────────────────────────────┤
│ [LAYOUT-001 Footer]                                           │
└──────────────────────────────────────────────────────────────┘
```

### Layer 2 — 元件配置

| 區塊 | 元件 | 來源 |
|------|------|------|
| 麵包屑 | Breadcrumb (COMP-008) | `ski.html:34-40` |
| 搜尋 form | SearchForm-Ski (COMP-009) | `ski.html:46-83` |
| → region select | Select (Bootstrap form-select) | `ski.html:55-63` |
| → name input | Input (Bootstrap form-control) | `ski.html:69` |
| → submit button | Button.btn-primary | `ski.html:73-75` |
| → download button | Button.btn-outline-secondary（初始 disabled）| `ski.html:76-79` |
| 結果區 | ResultsContainer (COMP-010) — 動態 | `ski.html:88-93` + `ski.js:32-103` |
| → table | ResultsTable (COMP-011) — JS 注入 | `ski.js:33-55` |
| → row | ResultRow-Ski (COMP-012) — JS 注入 | `ski.js:58-78` |
| → RegionBadge | RegionBadge (COMP-013) | `ski.js:71` + `custom.css:48-53` |
| → externalLink | LinkButton.btn-outline-secondary.btn-sm | `ski.js:62-66` |

### Layer 3 — 互動與 UI 文字

| 元件 | 互動 / 狀態 | UI 文字 |
|------|------------|---------|
| region select | 預設「全部地區」(value="")；6 個選項 | 「全部地區 / 北海道 / 長野 / 新潟 / 山形 / 青森 / 福島」 |
| name input | placeholder、autocomplete=off | placeholder「例：Furano、白馬」、label「雪場名稱（選填）」|
| submit button | submit → SSE EventSource | 「🔍 查詢」 |
| download button | 預設 disabled（aria-disabled=true）+ title「查詢後可下載 Excel」；查詢完成有結果後啟用 | 「⬇ Excel」 |
| results header | 動態顯示 | 「查詢結果 {N} 筆」+ 「已掃描 {done} / {total} 個雪場」 |
| 表頭 | 7 欄 | 「雪場 / 地區 / 票種（日文）/ 票種（中文）/ 票價 / 雪季 / 官網」 |

### Layer 4 — 響應式

| 斷點 | 行為 |
|------|------|
| `<576px` | 表單三欄變垂直堆疊（`col-sm-4` → full width）|
| `<768px` | results-table-wrap 仍可橫向 scroll（max-height: 60vh + overflow:auto，custom.css:67-69）|
| sticky 表頭 | thead th sticky top:0 z-index:2 始終可見（custom.css:71-75）|

### Layer 5 — 多狀態（**MANDATORY**）

#### State 1: 預設空狀態（初次進入）

```
┌─ Results container ────────────────────────┐
│            ⬆                                │
│      請選擇地區或輸入雪場名稱後按下查詢          │
│                                            │
└────────────────────────────────────────────┘
```
- 來源: `ski.html:88-93`
- 大號上箭頭 icon（`bi-arrow-up-circle fs-1 text-primary`）
- 提示文字: 「請選擇地區或輸入雪場名稱後按下查詢」

#### State 2: 查詢中（loading）

```
┌─ Results container ────────────────────────┐
│         ⟳ (spinner-border text-primary)     │
│      正在連線抓取票價，請稍候…              │
└────────────────────────────────────────────┘
```
- 來源: `ski.js:124-130`
- Bootstrap spinner + 文字「正在連線抓取票價，請稍候…」
- form submit button disabled

#### State 3: 有資料（data-loaded — SSE 漸進填入）

```
┌─ Results container ──────────────────────────────────────┐
│ 查詢結果 [42 筆]            已掃描 12 / 40 個雪場         │
│ ┌──────────────────────────────────────────────────────┐│
│ │ 雪場    │地區 │票種(日)│票種(中)│票價  │雪季 │官網   ││
│ ├──────────────────────────────────────────────────────┤│
│ │ 富良野  │北海道│大人1日券│一般成人 │6500 │24-25│ [↗] ││
│ │ ニセコ │北海道│ Adult  │ 大人   │8000 │24-25│ [↗] ││
│ │ 白馬    │長野 │ 1日券  │ 全日票 │5500 │24-25│ [↗] ││
│ │  ...                                                ││
│ └──────────────────────────────────────────────────────┘│
└──────────────────────────────────────────────────────────┘
```
- 來源: `ski.js:33-87`
- table-hover, table-striped, align-middle
- 地區欄使用彩色 region-badge
- 官網欄為小按鈕 `<a target="_blank">` 含 `bi-box-arrow-up-right` icon
- 表頭 sticky；results-table-wrap max-height: 60vh
- header 含進度: 「已掃描 {resortDone} / {resortTotal} 個雪場」

#### State 4: 查無資料（done event 時 resultCount=0）

```
┌─ Results container ────────────────────────┐
│ ⚠️ 沒有找到符合條件的資料，請嘗試其他地區或名稱。│
└────────────────────────────────────────────┘
```
- 來源: `ski.js:97-103, 157`
- `.alert.alert-warning` + `bi-info-circle-fill` icon
- 文字: 「沒有找到符合條件的資料，請嘗試其他地區或名稱。」

#### State 5: 錯誤（SSE error / 連線中斷）

```
┌─ Results container ────────────────────────┐
│ ⚠️ 查詢失敗：查詢進行中，請稍後再試           │
└────────────────────────────────────────────┘
```
- 來源: `ski.js:89-95`
- `.alert.alert-danger` + `bi-exclamation-triangle-fill` icon
- 文字: 「查詢失敗：{動態 error msg}」
  - 可能訊息: 「查詢進行中，請稍後再試」/「查詢逾時（45 秒），請縮小範圍後重試」/「連線中斷，請重試」/任意 backend 訊息

#### State 6: Excel 下載（無新 UI — 觸發瀏覽器下載）

- 來源: `ski.js:178-180` `window.location.href = '/api/ski/download?...'`
- 失敗時瀏覽器顯示 HTTP 429 plain text 或 500 plain text
- **[BROWNFIELD-GAP: Excel 下載失敗無 UI 提示 — 改 location.href 無 catch]**

> **註**: 本頁**無新增/編輯/刪除/檢視權限**狀態 — 純讀取操作。

---

## 5. PAGE-003: 機票查詢

**來源**: `flight.html`（125 行）+ `flight.js`（251 行） | **路由**: `/flight`（須登入）

### Layer 1 — 結構

```
┌──────────────────────────────────────────────────────────────┐
│ [LAYOUT-001 Header (active=機票)]                             │
├──────────────────────────────────────────────────────────────┤
│ container py-4                                                │
│   <nav 麵包屑> 首頁 / 機票查詢                                │
│   <h1>機票查詢</h1>                                          │
│   <p text-muted>搜尋台灣出發、前往日本滑雪地區的最低票價       │
│                                                              │
│  ┌─ Card: 搜尋條件 ────────────────────────────────────┐  │
│  │ 🔻(info) 搜尋條件                                     │  │
│  │ ┌出發機場▾┐┌目的地▾┐┌出發日期┐┌回程選填┐┌人數┐[🔍]│  │
│  │  說明: ℹ 機票資料來自 Google Flights ...              │  │
│  └────────────────────────────────────────────────────┘  │
│                                                              │
│  ┌─ Results container（動態）─────────────────────────┐    │
│  │ (預設空狀態 - 飛機 icon + 提示)                       │    │
│  └──────────────────────────────────────────────────┘    │
├──────────────────────────────────────────────────────────────┤
│ [LAYOUT-001 Footer]                                           │
└──────────────────────────────────────────────────────────────┘
```

### Layer 2 — 元件配置

| 區塊 | 元件 | 來源 |
|------|------|------|
| 搜尋 form | SearchForm-Flight (COMP-014) | `flight.html:51-110` |
| → 5 個 input | Select × 2 (origin/dest), DateInput × 2, NumberInput × 1 | `flight.html:54-94` |
| 結果 - 結果摘要列 | ResultSummary-Flight (COMP-015) | `flight.js:141-160` |
| → backend badge | BackendBadge (COMP-016) | `flight.js:144-149` (success/warning 變體) |
| → Google Flights 驗證 link | ExternalLinkButton | `flight.js:152-155` |
| → 下載 Excel button | DownloadButton (COMP-017) | `flight.js:156-159` + `flight.js:206-230` |
| 篩選列 | AirlineFilter (COMP-018) | `flight.js:164-173` |
| → 全部 button + 各航空 button (toggle) | FilterChip (COMP-019) | `flight.js:127-129` |
| 結果表格 | ResultsTable-Flight (COMP-020) | `flight.js:175-189` |
| → row | ResultRow-Flight (COMP-021) | `flight.js:109-123` |
| → 停留 badge | StopsBadge (COMP-022) | `flight.js:110-112` (success=直飛 / warning=N轉) |

### Layer 3 — 互動與 UI 文字

| 元件 | 行為 | UI 文字 |
|------|------|---------|
| origin select | 4 機場 | 「台北桃園 (TPE) / 台北松山 (TSA) / 高雄 (KHH) / 台中 (RMQ)」 |
| destination select | 7 目的地 + data-name | 「北海道 新千歲 (CTS) / 東京 成田 (NRT) / 東京 羽田 (HND) / 大阪 關西 (KIX) / 大阪 伊丹 (ITM) / 名古屋 中部 (NGO) / 沖繩 那霸 (OKA)」 |
| departure | required + min=today (JS 動態設定) | label「出發日期」 |
| ret-date | min=departure 同步 | label「回程（選填）」 |
| adults | type=number min=1 max=9 預設 1 | label「人數」 |
| submit | btn-info | 「🔍 搜尋」(md 以上含文字、sm 以下只有 icon) |
| 說明 | info 小提示 | 「ℹ 機票資料來自 Google Flights，價格為即時查詢，僅供參考。」 |
| 結果 header | h5 + badge | 「搜尋結果 {filtered} / {total} 筆」+ backend badge |
| Google Flights 連結 | 新分頁 | 「↗ Google Flights 驗證」+ title「在 Google Flights 驗證資料正確性」|
| 下載 Excel | 產生 blob | 「⬇ 下載 Excel」/ 載入中「⟳ 產生中…」 |
| airline filter「全部」| 清除 activeAirlines Set | 「全部」（active 時 btn-info 反白）|
| 航空 chips | toggle add/delete in Set | 動態（如「中華航空」「長榮航空」）|
| 來回程提示 | 條件性顯示（isRoundtrip）| 「ℹ 票價為**去回程合計**，回程班次詳情請點右上角「Google Flights 驗證」查看」 |
| 表頭 | 7 欄含排序提示 icon | 「航空公司 / 航班號 / 出發 / 抵達 / 飛行時間 / 轉機 / 票價」 |

### Layer 4 — 響應式

| 斷點 | 行為 |
|------|------|
| `<576px` | form 全部變 col-sm-* full → 垂直堆疊 |
| `<768px` | submit button 只顯示 icon（`d-none d-md-inline ms-1`）|
| 表格 | results-table-wrap 同 ski 頁 |

### Layer 5 — 多狀態

#### State 1: 預設空狀態

```
┌─ Results container ────────────────────────┐
│             ✈ (大 icon)                     │
│       請輸入出發日期後按下搜尋                 │
└────────────────────────────────────────────┘
```
- 來源: `flight.html:114-119`
- text-muted, py-5 置中

#### State 2: 查詢中

```
┌─ Results container ────────────────────────┐
│         ⟳ (spinner-border text-info)        │
│      正在搜尋最低票價，請稍候…               │
└────────────────────────────────────────────┘
```
- 來源: `flight.js:234-240`

#### State 3: 有資料

```
┌────────────────────────────────────────────────────────────┐
│ 搜尋結果 [12 / 18 筆] [SerpAPI ✓]   [↗驗證] [⬇下載 Excel]    │
│ ℹ 票價為去回程合計，回程班次詳情請點右上角...（roundtrip 時） │
├────────────────────────────────────────────────────────────┤
│ 🔻 篩選航空：[全部] [中華] [長榮] [星宇] [國泰]               │
├────────────────────────────────────────────────────────────┤
│ ┌──────────────────────────────────────────────────────┐ │
│ │航空公司│航班號  │出發 ↑│抵達 │飛行時間│轉機 │ 票價 ↑   │ │
│ ├──────────────────────────────────────────────────────┤ │
│ │中華航空│CI-100→210│08:30│13:45│9h15m │[直飛]│NT$ 18,500│ │
│ │長榮航空│BR-150→202│09:10│14:30│9h20m │[1轉] │NT$ 16,200│ │
│ │ ...                                                  │ │
│ └──────────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────────┘
```
- 來源: `flight.js:140-190`
- backend SerpAPI = 綠色 ✓ badge；fast-flights = 黃色 badge

#### State 4: 查無資料

```
⚠️ 沒有找到符合條件的航班，請嘗試其他日期或目的地。
```
- 來源: `flight.js:91-97` alert-warning

#### State 5: 查無篩選結果

```
[表頭仍顯示]
[tbody 單列] | 沒有符合篩選條件的航班 |
```
- 來源: `flight.js:188`

#### State 6: 錯誤

```
❌ 搜尋失敗：{error}
```
- 來源: `flight.js:243-249` alert-danger

#### State 7: 缺 departure（client-side 驗證）

```
[window.alert dialog]
  ┌──────────────┐
  │ 請輸入出發日期 │
  │      [確定]   │
  └──────────────┘
```
- 來源: `flight.js:35`
- **[BROWNFIELD-NOTE: 使用 native window.alert 而非自製 toast — 視覺體驗較差]**

#### State 8: 下載中

```
[Button ⟳ 產生中…]（disabled）
```
- 來源: `flight.js:208-209`

---

## 6. PAGE-004: 整合查詢

**來源**: `plan.html`（114 行）+ `plan.js`（225 行） | **路由**: `/plan`（須登入；OAuth callback 直送此頁）

### Layer 1 — 結構

```
┌──────────────────────────────────────────────────────────────┐
│ [LAYOUT-001 Header (active=整合查詢)]                         │
├──────────────────────────────────────────────────────────────┤
│ container py-4                                                │
│   <nav 麵包屑> 首頁 / 整合查詢                                │
│   <h1>整合查詢</h1>                                          │
│   <p text-muted>輸入日期與地區，一次查機票 + 雪票             │
│                                                              │
│  ┌─ Card: 搜尋條件 (6 cols on md+) ──────────────────────┐ │
│  │ 出發機場▾  目的地▾  雪場地區▾  出發日期  回程選  人數 🔍 │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                              │
│  ┌─ Results container（動態：兩個 collapsible card）─────┐  │
│  │ 機票結果 [N 筆] [SerpAPI ✓]              ▼ collapse  │  │
│  │ 雪票結果 [M 筆]                            ▼ collapse  │  │
│  └──────────────────────────────────────────────────────┘  │
├──────────────────────────────────────────────────────────────┤
│ [LAYOUT-001 Footer]                                           │
└──────────────────────────────────────────────────────────────┘
```

### Layer 2 — 元件配置

| 區塊 | 元件 | 來源 |
|------|------|------|
| 搜尋 form | SearchForm-Plan (COMP-023) | `plan.html:48-101` |
| 結果 - 下載按鈕 | DownloadButton-Plan (COMP-024) | `plan.js:103-108` |
| 機票 card | CollapsibleCard-Flight (COMP-025) | `plan.js:144-167` |
| → header（bg-info）| 含 collapse toggle | `plan.js:146-150` |
| → body | ResultsTable-FlightShort (top 20) | `plan.js:154-164` |
| 雪票 card | CollapsibleCard-Ski (COMP-026) | `plan.js:169-191` |
| → header（bg-primary）| 含 collapse toggle | `plan.js:171-175` |
| → body | ResultsTable-SkiShort | `plan.js:179-189` |

### Layer 3 — 互動與 UI 文字

| 元件 | 行為 | UI 文字 |
|------|------|---------|
| origin / dest / region | 同 PAGE-002/003 但目的地僅 5 個（無沖繩、伊丹）| ✓ |
| departure | required + min=today | ✓ |
| submit button | Promise.all 並行 | 「🔍」 |
| 機票 card header | data-bs-toggle="collapse" data-bs-target="#flight-collapse" | 「✈ 機票結果 [backend badge] [N 筆] ▼」 |
| 雪票 card header | data-bs-toggle="collapse" data-bs-target="#ski-collapse" | 「🏷 雪票結果 [M 筆] ▼」 |
| 下載按鈕 | 兩者都無結果則不顯示 | 「⬇ 下載整合 Excel」/「⟳ 產生中…」 |
| 機票 table | 機票 top 20 筆（截斷）| 6 欄: 「航空公司 / 出發 / 抵達 / 飛行時間 / 轉機 / 票價」 |
| 雪票 table | 全部雪票（無截斷）| 5 欄: 「雪場 / 地區 / 票種 / 票價 / 官網」 |
| Collapse 預設 | 兩 card 都 `collapse show`（開啟）| - |

### Layer 4 — 響應式

| 斷點 | 行為 |
|------|------|
| `<576px` | 6 個搜尋欄垂直堆疊 |
| `<768px` | submit 變單獨一列 |

### Layer 5 — 多狀態

#### State 1: 預設空狀態

```
┌─ plan-results ──────────────────────────────┐
│            ⊞ (大 icon)                       │
│      請填寫搜尋條件後按下查詢                 │
└─────────────────────────────────────────────┘
```
- 來源: `plan.html:106-110`

#### State 2: 查詢中

```
⟳ 同時查詢機票與雪票，請稍候…
```
- 來源: `plan.js:91-96`

#### State 3: 兩者皆有資料

如 Layer 1 結構描述，兩個 collapsible card 並列。

#### State 4: 機票失敗，雪票成功（部分失敗）

```
[機票 card]
  card body:
  ⚠️ {flightErr message}（alert-warning）
[雪票 card] 正常顯示
```
- 來源: `plan.js:154`

#### State 5: 兩者都失敗

- 兩個 card 各顯示 alert-warning
- 「下載」按鈕**不出現**（`hasAny=false`）
- 來源: `plan.js:99-108`

#### State 6: 機票結果為空（API ok 但 data=[]）

```
[機票 card body] | 無航班結果 |
```
- 來源: `plan.js:164`

#### State 7: 雪票結果為空

```
[雪票 card body] | 無雪票結果（無設定 ticket_url 的雪場會略過）|
```
- 來源: `plan.js:189`

#### State 8: collapse 收合 / 展開

- 點 card-header → bootstrap collapse 動畫 toggle
- icon `bi-chevron-down` 不會反向旋轉（**[BROWNFIELD-MICRO-ISSUE: 缺旋轉動畫]**）

---

## 7. PAGE-005: 個人 / 收藏

**來源**: `web/templates/profile.html`（70 行） | **路由**: `/profile`（須登入；後端 `Depends(get_current_user)` 雙重保護）

### Layer 1 — 結構

```
┌──────────────────────────────────────────────────────────────┐
│ [LAYOUT-001 Header（navbar 右側顯示 username）]               │
├──────────────────────────────────────────────────────────────┤
│ container py-4                                                │
│                                                              │
│   <h1>我的帳號</h1>                                          │
│   <p text-muted>歡迎，{username}（{email}）                   │
│                                                              │
│                          [⤴ 登出]    ← justify-content-end   │
│                                                              │
│   <h2>♥ 收藏清單</h2>                                        │
│                                                              │
│  ┌─ 收藏 grid (col-md-6 各佔半) ─────────────────────────┐ │
│  │ ┌──────────────────────┐ ┌──────────────────────┐  │ │
│  │ │ [⛷ 雪票]  雪場 A     │ │ [✈ 機票]  TPE→CTS    │  │ │
│  │ │            [🗑刪]    │ │            [🗑刪]    │  │ │
│  │ │ 富良野 ／ 北海道 ／ 6500│ │ 08:30 → 13:45 ／ NT 18500│ │
│  │ │ 2026-06-10                │ │ 2026-06-05            │  │ │
│  │ └──────────────────────┘ └──────────────────────┘  │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                              │
├──────────────────────────────────────────────────────────────┤
│ [LAYOUT-001 Footer]                                           │
└──────────────────────────────────────────────────────────────┘
```

### Layer 2 — 元件配置

| 區塊 | 元件 | 來源 |
|------|------|------|
| Title | h1 + welcome 文字 | `profile.html:7-8` |
| Logout 按鈕 | LogoutButton (COMP-027) | `profile.html:10-14` |
| 收藏 grid | FavoritesGrid (COMP-028) | `profile.html:16-50` |
| → 空狀態 alert | EmptyAlert (Bootstrap alert-info) | `profile.html:18-19` |
| → favorite card | FavoriteCard (COMP-029) | `profile.html:22-48` |
|   → type badge | TypeBadge (ski=primary, flight=info)| `profile.html:28-30` |
|   → 刪除按鈕 | DeleteButton (COMP-030) | `profile.html:33-35` |

### Layer 3 — 互動與 UI 文字

| 元件 | 行為 | UI 文字 |
|------|------|---------|
| Logout button | onclick → fetch POST /api/auth/logout → location.href='/' | 「⤴ 登出」（btn-outline-danger btn-sm） |
| 空狀態 alert | 條件渲染 `{% if not favorites %}` | 「尚無收藏。在雪票或機票查詢結果中按下 ♡ 即可收藏。」 |
| FavoriteCard - type=ski | bg-primary badge | 「⛷ 雪票」 |
| FavoriteCard - type=flight | bg-info badge | 「✈ 機票」 |
| FavoriteCard - label | 顯示 label or 預設 | label 或「未命名」 |
| FavoriteCard - 雪票摘要 | Jinja2 條件 | `{resort} ／ {region} ／ {price}` |
| FavoriteCard - 機票摘要 | Jinja2 條件 | `{dep_time} → {arr_time} ／ NT$ {price}` |
| 刪除 button | onclick → confirm → DELETE → remove DOM | 「🗑」（btn-outline-danger btn-sm） |
| 確認 dialog | window.confirm（**Rule 11 不可逆操作**）| 「確定刪除此收藏？」 |
| robots meta | noindex | （不被搜尋引擎索引）|

### Layer 4 — 響應式

| 斷點 | 行為 |
|------|------|
| `<768px` | grid 變 1 欄（col-md-6 → 全寬）|

### Layer 5 — 多狀態

#### State 1: 空狀態

```
┌─ alert-info ──────────────────────────────────────────┐
│ 尚無收藏。在雪票或機票查詢結果中按下 ♡ 即可收藏。       │
└──────────────────────────────────────────────────────┘
```

#### State 2: 有資料

如 Layer 1 結構描述。

#### State 3: 刪除中 / 刪除確認

```
[window.confirm dialog]
  ┌──────────────────────┐
  │ 確定刪除此收藏？      │
  │       [取消] [確定]   │
  └──────────────────────┘
```
- **Rule 11 不可逆操作確認**: ✅ 已有 confirm dialog（既有 brownfield 已符合）
- 確認後立即從 DOM 移除 `.col-md-6`（樂觀 UI 更新）

#### State 4: 刪除失敗（隱性）

- 後端回非 ok → **DOM 不移除**，但**也無錯誤提示**
- **[BROWNFIELD-GAP: 刪除失敗無 UI 反饋；屬於既有設計缺口]**

#### State 5: 登出中

- 無 loading 提示（fetch 完成後直接 `location.href='/'`）

> **註**: 本頁無「編輯」/「新增」（收藏只能在搜尋結果頁產生，目前 brownfield 該入口缺失）。

---

## 8. PAGE-006: 登入

**來源**: `templates/auth/login.html`（110 行）+ `auth.js`（108 行）+ inline `<script>` | **路由**: `/login`（公開；已登入則 302 /profile）

### Layer 1 — 結構

```
┌──────────────────────────────────────────────────────────────┐
│ [LAYOUT-001 Header]                                           │
├──────────────────────────────────────────────────────────────┤
│ container py-5 max-width:420px                                │
│  ┌─ Card shadow-sm border-0 ─────────────────────────────┐  │
│  │           🌨 登入                                       │  │
│  │                                                       │  │
│  │ [URL 參數 alert area — 動態]                           │  │
│  │                                                       │  │
│  │ ┌─ [G] 使用 Google 帳號登入 ─┐                        │  │
│  │ │  (btn-outline-danger lg)    │                        │  │
│  │ └──────────────────────────┘                        │  │
│  │                                                       │  │
│  │ ─────── 或使用帳號登入 ───────                         │  │
│  │                                                       │  │
│  │  Email 或使用者名稱                                    │  │
│  │  [_________________________________]                  │  │
│  │  密碼                                                 │  │
│  │  [_________________________________]                  │  │
│  │  [錯誤 alert area — 動態]                              │  │
│  │  [重寄驗證信 button — 條件顯示]                        │  │
│  │  ┌────── 登入 ──────┐                                │  │
│  │                                                       │  │
│  │ ─────────────                                         │  │
│  │ 還沒有帳號？立即註冊                                  │  │
│  └──────────────────────────────────────────────────────┘  │
├──────────────────────────────────────────────────────────────┤
│ [LAYOUT-001 Footer]                                           │
└──────────────────────────────────────────────────────────────┘
```

### Layer 2 — 元件配置

| 區塊 | 元件 | 來源 |
|------|------|------|
| 卡片容器 | AuthCard (COMP-031) | `login.html:10-58` |
| URL alert area | URLAlert-Login (COMP-032，動態) | `login.html:18` + inline JS `:62-74` |
| Google 登入按鈕 | GoogleLoginButton (COMP-033) | `login.html:21-31` |
| Divider | Divider (Bootstrap hr w/text) | `login.html:32-34` |
| 登入表單 | LoginForm (COMP-034) | `login.html:36-51` |
| → identifier input | Input | `login.html:38-39` |
| → password input | PasswordInput | `login.html:41-43` |
| → error alert | InlineErrorAlert (COMP-035) | `login.html:45` |
| → resend area | ResendVerificationArea (COMP-036) | `login.html:46-49` |
| → submit | Button.btn-primary.w-100 | `login.html:50` |
| Register link | TextLink | `login.html:53-55` |

### Layer 3 — 互動與 UI 文字

| 元件 | 行為 | UI 文字 |
|------|------|---------|
| 標題 | h4 + bi-snow icon | 「🌨 登入」 |
| Google 登入按鈕 | href="/api/auth/google/login"（含 Google logo SVG inline）| 「[G logo] 使用 Google 帳號登入」 |
| Divider | 中段文字 | 「或使用帳號登入」 |
| identifier input | type=text required autocomplete=username | label「Email 或使用者名稱」、placeholder「輸入 Email 或使用者名稱」 |
| password input | type=password required autocomplete=current-password | label「密碼」 |
| error alert | d-none 預設；JS 控制顯示 | 動態：401 = 「Email 或密碼錯誤」、403 = 「請先驗證您的 Email 後再登入...」、5xx = catch 訊息 |
| resend area | d-none 預設；403 時顯示 | 「重寄驗證信」(btn-outline-warning) |
| submit | type=submit；submitting 時 disabled | 「登入」 |
| Register link | <a href="/register"> | 「還沒有帳號？立即註冊」 |

### Layer 4 — 響應式

| 斷點 | 行為 |
|------|------|
| `<420px` | container max-width=420px 自適應 |
| 全斷點 | 卡片固定 max-width 420px 置中 |

### Layer 5 — 多狀態

#### State 1: 預設（無 URL 參數）

```
[卡片內容如 Layer 1]
[URL alert area 為空]
[error alert d-none]
[resend area d-none]
```

#### State 2: Email 驗證成功（?verified=1）

```
┌─ URL alert ─────────────────────────────────┐
│ ✅ Email 驗證成功！請登入您的帳號。           │ (alert-success)
└─────────────────────────────────────────────┘
```
- 來源: `login.html:66-67`

#### State 3: token 失效 / 已使用（?error=invalid_token / token_used）

```
┌─ URL alert ─────────────────────────────────┐
│ ❌ 驗證連結已失效或已使用，請重新寄送驗證信。 │ (alert-danger)
└─────────────────────────────────────────────┘
```
- 來源: `login.html:68-69`

#### State 4: token 過期（?error=token_expired）

```
┌─ URL alert ─────────────────────────────────┐
│ ⏰ 驗證連結已過期（24 小時），請重新寄送驗證信。│ (alert-warning)
└─────────────────────────────────────────────┘
```
- 來源: `login.html:70-71`

#### State 5: 未驗證導向（?error=unverified）

```
┌─ URL alert ─────────────────────────────────┐
│ 📧 請先驗證您的 Email 後再登入。              │ (alert-warning)
└─────────────────────────────────────────────┘
```
- 來源: `login.html:72-73`

#### State 6: OAuth 各種錯誤（?error=oauth_state_mismatch / google_denied / google_token_failed / google_userinfo_failed）

- **[BROWNFIELD-GAP: 上述 OAuth 錯誤碼無對應 alert 訊息 — 用戶看不到任何提示]**
- 來源缺漏: `login.html:62-74` 的 inline JS 條件只覆蓋 4 個 case

#### State 7: 認證失敗（API 401）

```
[error alert 顯示]
┌─ alert-danger ──────────────────────────────┐
│ Email 或密碼錯誤                              │
└─────────────────────────────────────────────┘
```
- 來源: `auth.js:34-39`
- submit button 重新 enable

#### State 8: 未驗證 email（API 403）

```
[error alert 顯示]
┌─ alert-danger ──────────────────────────────┐
│ 請先驗證您的 Email 後再登入...                │
└─────────────────────────────────────────────┘
[resend area 顯示]
┌─ Button btn-outline-warning ────────────────┐
│  重寄驗證信                                  │
└─────────────────────────────────────────────┘
```
- 來源: `auth.js:29-33` 自動 remove d-none from resend-area

#### State 9: 重寄驗證信中

```
[resend button] 寄送中... (disabled)
```
- 來源: `login.html:87-88`

#### State 10: 重寄驗證信成功 / 失敗

```
[error alert 區（變色）]
- 成功: alert-info「驗證信已寄出」(json.message)
- 失敗: alert-danger「{message}」
```
- 來源: `login.html:96-99`

#### State 11: identifier 不含 @（用戶試圖重寄但用 username）

```
[window.alert]
  請在上方輸入您的 Email（重寄驗證信需要 Email，不是使用者名稱）
```
- 來源: `login.html:82-86`

#### State 12: 登入中

- submit button disabled
- 來源: `auth.js:19, 41`

---

## 9. PAGE-007: 註冊

**來源**: `templates/auth/register.html`（58 行）+ `auth.js`（108 行） | **路由**: `/register`（公開）

### Layer 1 — 結構（form 模式）

```
┌──────────────────────────────────────────────────────────────┐
│ [LAYOUT-001 Header]                                           │
├──────────────────────────────────────────────────────────────┤
│ container py-5 max-width:420px                                │
│  ┌─ Card ─────────────────────────────────────────────────┐ │
│  │           🌨 建立帳號                                    │ │
│  │                                                       │ │
│  │  Email                                                │ │
│  │  [_________________________________]                  │ │
│  │  用戶名稱                                              │ │
│  │  [_________________________________]                  │ │
│  │  密碼（至少 8 字元）                                    │ │
│  │  [_________________________________]                  │ │
│  │  [錯誤 alert area — 動態]                              │ │
│  │  ┌────── 建立帳號 ──────┐                             │ │
│  │ ────────                                              │ │
│  │ 已有帳號？立即登入                                    │ │
│  └──────────────────────────────────────────────────────┘ │
├──────────────────────────────────────────────────────────────┤
│ [LAYOUT-001 Footer]                                           │
└──────────────────────────────────────────────────────────────┘
```

### Layer 1.5 — 結構（check-email 確認面板模式 — 註冊成功後）

```
┌─ Card ─────────────────────────────────────────────────┐
│           🌨 註冊成功                                    │
│                                                       │
│                  📧                                    │
│              驗證信已寄出                              │
│                                                       │
│  ℹ 已寄驗證信到：                                      │
│     user@example.com                                   │
│     請至信箱點擊「驗證我的帳號」按鈕...                 │
│                                                       │
│  • 連結有效期 24 小時                                  │
│  • 沒收到？檢查垃圾信件夾、或到登入頁用「重寄」按鈕      │
│  • 已驗證後可以用 Email 或使用者名稱登入                │
│                                                       │
│  ┌──── 回登入頁 ────┐                                 │
└────────────────────────────────────────────────────────┘
```

### Layer 2 — 元件配置

| 區塊 | 元件 | 來源 |
|------|------|------|
| 卡片容器 | AuthCard (COMP-031 重用) | `register.html:10-57` |
| 註冊表單 | RegisterForm (COMP-037) | `register.html:16-31` |
| → email input | Input type=email autocomplete=email required | `register.html:18-19` |
| → username input | Input type=text autocomplete=username required | `register.html:22-23` |
| → password input | Input type=password minlength=8 autocomplete=new-password required | `register.html:26-27` |
| → error alert | InlineErrorAlert (COMP-035 重用) | `register.html:29` |
| → submit button | Button.btn-primary.w-100 | `register.html:30` |
| Check-email 面板 | CheckEmailPanel (COMP-038) | `register.html:33-49` |
| Login link | TextLink | `register.html:52-54` |

### Layer 3 — 互動與 UI 文字

| 元件 | 行為 | UI 文字 |
|------|------|---------|
| Title | h4 + bi-snow icon；註冊成功後改為「註冊成功」 | 預設「建立帳號」/ 成功「註冊成功」(JS 改) |
| Email input | required type=email autocomplete=email | label「Email」 |
| Username input | required autocomplete=username | label「用戶名稱」 |
| Password input | required minlength=8 autocomplete=new-password | label「密碼（至少 8 字元）」 |
| Error alert | d-none → 顯示 | 動態：「密碼至少 8 個字元」/「Email 格式不正確」/「Email 或用戶名稱已被使用」 / catch 訊息 |
| Submit | submit → fetch POST /api/auth/register | 「建立帳號」 |
| Check-email panel | 註冊成功時顯示，form 隱藏 | （見 Layer 1.5）|
| Email addr | check-panel 中動態顯示用戶輸入的 email | （strong + text-break）|
| 回登入頁 | btn-outline-secondary | 「回登入頁」 |
| Login link | <a href="/login"> | 「已有帳號？立即登入」 |

### Layer 4 — 響應式

同 PAGE-006（max-width 420px 自適應）

### Layer 5 — 多狀態

#### State 1: 預設 form

```
[Form 完整顯示]
[CheckEmailPanel d-none]
[error alert d-none]
```

#### State 2: 提交中

- submit button disabled
- 來源: `auth.js:56`

#### State 3: 提交失敗

```
[error alert 顯示]
┌─ alert-danger ──────────────────────────────┐
│ {detail message}                              │
└─────────────────────────────────────────────┘
[submit button 重新 enable]
```
- 來源: `auth.js:80-83`

#### State 4: 提交成功 → 切換到 check-email 面板

```
[Form classList.add('d-none')]
[Divider d-none]
[Login link d-none]
[CheckEmailPanel classList.remove('d-none') — 詳見 Layer 1.5]
[Title 改為「註冊成功」]
```
- 來源: `auth.js:67-79`

---

## 10. 通用 UI 模式（跨頁面）

### Modal / Confirm Dialog

- **方式**: 全部使用 `window.confirm()` JS native dialog
- **位置**: PAGE-005 刪除收藏前
- **[BROWNFIELD-NOTE: 未使用 Bootstrap Modal — 視覺體驗較差但符合 Rule 11 不可逆操作確認]**

### Toast / Notification

- **方式**: 全部使用 `window.alert()` JS native dialog 或 inline `<div class="alert">` block
- **使用場景**: 收藏失敗、下載失敗、缺 departure 等
- **[BROWNFIELD-GAP: 未使用 Bootstrap Toast — 一致性差]**

### Drawer

- **不存在** — 本系統無 drawer 模式

### Dropdown Menu

- **不存在** — navbar 為平鋪式（mobile 用 collapse 漢堡選單）

---

## 11. UI 文字總覽（i18n 候選 — 詳見 i18n-keys.md）

> 所有 UI 文字硬編碼於 templates 與 JS，**未使用 i18n key**（NFR-015 zh-TW only）。i18n 候選列入 `uiux/i18n-keys.md`（建議 only）。

---

## 12. 追溯矩陣（PAGE → FUNC → FR）

| PAGE | FUNC | FR | 路由 |
|------|------|-----|------|
| LAYOUT-001 | — | FR-015, FR-016 | (繼承) |
| PAGE-001 | — | FR-016 | `/` |
| PAGE-002 | FUNC-001..014 | FR-001, FR-002, FR-003, FR-015, FR-016 | `/ski` |
| PAGE-003 | FUNC-015..019 | FR-004, FR-005, FR-015, FR-016 | `/flight` |
| PAGE-004 | FUNC-020..021 | FR-006, FR-015, FR-016 | `/plan` |
| PAGE-005 | FUNC-041, FUNC-043..045 | FR-013, FR-014, FR-015, FR-016 | `/profile` |
| PAGE-006 | FUNC-028..034, FUNC-036..040 | FR-008, FR-010, FR-011, FR-012, FR-016 | `/login` |
| PAGE-007 | FUNC-022..027 | FR-007, FR-010, FR-016 | `/register` |

---

## 13. Brownfield 已知問題 / 設計缺口

| ID | 問題 | 影響 | 後續處置 |
|----|------|------|---------|
| GAP-001 | 收藏入口缺失：`window.addFavorite` 已定義但 ski.js / flight.js 不呼叫 | 用戶無法新增收藏（FUNC-043 UI 入口）| 後續 TASK 補 ♡ 按鈕 |
| GAP-002 | Excel 下載失敗無 UI 反饋（ski 用 location.href 無 catch）| 用戶看到瀏覽器 plain text 錯誤 | 後續 TASK 改 fetch + alert |
| GAP-003 | OAuth 4 個錯誤 query 無對應 alert（state_mismatch / google_denied / google_token_failed / google_userinfo_failed）| 用戶看到登入頁但無錯誤提示 | 後續 TASK 補 alert |
| GAP-004 | 刪除收藏失敗靜默（無 alert）| 用戶以為刪除成功 | 後續 TASK 補 catch + alert |
| GAP-005 | 缺 departure 用 window.alert 而非自製 toast | 視覺體驗較差但功能正確 | 後續 TASK 改 Toast |
| INCONSIS-001 | 首頁 features card 仍標「即將推出」+ disabled，但 `/plan` 已上線 | 用戶混淆 | 後續 TASK 修正 |
| INCONSIS-002 | navbar 已登入時改 href 為 /profile 但仍顯示「登入」icon `bi-person-circle`（既符合「個人」語意）| 可接受 | 不修 |

---

## 14. 自我驗證

- [x] 8 個項目（1 LAYOUT + 7 PAGE）都有反向追溯描述
- [x] 每個 PAGE 都包含 5 個 Layer
- [x] Layer 5 涵蓋所有可能狀態（空 / loading / 有資料 / 錯誤 / 各種子狀態）
- [x] 每個元件描述都標來源 file:line
- [x] 來源**權威為 templates HTML**（已多次強調）
- [x] UI 文字以 zh-TW 完整列出（按鈕 / 標籤 / placeholder / error / tooltip 等）
- [x] 響應式行為記錄（斷點 + 行為）
- [x] [BROWNFIELD-GAP] / [INFERRED-FROM-MAIN] / [BROWNFIELD-NOTE] 標記
- [x] 追溯矩陣 PAGE → FUNC → FR
- [x] Pencil MCP 標記 skipped（無 .pen 引用）
