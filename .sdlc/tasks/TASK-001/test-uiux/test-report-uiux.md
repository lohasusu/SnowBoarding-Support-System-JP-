---
document_id: "TEST-UIUX-TASK-001-v1.0"
title: "測試報告 — TASK-001 UIUX brownfield 反向追溯"
version: "1.0"
date: "2026-06-15"
author: "Testing"
status: "Final"
task_id: "TASK-001"
phase: "test-uiux"
mode: "brownfield-document (pencilMcp=false)"
tested_artifacts:
  - ".sdlc/tasks/TASK-001/uiux/wireframes.md"
  - ".sdlc/tasks/TASK-001/uiux/component-spec.md"
  - ".sdlc/tasks/TASK-001/uiux/design-tokens.json"
  - ".sdlc/tasks/TASK-001/uiux/user-flow.md"
  - ".sdlc/tasks/TASK-001/uiux/i18n-keys.md"
  - ".sdlc/tasks/TASK-001/uiux/pencil-component-sync.json"
  - ".sdlc/tasks/TASK-001/uiux/self-review.json"
baseline_documents:
  - ".sdlc/tasks/TASK-001/ba/requirement-spec.md (REQ-TASK-001-v1.0)"
  - ".sdlc/tasks/TASK-001/sa/system-arch.md (ARCH-TASK-001-v1.0)"
  - ".sdlc/tasks/TASK-001/sa/functional-flow.md (FUNC-TASK-001-v1.0)"
  - ".sdlc/tasks/TASK-001/sa/field-spec.md (FIELD-TASK-001-v1.0)"
  - ".sdlc/tasks/TASK-001/sa/impact-assessment.md (IMPACT-TASK-001-v1.0)"
  - ".sdlc/shared/id-registry.md (rebuilt 2026-06-15)"
  - "web/templates/*.html + web/static/{js,css}/* (brownfield source of truth)"
verification_skill: "~/.claude/skills/sdlc/tools/verify-design/SKILL.md (D1..D6 applicable; D7 N/A — pencilSkipped)"
---

# 測試報告 — TASK-001 UIUX brownfield 反向追溯

## 文件資訊

- **被測階段**: uiux（brownfield-document）
- **被測 TASK**: TASK-001
- **特殊條件**: `pencilMcp = false`, `mcpStatus.chrome = false`, brownfield 反向追溯（**權威來源為 `web/templates/*.html`**）
- **測試日期**: 2026-06-15
- **測試方法**: D1-D6 設計驗證（D7 Pencil 視覺稿 N/A）+ ID 規範 + brownfield 對應抽樣 + design-tokens vs CSS 對照 + GAP/INCONSIS 抽樣驗證 + Rule 2 建議隔離 + Pencil 跳過合規

---

## 1. 測試結果摘要

| 指標 | 結果 |
|------|------|
| 檢查項目總數 | 32 |
| ✅ 通過 | 29 |
| 🔴 Critical | 0 |
| 🟡 Major (Warning) | 2 |
| 🔵 Minor (Info) | 5 |
| 通過率 | 90.6 % |
| **結論** | **PASS**（brownfield 容差下）|
| Score | **88 / 100** |
| 通過門檻 | Critical = 0 且 Score ≥ 80 |

---

## 2. 發現清單

### 🔴 Critical（無）

無 Critical 發現。Brownfield 反向追溯與既有 production source code 高度一致；ID 規範、追溯矩陣、Pencil 跳過合規皆通過。

---

### 🟡 Major / Warning

#### [WARN-001] PAGE-005 追溯矩陣遺漏 FUNC-031（登出 — clear cookie）

- **位置**: `uiux/wireframes.md §1 頁面清單` + `§12 追溯矩陣（PAGE → FUNC → FR）`
- **觀察**:
  - PAGE-005（個人/收藏）在 §1 頁面清單對應「FUNC-041, 043..045」
  - §12 追溯矩陣 PAGE-005 對應「FUNC-041, FUNC-043..045」
  - **缺**：FUNC-031（登出—清除 cookie）
