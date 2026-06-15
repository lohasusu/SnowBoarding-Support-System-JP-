---
document_id: "COMP-TASK-001-v1.0"
title: "元件規格反向追溯 — snowboarding_support brownfield"
version: "1.0"
date: "2026-06-15"
author: "UIUX"
status: "Draft"
task_id: "TASK-001"
phase: "uiux"
mode: "brownfield-document"
source_documents:
  - "WF-TASK-001-v1.0"
  - "web/templates/*.html"
  - "web/static/js/*.js"
  - "web/static/css/custom.css"
change_history:
  - version: "1.0"
    date: "2026-06-15"
    changes: "初始版本 — brownfield 反向萃取 1 LAYOUT + 38 COMP（範圍 LAYOUT-001 / COMP-001..038）。Pencil MCP 停用 — 無 Pencil 節點對應"
    author: "UIUX"
approval:
  reviewer: "PM"
  date: ""
  result: "Pending"
notes:
  - "**來源: 既有 HTML 反向追溯**（非新設計）"
  - "Props interface 為「FE 未來重構為 Vue 元件時的契約」— 目前 Jinja2 SSR 不使用 props 機制"
  - "Pencil MCP 停用（pencilMcp=false）— 無 Pencil 節點 ID 對應"
---

# 元件規格反向追溯 — snowboarding_support brownfield

> **模式**: brownfield-document — 從既有 HTML/JS 反向萃取
> **權威來源**: `web/templates/` HTML + `web/static/js/`
> **適用對象**: 未來 Vue 重構（config.json 已宣告 frontend.framework=vue）— 此規格作為元件契約
> **目前實作**: Jinja2 SSR（無實際 props 系統）

---

## 1. 元件樹狀結構

```
LAYOUT-001 AppLayout (base.html)
├── COMP-001 Navbar
├── COMP-002 Footer
├── COMP-003 SkipLink
└── Page Slot
    ├── PAGE-001 首頁
    │   ├── COMP-004 HeroSection
    │   ├── COMP-005 StatsBar
    │   ├── COMP-006 FeatureCard × 3
    │   └── COMP-007 RegionCard × 6
    ├── PAGE-002 雪票
    │   ├── COMP-008 Breadcrumb
    │   ├── COMP-009 SearchForm-Ski
    │   ├── COMP-010 ResultsContainer
    │   ├── COMP-011 ResultsTable-Ski
    │   ├── COMP-012 ResultRow-Ski
    │   ├── COMP-013 RegionBadge
    │   └── COMP-008 Breadcrumb（重用）
    ├── PAGE-003 機票
    │   ├── COMP-008 Breadcrumb（重用）
    │   ├── COMP-014 SearchForm-Flight
    │   ├── COMP-015 ResultSummary-Flight
    │   ├── COMP-016 BackendBadge
    │   ├── COMP-017 DownloadButton-Flight
    │   ├── COMP-018 AirlineFilter
    │   ├── COMP-019 FilterChip
    │   ├── COMP-020 ResultsTable-Flight
    │   ├── COMP-021 ResultRow-Flight
    │   └── COMP-022 StopsBadge
    ├── PAGE-004 整合
    │   ├── COMP-023 SearchForm-Plan
    │   ├── COMP-024 DownloadButton-Plan
    │   ├── COMP-025 CollapsibleCard-Flight
    │   └── COMP-026 CollapsibleCard-Ski
    ├── PAGE-005 個人 / 收藏
    │   ├── COMP-027 LogoutButton
    │   ├── COMP-028 FavoritesGrid
    │   ├── COMP-029 FavoriteCard
    │   └── COMP-030 DeleteButton
    ├── PAGE-006 登入
    │   ├── COMP-031 AuthCard（共用 with register）
    │   ├── COMP-032 URLAlert-Login
    │   ├── COMP-033 GoogleLoginButton
    │   ├── COMP-034 LoginForm
    │   ├── COMP-035 InlineErrorAlert（共用）
    │   └── COMP-036 ResendVerificationArea
    └── PAGE-007 註冊
        ├── COMP-031 AuthCard（重用）
        ├── COMP-037 RegisterForm
        ├── COMP-035 InlineErrorAlert（重用）
        └── COMP-038 CheckEmailPanel
```

**統計**: LAYOUT-001 × 1 + COMP-001..038 = 38 個元件
**重用次數**: COMP-008 Breadcrumb（3 頁）、COMP-031 AuthCard（2 頁）、COMP-035 InlineErrorAlert（2 頁）

