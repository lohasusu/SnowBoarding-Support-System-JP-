---
document_id: "FEREPORT-TASK-002-v1.0"
title: "FE 變更報告 — SQLite → PostgreSQL 持久化遷移（No-FE-Changes）"
version: "1.0"
date: "2026-06-11"
author: "FE"
task_id: "TASK-002"
phase: "fe"
mode: "no-op"
source_documents:
  - "FEMAP-TASK-002-v1.0 (.sdlc/tasks/TASK-002/sd/fe-api-mapping.md)"
  - "REQ-TASK-002-v1.0 §1.4 (BA 範圍排除聲明)"
  - "ARCH-TASK-002-v1.0 (SA 架構不變項)"
  - "state.json TASK-002.phases.uiux.status = skipped"
approval:
  reviewer: "PM"
  date: ""
  result: "Pending"
  notes: ""
---

# FE 變更報告 — SQLite → PostgreSQL 持久化遷移

## 1. 結論（TL;DR）

**0 FE changes confirmed.** 本 TASK 為純後端持久化遷移（SQLite → PostgreSQL），FE 階段為 no-op：

| 指標 | 值 |
|------|---|
| 新增檔案 | 0 |
| 修改檔案 | 0 |
| 刪除檔案 | 0 |
| LOC 變更 | 0 |
| 新依賴套件 | 0 |
| 新路由 / 新頁面 | 0 |
| 偏差數 [DEVIATION] | 0 |

## 2. 為何 0 FE 變更（證據鏈）

引用 SD fe-api-mapping.md §1.1「無 FE 變更」表格：

| 來源 | 證據 | 推論 |
|------|------|------|
| **BA requirement-spec.md §1.4「不在範圍內」** | 「認證流程外部行為變更（HTTP 狀態碼 / cookie 行為 / OAuth flow / Email 驗證流程）」明示排除 | 既有 28 endpoint 外部 contract 不變 → FE 無變動需求 |
| **SA system-arch.md §1 架構不變項** | 「28 個 API endpoint 外部行為零變化（NFR-002 強制保證）」「6 個既有 MOD (MOD-001..006) 邊界完全不變」 | API 契約不變 → 前端 fetch 邏輯不變 |
| **state.json TASK-002.phases.uiux.status** | `"skipped"` / skipReason: 「純後端重構 — SQLite→PostgreSQL 持久層遷移，無 UI 變更」 | 無 UIUX wireframes / component-spec → 無新元件需實作 |
| **state.json TASK-002.phases.test-uiux.status** | `"skipped"` / skipReason: 「依賴的 uiux 階段已 skipped，無被測產出」 | 對應 testing 也排除 — 雙重確認 |
| **SD code-arch.md §2** | `web/templates/` + `web/static/js/` 標 [REUSE] | SD 直接指示 FE 工件 100% 重用，不可動 |
| **SD api-spec.md** | API-101 `GET /api/db/healthz` 為唯一新 API；fe-api-mapping §3 明示其呼叫者為 Deployer / Railway / Operator / Monitor，**非 FE 元件** | API-101 不需 FE 整合 |

## 3. FE 工件清單（逐檔零修改驗證）

按 SD fe-api-mapping.md §1.2 列出的 FE 工件範圍，FE 逐一檢查：

### 3.1 `web/static/js/*.js`（4 個檔案）

| 檔案 | 行數 | 修改 | DB-related 關鍵字搜尋 | 結論 |
|------|------|------|----------------------|------|
| `auth.js` | 98 | 0 | 0 hits | ✅ 不動 |
| `ski.js` | 181 | 0 | 0 hits | ✅ 不動 |
| `flight.js` | 250 | 0 | 0 hits | ✅ 不動 |
| `plan.js` | 225 | 0 | 0 hits | ✅ 不動 |
| **小計** | **754 LOC** | **0** | **0** | ✅ |

關鍵字 = `sqlite|postgres|postgresql|migration|migrate|psycopg|DATABASE_URL|snowtrip\.db|\.db|database|資料庫`（case-insensitive）

### 3.2 `web/templates/*.html`（8 個檔案，含 auth/ 子目錄）

| 檔案 | 行數 | 修改 | DB-related 關鍵字搜尋 | 結論 |
|------|------|------|----------------------|------|
| `base.html` | 189 | 0 | 0 hits | ✅ 不動 |
| `index.html` | 177 | 0 | 0 hits | ✅ 不動 |
| `ski.html` | 97 | 0 | 0 hits | ✅ 不動 |
| `flight.html` | 124 | 0 | 0 hits | ✅ 不動 |
| `plan.html` | 114 | 0 | 0 hits | ✅ 不動 |
| `profile.html` | 69 | 0 | 0 hits | ✅ 不動 |
| `auth/login.html` | 109 | 0 | 0 hits | ✅ 不動 |
| `auth/register.html` | 40 | 0 | 0 hits | ✅ 不動 |
| **小計** | **919 LOC** | **0** | **0** | ✅ |

### 3.3 Vue / Vite components

| 項目 | 狀態 |
|------|------|
| Vue / Vite 重構 | **未開始**（CLAUDE.md 標「未來重構」）— 本 TASK 不在此範圍 |

### 3.4 UIUX 輸入工件（按 sdlc-fe Step 0 預期必讀）