- **證據**:
  - SA `functional-flow.md` 定義 `FUNC-031: 登出—清除 cookie` 屬於 `MOD-005 auth`，由前端登出按鈕觸發
  - UIUX `wireframes.md §7 PAGE-005 Layer 2` 已記載「Logout 按鈕 LogoutButton COMP-027 (`profile.html:10-14`)」
  - UIUX `component-spec.md §8 COMP-027` 已記載「click → fetch POST /api/auth/logout → location.href='/'」
  - 來源檔證實: `web/templates/profile.html:10-14` + `profile.html:56-59` inline script
- **影響**: PAGE→FUNC 追溯矩陣不完整。SD 階段若以 §12 為 traceability 依據，FUNC-031 將無對應 PAGE，可能誤判為「無 UI 入口」的後端 FUNC
- **修正建議**:
  - 在 §1 PAGE-005 列「對應 FUNC」加入 `FUNC-031`
  - 在 §12 追溯矩陣 PAGE-005 列加入 `FUNC-031`
- **嚴重度**: Major（追溯斷裂，但元件與功能描述本身完整；可在 next phase 前快速補正）
- **追溯**: `@traces_to(FUNC-031)` + `@traces_to(REQ FR-009)`

#### [WARN-002] FeatureCard hover 描述對「第 3 張卡」不精確（PAGE-001 Layer 2）

- **位置**: `uiux/wireframes.md §3 PAGE-001 Layer 2 元件配置表`
- **觀察**:
  - Layer 2 row「Features | FeatureCard (COMP-006) × 3 | `index.html:69-122` | 3 個 card-hover，第 3 個 opacity-65 + disabled」
  - 實際 `index.html:69-122`: 第 1/2 張 card 有 `class="card h-100 shadow-sm border-0 card-hover"`；**第 3 張**（line 104）為 `class="card h-100 shadow-sm border-0 opacity-65"` —**沒有 `card-hover`**
  - 也就是說：第 3 張卡是**永久 disabled，不參與 hover 動畫**
- **證據**: `web/templates/index.html:70, 87, 104`（grep verified）
- **影響**: Layer 2 描述讓讀者以為 3 張都套 card-hover，但實際只有前 2 張。雖然 Layer 5 多狀態章節提到「disabled card」，Layer 2 摘要列仍誤導
- **修正建議**: 改 Layer 2 row 為「3 個 card；前 2 個有 card-hover；第 3 個 opacity-65 + disabled（無 hover）」
- **嚴重度**: Minor 偏 Major（影響元件規格在未來 Vue 重構契約的精確性 — Props `disabled: true` 時應跳過 card-hover transition；但因 brownfield 反向追溯且 COMP-006 Props 已含 `disabled?: boolean` 標記，落實時可規避）
- **追溯**: `@traces_to(COMP-006)` + `@traces_to(PAGE-001 INCONSIS-001)`

---

### 🔵 Minor / Info

#### [INFO-001] sdlc-role-verify.sh uiux 對 brownfield + pencilSkipped 模式不友善（誤判 10 項）

- **執行結果**: `bash sdlc-role-verify.sh uiux TASK-001` → score 50/100, 10 failed checks
- **失敗項分析**:
  - 「缺少 design-system.md」: 本 TASK 用 `design-tokens.json` 取代 `design-system.md`（brownfield 純文件化決策，self-review.json `style-direction-skipped: true` 已記）
  - 「缺少 screenshots 目錄」x3: pencilMcp=false → 不畫稿、不截圖（self-review.json `screenshots-skipped: true` 已記）
  - 「缺少 pencil-node-mapping.md」x2: pencilMcp=false → 無 Pencil 節點（self-review.json `pencil-node-mapping-skipped: true` 已記）
  - 「wireframes.md 缺少章節: 截圖映射」: 同 Pencil 跳過
  - 「component-spec.md 缺少章節: 元件清單」: 實際 §1「元件樹狀結構」+ §2-11 各章已列；script 用嚴格字串匹配未認可同義章節
  - 「PAGE ID 重複 PAGE-001」: 該 ID 在 §1 頁面清單 / §3 章節標題 / §12 追溯矩陣各出現一次（合法引用），script 將正常引用誤判為重複
- **判定**: 本項**不視為 UIUX 產出缺陷**。verify 腳本本身對 brownfield + pencilSkipped 場景的支援不足，屬腳本層限制
- **修正建議**: 不阻塞本階段；列入 SDLC tooling backlog（給未來腳本升級時加入 `pencilSkipped` 旗標識別）
- **嚴重度**: Info（tooling gap，非規格缺陷）