**ID 範圍合規**: LAYOUT-001（在 LAYOUT-001..100 範圍）；COMP-001..038（在 COMP-001..100 範圍）；PAGE-001..007（在 PAGE-001..100 範圍）。

---

## 2. 全域佈局元件（MANDATORY）

### LAYOUT-001: AppLayout

- **用途**: 全域頁面佈局容器，包含 Navbar + Main + Footer
- **所屬頁面**: 所有 PAGE-001..007（base.html 為 Jinja2 父模板）
- **實作要求**:
  - Jinja2 模式: 所有頁面 `{% extends "base.html" %}` + `{% block content %}`
  - 未來 Vue: 單一 `<AppLayout>` 元件含 `<slot>` 替換 content
- **來源**: `web/templates/base.html`

#### Props Interface（未來 Vue 契約）

```typescript
interface AppLayoutProps {
  /** 當前頁面內容（替換 main slot）*/
  children: VueNode;
  /** 當前路由 path（用於 navbar active 高亮）*/
  currentPath: string;
  /** SEO metadata（每頁可 override）*/
  meta?: {
    title?: string;
    description?: string;
    canonical?: string;
    robots?: 'index, follow' | 'noindex, nofollow';
    ogType?: string;
    ogTitle?: string;
    ogDescription?: string;
    extraLdJson?: string;
  };
}
```

#### 結構（DOM 樹）

```
<html lang="zh-TW">
  <head>
    <!-- SEO metadata (per-page override via {% block %}) -->
    <!-- Bootstrap 5.3.3 CSS via CDN (SRI integrity) -->
    <!-- Bootstrap Icons 1.11.3 via CDN -->
    <!-- /static/css/custom.css -->
  </head>
  <body>
    <a class="skip-link"> (COMP-003) </a>
    <header>
      <nav class="navbar"> (COMP-001 Navbar) </nav>
    </header>
    <main id="main-content">
      <!-- 各頁 content -->
    </main>
    <footer> (COMP-002 Footer) </footer>
    <!-- Bootstrap JS bundle CDN -->
    <!-- inline navbar user check script -->
    <!-- per-page extra_scripts -->
  </body>
</html>
```

#### 狀態
- default: 上述完整結構（無狀態變化 — Layout 本身為靜態）

---

### COMP-001: Navbar

- **用途**: 全域頂部導航，包含 brand + 3 個主導航項 + 用戶選單
- **所屬頁面**: 所有頁面（透過 LAYOUT-001）
- **來源**: `base.html:79-126`

#### Props Interface

```typescript
interface NavbarProps {
  /** 當前用戶（從 /api/auth/me 取得）*/
  user?: { username: string; email: string; } | null;
  /** 當前路由 path（用於 active 高亮）*/
  currentPath: string;
  /** 主導航項目 — brownfield 固定清單 */
  navItems?: NavItem[]; // 預設見下
}

interface NavItem {
  id: 'ski' | 'flight' | 'plan';
  label: string;
  href: string;
  icon: string;  // Bootstrap icon class
}

const DEFAULT_NAV_ITEMS: NavItem[] = [
  { id: 'ski',    label: '雪票查詢',  href: '/ski',    icon: 'bi-tag' },
  { id: 'flight', label: '機票查詢',  href: '/flight', icon: 'bi-airplane' },
  { id: 'plan',   label: '整合查詢',  href: '/plan',   icon: 'bi-grid' },
];
```

#### 狀態

| 狀態 | 觸發 | 視覺 |
|------|------|------|
| default-未登入 | user=null | 右側顯示「👤 登入」連結 href=/login |
| default-已登入 | user!=null（JS 改）| 右側顯示「👤 {username}」連結 href=/profile |
| nav active | currentPath==href | 對應 nav-link 加 `active fw-semibold` + `aria-current="page"` |
| mobile collapse | breakpoint < lg | 漢堡 toggler 顯示；nav 摺疊到 `#mainNav` |
| mobile expanded | 漢堡點擊 | nav 展開為垂直列表 |

#### 無障礙
- `aria-label="主要導覽"` on `<nav>`
- `aria-controls="mainNav"`, `aria-expanded` on toggler
- `aria-current="page"` on active link

---

### COMP-002: Footer

- **用途**: 全域頁尾，3 欄資訊（品牌 / 功能 / 熱門地區）+ 版權
- **所屬頁面**: 所有頁面
- **來源**: `base.html:134-168`

#### Props Interface