| 工件 | 狀態 | 處理方式 |
|------|------|---------|
| `uiux/wireframes.md` | 不存在（UIUX skipped）| 無 PAGE-NNN 需實作 → sdlc-fe Rule 3「頁面數 = wireframes PAGE 數」自動滿足（0 = 0）|
| `uiux/component-spec.md` | 不存在 | 無 COMP 需實作 |
| `uiux/design-system.md` | 不存在 | 無 Design Token 需引用 → sdlc-fe Rule 1（零裸色碼）+ Rule 2（零裸間距）N/A |
| `uiux/design-tokens.json` | 不存在 | 同上 |

## 4. API-101 觀察者映射（FE 不參與）

依 SD fe-api-mapping §3：

| 呼叫者 | 角色 | FE 涉入？ |
|--------|------|---------|
| Deployer | FUNC-107 production cutover smoke test | ❌ 否 |
| Railway healthcheck | 平台層輪詢 | ❌ 否 |
| Operator | 異常排查 | ❌ 否 |
| Monitoring | 未來指標匯出 | ❌ 否 |
| Tester (test-be) | NFR-001 持久性驗證 | ❌ 否（後端測試） |

**結論**: API-101 不需 FE fetch 呼叫、不需 dashboard UI、不需頁面整合。

## 5. 一致性檢查（sdlc-fe Rules）

| Rule | 適用？ | 驗證結果 |
|------|------|---------|
| Rule 1: 零裸色碼 | N/A（無 FE 變更 → 無新樣式）| ✅ 自動滿足 |
| Rule 2: 零裸間距 | N/A（同上）| ✅ 自動滿足 |
| Rule 3: 頁面數 = wireframes PAGE 數 | N/A（uiux skipped → 0 PAGE 需實作 = 0 PAGE 變更）| ✅ 自動滿足 |
| Rule 4: 偏差標記 | N/A（無實作 → 無偏差）| ✅ [DEVIATION]=0 |
| Rule 5: UI 文字照抄規格 | N/A（無新 UI Copy）| ✅ 自動滿足 |
| Rule 6: TASK 範圍圍欄 | 適用 — SD 未授權任何 FE 檔案修改 | ✅ 0 file 改動 |
| Rule 7: 編譯即正確性底線 | N/A（無 TypeScript/TSX；vanilla JS + Jinja2）| ✅ 自動滿足 |

## 6. 反越界自檢

| 不可做的事 | 自檢 |
|-----------|------|
| 自行新增 JS / 模板檔案 | ✅ 沒做 |
| 自行為 API-101 加 dashboard UI | ✅ 沒做（不在 BA 範圍）|
| 自行翻譯 / 改 UI 文字 | ✅ 沒做（sdlc-fe Rule 5）|
| 動既有 28 endpoint 的 fetch 邏輯 | ✅ 沒做（NFR-002 強制不變）|
| 修改前 TASK（TASK-001）產出 | ✅ 沒做（sdlc-fe Rule 6）|

## 7. NFR-002 22 AC FE 影響分析

詳見 SD fe-api-mapping.md §2（22 AC 逐一評估表）。從 **FE 視角**摘要：

- 22 AC 的 FE 行為 = HTTP request/response 流（auth.js / flight.js / ski.js / plan.js 內既有 `fetch()` 呼叫）
- API 外部 contract 不變（NFR-002 保證 → SD api-spec.md 28 個 endpoint 標 [REUSE]）
- 既有 fetch 程式碼**無需任何修改**即可繼續正確運作
- 預期 FE 端 22 / 22 AC 通過

## 8. [FE 建議]（非規格範圍）

> **嚴格隔離**: 以下為 FE 視角建議，**不在本 TASK BA 授權範圍內**，僅供 PM 規劃後續 TASK 參考。

### [FE 建議 1]: API-101 健康狀態可選擇納入 Profile / 維運頁面

- **理由**: API-101 healthcheck 目前僅供 Deployer / Railway / Monitor 消費；若未來開設「管理員儀表板」TASK，可考慮在 Profile 頁面（管理員角色）加 DB health badge（綠/紅圓點）
- **影響**: 0（不在本 TASK 範圍 — BA 未要求）
- **建議時機**: 新 TASK「admin dashboard」啟動時納入

### [FE 建議 2]: Vue / Vite 重構 TASK 啟動前，建議先建立既有 28 endpoint 的 API client TypeScript 型別

- **理由**: CLAUDE.md 標「Vue + Vite（前端，未來重構）」；未來重構時若有強型別 OpenAPI client，可大幅降低 PG migration 後的迴歸風險（搭配 SD api-spec.yaml OpenAPI 機器可讀規格）
- **影響**: 0（本 TASK 範圍外）
- **建議時機**: Vue 重構 TASK kickoff 前的 SA 階段

## 9. 自我驗證

| 檢查項 | 通過 | 說明 |
|--------|------|------|
| 確認 SD fe-api-mapping 明示 0 FE 變更 | ✅ | §2 證據鏈 |
| 實際檢查 FE 程式碼無 DB-related 字串 | ✅ | §3.1 + §3.2（12 檔 1673 LOC、0 hits）|
| 實際 git diff 確認 0 file 變更 | ✅ | §3 統計（0 modified）|
| API-101 確認非 FE 元件 | ✅ | §4 |
| sdlc-fe Rules 1-7 全部驗證 | ✅ | §5 |
| 反越界自檢通過 | ✅ | §6 |
| NFR-002 22 AC FE 視角分析 | ✅ | §7 |
| [FE 建議] 物理隔離 | ✅ | §8 標明非規格範圍 |
| 沒有 [BLOCKED_ON_SD] | ✅ | 規格充分，無需阻塞 |
| 沒有 [DEVIATION] / [INTERPRETATION] | ✅ | 0 偏差 |

**總分**: 95 / 100（詳見 self-review.json）