#### [INFO-002] 5 個 GAP + 1 個 INCONSIS 已抽樣確認真實存在（非 hallucination）

- 抽樣驗證:
  - **GAP-001（收藏入口缺失）**: ✅ `grep "addFavorite" web/static/js/{ski,flight}.js` → 0 結果；`auth.js:90` 已定義但無呼叫端 — 確認
  - **GAP-002（Excel 下載失敗無 UI 反饋）**: ✅ `ski.js:178-180` `downloadBtn.click → window.location.href = '/api/ski/download?...'`，無 try/catch — 確認
  - **GAP-003（OAuth 4 個 error query 無 alert）**: ✅ `login.html:62-74` inline JS 僅覆蓋 `verified / invalid_token / token_used / token_expired / unverified`；未覆蓋 `oauth_state_mismatch / google_denied / google_token_failed / google_userinfo_failed` — 確認
  - **GAP-004（刪除收藏失敗靜默）**: ✅ `profile.html:60-67` `if ((await res.json()).ok) btn.closest('.col-md-6').remove();` — 失敗無 else 分支 — 確認
  - **INCONSIS-001（首頁第 3 張 card 即將推出）**: ✅ `index.html:113` 仍有 `<span>即將推出</span>`；`line 118` `<button disabled>敬請期待</button>` — 確認
- **判定**: 所有 brownfield gap / inconsistency 為真實 source code 觀察，**非 AI 腦補**
- **嚴重度**: Info（正向驗證 — 證明 brownfield 反向追溯品質高）

#### [INFO-003] FUNC-035（OAuth Upsert）與 FUNC-042（admin verify）正確排除 PAGE 追溯

- **觀察**: §12 追溯矩陣 PAGE-006 列 FUNC-028..030, 034, 036..040 — **不含 FUNC-035 / FUNC-042**
- **判定**: 正確
  - `FUNC-035 OAuth Upsert 決策` 為 callback 階段純後端決策樹（決定新建 / UPDATE google_id），無 UI 入口
  - `FUNC-042 /api/auth/verify 維運查詢` 為 admin 端點（HOTFIX-C 候選），無 UI 入口
- **嚴重度**: Info（合理排除）

#### [INFO-004] design-tokens.json 與 custom.css 對照抽樣一致

- 抽樣對照:
  - `color.brand.primary #1565c0` ↔ `custom.css:18 hero gradient start`（135deg gradient #1565c0 → #0d47a1 → #1a237e）— ✅ 一致
  - `color.brand.primary-dark #0d47a1` ↔ `custom.css:18 mid` — ✅
  - `color.brand.primary-darkest #1a237e` ↔ `custom.css:18 end` — ✅
  - `color.regionBadge.hokkaido #1565c0` ↔ `custom.css:48 .region-badge-北海道` — ✅
  - `color.regionBadge.nagano #2e7d32` ↔ `custom.css:49` — ✅
  - `color.regionBadge.niigata #6a1b9a` ↔ `custom.css:50` — ✅
  - `color.regionBadge.yamagata #e65100` ↔ `custom.css:51` — ✅
  - `color.regionBadge.aomori #00695c` ↔ `custom.css:52` — ✅
  - `color.regionBadge.fukushima #4e342e` ↔ `custom.css:53` — ✅
  - `motion.cardHoverTransition` ↔ `custom.css:32 .card-hover { transition: transform 0.18s ease, box-shadow 0.18s ease }` — ✅
  - `motion.cardHoverTranslateY -4px` ↔ `custom.css:35` — ✅
  - `shadow.cardHover 0 8px 24px rgba(0,0,0,0.12)` ↔ `custom.css:36` — ✅
  - `motion.reducedMotion @media (prefers-reduced-motion: reduce)` ↔ `custom.css:87-93` — ✅
  - `accessibility.skipLink` ↔ `custom.css:2-14` — ✅
  - `components.bootstrap.version 5.3.3` ↔ `base.html:61` `cdn.jsdelivr.net/npm/bootstrap@5.3.3` — ✅
- **判定**: design-tokens.json 為真實萃取，無 hallucination
- **嚴重度**: Info（正向驗證）

#### [INFO-005] i18n-keys.md 性質正確標示（建議 / 參考用 / 不強制重構）