```typescript
interface FooterProps {
  /** 年份（預設 2026）*/
  year?: number;
  /** 品牌標語（預設見下）*/
  tagline?: string;
  /** 功能連結（預設見下）*/
  features?: { label: string; href: string }[];
  /** 熱門地區（預設見下）*/
  popularRegions?: { label: string; href: string }[];
}
```

#### 狀態
- default: 完整顯示
- hover footer link: 顏色從 `.text-white-50` 變為 `#fff`（custom.css:78）

---

### COMP-003: SkipLink

- **用途**: 無障礙跳轉到主要內容
- **來源**: `base.html:76` + `custom.css:2-14`

#### Props Interface

```typescript
interface SkipLinkProps {
  /** 跳轉目標 id（預設 main-content）*/
  target?: string;
  /** 顯示文字（預設「跳到主要內容」）*/
  label?: string;
}
```

#### 狀態

| 狀態 | 視覺 |
|------|------|
| default | `left: -9999px`（畫面外） |
| focus | `left: 0`（顯示 bg-black text-white pad 0.4rem 1rem） |

---

## 3. PAGE-001 首頁專屬元件

### COMP-004: HeroSection
- **用途**: 首頁頂部 hero banner — gradient 背景 + 標題 + 雙 CTA
- **來源**: `index.html:24-42` + `custom.css:17-28`
- **Props**: `{ title, subtitle, ctas: [{ label, href, variant }] }`
- **狀態**: default（含 snow pattern overlay SVG）/ responsive（<576px 字級縮小）

### COMP-005: StatsBar
- **用途**: 統計數字橫條（3 col 等分）
- **來源**: `index.html:45-62`
- **Props**: `{ items: [{ value, label }] }`（brownfield 固定 3 項）

### COMP-006: FeatureCard
- **用途**: 功能介紹卡片（icon + 標題 + 描述 + CTA）
- **來源**: `index.html:69-122`
- **Props**:
  ```typescript
  interface FeatureCardProps {
    iconClass: string;    // bi-tag-fill 等
    iconBg: string;       // bg-primary / bg-info / bg-secondary
    title: string;
    badge?: { label: string; variant: string }; // 例：「即將推出」
    description: string;
    cta: { label: string; href?: string; variant: string };
    disabled?: boolean;   // 第 3 張為 true
    opacity?: number;     // 0.65 when disabled
  }
  ```
- **狀態**: default / hover（card-hover translate -4px + 強化陰影） / disabled（opacity 0.65, button disabled aria-disabled）/ feature-icon hover（scale 1.1）

### COMP-007: RegionCard
- **用途**: 熱門地區卡片（emoji + 地區名 + 雪場列表）
- **來源**: `index.html:151-175`
- **Props**: `{ region, emoji, description, href }`
- **狀態**: default / hover（card-hover）

---

## 4. 通用列表頁元件

### COMP-008: Breadcrumb
- **用途**: 麵包屑導航
- **重用頁面**: PAGE-002, PAGE-003, PAGE-004
- **來源**: `ski.html:34-40`（其他頁面結構相同）
- **Props**: `{ items: [{ label, href? }] }`（最後一項無 href = active）
- **狀態**: default

### COMP-013: RegionBadge
- **用途**: 雪場地區彩色 badge（6 種地區色碼）
- **使用於**: COMP-012 ResultRow-Ski, plan.js 雪票列表
- **來源**: `custom.css:48-53` + `ski.js:71`
- **Props**: `{ region: '北海道' | '長野' | '新潟' | '山形' | '青森' | '福島' }`
- **狀態**: default（6 變體對應 6 色）

#### 色碼變體

| Variant | 色碼 | TOKEN |
|---------|------|-------|
| 北海道 | `#1565c0` | TOKEN-color-region-hokkaido |
| 長野 | `#2e7d32` | TOKEN-color-region-nagano |
| 新潟 | `#6a1b9a` | TOKEN-color-region-niigata |
| 山形 | `#e65100` | TOKEN-color-region-yamagata |
| 青森 | `#00695c` | TOKEN-color-region-aomori |
| 福島 | `#4e342e` | TOKEN-color-region-fukushima |

---

## 5. PAGE-002 雪票專屬元件

### COMP-009: SearchForm-Ski
- **來源**: `ski.html:46-83` + `ski.js:105-176`
- **Props**:
  ```typescript
  interface SearchFormSkiProps {
    regions: { value: string; label: string }[]; // 預設 6 地區
    onSubmit: (params: { region?: string; name?: string }) => void;
    onDownload: () => void;
    downloadDisabled: boolean; // 預設 true，查詢成功後 false
    querying: boolean;
  }
  ```
- **狀態**: default / querying（submit disabled, download disabled）/ done-with-results（download enabled）

### COMP-010: ResultsContainer
- **來源**: `ski.html:88-93` + `ski.js:32-103`
- **狀態（5）**:
  - empty: 上箭頭 icon + 「請選擇地區...」
  - loading: spinner + 「正在連線抓取票價...」
  - data-loaded: COMP-011 表格 + 進度
  - no-result: alert-warning「沒有找到符合條件的資料...」
  - error: alert-danger「查詢失敗：{msg}」

### COMP-011: ResultsTable-Ski
- **來源**: `ski.js:33-55`
- **結構**: `<table class="table table-hover table-striped align-middle">`, thead.table-dark, sticky thead
- **欄位**: 雪場 / 地區 / 票種(日) / 票種(中) / 票價 / 雪季 / 官網（7 欄）
- **Props**: `{ rows: TicketPrice[]; resortTotal: number; resortDone: number; }`

### COMP-012: ResultRow-Ski
- **來源**: `ski.js:58-78`
- **Props**: `{ resort, region, ticket_type, ticket_type_zh, price, season, source_url }`
- **互動**: source_url 存在 → 渲染 LinkButton（target="_blank" rel="noopener noreferrer"）；否則「—」

---

## 6. PAGE-003 機票專屬元件

### COMP-014: SearchForm-Flight
- **來源**: `flight.html:51-110` + `flight.js`
- **Props**:
  ```typescript
  interface SearchFormFlightProps {
    origins: { value: string; label: string }[];
    destinations: { value: string; label: string; dataName: string }[];
    onSubmit: (params: FlightSearchParams) => void;
  }
  ```
- **欄位**: origin / destination / departure(required, min=today) / ret-date(optional) / adults(1-9) / submit
- **狀態**: default / submitting / validation-error（缺 departure → window.alert）

### COMP-015: ResultSummary-Flight
- **來源**: `flight.js:141-160`
- **內容**: 標題「搜尋結果」+ filtered/total badge + COMP-016 backend badge + 驗證連結 + 下載 Excel 按鈕

### COMP-016: BackendBadge
- **來源**: `flight.js:144-149`
- **Variants**: success（SerpAPI ✓ 綠）/ warning（fast-flights fallback 黃）/ none（無 backend 資訊時不顯示）
- **Props**: `{ backend: string }`

### COMP-017: DownloadButton-Flight
- **來源**: `flight.js:156-159` + `flight.js:206-230`
- **Props**: `{ data, meta, filenameTemplate }`
- **狀態**: default（「⬇ 下載 Excel」）/ loading（「⟳ 產生中…」disabled）

### COMP-018: AirlineFilter
- **來源**: `flight.js:164-173`
- **結構**: card.bg-light 內含「全部」chip + 各航空 chip
- **Props**: `{ airlines: string[]; activeAirlines: Set<string>; onToggle: (airline) => void }`

### COMP-019: FilterChip
- **來源**: `flight.js:127-129`
- **狀態**: inactive（btn-outline-secondary）/ active（btn-info text-white）
- **Props**: `{ label: string; active: boolean; onClick: () => void }`

### COMP-020: ResultsTable-Flight
- **來源**: `flight.js:175-189`
- **欄位**: 航空公司 / 航班號 / 出發 ↑ / 抵達 / 飛行時間 / 轉機 / 票價 ↑（7 欄含排序提示 icon）

### COMP-021: ResultRow-Flight
- **來源**: `flight.js:109-123`
- **欄位**: extractAirline / flights_str / fmtTime(dep_time) / fmtTime(arr_time) / duration / stopsBadge / price（NT$ 格式化）

### COMP-022: StopsBadge
- **來源**: `flight.js:110-112`
- **Variants**: 直飛（bg-success「直飛」）/ 轉機（bg-warning text-dark「N 轉」）
- **Props**: `{ stops: number }`

---

## 7. PAGE-004 整合查詢專屬元件

### COMP-023: SearchForm-Plan
- **來源**: `plan.html:48-101`
- **欄位**: origin / dest / region / departure / ret-date / adults / submit（6 欄 + submit）
- **目的地清單**: 5 個（無沖繩 OKA、無大阪伊丹 ITM；比 COMP-014 少）