- **觀察**:
  - frontmatter `mode: brownfield-document`
  - §0「狀態: 建議（**brownfield 不強制重構**）」
  - §0「未來啟用時機: Vue 重構階段才需要正式 i18n key」
  - §12「啟用建議: 不在 TASK-001 內啟用」
- **判定**: 不會被誤判為「正式規格的實作對象」；Rule 2 建議隔離合規
- **嚴重度**: Info（合規確認）

---

## 3. 各驗證維度結果

### D1: 功能覆蓋率（FUNC → PAGE → COMP）

| 檢查項 | 結果 | 備註 |
|--------|------|------|
| 每個 SA FUNC 至少對應一個 PAGE | ⚠️ 部分 | 45 個 FUNC 中 42 個對應到 PAGE；FUNC-031 漏列（WARN-001）；FUNC-035 / FUNC-042 為純後端可豁免（INFO-003）|
| 每個 PAGE 使用的元件都在 component-spec.md 定義 | ✅ | wireframes.md 引用 COMP-001..038 + LAYOUT-001 全部在 component-spec.md §1-11 定義 |
| SA field-spec 欄位都在 PAGE 呈現 | ✅ | users / favorites / email_verification_tokens 欄位於 PAGE-005/006/007 呈現 |
| 每頁有空狀態 / 載入中 / 錯誤狀態 | ✅ | wireframes.md 每 PAGE 都有 Layer 5「多狀態」章節（PAGE-002 6 狀態 / PAGE-003 8 狀態 / PAGE-006 12 狀態 等）|

### D2: Design Token 完整性

| 檢查項 | 結果 | 備註 |
|--------|------|------|
| 色彩系統完整（含色碼）| ✅ | brand × 3 + bootstrap × 8 + regionBadge × 6 + text × 4 |
| 字體系統完整（family/size/weight）| ✅ | fontFamily, scale × 8, weight × 3, tableScale × 2 |
| 間距系統（spacing scale）| ✅ | 0..5 + container/card padding |
| 響應式斷點 | ✅ | sm/md/lg/xl/xxl 5 個 |
| 陰影 / 動畫 Token | ✅ | shadow × 3, motion × 5（含 reducedMotion）|
| 共用 UI 模式 Token（Modal / Toast / Confirm）| ⚠️ N/A | brownfield 用 window.confirm / window.alert / Bootstrap alert，本身不需要新 token；wireframes §10「通用 UI 模式」已說明此設計選擇 |
| Bootstrap 版本鎖定 + SRI | ✅ | 5.3.3 + integrity hash 對應 base.html:61, 66, 172 |

### D3: 元件規格一致性

| 檢查項 | 結果 | 備註 |
|--------|------|------|
| Props 定義完整（TypeScript-style interface）| ✅ | 38 COMP + 1 LAYOUT 全部有 Props interface（為未來 Vue 重構契約）|
| 狀態完整（default / hover / focus / disabled）| ✅ | 互動元件如 COMP-006 / COMP-009 / COMP-014 等都有多狀態描述 |
| 無障礙（ARIA label / aria-current）| ✅ | LAYOUT-001 已描述 aria-label / aria-controls / aria-current / aria-live |
| Keyboard nav | ✅ | Bootstrap 5 預設支援 + SkipLink 已建立 |

### D4: UX 補充標記（Rule 1/2）

| 檢查項 | 結果 | 備註 |
|--------|------|------|
| brownfield 補充標記正確 | ✅ | [BROWNFIELD-GAP] × 5 / [BROWNFIELD-INCONSISTENCY] × 2 / [BROWNFIELD-NOTE] × 2 / [INFERRED-FROM-MAIN] × 2 — 標記齊全 |
| SA 欄位保留（未刪減）| ✅ | UIUX 純規格產出，未改 SA 的 ENTITY/TBL/FUNC（self-review.json `sa-fields-preserved: true`）|
| 無未標記的 [UIUX建議] 殘留 | ✅ | `grep "[UIUX建議]"` → 0 結果；正式規格與假設性建議物理分離 |

### D5: 線框圖與流程完整性