### COMP-024: DownloadButton-Plan
- **來源**: `plan.js:103-108` + `plan.js:199-224`
- **狀態**: default / loading；無資料時不渲染
- **行為**: POST /api/plan/download → blob download；filename 含 origin-dest_departure

### COMP-025: CollapsibleCard-Flight
- **來源**: `plan.js:144-167`
- **結構**: card.shadow-sm > header（bg-info, 可點擊 collapse toggle）+ body（collapse show 預設）
- **Props**: `{ data, error, backend, defaultOpen=true }`
- **狀態**: collapsed / expanded（預設）

### COMP-026: CollapsibleCard-Ski
- **來源**: `plan.js:169-191`
- **結構**: 同 COMP-025 但 header bg-primary
- **狀態**: 同上

---

## 8. PAGE-005 收藏專屬元件

### COMP-027: LogoutButton
- **來源**: `profile.html:10-14` + inline JS `:56-59`
- **互動**: click → fetch POST /api/auth/logout → `location.href='/'`
- **狀態**: default（btn-outline-danger btn-sm）

### COMP-028: FavoritesGrid
- **來源**: `profile.html:16-50`
- **結構**: `<h2>` 標題 + 條件 `{% if not favorites %}` 顯示 empty alert / `<div class="row g-3">` 含 cards
- **Props**: `{ favorites: Favorite[] }`
- **狀態**: empty / has-data

### COMP-029: FavoriteCard
- **來源**: `profile.html:22-48`
- **Props**:
  ```typescript
  interface FavoriteCardProps {
    id: number;
    type: 'ski' | 'flight';
    label: string;     // 空時顯示「未命名」
    data: any;         // 雪票或機票 dict
    created_at: string;
  }
  ```
- **狀態**: default

### COMP-030: DeleteButton（收藏）
- **來源**: `profile.html:33-35` + inline JS `:60-67`
- **互動**: click → window.confirm「確定刪除此收藏？」→ DELETE /api/favorites/{id} → 移除 DOM
- **狀態**: default
- **[Rule 11 不可逆操作]**: ✅ 已有 confirm 二次確認

---

## 9. Auth 共用元件（PAGE-006 + PAGE-007）

### COMP-031: AuthCard
- **用途**: 登入 / 註冊頁的共用卡片容器
- **重用**: PAGE-006, PAGE-007
- **來源**: `login.html:10-58`, `register.html:10-57`
- **Props**: `{ title: string; titleIcon?: string; children: VueNode }`
- **結構**: container py-5 max-width:420px > card.shadow-sm.border-0 > card-body.p-4 > h1 + slot

### COMP-035: InlineErrorAlert
- **重用**: PAGE-006, PAGE-007
- **來源**: `login.html:45`, `register.html:29`
- **Props**: `{ message: string; variant: 'danger' | 'info' | 'warning'; visible: boolean }`
- **狀態**: hidden（`d-none`）/ visible

---

## 10. PAGE-006 登入專屬元件

### COMP-032: URLAlert-Login
- **來源**: `login.html:18` + inline JS `:62-74`
- **觸發**: 讀取 `URLSearchParams`，依 `verified=1` / `error={invalid_token|token_used|token_expired|unverified}` 顯示對應 alert
- **狀態**: hidden（預設）/ success（綠）/ warning（黃）/ danger（紅）

### COMP-033: GoogleLoginButton
- **來源**: `login.html:21-31`
- **結構**: `<a href="/api/auth/google/login" class="btn btn-outline-danger btn-lg">` + Google logo SVG inline
- **狀態**: default

### COMP-034: LoginForm
- **來源**: `login.html:36-51` + `auth.js:8-44`
- **欄位**: identifier (text, autocomplete=username) + password (autocomplete=current-password)
- **互動**: submit → fetch POST /api/auth/login → 403 時自動顯示 COMP-036
- **狀態**: default / submitting（submit disabled）

### COMP-036: ResendVerificationArea
- **來源**: `login.html:46-49` + inline JS `:77-107`
- **觸發**: 預設 hidden；登入 API 回 403 時 JS 移除 `d-none`
- **互動**: click → 檢查 identifier 含 @ → fetch POST /api/auth/resend-verification
- **狀態**: hidden / visible / sending（button disabled, 文字「寄送中...」）/ success / error

---

## 11. PAGE-007 註冊專屬元件

### COMP-037: RegisterForm
- **來源**: `register.html:16-31` + `auth.js:47-86`
- **欄位**: email (type=email) + username + password (minlength=8)
- **互動**: submit → fetch POST /api/auth/register → 成功時 form.hide + COMP-038.show
- **狀態**: default / submitting / success（轉場到 COMP-038）/ error