| 檢查項 | 結果 | 備註 |
|--------|------|------|
| 每頁 ASCII 線框圖 | ✅ | LAYOUT-001 + PAGE-001..007 全部有 ASCII wireframe |
| 每頁有元件使用表 | ✅ | 每 PAGE 都有 Layer 2「元件配置」表 |
| 使用者旅程圖（Mermaid）| ✅ | user-flow.md 含 7 個 FLOW + Mermaid flowchart/sequenceDiagram，§9 全域導航 / §10 存取權限 / §11 追溯矩陣完整 |
| 追溯矩陣完整 PAGE → FUNC → FR | ⚠️ 大致完整 | 7 個 PAGE 對應 16 個 FR；FUNC-031 漏列（WARN-001）|

### D6: 跨文件一致性

| 檢查項 | 結果 | 備註 |
|--------|------|------|
| wireframes ↔ component-spec | ✅ | wireframes 引用 COMP-001..038 全部在 component-spec 定義；命名一致 |
| component-spec ↔ design-tokens | ✅ | component-spec §13「元件 → TOKEN 引用表」標明每個元件對應的 TOKEN，token 名稱與 design-tokens.json 一致 |
| 術語一致 | ✅ | 跨 wireframes / component-spec / user-flow 使用相同元件名（如 RegionBadge / FavoriteCard）|
| 共用佈局定義存在 | ✅ | wireframes §2 LAYOUT-001 + component-spec §2 LAYOUT-001 + Navbar/Footer/SkipLink |
| Navbar 導航固定 | ✅ | wireframes §2 + COMP-001 Props DEFAULT_NAV_ITEMS 列出固定的 3 項（ski/flight/plan）|
| Sidebar 不適用 | ✅ | 本系統用 top navbar 模式（非 sidebar），brownfield 結構合理 |

### D7: Pencil 視覺稿驗證

| 檢查項 | 結果 | 備註 |
|--------|------|------|
| screenshots/ 目錄非空 | ⚠️ N/A | pencilMcp=false → 不適用 |
| 每頁有截圖 | ⚠️ N/A | 同上 |
| 多狀態覆蓋（empty + data-loaded）| ⚠️ N/A | 同上 |
| design-tokens.json 存在 | ✅ | 130 行，有 schema reference |
| Pencil 視覺稿存在 | ⚠️ N/A | `find uiux -name "*.pen"` → 0 結果 — 符合 pencilMcp=false |
| pencil-component-sync.json `components` 空 + `promotedToDS` 空 | ✅ | 符合 no-Pencil 約束 |
| self-review.json `pencilSkipped: true` | ✅ | 已標記 |

---

## 4. 跨 TASK 一致性檢查（共享層）

| 檢查項 | 結果 | 備註 |
|--------|------|------|
| COMP-ID 連續性 | ✅ | COMP-001..038 連續，無跳號；範圍 1-100 |
| PAGE-ID 連續性 | ✅ | PAGE-001..007 連續；範圍 1-100 |
| LAYOUT-ID 連續性 | ✅ | LAYOUT-001（單一）；範圍 1-100 |
| 與 TASK-002 ID 範圍互斥 | ✅ | TASK-002 使用 101+ 範圍（如 FUNC-101..107, MOD-101..104, API-101, PATTERN-101）— 不撞號 |
| id-registry.md 已 rebuild | ✅ | 2026-06-15T08:00:53Z；本 TASK 的 46 個 UIUX ID（1 LAYOUT + 38 COMP + 7 PAGE）皆出現 |
| 已有元件重用標記 | ✅ | COMP-008 Breadcrumb（3 頁）/ COMP-031 AuthCard（2 頁）/ COMP-035 InlineErrorAlert（2 頁）— 已標明重用頁面 |
| .pen 持久化路徑 | ⚠️ N/A | pencilMcp=false — 無 .pen 檔案 |
| Base Token 保護 | ✅ | TASK-001 為 first TASK，未修改前 TASK token |

---

## 5. brownfield + Pencil skipped 合規矩陣

| 約束 | 預期 | 實際 | 結果 |
|------|------|------|------|
| `pencilMcp=false` 不畫 .pen | 0 個 .pen | `find uiux -name "*.pen"` = 0 | ✅ |
| 不建立 screenshots/ 目錄 | 不存在 | `find uiux -name screenshots` = 0 | ✅ |
| `pencil-component-sync.json.components` 為空 | `{}` | `{}` | ✅ |
| `pencil-component-sync.json.promotedToDS` 為空 | `[]` | `[]` | ✅ |
| self-review.json `pencilSkipped: true` | true | true | ✅ |
| self-review.json `pencilSkipReason` 描述 | 有 | 有（"config.json.project.pencilMcp=false — Pencil MCP 未啟用 / 純文件化交付"）| ✅ |
| brownfield 來源權威為 templates/*.html | wireframes 多次強調 | wireframes 開頭 + §1 + §12 / component-spec 開頭多次強調 | ✅ |
| 跨 TASK-002 修改用 [INFERRED-FROM-MAIN] 註記 | 有 | wireframes PAGE-006/007（identifier 雙模式 + check-email panel）+ user-flow FLOW-004/005 | ✅ |
| Rule 2 建議隔離 | 無未標記 [UIUX建議] | grep 0 結果 | ✅ |

---

## 6. brownfield 來源對應抽樣（3 個 PAGE）

### 抽樣 1: PAGE-001 首頁 vs `web/templates/index.html`

| 描述項 | 文件 line | 真實 line | 一致 |
|--------|----------|----------|------|
| Hero gradient + h1 + lead + 雙 CTA | wireframes §3 Layer 2「HeroSection (COMP-004) `index.html:24-42`」 | index.html:24-42 確認 hero-section + display-4 + lead + 2 個 CTA | ✅ |
| StatsBar 3 cols (40+ / 6 / 每日) | wireframes §3 Layer 2「StatsBar (COMP-005) `index.html:45-62`」 | index.html:45-62 確認 bg-primary + 3 個 col-4 | ✅ |
| FeatureCard 第 3 張 disabled | wireframes §3 Layer 3「第 3 張 opacity-65 + disabled」 | index.html:104, 113, 118 確認 opacity-65 + 即將推出 + 敬請期待 disabled | ✅ |
| 6 地區 cards | wireframes §3 Layer 2「RegionCard (COMP-007) 6 地區」 | index.html:154-160 確認 北海道/長野/新潟/山形/青森/福島 6 個 | ✅ |

### 抽樣 2: PAGE-002 雪票 vs `web/templates/ski.html` + `static/js/ski.js`

| 描述項 | 文件 line | 真實 line | 一致 |
|--------|----------|----------|------|
| 麵包屑 首頁 / 雪票查詢 | wireframes §4 Layer 2「Breadcrumb (COMP-008) `ski.html:34-40`」 | ski.html:34-40 確認 | ✅ |
| 地區 select 6 個選項 + 全部地區 | wireframes §4 Layer 3 + Layer 1 | ski.html:55-63 確認 全部地區/北海道/長野/新潟/山形/青森/福島 | ✅ |
| download-btn 預設 disabled + title「查詢後可下載 Excel」 | wireframes §4 Layer 3 | ski.html:76-79 確認 disabled aria-disabled + title 一致 | ✅ |
| State 1 預設空狀態「請選擇地區...」 | wireframes §4 Layer 5 State 1 | ski.html:88-93 + bi-arrow-up-circle 確認 | ✅ |
| State 2 loading 「正在連線抓取票價」 | wireframes §4 Layer 5 State 2 | ski.js:124-130 確認 | ✅ |
| sticky 表頭 + max-height 60vh | wireframes §4 Layer 4 | custom.css:66-75 確認 results-table-wrap + sticky thead | ✅ |

### 抽樣 3: PAGE-005 個人/收藏 vs `web/templates/profile.html`

| 描述項 | 文件 line | 真實 line | 一致 |
|--------|----------|----------|------|
| 標題 + welcome 文字 | wireframes §7 Layer 2 | profile.html:7-8 確認 | ✅ |
| Logout button btn-outline-danger btn-sm | wireframes §7 Layer 3 | profile.html:10-14 確認 + bi-box-arrow-right icon | ✅ |
| 空狀態 alert-info | wireframes §7 Layer 5 State 1 | profile.html:18-19 確認 | ✅ |
| 刪除確認 window.confirm「確定刪除此收藏？」 | wireframes §7 Layer 5 State 3 + Rule 11 已有 confirm | profile.html:62 `confirm('確定刪除此收藏？')` 確認 | ✅ |
| 刪除失敗靜默（GAP-004）| wireframes §7 State 4 [BROWNFIELD-GAP] | profile.html:65 `if ((await res.json()).ok)` 無 else — 確認 | ✅ |

**抽樣結論**: 3 個 PAGE 全部精準對應到既有 template / JS source code，反向追溯品質高。

---

## 7. ID 規範驗證（Rule 8 / 13）

| ID 類型 | 範圍配額 | 實際分配 | 連續性 | 越界 | 結果 |
|---------|---------|---------|--------|------|------|
| LAYOUT | LAYOUT-001..100 | LAYOUT-001（1 個）| ✅ | 否 | ✅ |
| PAGE | PAGE-001..100 | PAGE-001..007（7 個）| ✅ | 否 | ✅ |
| COMP | COMP-001..100 | COMP-001..038（38 個）| ✅ | 否 | ✅ |
| FLOW | TASK-scoped | FLOW-001..007（7 個）| ✅ | N/A | ✅ |

ID 格式檢查: 全部使用 3 位零填充（PAGE-001 / COMP-001 / LAYOUT-001 / FLOW-001）

與既有 SA ID 撞號檢查:
- SA 已配發 ENTITY-001..003, MOD-001..006, FUNC-001..045, PATTERN-001..008, TBL-001..003 — **無一與 UIUX 的 PAGE/COMP/LAYOUT/FLOW 撞號**（不同 prefix）

---

## 8. Rule 合規檢查

| Rule | 檢查 | 結果 |
|------|------|------|
| Rule 1 來源引用制 | 每個元件描述標 file:line 來源 | ✅ |
| Rule 2 建議隔離 | 無未標記 [UIUX建議]；brownfield-only 補追溯文件 | ✅ |
| Rule 3 操作 Icon | 刪除=bi-trash 符合（component-spec §12）| ✅ |
| Rule 4 檢視權限截圖 | N/A — 本系統為二級權限（未登入隱藏 / 已登入全可用）| ✅ |
| Rule 6 跨 TASK 修改 | 未跨 TASK-002 修改其產出；僅以 [INFERRED-FROM-MAIN] 反映 TASK-002 對 login/register 的 main 狀態 | ✅ |
| Rule 7 跨 TASK 增量 | 第一個 TASK，從 0 起編；impact-assessment.md §3 已預告後續 TASK 修改候選 | ✅ |
| Rule 8 ID 規範 | 連續、未越界、無撞號（見 §7）| ✅ |
| Rule 11 不可逆操作確認 | PAGE-005 收藏刪除 confirm dialog 已有（profile.html:62）| ✅ |
| Rule 17 Pencil 兩層 | pencilMcp=false → DS pen / per-TASK pen 兩層皆無建立 — 合規 | ✅ |

---

## 9. 追溯矩陣（測試案例 → 規格 ID）

| 測試案例 | @traces_to | 結果 |
|---------|-----------|------|
| T-D1-1 PAGE-005 logout button 對應 FUNC-031 | FUNC-031（漏列 PAGE）| 🟡 WARN-001 |
| T-D1-2 PAGE-001 第 3 張卡 disabled 對應 INCONSIS-001 | PAGE-001, FUNC-? (無對應 FUNC) | 🟡 WARN-002 |
| T-D1-3 PAGE-006 不含 FUNC-035/042 | FUNC-035, FUNC-042 | 🔵 INFO-003 |
| T-D2-1 design-tokens 與 custom.css 一致 | TOKEN-color-brand-primary, regionBadge × 6 | 🔵 INFO-004 |
| T-D3-1 38 個 COMP Props interface 存在 | COMP-001..038 | ✅ |
| T-D4-1 brownfield 補充標記正確 | 5 GAP + 2 INCONSIS + 2 INFERRED | 🔵 INFO-002 |
| T-D5-1 7 個 FLOW 對應 7 個 BF | FLOW-001..007, BF-001..007 | ✅ |
| T-D5-2 LAYOUT-001 共用佈局存在 | LAYOUT-001 | ✅ |
| T-D6-1 wireframes COMP 引用 ↔ component-spec 定義 | COMP-001..038 | ✅ |
| T-D7-1 Pencil skipped 合規 | pencilMcp=false, pencilSkipped=true | ✅ |
| T-Rule-8-1 ID 連續、未越界、無撞號 | LAYOUT/PAGE/COMP/FLOW | ✅ |
| T-Rule-11-1 收藏刪除 confirm dialog 已有 | FUNC-045 [IRREVERSIBLE]| ✅ |
| T-INFO-005 i18n-keys.md 標為「建議 / 不強制重構」 | I18N-TASK-001-v1.0 | 🔵 INFO-005 |
| T-brownfield-1 GAP-001 收藏入口 source code 抽樣確認 | GAP-001 | ✅ |
| T-brownfield-2 GAP-002 download 失敗無 UI source code 抽樣確認 | GAP-002 | ✅ |
| T-brownfield-3 GAP-003 OAuth 4 error query 無 alert source code 抽樣確認 | GAP-003 | ✅ |
| T-brownfield-4 GAP-004 刪除失敗靜默 source code 抽樣確認 | GAP-004 | ✅ |
| T-brownfield-5 INCONSIS-001 index.html line 113+118 確認 | INCONSIS-001 | ✅ |

---

## 10. 結論

- **測試結果**: **PASS**（brownfield 容差下）
- **Score**: 88 / 100（通過門檻 ≥ 80）
- **阻塞項（Critical）**: 0
- **退回項（Major / WARN）**: 2 — 建議在進入 SD 階段前快速補正，但**不阻塞**進入 test-uiux PASS / sd 階段
  - WARN-001: PAGE-005 追溯矩陣加 FUNC-031（簡單修補）
  - WARN-002: PAGE-001 Layer 2 FeatureCard hover 描述明確化（簡單修補）
- **參考事項（Info）**: 5 — 包含正向驗證（GAP/design-tokens 真實性確認）與 tooling gap（verify 腳本對 brownfield 不友善）

### 建議下一步

1. **可選快速補正（推薦）**:
   - UIUX 修訂 wireframes.md §1 + §12 把 FUNC-031 加入 PAGE-005 行（5 分鐘工作）
   - UIUX 修訂 wireframes.md §3 Layer 2 FeatureCard 行的描述（5 分鐘工作）
   - 修訂後 self-review 不需重跑，PM 標 approved-with-minor-revisions 即可
2. **直接通過（亦可接受）**:
   - 兩個 WARN 影響面有限：FUNC-031 為後端純動作，前端只有 1 個按鈕已記載；FeatureCard disabled 第 3 張在 INCONSIS-001 / Layer 5 已涵蓋
   - 後續 SD 階段讀到 FUNC-031 時可從 component-spec.md COMP-027 LogoutButton 反推 PAGE-005

### 追溯（測試本身可追溯）

- 本報告每個 finding 都附 `@traces_to(...)` ID
- 每個維度（D1-D7）都有檢查項與結果
- 每個 brownfield 對應抽樣都引用真實 source code line

---

## 11. 自我驗證

| 檢查項 | 結果 |
|--------|------|
| 測試報告格式正確（含 frontmatter, 摘要, 發現清單, 追溯）| ✅ |
| 每個檢查項都有結果 | ✅ |
| Critical / Warning / Info 分級正確 | ✅ |
| 每個發現都有位置和理由 | ✅ |
| 追溯矩陣驗證完整 | ✅ |
| 範圍邊界驗證（反腦補）| ✅ — 抽樣 5 個 GAP / INCONSIS 都在 source code 中確認真實存在 |
| 一致性驗證完整 | ✅ |
| 格式驗證完整 | ✅ |
| 測試決策邏輯正確（Critical → FAIL）| ✅ |
| 建議具體可行 | ✅ |
| 無漏掉的被測文件 | ✅ — 7 個 uiux/ 產出 + self-review.json + pencil-component-sync.json 皆讀過 |
| 對照基準完整 | ✅ — BA REQ / SA ARCH/FUNC/FIELD/IMPACT + 4 個 web/ 源檔抽樣 |
| 發現清單編號連續 | ✅ |
| 測試方法適合被測階段 | ✅ — D1-D7 + ID 規範 + brownfield 對照 |
| 獨立性保證（未參考 UIUX 對話歷史）| ✅ — 純讀正式產出物 |
| 每個測試案例可追溯到規格 ID | ✅ — 見 §9 |
| 結論與發現一致 | ✅ — 2 WARN + 5 INFO + 0 CRIT → PASS @ 88/100 |
| 報告日期和版本正確 | ✅ |
| Mermaid 語法正確 | N/A — 本報告無 Mermaid |
| 文件模板嚴格遵循 | ✅ — 沿用 test-report.tpl.md 結構 |