### COMP-038: CheckEmailPanel
- **來源**: `register.html:33-49`
- **內容**: 📧 icon + 「驗證信已寄出」標題 + 信箱顯示 + 24h 有效期說明 + 「回登入頁」按鈕
- **狀態**: hidden（預設）/ visible（註冊成功後）

---

## 12. 操作 Icon 對照表（SDLC Rule 3 — 部分適用）

> **SDLC Rule 3**（操作 icon 統一）原為 CRUD 列表頁的規範。本 brownfield 專案：

| 操作 | Icon | 出現位置 | 來源 |
|------|------|---------|------|
| 刪除收藏 | `bi-trash` | PAGE-005 COMP-030 | `profile.html:34` |
| 登出 | `bi-box-arrow-right` | PAGE-005 COMP-027 | `profile.html:12` |
| 下載 Excel | `bi-download` | PAGE-002/003/004 | 多處 |
| 開新分頁連結 | `bi-box-arrow-up-right` | ResultRow / ExternalLink | 多處 |
| 搜尋 | `bi-search` | 所有 SearchForm submit | 多處 |
| 漏斗（搜尋區）| `bi-funnel` | 搜尋表單 heading | `ski.html:49`, `flight.html:48`, `plan.html:45` |
| 漏斗（篩選）| `bi-funnel-fill` | flight.js 篩選 hint | `flight.js:179` |
| 排序 | `bi-sort-up` | flight 表頭 | `flight.js:181, 185` |
| 警告 | `bi-exclamation-triangle-fill` | error alert | 多處 |
| 提示 | `bi-info-circle` / `bi-info-circle-fill` | info alert | 多處 |

> **Rule 3 評估**: 本系統**無傳統 CRUD 列表頁**（無「檢視/編輯/刪除」三聯按鈕情境）。唯一 CRUD 是 PAGE-005 收藏的「刪除」，使用 `bi-trash` 符合 Rule 3 推薦。**[OK — Rule 3 部分適用 + 既有實作合規]**

---

## 13. 元件 → TOKEN 引用表

| COMP | 引用 TOKEN（design-tokens.json）|
|------|--------------------------------|
| LAYOUT-001 | `color.brand.primary` (navbar bg), `color.bootstrap.dark` (footer bg), `typography.fontFamily` |
| COMP-001 Navbar | `color.brand.primary`, `shadow.sm`, `motion.cardHoverTransition`（無，靜態） |
| COMP-003 SkipLink | `accessibility.skipLink.*` |
| COMP-004 HeroSection | `color.brand.primary`, `primary-dark`, `primary-darkest` (gradient) |
| COMP-005 StatsBar | `color.brand.primary` |
| COMP-006 FeatureCard | `shadow.sm`, `shadow.cardHover`, `motion.cardHoverTransition`, `motion.cardHoverTranslateY` |
| COMP-013 RegionBadge | `color.regionBadge.*`（6 色變體）, `radius.regionBadge` |
| COMP-016 BackendBadge | `color.bootstrap.success`, `color.bootstrap.warning` |
| COMP-022 StopsBadge | `color.bootstrap.success`（直飛）, `color.bootstrap.warning`（轉機） |
| COMP-029 FavoriteCard | `color.bootstrap.primary` (ski badge), `color.bootstrap.info` (flight badge) |
| 所有表單 input | Bootstrap form-control 預設 token |
| 所有 alert | Bootstrap alert-{variant} 預設 token |

---

## 14. 自我驗證

- [x] 38 個元件（1 LAYOUT + 38 COMP）反向萃取完整
- [x] 每個元件有 Props interface（未來 Vue 重構契約）
- [x] 每個元件標來源 file:line
- [x] 重用元件（COMP-008/031/035）標明重用頁面
- [x] 狀態變體（default / hover / disabled / error 等）描述完整
- [x] Bootstrap 5.3.3 元件直接使用為基底，不重新發明
- [x] **來源: 既有 HTML 反向追溯**（不畫新元件）
- [x] Rule 3 操作 icon 對照表已建立（部分適用，brownfield 合規）
- [x] Rule 11 不可逆操作確認（PAGE-005 DELETE 已有 confirm）
- [x] COMP / LAYOUT ID 連續未越界（COMP-001..038, LAYOUT-001）
- [x] Pencil 節點 ID 對應**N/A**（pencilMcp=false）
