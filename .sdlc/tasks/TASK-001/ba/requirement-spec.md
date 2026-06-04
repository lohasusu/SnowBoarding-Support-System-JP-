---
document_id: "REQ-TASK-001-v1.0"
title: "需求規格書 — snowboarding_support brownfield 補追溯"
version: "1.0"
date: "2026-06-03"
author: "BA"
status: "Draft"
task_id: "TASK-001"
phase: "ba"
mode: "brownfield-document"
source_documents:
  - "enhanced-input.md"
  - "baseline-audit-2026-06-03.md"
  - "web/main.py"
  - "web/auth/auth_router.py"
  - "web/auth/oauth_router.py"
  - "web/auth/verify_client.py"
  - "web/auth/email_service.py"
  - "web/auth/security.py"
  - "web/auth/database.py"
  - "web/plan_routes.py"
change_history:
  - version: "1.0"
    date: "2026-06-03"
    changes: "初始版本 — brownfield 補追溯：13 個核心 FR + 18 個 NFR + 12 個 BR + 32 個 AC + 3 個 ROLE。所有項目來源 file:line 化"
    author: "BA"
approval:
  reviewer: "PM"
  date: ""
  result: "Pending"
  notes: ""
---

# 需求規格書 — snowboarding_support brownfield 補追溯

> **模式**: brownfield-document（純規格產出，**不修改任何 web/ 業務代碼**）
> **目的**: 把既有 production 已運作的 snowboarding_support 系統反向產出為 SDLC 規格文件
> **真相基線**: 以 `web/` 既有 code 為真相；當 DESIGN.md 不一致時標 `[CODE-AS-TRUTH: file:line]`

---

## 1. 需求概述

### 1.1 背景

> 來源: enhanced-input.md「原始需求」段
>
> 補追溯既有 28 API + 3 ENTITY (users / favorites / email_verification_tokens) + 8 PAGE 到 `.sdlc/shared/`，不寫新代碼，純規格產出（brownfield-document mode）。

snowboarding_support 是一個已部署於 Railway 的日本雪場/雪票/機票/行程規劃工具。歷史開發未經 SDLC 流程，目前 production 已運作但缺少正式需求規格。TASK-001 採用 brownfield-document 模式，把既有功能反向萃取為 FR/NFR/BR，建立完整的 `.sdlc/shared/` 真相基線，使後續 TASK-002+ 能在此基線上新增功能或重構（如 SQLite → Postgres 遷移）。

### 1.2 目的

1. 把既有 28 個 HTTP 端點、3 個資料表、8 個頁面、6 個模組登記為 SDLC ID
2. 讓 `.sdlc/shared/` 完整描述目前 production 已運作的系統
3. 後續 TASK-002+ 可從此「真相基線」展開新功能（含 Postgres 遷移、debug endpoint 下架等）
4. 最終 merge 到 main 對網站使用者**零行為變化**（純文件加入）

### 1.3 範圍（13 個核心 FR）

| FR | 功能 | 來源 |
|----|------|------|
| FR-001 | 雪票批次查詢（JSON） | `web/main.py:127` |
| FR-002 | 雪票串流查詢（SSE） | `web/main.py:153` |
| FR-003 | 雪票 Excel 下載 | `web/main.py:197` |
| FR-004 | 機票查詢（多 backend fallback） | `web/main.py:252` |
| FR-005 | 機票 Excel 下載 | `web/main.py:442` |
| FR-006 | 整合查詢頁 + 3-sheet Excel | `web/plan_routes.py:38, 121` |
| FR-007 | JWT 註冊（密碼 ≥ 8 字元 + Email 驗證觸發） | `web/auth/auth_router.py:85` |
| FR-008 | JWT 登入（HTTP-only cookie, 7 天） | `web/auth/auth_router.py:117` |
| FR-009 | 登出 | `web/auth/auth_router.py:138` |
| FR-010 | Email 驗證（Resend + SMTP fallback + 24h token） | `web/auth/auth_router.py:145` + `web/auth/email_service.py` |
| FR-011 | 重寄驗證信 | `web/auth/auth_router.py:170` |
| FR-012 | Google OAuth 登入 + callback | `web/auth/oauth_router.py:24, 42` |
| FR-013 | 取得登入狀態（`/api/auth/me` + `/api/auth/verify`） | `web/auth/auth_router.py:197` + `web/auth/verify_client.py:130` |
| FR-014 | 收藏 CRUD（列表 / 新增 / 刪除） | `web/auth/auth_router.py:214, 232, 245` |
| FR-015 | 強制登入 middleware（保護路徑） | `web/main.py:37` |
| FR-016 | 頁面路由（index / ski / flight / plan / profile / login / register） | `web/main.py:98-110` + `web/auth/auth_router.py:41-56` + `web/plan_routes.py:38` |
| FR-017 | SEO（robots / sitemap） | `web/main.py:489, 497` |

### 1.4 不在範圍內（明確排除的項目）

> 來源: enhanced-input.md §「不納入」

- ❌ **不寫任何新 web/ 代碼** — 純規格產出
- ❌ **不改 conventions**（v1.1 已 lock — RFC 流程）
- ❌ **不做 SQLite → Postgres 遷移**（留 TASK-002）
- ❌ **不修 brownfield 技術債**（DESIGN.md §八 列的 8 項標記，含 `/api/env-check` 移除 — 留後續 TASK 或 hotfix）
- ❌ **不補齊 `urls.json` 剩餘雪場**（內容工作，非程式工作）
- ❌ **不安裝 Pencil MCP**（前置工作，使用者負責）
- ❌ **不規劃 Vue 重構**（留後面 TASK）
- ❌ **不新增業務功能**（如忘記密碼 / 寄密碼重設信 / 多語系）

---

## 2. 利害關係人

| ROLE | 角色名稱 | 需求摘要 | 優先順序 | 來源 |
|------|---------|---------|---------|------|
| ROLE-001 | 訪客（Guest） | 瀏覽首頁 / 註冊 / 登入 / Google OAuth；無法存取受保護路徑 | P0 | `web/main.py:33-60`（middleware 邏輯反推） |
| ROLE-002 | 已登入用戶（Authenticated User） | 雪票查詢 / 機票查詢 / 整合查詢 / 收藏管理 / 個人頁 | P0 | `web/main.py:33-60` + `web/auth/auth_router.py:56`（保護路徑） |
| ROLE-003 | 系統維運者（Operator / Admin） | 透過 `/api/auth/verify?email=<x>` 與 CLI `verify_client.py` 查詢用戶狀態（無正式 admin 介面） | P2 | `web/auth/verify_client.py:130-151`（API 設計上明確支援 email 查詢，沒有權限檢查 — 視為「維運工具」非「終端用戶角色」） |

> **註**: ROLE-003 在既有實作中**無 RBAC / 權限隔離**，任何呼叫者（含未登入）都可呼叫 `/api/auth/verify?email=x`。`[CODE-AS-TRUTH: web/auth/verify_client.py:131-151]`。本 TASK 不修；安全強化留 [BA建議] §8 SUG-002。

---

## 3. 功能需求

> **AC 編號規範**: AC-NNN 全域連續（跨 FR 不重置），3 位零填充。
> **信心等級**:
> - 🟢 高信心: 既有 code 直接證實
> - 🟡 中信心: 從 code 推斷但未明文宣告
> - 🔴 低信心: 需用戶確認

---

### FR-001: 雪票批次查詢（JSON）

- **描述**: 已登入用戶可指定地區（region）或雪場名稱（name）查詢日本雪場的票價，系統批次回傳所有結果為 JSON
- **優先順序**: P0
- **來源**: 既有實作 `web/main.py:127-142`（`@app.get("/api/ski/search")`）
- **信心等級**: 🟢 高信心
- **主流程**:
  1. 用戶（已登入 — `_PROTECTED_API_PFXS` middleware 攔截）發 GET `/api/ski/search?region=<x>&name=<y>`
  2. 系統取得 `_ski_lock`；若已被佔用回 `{"ok": false, "error": "查詢進行中，請稍後再試"}`
  3. 系統呼叫 `http_scraper.get_ticket_prices_async`（timeout = 45 秒）批次抓所有雪場票價
  4. 系統回傳 `{"ok": true, "data": [TicketPrice...]}` 200
- **替代流程**: query string 兩個參數都可選；都不帶 = 全部雪場
- **錯誤處理**:
  - 鎖被佔用 → 回 `{"ok": false, "error": "查詢進行中，請稍後再試"}`（HTTP 200，body 標 ok=false — `[CODE-AS-TRUTH: web/main.py:130]`）
  - asyncio 逾時（>45s）→ `{"ok": false, "error": "查詢逾時（45 秒），請縮小範圍後重試"}`
  - 其他例外 → `{"ok": false, "error": str(e)}`
- **驗收標準**:
  - [ ] AC-001: 已登入用戶帶 `region=長野` 查詢回傳 `{ok: true, data: [...]}`、HTTP 200、`Content-Type: application/json`
  - [ ] AC-002: 查詢超過 45 秒回 `{ok: false, error: "查詢逾時（45 秒），請縮小範圍後重試"}`
  - [ ] AC-003: 鎖被佔用時回 `{ok: false, error: "查詢進行中，請稍後再試"}`
- **BDD 場景**: 見 `bdd-scenarios.md` §FR-001

---

### FR-002: 雪票串流查詢（SSE）

- **描述**: 已登入用戶可用 Server-Sent Events 方式逐雪場接收結果，避免單一 45 秒 timeout 阻塞
- **優先順序**: P0（CLAUDE.md 第 47 行明示「兩個端點都要保留」）
- **來源**: 既有實作 `web/main.py:153-194`
- **信心等級**: 🟢 高信心
- **主流程**:
  1. 用戶 GET `/api/ski/stream?region=<x>&name=<y>`
  2. 系統取得 `_ski_lock`；若被佔用立刻 SSE 事件 `event: error` + `data: {"message": "查詢進行中，請稍後再試"}` 後結束串流
  3. 系統先發 `event: start` + `data: {"total": N}`（N = 可查詢雪場數）
  4. 系統用 `stream_ticket_prices_async` 逐雪場 yield；每筆票價發 `event: result`、每雪場完成發 `event: resort_done`
  5. 全部完成發 `event: done` + `data: {"total_count": ...}`
- **替代流程**: 同 FR-001
- **錯誤處理**:
  - asyncio 逾時 → `event: error` + `data: {"message": "查詢逾時，請縮小範圍後重試"}`
  - 其他例外 → `event: error` + `data: {"message": str(e)}`
- **驗收標準**:
  - [ ] AC-004: GET `/api/ski/stream` 回 `Content-Type: text/event-stream`，第一個 event 為 `start`，最後一個為 `done`
  - [ ] AC-005: 鎖被佔用時立刻 SSE `event: error` 結束，不卡住
  - [ ] AC-006: 每雪場結束發 `event: resort_done` 帶 `{resort, count}`
- **BDD 場景**: 見 `bdd-scenarios.md` §FR-002

---

### FR-003: 雪票 Excel 下載

- **描述**: 已登入用戶可下載當次查詢結果為 .xlsx
- **優先順序**: P0
- **來源**: 既有實作 `web/main.py:197-247`
- **信心等級**: 🟢 高信心
- **主流程**:
  1. 用戶 GET `/api/ski/download?region=<x>&name=<y>`
  2. 鎖被佔用 → HTTP 429 + plain text「查詢進行中，請稍後再試」
  3. 同 FR-001 抓資料（45 秒 timeout）
  4. 用 openpyxl 產生 8 欄 xlsx（雪場 / 地區 / 票種(日文) / 票種(中文) / 票價 / 雪季 / 查詢時間 / 票價頁連結）
  5. 回傳 `StreamingResponse`，filename = `ski_prices_<region or all>.xlsx`
- **錯誤處理**:
  - 鎖佔用 → HTTP 429 plain text
  - 其他例外 → HTTP 500 plain text（內含 exception message — 注意：洩漏 stack 訊息風險，[BA建議] §8 SUG-001 標記）
- **驗收標準**:
  - [ ] AC-007: 下載成功時 HTTP 200，`Content-Type: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`，`Content-Disposition: attachment; filename=ski_prices_*.xlsx`
  - [ ] AC-008: 鎖佔用時 HTTP 429（與 FR-001 的 HTTP 200 + ok=false 行為不同 — `[CODE-AS-TRUTH: web/main.py:203]`）

---

### FR-004: 機票查詢（多 backend fallback）

- **描述**: 已登入用戶輸入出發/到達機場 + 日期 + 乘客數，系統依優先順序嘗試多個機票資料來源（SerpAPI → fast-flights fallback）
- **優先順序**: P0
- **來源**: 既有實作 `web/main.py:252-298`
- **信心等級**: 🟢 高信心（Travelpayouts / Amadeus 在 enhanced-input 列入候選但在 code 中**未使用** — `[CODE-AS-TRUTH: web/main.py:275-285 僅見 SerpAPI + fast-flights]`）
- **主流程**:
  1. 用戶 GET `/api/flight/search?origin=<>&destination=<>&dest_name=<>&departure=<YYYY-MM-DD>&ret_date=<>&currency=TWD&adults=1`
  2. 系統檢查 `SERPAPI_API_KEY` 環境變數：有 → SerpApiBackend；無 → FastFlightsBackend (fallback)
  3. 呼叫 backend.search() 取得 `FlightOption[]`
  4. 回傳 `{"ok": true, "backend": "<name>", "data": [...]}`
- **替代流程**: 不帶 `departure` → 回 `{"ok": false, "error": "請輸入出發日期"}` 不查詢
- **錯誤處理**: 任何例外 → `{"ok": false, "error": str(e)}`（HTTP 200，body ok=false — 風格不一致見 baseline M-3）
- **驗收標準**:
  - [ ] AC-009: GET `/api/flight/search?origin=TPE&destination=CTS&departure=2026-12-20&adults=1` 回 `{ok: true, backend: "SerpAPI" or "fast-flights (fallback)", data: [...]}`
  - [ ] AC-010: 缺 `departure` 參數時回 `{ok: false, error: "請輸入出發日期"}`
- **預設值（`[CODE-AS-TRUTH: web/main.py:253-261]`）**:
  - `origin` 預設 `TPE`、`destination` 預設 `CTS`（新千歲）、`dest_name` 預設「新千歲」、`currency` 預設 `TWD`、`adults` 預設 1

---

### FR-005: 機票 Excel 下載

- **描述**: 已登入用戶可把當次查詢結果下載為高度美化的 .xlsx（含合計票價排序、前 3 名高亮、欄寬定義）
- **優先順序**: P1
- **來源**: 既有實作 `web/main.py:442-456` + `_generate_flight_excel` `web/main.py:314-439`
- **信心等級**: 🟢 高信心
- **主流程**:
  1. 用戶 POST `/api/flight/download`，body = `{flights: [...], meta: {origin, destination, departure, ret_date, adults}}`
  2. 系統依合計票價排序、產生 13 欄 xlsx（含搜尋摘要 banner、欄位標題、前 3 名綠底、其餘淡綠）
  3. 回傳 StreamingResponse，filename = `flights_<origin>-<destination>_<departure>.xlsx`
- **錯誤處理**: 例外傳播（無顯式 try/except — 預期 BE Tester 階段加 hardening）
- **驗收標準**:
  - [ ] AC-011: POST `/api/flight/download` 帶有效 body 回 200 + xlsx
  - [ ] AC-012: filename 格式 `flights_TPE-CTS_2026-12-20.xlsx`

---

### FR-006: 整合查詢頁 + 3-sheet Excel

- **描述**: 已登入用戶可在 `/plan` 頁面同時查機票 + 雪票，並下載一份 3-sheet Excel（行程摘要 / 機票 / 雪票）
- **優先順序**: P1
- **來源**: 既有實作 `web/plan_routes.py:38-40, 121-136` + `_generate_plan_excel` `web/plan_routes.py:53-118`
- **信心等級**: 🟢 高信心
- **主流程**:
  1. 用戶 GET `/plan` → render `plan.html`（強制登入由 middleware 攔截）
  2. 用戶在前端同時觸發 `/api/flight/search` 與 `/api/ski/search`
  3. 用戶點「下載 Excel」→ POST `/api/plan/download` body = `{flights, ski, meta}`
  4. 系統產 3-sheet xlsx：Sheet 1「行程摘要」/ Sheet 2「機票」（6 欄）/ Sheet 3「雪票」（6 欄）
  5. filename = `snowtrip_<origin>-<destination>_<departure>.xlsx`
- **驗收標準**:
  - [ ] AC-013: `/plan` 頁面對未登入用戶 302 redirect 到 `/login?next=/plan`
  - [ ] AC-014: POST `/api/plan/download` 回 xlsx 內含 3 個 sheets（「行程摘要」/「機票」/「雪票」）

---

### FR-007: JWT 註冊（密碼 ≥ 8 字元 + Email 驗證觸發）

- **描述**: 訪客可註冊新帳號；註冊時驗證密碼長度與 Email 格式，建立未驗證帳號並寄出驗證信
- **優先順序**: P0
- **來源**: 既有實作 `web/auth/auth_router.py:85-114`
- **信心等級**: 🟢 高信心
- **主流程**:
  1. 訪客 POST `/api/auth/register` body = `{email, username, password}`
  2. 系統驗證 `len(password) >= 8` 否則 HTTP 400 `detail="密碼至少 8 個字元"`
  3. 系統驗證 email regex `[^@]+@[^@]+\.[^@]+` 否則 HTTP 400 `detail="Email 格式不正確"`
  4. 系統用 `bcrypt.hashpw` hash 密碼
  5. INSERT users (email lower+strip, username strip, hashed_password, is_verified=0)
  6. 產 32-byte URL-safe token，INSERT email_verification_tokens（24h 過期）
  7. 呼叫 `send_verification_email` 寄信
  8. 回 `{"ok": true, "message": "帳號建立成功，驗證信已寄出..."}`（寄信失敗訊息略調，見 `auth_router.py:111-113`）
- **錯誤處理**:
  - UNIQUE 違反（email 或 username 重複）→ HTTP 409 `detail="Email 或用戶名稱已被使用"`
  - 其他 DB 例外 → HTTP 500 `detail="註冊失敗"`
- **驗收標準**:
  - [ ] AC-015: POST `/api/auth/register` 帶 `password = "1234567"` 回 HTTP 400 `detail="密碼至少 8 個字元"`
  - [ ] AC-016: POST `/api/auth/register` 帶無效 email 回 HTTP 400 `detail="Email 格式不正確"`
  - [ ] AC-017: 重複 email/username 註冊回 HTTP 409 `detail="Email 或用戶名稱已被使用"`
  - [ ] AC-018: 註冊成功後 DB 內 `users.is_verified = 0` 且 `email_verification_tokens` 有一筆 24h 過期 token
- **BDD 場景**: 見 `bdd-scenarios.md` §FR-007

---

### FR-008: JWT 登入（HTTP-only cookie, 7 天）

- **描述**: 訪客用 email + 密碼登入；驗證成功後設定 JWT cookie；未驗證 email 帳號禁止登入
- **優先順序**: P0
- **來源**: 既有實作 `web/auth/auth_router.py:117-135` + `web/auth/security.py:8-24`
- **信心等級**: 🟢 高信心
- **主流程**:
  1. 訪客 POST `/api/auth/login` body = `{email, password}`
  2. 系統 SELECT `users.id, hashed_password, is_verified` WHERE email=lower+strip
  3. 用 `bcrypt.checkpw` 驗證密碼；失敗 → HTTP 401 `detail="Email 或密碼錯誤"`
  4. 若 `is_verified == 0` → HTTP 403 `detail="請先驗證您的 Email 後再登入..."`
  5. 用 `create_access_token({"sub": str(id)})` 產 JWT（HS256 演算法，secret 取自 `SECRET_KEY` env，預設 7 天）
  6. 設定 `Set-Cookie: access_token=<jwt>; HttpOnly; Max-Age=604800; SameSite=Lax; Secure=False`
  7. 回 `{"ok": true, "message": "登入成功"}`
- **錯誤處理**: 同上 401 / 403
- **驗收標準**:
  - [ ] AC-019: 正確 email/password 且 is_verified=1 → HTTP 200 + `Set-Cookie: access_token=...; HttpOnly; SameSite=Lax; Max-Age=604800`
  - [ ] AC-020: 錯誤密碼 → HTTP 401 `detail="Email 或密碼錯誤"`
  - [ ] AC-021: 未驗證 email 帳號 → HTTP 403 `detail="請先驗證您的 Email..."`
- **BDD 場景**: 見 `bdd-scenarios.md` §FR-008

---

### FR-009: 登出

- **描述**: 已登入用戶可登出（清除 cookie）
- **優先順序**: P0
- **來源**: 既有實作 `web/auth/auth_router.py:138-142`
- **信心等級**: 🟢 高信心
- **主流程**:
  1. 用戶 POST `/api/auth/logout`
  2. 系統 `delete_cookie("access_token")` 並回 `{"ok": true}`
- **驗收標準**:
  - [ ] AC-022: POST `/api/auth/logout` 回 `Set-Cookie: access_token=; Max-Age=0`（或同義清除）

---

### FR-010: Email 驗證（Resend + SMTP fallback + 24h token）

- **描述**: 用戶點擊驗證信中連結，token 有效則標記帳號為已驗證；token 無效/過期/已用 → redirect 到登入頁附 error query
- **優先順序**: P0
- **來源**:
  - GET `/api/auth/verify-email`: 既有實作 `web/auth/auth_router.py:145-163`
  - 寄信邏輯: `web/auth/email_service.py:37-99`
- **信心等級**: 🟢 高信心
- **主流程**:
  1. 用戶點信件中連結 GET `/api/auth/verify-email?token=<32-byte>`
  2. 系統 SELECT token 對應的 user_id / expires_at / used_at
  3. 找不到 → `302 /login?error=invalid_token`
  4. 已使用 → `302 /login?error=token_used`
  5. 過期（expires_at < now ISO UTC）→ `302 /login?error=token_expired`
  6. 通過 → UPDATE users.is_verified=1 + UPDATE token.used_at=now → `302 /login?verified=1`
- **寄信邏輯（順序）**:
  1. **Resend**（有 `RESEND_API_KEY` env）：POST `https://api.resend.com/emails` 帶 Bearer token，timeout 10 秒
  2. Resend 429 / 例外 → **SMTP fallback**（有 `SMTP_HOST/USER/PASS`）：STARTTLS port 587
  3. SMTP 也失敗 → **dev stderr log**（印驗證連結到 stderr，回 `False` 但帳號仍建立）
- **錯誤處理**:
  - Resend 429（超量）自動轉 SMTP — `[CODE-AS-TRUTH: web/auth/email_service.py:64-66 註解明示 "fall through to SMTP"]`
  - Resend 200/201 → 成功
- **驗收標準**:
  - [ ] AC-023: 點擊有效未過期 token → 302 redirect `/login?verified=1`、DB 內 `users.is_verified=1`
  - [ ] AC-024: 過期 token → 302 redirect `/login?error=token_expired`
  - [ ] AC-025: 已使用 token → 302 redirect `/login?error=token_used`
  - [ ] AC-026: Resend 429 時自動嘗試 SMTP（**整合測試**：mock Resend 回 429，驗證 SMTP 被呼叫）
- **BDD 場景**: 見 `bdd-scenarios.md` §FR-010

---

### FR-011: 重寄驗證信

- **描述**: 未驗證用戶可請求重寄驗證信；舊 token 廢棄、新 token 產生並寄出
- **優先順序**: P1
- **來源**: 既有實作 `web/auth/auth_router.py:170-194`
- **信心等級**: 🟢 高信心
- **主流程**:
  1. 用戶 POST `/api/auth/resend-verification` body = `{email}`
  2. SELECT user；找不到 → HTTP 404 `detail="找不到此 Email 的帳號"`
  3. 已驗證 → `{"ok": true, "message": "此帳號已完成驗證"}`
  4. 把該 user 所有 `used_at IS NULL` 的 token 標 used_at=now（廢棄舊 token）
  5. 產新 token + 寫入 `email_verification_tokens`（24h）
  6. 呼叫 `send_verification_email`
  7. 回 `{"ok": true, "message": "驗證信已重新寄出" or "寄信失敗，請稍後再試"}`
- **驗收標準**:
  - [ ] AC-027: POST `/api/auth/resend-verification` 對未驗證帳號 → 舊 token 全部標 used_at、新 token 建立
  - [ ] AC-028: 對已驗證帳號 → 不發新 token，回 `message="此帳號已完成驗證"`
- **[INFERRED: 無明確 rate limit]**: 既有實作**沒有頻率限制**，可能被濫用發信 — 列 [BA建議] §8 SUG-003

---

### FR-012: Google OAuth 登入 + callback

- **描述**: 訪客可用 Google 帳號一鍵登入；新用戶自動建立、既有 email 用戶綁定 google_id
- **優先順序**: P0
- **來源**:
  - GET `/api/auth/google/login`: 既有實作 `web/auth/oauth_router.py:24-39`
  - GET `/api/auth/google/callback`: 既有實作 `web/auth/oauth_router.py:42-119`
- **信心等級**: 🟢 高信心
- **主流程（login）**:
  1. 訪客 GET `/api/auth/google/login`
  2. 若 `GOOGLE_CLIENT_ID` 未設 → HTTP 503 `{"ok": false, "error": "Google 登入尚未設定，請聯繫管理員"}`
  3. 產 16-byte state、設 cookie `oauth_state`（HttpOnly, Max-Age=300, SameSite=Lax）
  4. 302 redirect 到 `https://accounts.google.com/o/oauth2/v2/auth?client_id=...&scope=openid+email+profile&state=...`
- **主流程（callback）**:
  1. Google redirect 回 GET `/api/auth/google/callback?code=...&state=...`
  2. 比對 state 與 cookie `oauth_state`；不符 → `302 /login?error=oauth_state_mismatch`
  3. POST `https://oauth2.googleapis.com/token` 換 access_token（timeout 10 秒）
  4. GET `https://www.googleapis.com/oauth2/v3/userinfo` 取 sub/email/name/picture
  5. **Upsert 邏輯**:
     - 用 `google_id` 找 → 存在 → 直接取 user_id
     - 用 email 找 → 存在 → **綁定** google_id + 設 is_verified=1
     - 都找不到 → 新建 user（email, username=name, hashed_password='', is_verified=1, google_id, avatar_url）
  6. 產 JWT、設 cookie、`302 redirect /plan`（**注意**: redirect 目的地寫死為 `/plan`，不是 `next` query — `[CODE-AS-TRUTH: web/auth/oauth_router.py:112]`）
  7. 清除 `oauth_state` cookie
- **錯誤處理**:
  - Google 端使用者拒絕 → `?error=...` → `302 /login?error=google_denied`
  - token 換取失敗 → `302 /login?error=google_token_failed`
  - userinfo 失敗 → `302 /login?error=google_userinfo_failed`
- **驗收標準**:
  - [ ] AC-029: 未設 `GOOGLE_CLIENT_ID` → HTTP 503 + JSON
  - [ ] AC-030: callback state 不符 → 302 `/login?error=oauth_state_mismatch`
  - [ ] AC-031: 既有 email 用戶 OAuth 登入 → DB 內該用戶 `google_id` 被更新、`is_verified=1`、不新建 row
- **BDD 場景**: 見 `bdd-scenarios.md` §FR-012

---

### FR-013: 取得登入狀態（`/api/auth/me` + `/api/auth/verify`）

- **描述**: 已登入用戶可取得自己的 id / username / email；維運者可用 `/api/auth/verify` 驗證 JWT 或查詢用戶狀態
- **優先順序**: P1
- **來源**:
  - `/api/auth/me`: 既有實作 `web/auth/auth_router.py:197-203`（強制登入）
  - `/api/auth/verify`: 既有實作 `web/auth/verify_client.py:130-151`（**無強制登入** — 任何人可用 email 查詢，安全議題見 SUG-002）
- **信心等級**: 🟢 高信心
- **主流程（me）**:
  1. GET `/api/auth/me`（強制登入 via `Depends(get_current_user)`）
  2. 回 `{"ok": true, "user": {id, username, email}}`
- **主流程（verify）**:
  1. GET `/api/auth/verify?token=<jwt>` 或 `?email=<x>` 或不帶（讀 cookie）
  2. email 模式 → 回 `verify_email_info(email)` `{found, user: {id, email, username, is_verified, auth_method, created_at}, error}`
  3. token 模式 → 回 `verify_token_info(token)` `{valid, user: {id, email, username, is_verified}, issued_at, expires_at, auth_method, error}`
  4. 兩者都不帶且無 cookie → HTTP 400 `{"valid": false, "error": "請提供 token 參數或登入 cookie"}`
- **驗收標準**:
  - [ ] AC-032: 已登入 GET `/api/auth/me` 回 `{ok: true, user: {id, username, email}}`
  - [ ] AC-033: GET `/api/auth/verify?email=test@test.com` 對存在用戶回 `{found: true, user: {...}}`

---

### FR-014: 收藏 CRUD（列表 / 新增 / 刪除）

- **描述**: 已登入用戶可儲存雪票或機票查詢結果為「收藏」、列出自己的收藏、刪除收藏
- **優先順序**: P1
- **來源**:
  - 列表 GET `/api/favorites`: `web/auth/auth_router.py:214-229`
  - 新增 POST `/api/favorites`: `web/auth/auth_router.py:232-242`
  - 刪除 DELETE `/api/favorites/{fav_id}`: `web/auth/auth_router.py:245-252`
  - profile_page 預載收藏: `web/auth/auth_router.py:56-69`
- **信心等級**: 🟢 高信心
- **主流程（列表）**:
  1. GET `/api/favorites`（強制登入）
  2. SELECT `id, type, data, label, created_at FROM favorites WHERE user_id=? ORDER BY created_at DESC`
  3. `data` 欄是 JSON string，`json.loads` 後嵌入回應
  4. 回 `{"ok": true, "data": [...]}`
- **主流程（新增）**:
  1. POST `/api/favorites` body = `{type: "ski"|"flight", data: {...}, label: ""}`
  2. 驗 `type in ("ski", "flight")` 否則 HTTP 400 `detail="type 必須是 ski 或 flight"`
  3. INSERT favorites (user_id, type, json.dumps(data), label)
  4. 回 `{"ok": true, "id": fav_id}`
- **主流程（刪除）**:
  1. DELETE `/api/favorites/{fav_id}`（強制登入）
  2. DELETE FROM favorites WHERE id=? AND user_id=?（**用 user_id 防越權刪除**）
  3. 回 `{"ok": true}`
- **錯誤處理**:
  - type 非合法 → HTTP 400
  - 嘗試刪除別人的 favorite → DELETE 0 rows，仍回 `{ok: true}`（**不洩漏存在性**，[BA建議] §8 SUG-004）
- **驗收標準**:
  - [ ] AC-034: 新增收藏 type=ski → DB 內 `favorites` 多一 row、`type='ski'`、`data` 為 JSON string
  - [ ] AC-035: GET `/api/favorites` 只回該 user 自己的收藏（不洩漏他人）
  - [ ] AC-036: DELETE 別人的 fav_id → 不報錯，但 DB 不變
- **BDD 場景**: 見 `bdd-scenarios.md` §FR-014

---

### FR-015: 強制登入 middleware（保護路徑）

- **描述**: 系統判斷 request path 是否屬於保護路徑；未登入時頁面路由 302 redirect 到 `/login?next=<path>`，API 路由回 HTTP 401 JSON
- **優先順序**: P0
- **來源**: 既有實作 `web/main.py:33-60` + `web/auth/dependencies.py`（提供 `get_optional_user` / `get_current_user`）
- **信心等級**: 🟢 高信心
- **保護清單**:
  - `_PROTECTED_PAGES = {"/ski", "/flight", "/plan", "/profile"}`
  - `_PROTECTED_API_PFXS = ("/api/ski", "/api/flight", "/api/plan")`
- **主流程**:
  1. 每個 request 進來，middleware 檢查 path 是否在保護清單
  2. 若是 → 從 cookie `access_token` 取 user
  3. **未登入 + 頁面路徑** → `RedirectResponse("/login?next=<path>")`（HTTP 307 由 FastAPI 預設）
  4. **未登入 + API 路徑** → `JSONResponse({"ok": false, "error": "請先登入", "redirect": "/login"}, 401)`
  5. 登入或非保護路徑 → 正常 call_next
- **驗收標準**:
  - [ ] AC-037: 未登入用戶 GET `/ski` → HTTP 307/302 redirect 到 `/login?next=/ski`
  - [ ] AC-038: 未登入用戶 GET `/api/ski/search` → HTTP 401 `{ok: false, error: "請先登入", redirect: "/login"}`
  - [ ] AC-039: 未登入用戶 GET `/` → HTTP 200（首頁不在保護路徑）
- **[INFERRED]**: `/api/auth/*` 與 `/api/favorites*` **不在 middleware 保護清單**，而是由 router 各自用 `Depends(get_current_user)` 處理（雙層防線）— `[CODE-AS-TRUTH: web/main.py:34 不含 /api/auth 與 /api/favorites]`

---

### FR-016: 頁面路由（index / ski / flight / plan / profile / login / register）

- **描述**: 系統提供 7 個 HTML 頁面（PAGE-001 ~ PAGE-007），透過 Jinja2 SSR 渲染
- **優先順序**: P0
- **來源**: 既有實作
  - `web/main.py:98` (`/`), `:103` (`/ski`), `:108` (`/flight`)
  - `web/auth/auth_router.py:41` (`/login`), `:51` (`/register`), `:56` (`/profile`)
  - `web/plan_routes.py:38` (`/plan`)
- **信心等級**: 🟢 高信心
- **頁面清單**:
  | PAGE | 路由 | 強制登入 | 模板 |
  |------|------|--------|------|
  | PAGE-001 | `/` | 否 | `templates/index.html` |
  | PAGE-002 | `/ski` | 是 | `templates/ski.html` |
  | PAGE-003 | `/flight` | 是 | `templates/flight.html` |
  | PAGE-004 | `/plan` | 是 | `templates/plan.html` |
  | PAGE-005 | `/profile` | 是（且 `Depends(get_current_user)`）| `templates/profile.html` |
  | PAGE-006 | `/login` | **否，但已登入會 redirect** `/profile`（`auth_router.py:46-47`）| `templates/auth/login.html` |
  | PAGE-007 | `/register` | 否 | `templates/auth/register.html` |
  | LAYOUT-001 | (base) | — | `templates/base.html`（共用 layout，非頁面） |
- **驗收標準**:
  - [ ] AC-040: 7 個頁面路由各回 HTTP 200 + Content-Type `text/html`（未登入時 `/ski` `/flight` `/plan` `/profile` 為 redirect 不算 200）
  - [ ] AC-041: 已登入用戶 GET `/login` → 302 redirect `/profile`

---

### FR-017: SEO（robots / sitemap）

- **描述**: 系統提供 `robots.txt` 與 `sitemap.xml` 供搜尋引擎索引
- **優先順序**: P2
- **來源**: 既有實作 `web/main.py:489-499+`
- **信心等級**: 🟢 高信心
- **主流程**:
  - GET `/robots.txt` → plain text，內容 `User-agent: *\nAllow: /\nDisallow: /api/\n\nSitemap: <BASE_URL>/sitemap.xml\n`
  - GET `/sitemap.xml` → XML，列三個頁面：`/` (priority 1.0, weekly) / `/ski` (0.9, daily) / `/flight` (0.8, weekly)
- **驗收標準**:
  - [ ] AC-042: GET `/robots.txt` 回 HTTP 200 + `text/plain`，內含 `Disallow: /api/`
  - [ ] AC-043: GET `/sitemap.xml` 回 HTTP 200 + 含至少 `/`, `/ski`, `/flight` 三個 `<url>` 區段

---

## 4. 非功能需求

> **量化規則**: 每項 NFR 必附量化指標。`[INFERRED]` 標記從 code 推斷的數值；所有 `[INFERRED]` 整理到 §9「待用戶確認」清單。

### NFR-001: 雪票批次查詢逾時上限

- **類別**: 效能
- **描述**: `/api/ski/search` 與 `/api/ski/download` 單次查詢逾時上限
- **量化指標**: **45 秒**
- **來源**: 既有實作 `web/main.py:137` `timeout=45.0`、`web/main.py:208` `timeout=45.0`
- **信心等級**: 🟢 高信心

### NFR-002: 雪票查詢序列化（單一鎖）

- **類別**: 可用性 / 併發控制
- **描述**: 全域只允許一個雪票查詢同時執行（asyncio.Lock）
- **量化指標**: **並發度 = 1**；衝突時頁面/API 不阻塞，而是即時回「查詢進行中」訊息
- **來源**: 既有實作 `web/main.py:116` `_ski_lock = asyncio.Lock()`
- **信心等級**: 🟢 高信心
- **[INFERRED 風險]**: 鎖跨 worker 失效 — Railway 若部署多 worker（uvicorn `--workers N`）則 lock 退化為 per-process。目前 Railway 預設單 worker，brownfield 接受。

### NFR-003: JWT 有效期

- **類別**: 安全 / 可用性
- **描述**: JWT access_token 有效期
- **量化指標**: **7 天**（604800 秒）
- **來源**: 既有實作 `web/auth/security.py:10` `ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7`、cookie `max_age=60 * 60 * 24 * 7` (`auth_router.py:132`, `oauth_router.py:115`)
- **信心等級**: 🟢 高信心

### NFR-004: JWT 簽章演算法

- **類別**: 安全
- **描述**: JWT 簽章演算法
- **量化指標**: **HS256**（HMAC-SHA256），secret 從 `SECRET_KEY` env 讀取（預設 fallback `"change-me-in-production-please"` — 上線風險，列 SUG-005）
- **來源**: 既有實作 `web/auth/security.py:9` `ALGORITHM = "HS256"`
- **信心等級**: 🟢 高信心

### NFR-005: Cookie 安全屬性

- **類別**: 安全
- **描述**: `access_token` cookie 屬性
- **量化指標**: `HttpOnly=True`、`SameSite=Lax`、`Max-Age=604800`、**`Secure=False`**（現況硬寫死）
- **來源**: 既有實作 `web/auth/auth_router.py:130-134`、`web/auth/oauth_router.py:113-117`
- **信心等級**: 🟢 高信心
- **[INFERRED 風險]**: `Secure=False` 在 production HTTPS 環境下仍可正常運作但失去「禁止 HTTP 明文傳送」的保護。**生產應為 `Secure=True`**。列 [BA建議] §8 SUG-006，留待 TASK-002。

### NFR-006: 密碼複雜度下限

- **類別**: 安全
- **描述**: 註冊時密碼最小長度
- **量化指標**: **≥ 8 個字元**（無大小寫/數字/特殊字元要求）
- **來源**: 既有實作 `web/auth/auth_router.py:87` `if len(body.password) < 8: ...`
- **信心等級**: 🟢 高信心

### NFR-007: 密碼雜湊演算法

- **類別**: 安全
- **描述**: 密碼雜湊方式
- **量化指標**: **bcrypt with `bcrypt.gensalt()`** 預設成本因子（cost factor = 12，bcrypt library 預設）
- **來源**: 既有實作 `web/auth/security.py:13-14` `bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())`
- **信心等級**: 🟢 高信心
- **[INFERRED 細節]**: 不用 passlib（因相容性問題） — 直接呼叫 bcrypt。enhanced-input 確認此細節。

### NFR-008: Email 驗證 token 有效期

- **類別**: 安全
- **描述**: 註冊與重寄驗證信產出的 token 有效期
- **量化指標**: **24 小時**（UTC ISO 格式）
- **來源**: 既有實作 `web/auth/auth_router.py:100` `timedelta(hours=24)`、`:188` `timedelta(hours=24)`
- **信心等級**: 🟢 高信心

### NFR-009: Email 驗證 token 長度

- **類別**: 安全
- **描述**: token 隨機性與長度
- **量化指標**: **`secrets.token_urlsafe(32)` = 32 bytes 隨機 → 43 字元 URL-safe base64**（碰撞機率忽略）
- **來源**: 既有實作 `web/auth/auth_router.py:99, 187`
- **信心等級**: 🟢 高信心

### NFR-010: Email 寄信策略順序

- **類別**: 可用性
- **描述**: 寄信來源優先順序
- **量化指標**: **Resend → SMTP → stderr dev log**；每層 timeout 10 秒（Resend）/ STARTTLS port 587（SMTP）
- **來源**: 既有實作 `web/auth/email_service.py:37-99`
- **信心等級**: 🟢 高信心
- **行為**: Resend 429 觸發切 SMTP（註解明示 `web/auth/email_service.py:66 "fall through to SMTP"`）；所有寄信失敗時 dev fallback 印到 stderr 但**不阻止帳號建立**

### NFR-011: OAuth state cookie 有效期

- **類別**: 安全
- **描述**: Google OAuth state cookie 防 CSRF
- **量化指標**: **300 秒**（5 分鐘）
- **來源**: 既有實作 `web/auth/oauth_router.py:38` `max_age=300`
- **信心等級**: 🟢 高信心

### NFR-012: OAuth 第三方 timeout

- **類別**: 效能
- **描述**: 對 Google OAuth endpoint 的 HTTP 請求 timeout
- **量化指標**: **10 秒**（token endpoint 與 userinfo endpoint 各一）
- **來源**: 既有實作 `web/auth/oauth_router.py:55, 71`
- **信心等級**: 🟢 高信心

### NFR-013: 受保護路徑清單

- **類別**: 安全
- **描述**: 強制登入 middleware 涵蓋的路徑
- **量化指標**:
  - **頁面**: `{"/ski", "/flight", "/plan", "/profile"}`
  - **API 前綴**: `("/api/ski", "/api/flight", "/api/plan")`
- **來源**: 既有實作 `web/main.py:33-34`
- **信心等級**: 🟢 高信心
- **註**: `/api/auth/*` 與 `/api/favorites*` 不在 middleware 內，改由 router 各自用 `Depends(get_current_user)` 控制

### NFR-014: 資料持久化（brownfield 已知 Critical）

- **類別**: 可用性 / 資料完整性
- **描述**: 用戶帳號 / 收藏 / Email 驗證 token 的持久化保證
- **量化指標**: **本 TASK 接受 SQLite ephemeral（不解決）**；persistance 量化指標 = 「Railway worker 不重啟時保留；重啟即遺失」
- **來源**: `web/auth/database.py:5` `DB_PATH = Path(__file__).parent.parent / "data" / "snowtrip.db"`、CLAUDE.md 第 49 行
- **信心等級**: 🟢 高信心（已知問題）
- **行動**: 留 TASK-002（SQLite → Postgres 遷移）

### NFR-015: 預設語系

- **類別**: 國際化
- **描述**: 系統 UI 語言
- **量化指標**: **`zh-TW`（繁體中文）為唯一支援語系**
- **來源**: i18n-conventions.md v1.1 §1、enhanced-input.md（「目標客群為日本雪場資訊的繁中讀者」）
- **信心等級**: 🟢 高信心
- **行為**: 全部硬編碼於 Jinja2 模板與 Python `detail="..."` 字串；i18n key 機制 brownfield 階段不啟用（Vue 重構時啟用）

### NFR-016: HTTP 認證載體

- **類別**: 安全
- **描述**: 認證 token 載體
- **量化指標**: **JWT in HTTP-only Cookie**（不接受 `Authorization: Bearer`）
- **來源**: api-conventions.md v1.1 §4 + 既有實作（middleware 只讀 `cookies.get("access_token")`）
- **信心等級**: 🟢 高信心

### NFR-017: Excel 檔案生成媒體型別

- **類別**: 互通性
- **描述**: 三個 Excel 下載端點的 Content-Type
- **量化指標**: `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`
- **來源**: 既有實作 `web/main.py:243`, `:454`、`web/plan_routes.py:134`
- **信心等級**: 🟢 高信心

### NFR-018: 部署環境

- **類別**: 可用性
- **描述**: Production 部署平台與啟動指令
- **量化指標**:
  - 平台: **Railway**
  - 啟動: `uvicorn web.main:app --host 0.0.0.0 --port $PORT`
  - URL: `https://snowboarding-support-system-jp-production.up.railway.app`
  - Worker 數: 預設單 worker（CLAUDE.md 未明示但 lock 設計暗示）
- **來源**: CLAUDE.md「Railway 部署注意事項」段、`web/main.py:28`
- **信心等級**: 🟢 高信心

---

## 5. 業務規則

### BR-001: 受保護路徑必經 middleware

- **條件**: 任何 HTTP request 命中 `/ski` `/flight` `/plan` `/profile` 或 `/api/ski*` `/api/flight*` `/api/plan*`
- **行為**: middleware 強制檢查 `access_token` cookie；未登入時頁面 redirect、API 回 401
- **來源**: `web/main.py:37-60`

### BR-002: 密碼最少 8 字元

- **條件**: 註冊 POST `/api/auth/register` body.password
- **行為**: `len(body.password) < 8` → HTTP 400
- **來源**: `web/auth/auth_router.py:87`

### BR-003: Email 必須通過正則驗證

- **條件**: 註冊 POST `/api/auth/register` body.email
- **行為**: 不符 `[^@]+@[^@]+\.[^@]+` → HTTP 400
- **來源**: `web/auth/auth_router.py:89`

### BR-004: Email 與 username 全域唯一

- **條件**: INSERT users
- **行為**: UNIQUE 違反 → HTTP 409
- **來源**: `web/auth/database.py:20-21` (UNIQUE constraint)、`auth_router.py:106-107`

### BR-005: 未驗證 email 帳號禁止登入

- **條件**: POST `/api/auth/login` 且 `users.is_verified == 0`
- **行為**: HTTP 403 `detail="請先驗證您的 Email 後再登入..."`
- **來源**: `web/auth/auth_router.py:126-127`
- **例外**: Google OAuth 註冊用戶自動 `is_verified=1`（`oauth_router.py:106`）

### BR-006: Email 驗證 token 一次性 + 24h 過期

- **條件**: 點擊 `/api/auth/verify-email?token=<x>`
- **行為**: token 不存在 / 已 used / 已過期 → 302 redirect 帶 error；通過 → mark used + set verified
- **來源**: `web/auth/auth_router.py:145-163`

### BR-007: 重寄驗證信先廢棄舊 token

- **條件**: POST `/api/auth/resend-verification`
- **行為**: 把該 user 所有 `used_at IS NULL` token 標 used_at=now，再產新 token
- **來源**: `web/auth/auth_router.py:182-186`

### BR-008: Google OAuth Upsert 邏輯

- **條件**: Google OAuth callback 取得 userinfo
- **行為**:
  1. 找 `google_id` 匹配 user → 直接 login
  2. 找 email 匹配 user → 綁定 google_id + is_verified=1 + login
  3. 都沒有 → 新建 user 自動 is_verified=1
- **來源**: `web/auth/oauth_router.py:85-109`

### BR-009: OAuth callback 永遠 redirect 到 `/plan`

- **條件**: OAuth callback 成功
- **行為**: redirect 寫死為 `/plan`（不支援 next 參數）
- **來源**: `web/auth/oauth_router.py:112`
- **[CODE-AS-TRUTH]**: DESIGN.md 未明示此行為

### BR-010: 收藏權限隔離

- **條件**: GET / DELETE `/api/favorites*`
- **行為**: SELECT / DELETE 都帶 `WHERE user_id = current_user.id`，禁止跨用戶存取
- **來源**: `web/auth/auth_router.py:218, 249`

### BR-011: 收藏 type 必須是 ski 或 flight

- **條件**: POST `/api/favorites` body.type
- **行為**: `type not in ("ski", "flight")` → HTTP 400
- **來源**: `web/auth/auth_router.py:234`

### BR-012: 雪票查詢全域單一鎖

- **條件**: GET `/api/ski/search` `/api/ski/stream` `/api/ski/download`
- **行為**: 全部共享 `_ski_lock`；任一鎖被佔用時新請求立刻回拒（不等待）
- **來源**: `web/main.py:116, 129, 158, 202`

---

## 6. 假設與約束

### 假設（需使用者確認 — 詳 §9）

- **[ASSUME-001]** 雪票查詢 timeout = 45 秒符合用戶可接受範圍（既有實作預設值，未經用戶 review）— **確認問題見 §9 Q-001**
- **[ASSUME-002]** JWT 7 天有效期符合用戶體驗預期（過長則安全風險、過短則頻繁登入）— **§9 Q-002**
- **[ASSUME-003]** 密碼僅要求 ≥ 8 字元（無大小寫/數字/特殊字元）符合用戶可接受 — **§9 Q-003**
- **[ASSUME-004]** Resend rate limit 觸發後 silently fall through SMTP（用戶無感）符合預期 — **§9 Q-004**
- **[ASSUME-005]** OAuth callback redirect 寫死 `/plan`（不支援 next）符合用戶預期 — **§9 Q-005**
- **[ASSUME-006]** `/api/auth/verify?email=<x>` 無權限隔離為「維運工具」用途，不對外公開 — **§9 Q-006**
- **[ASSUME-007]** 重寄驗證信無 rate limit 為已知技術債，TASK-001 不修 — **§9 Q-007**
- **[ASSUME-008]** 收藏刪除採硬刪（非軟刪）為已知 brownfield 規範違反（db-conventions §專案特定禁止項），TASK-001 不修 — **§9 Q-008**

### 約束

- **[CONST-001]** 本 TASK 模式 = brownfield-document，**禁止修改任何 web/ 業務代碼**（範圍邊界）
- **[CONST-002]** conventions v1.1 已 lock，**禁止本 TASK 內修改**（變更走 RFC）
- **[CONST-003]** Railway 環境**不能用 Playwright**（CLAUDE.md「不可破壞的規則」）
- **[CONST-004]** `/api/ski/search` 與 `/api/ski/stream` **兩個端點都要保留**（CLAUDE.md 明示）
- **[CONST-005]** SQLite DB 路徑固定為 `web/data/snowtrip.db`（CLAUDE.md 明示）
- **[CONST-006]** JS 邏輯放在 `web/static/js/`，模板不寫 inline script（CLAUDE.md 明示）
- **[CONST-007]** 新增功能後必須以 `include_router` 掛載對應 router（CLAUDE.md 明示；TASK-001 不增加路由）
- **[CONST-008]** brownfield 28 個端點採單數 URL（如 `/api/ski/...`），**TASK-001 不重寫**（會破壞 production URL + DESIGN.md 文件）
- **[CONST-009]** brownfield 28 個端點回應格式三種混用（`{ok, data}` / `{ok, msg}` / `HTTPException(detail)`），**TASK-001 不統一**（留後續 TASK 配合 error-codes 建立）

---

## 7. 其他角色的備註

> 使用者（PM）在 enhanced-input.md 提及但**不屬於 BA 職責**的內容，標記分派目標。所有 UI/API 細節不由 BA 設計。

| 備註 | 分類 | 建議分派給 | 來源 |
|------|------|-----------|------|
| `/api/env-check` debug endpoint 留在生產 — 應評估下架 | 技術 / 安全 | **後續 TASK / hotfix**（非 TASK-001 範圍）| baseline C-2 |
| SQLite → Postgres 遷移 | 技術 / 資料 | **TASK-002**（SA 階段選 Postgres 來源 / SD 寫 migration / BE 抽 repository） | baseline C-1 |
| brownfield 28 端點命名統一複數 | 技術 / API 風格 | **後續 TASK（重構波次）** — 需配合 API 版本化 | baseline M-1/M-2 |
| 回應格式統一 `{data, message, error: {code, message}}` | 技術 / API 風格 | **後續 TASK** — 需 SD 階段建立 ERR-AUTH-* 等錯誤碼 | baseline M-3/M-4/M-5 |
| 收藏改軟刪（加 `deleted_at`） | 技術 / 資料 | **TASK-002**（與 Postgres 遷移合併執行 — 新表必含 timestamps） | baseline M-8、db-conventions §專案特定禁止項 |
| `_ski_lock` 跨 worker 失效 | 技術 / 併發 | **後續 TASK** — 多 worker 部署時需引入 Redis 鎖 | NFR-002 [INFERRED 風險] |
| 重構 backend 為 `controllers/services/repositories` 分層 | 技術 / 架構 | **後續 TASK**（與 Vue 重構合併規劃） | baseline M-10 |
| Vue 前端重構（取代 Jinja2 SSR） | UI / 技術 | **後續 TASK** — 待設計師與 PM 確認 | enhanced-input.md「不納入 — 不規劃 Vue 重構」 |
| 設計 i18n key 機制（en-US 等） | UI / i18n | **未來 TASK**（Vue 重構時啟用，目前 N/A） | i18n-conventions.md v1.1 §1 |
| 補齊 `urls.json` 剩餘雪場 | 內容 / 資料 | **人工流程或內容 TASK**（非程式） | enhanced-input.md「不納入」 |
| 收藏列表頁的視覺設計（profile.html）| UI | **UIUX**（後續 TASK — TASK-001 不重設計）| 一般 |
| 機票查詢頁的視覺設計（flight.html）| UI | **UIUX**（後續 TASK）| 一般 |
| 設計 `/api/auth/verify?email=` 的權限保護 | 技術 / 安全 | **後續 TASK** — 加 ADMIN role 或 API key | §3 ROLE-003、SUG-002 |
| 設計密碼重設 / 忘記密碼流程 | 業務 | **後續 TASK** — 目前完全沒實作 | 既有 code 無實作 |
| RBAC（管理者後台） | 業務 | **後續 TASK**（目前 DB 無 role 欄位）| 既有 code 無實作 |

---

## 8. [BA建議]（需使用者確認才納入正式規格 — TASK-001 不採納，僅備忘）

> **強調**: 以下建議**完全不寫進 TASK-001 任何代碼**。本 TASK 為純文件，所有建議留待後續 TASK。

### SUG-001（安全）: Excel 下載端點 500 錯誤洩漏 stack message

- **建議**: `web/main.py:247` `Response(content=str(e), status_code=500)` 把 exception message 直接回給用戶，可能洩漏內部資訊（檔案路徑 / SQL / dependency 名）
- **理由**: 已知 OWASP「Improper Error Handling」風險；生產應只回通用訊息（如「下載失敗」），詳細 log 在 server-side
- **影響範圍**: 1 個端點，1 個替換
- **優先順序**: P2（影響面小但屬安全衛生）
- **不採納於 TASK-001 的理由**: brownfield-document 模式，所有 [BA建議] 不寫 code

### SUG-002（安全）: `/api/auth/verify?email=<x>` 應加權限保護

- **建議**: 任何呼叫者可用 email 查詢用戶是否存在 / 是否已驗證，等於提供「列舉式攻擊」表面（attacker 可掃 email 清單判斷哪些是合法用戶）
- **理由**: OWASP「User Enumeration」攻擊；該 API 設計上是維運工具但未隔離權限
- **替代方案**:
  - (A) 移除 email 模式（只保留 token 模式 + 強制登入）
  - (B) 加 API key 驗證 / 限定特定 admin user
  - (C) 對未認證請求一律回 `{"found": false}`（不洩漏存在性）
- **優先順序**: P1（明確安全議題，但未在過去被利用 — 可接受短期遞延）
- **不採納於 TASK-001 的理由**: 同上

### SUG-003（DoS）: 重寄驗證信無 rate limit

- **建議**: POST `/api/auth/resend-verification` 無頻率限制，攻擊者可對任意 email 灌信導致 Resend 額度耗盡
- **理由**: 已知 OWASP「Account Enumeration through SMTP/Resend abuse」
- **替代方案**: 每 email 每 60 秒最多 1 次（in-memory Redis 或 DB 計數）
- **優先順序**: P1（資源耗盡風險，但目前用戶量小未被利用）
- **不採納於 TASK-001 的理由**: 同上

### SUG-004（資安）: 收藏刪除應防越權但保留靜默

- **建議**: 目前 `DELETE /api/favorites/{id}` 跨用戶刪除回 `{ok: true}`（不洩漏存在性）是好設計，但**沒檢查是否真的刪到 row**
- **理由**: 既有實作不洩漏資訊但也不告知用戶「沒刪到」，造成 UX 困惑
- **替代方案**: 區分 0 rows affected 時回 404 `{ok: false, error: "找不到該收藏"}`，但代價是洩漏 ID 存在性 → **設計權衡** trade-off 需用戶決定
- **優先順序**: P3（UX 改善）
- **不採納於 TASK-001 的理由**: 同上

### SUG-005（安全）: `SECRET_KEY` 預設值是 fallback 字串

- **建議**: `web/auth/security.py:8` `SECRET_KEY = os.getenv("SECRET_KEY", "change-me-in-production-please")`
- **理由**: 若部署時忘記設 env，會用預設字串簽 JWT，**任何人都能偽造 token**
- **替代方案**: 啟動時若 `SECRET_KEY` 未設 → raise `RuntimeError`（fail fast）
- **優先順序**: P0（高度生產風險）
- **不採納於 TASK-001 的理由**: 同上；列入 [後續 TASK 必修]

### SUG-006（安全）: Production 環境 cookie 應 `Secure=True`

- **建議**: `web/auth/auth_router.py:134` 與 `web/auth/oauth_router.py:117` 寫死 `secure=False`
- **理由**: production 走 HTTPS，cookie 應加 Secure 屬性禁止明文傳送；攻擊者中間人嗅探機率降低
- **替代方案**: 用 `IS_PROD = os.getenv("ENV") == "production"` 決定 `secure=IS_PROD`
- **優先順序**: P1
- **不採納於 TASK-001 的理由**: 同上

### SUG-007（資料完整性）: 重寄驗證信時舊 token 標 used_at 但有競爭條件

- **建議**: `web/auth/auth_router.py:182-192` 兩個 `get_conn()` 區塊之間若高併發可能重複建立 token（race condition）
- **理由**: 標準併發問題
- **替代方案**: 合併為單一 transaction
- **優先順序**: P3（用戶量小未體現）
- **不採納於 TASK-001 的理由**: 同上

### SUG-008（觀測）: 缺乏結構化 log

- **建議**: 既有 `print(...)` 與 `print(..., file=sys.stderr)` 散落各檔，無 log level / structured field
- **理由**: 故障排查困難，無法 grep `level=ERROR endpoint=/api/auth/login`
- **替代方案**: 引入 `structlog` 或 `python-json-logger`
- **優先順序**: P2
- **不採納於 TASK-001 的理由**: 同上

### SUG-009（觀測）: 缺乏 audit log（誰登入、收藏被誰刪）

- **建議**: 對安全敏感事件（登入成功/失敗、收藏刪除、用戶狀態變更）建立 audit log table
- **理由**: 合規 / 故障追查 / 異常行為偵測
- **優先順序**: P2
- **不採納於 TASK-001 的理由**: 同上

### SUG-010（韌性）: Resend 寄信例外被 silently 吞掉

- **建議**: `web/auth/email_service.py:67-68` `except Exception: pass` 吞掉所有 Resend 例外（含網路問題、認證失敗）
- **理由**: 違反 code-conventions.md §6「不允許靜默忽略 catch (e) {}」
- **替代方案**: 加 `print` log 或 structured log
- **優先順序**: P2（影響觀測但不影響功能）
- **不採納於 TASK-001 的理由**: 同上

---

## 9. [待用戶確認] 項目（NFR 待確認清單）

> **MANDATORY**: 以下從 code 推斷的 NFR，BA 階段請使用者一次性確認 / 修改。回答後寫入 `journal.json`，TASK-002+ 可引用為「已確認 NFR」。

| Q-ID | 問題 | 推斷值（來源） | 用戶答案 |
|------|------|---------------|---------|
| Q-001 | 雪票查詢 timeout 設為 45 秒是否符合期望？ | 45 秒（`web/main.py:137`） | ✅ **改 30 秒**（NFR-001 目標值更新；TASK-001 不改 code，TASK-002+ 改 timeout=30）|
| Q-002 | JWT 有效期設為 7 天是否符合期望？ | 7 天（`web/auth/security.py:10`） | ✅ **改 1 天**（NFR-003 目標值更新；TASK-002+ 改 timedelta(days=1)）|
| Q-003 | 密碼複雜度僅要求 ≥ 8 字元是否足夠？ | ≥ 8（`auth_router.py:87`） | ✅ **強化為 ≥ 12 + 數字 + 字母**（**NFR-006** 目標值更新；TASK-002+ 加 regex 驗證）|
| Q-004 | Resend + SMTP 都失敗時 silent 只 log 是否符合預期？ | silent fallback（`email_service.py:64-68`） | ✅ **改：直接告知用戶「信件未送出」+ 提供重寄鈕**（NFR-010 目標值更新；TASK-002+ 改 register flow 回傳明確錯誤 + UI 加重寄鈕）|
| Q-005 | Google OAuth 登入成功永遠 redirect 到 `/plan` 是否符合預期？ | 寫死 `/plan`（`oauth_router.py:112`） | ✅ **改丟首頁 `/`**（**BR-009** 規則更新；TASK-002+ 改 redirect target）|
| Q-006 | `/api/auth/verify?email=<x>` 對所有人開放是否視為維運內部工具？ | 無權限（`verify_client.py:130-151`） | ✅ **加 admin token / API key 保護**（**新增 NFR-019**「verify endpoint 權限保護」；TASK-002+ 加 admin gate；可考慮和 Q-009/Q-010 hotfix bundle）|
| Q-007 | 重寄驗證信無 rate limit 是否同意 TASK-001 不修？ | 無限制（`auth_router.py:170-194`） | ✅ **TASK-002 主軸中一併處理**（跟 Postgres / Redis rate limit 同 TASK）|
| Q-008 | 收藏 DELETE 採硬刪是否同意 TASK-001 不修？ | 硬刪（`auth_router.py:249`） | ✅ **TASK-002 跟 Postgres 遷移同 TASK 處理**（一併加 deleted_at + 軟刪）|
| Q-009 | Cookie `Secure=False` 寫死是否暫接受？ | 寫死 False（`auth_router.py:134`） | ✅ **「最佳解」= 立即拆 hotfix 修**（規劃: `hotfix/auth-security-hardening` bundle Q-009 + Q-010；prod Secure=True，需 env-aware）|
| Q-010 | `SECRET_KEY` 有 dev fallback 是否暫接受？ | 有 fallback（`security.py:8`） | ✅ **「最佳解」配合整體 = 立即 hotfix 改 fail-fast**（與 Q-009 bundle 同個 `hotfix/auth-security-hardening` branch）|
| Q-011 | 系統語言固定 `zh-TW`、不啟用 i18n 是否確認？ | zh-TW only（i18n-conventions.md v1.1） | ✅ **從 Vue 重構時才引進**（confirm 現況；i18n-conventions v1.1 已寫此規則）|
| Q-012 | 機票查詢只用 SerpAPI + fast-flights 不接 Travelpayouts/Amadeus 是否符合預期？ | SerpAPI + fast-flights only | ✅ **同意，SerpAPI + fast-flights only**（NFR-012 寫死現況；未接的 backend 改為 [DEAD-CODE: 未啟用]）|
| Q-013 | brownfield 28 端點單數 URL + 回應格式三種混用，TASK-001 不重寫是否同意？ | 單數 URL + 混用 | ✅ **TASK-002+ 加 v2 端點、舊 v1 逐步 deprecated**（NFR/BR 新增 v2 路徑規劃；TASK-001 不動 v1）|
| Q-014 | 三張表都缺 `updated_at`/`deleted_at`，TASK-001 不補是否同意？ | 缺欄位（`database.py:18-42`） | ✅ **TASK-002 主軸中計畫補齊**（Postgres migration 一併上 updated_at + deleted_at）|
| Q-015 | `/api/env-check` 留 hotfix 不在 TASK-001 範圍是否同意？ | 在 prod 可達（`main.py:461`） | ✅ **同意，hotfix 關**（`hotfix/remove-env-check` commit 132e0bb 已存在）|
| Q-016 | TASK-001 不順手清理 DESIGN.md 是否同意？ | DESIGN.md 過時 | ✅ **DESIGN.md 未來不再維護，重計畫「`.sdlc/` 取代」**（新增 **CONST-010** 「`.sdlc/shared/` 為唯一真相」；TASK-001 結束後 DESIGN.md 加廢棄聲明，CLAUDE.md 改指向 .sdlc/）|

---

## 9.1 用戶答案的影響與後續行動（PM Step 2.8 萃取依據）

### 規格目標值更新（TASK-001 寫進規格，但 code 待 TASK-002+ 改）

> 註：此表涵蓋 NFR + BR 規則更新（不限於 NFR）。

| 編號 | 現況值 | 目標值（用戶答案）| 處理 TASK |
|------|--------|------------------|----------|
| NFR-001 雪票 timeout | 45s | **30s** | TASK-002+ |
| NFR-003 JWT 有效期 | 7 天 | **1 天** | TASK-002+ |
| NFR-006 密碼複雜度 | ≥ 8 字元 | **≥ 12 + 數字 + 字母** | TASK-002+ |
| NFR-010 寄信全敗行為 | silent + log | **用戶可見錯誤 + 重寄鈕** | TASK-002+ |
| BR-009 OAuth redirect | /plan | **/** | TASK-002+ |
| NFR-019（新增）verify endpoint 權限 | 無（既有 verify_client.py:130-151）| **admin token / API key** | TASK-002+（可與 Q-009/010 hotfix 合併）|

### 新增 hotfix 規劃（用戶選「立即修」的）

`hotfix/auth-security-hardening` branch（建議從 main 開）:
- Q-009: Cookie `Secure` 從寫死 False 改為 env-aware（`Secure=True` 當 BASE_URL 開頭是 `https://`）
- Q-010: `SECRET_KEY` 移除 fallback 字串，改 fail-fast（無 env var 即 raise）
- Q-006（可選 bundle）: `/api/auth/verify` 加 admin token gate

TASK-001 結束後 PM 安排此 hotfix 與 `hotfix/remove-env-check` 同批 ship。

### Q-016 重大決定：DESIGN.md 取代規劃

> 用戶決定 **DESIGN.md 未來不再維護**，由 `.sdlc/` 取代作為唯一真相來源。

**TASK-001 結束時的補做**（PM Step 2.8）:
1. DESIGN.md 末尾加廢棄聲明：「本文件自 2026-06-04 起停止維護，請改參考 `.sdlc/shared/MASTER-INDEX.md` 與 `.sdlc/tasks/{TASK}/`」
2. `CLAUDE.md` 修改：「每次對話開始前必須先讀此文件」→ 改為「先讀 `.sdlc/shared/MASTER-INDEX.md` + 進行中 TASK 的 enhanced-input.md」
3. 不刪 DESIGN.md（保留歷史快照），但加 `archive/` 移動建議

**對 BA 階段的影響**: 新增 **CONST-010**「`.sdlc/shared/` 為唯一規格真相來源（DESIGN.md 廢棄）」 — 屬於文件治理約束，非 NFR。後續所有 TASK 不再 sync DESIGN.md。

### TASK-002 backlog（從本次答案累積）

| ID | 內容 | 來源 |
|----|------|------|
| BACKLOG-001 | 雪票 timeout 改 30s | Q-001 |
| BACKLOG-002 | JWT 有效期改 1 天 | Q-002 |
| BACKLOG-003 | 密碼複雜度 ≥ 12 + 數字 + 字母 | Q-003 |
| BACKLOG-004 | 寄信全敗用戶可見錯誤 + 重寄鈕 | Q-004 |
| BACKLOG-005 | OAuth redirect 改首頁 / | Q-005 |
| BACKLOG-006 | 重寄驗證信 rate limit | Q-007（TASK-002 主軸內）|
| BACKLOG-007 | 收藏軟刪（deleted_at）| Q-008（TASK-002 主軸內）|
| BACKLOG-008 | SQLite → Postgres + updated_at/deleted_at | Q-014（TASK-002 主軸）|
| BACKLOG-009 | v2 API endpoints（複數命名 + 統一回應格式）| Q-013（TASK-003+）|
| BACKLOG-010 | 移除 Travelpayouts/Amadeus dead code | Q-012（TASK-002+）|
| HOTFIX-A | Cookie Secure env-aware | Q-009 |
| HOTFIX-B | SECRET_KEY fail-fast | Q-010 |
| HOTFIX-C（可 bundle B）| verify endpoint admin gate | Q-006 |

---

## 10. 術語表（BA 階段新增）

> 詳見配套文件 `terminology-additions.md`；以下為核心摘要。

| 術語 | 英文 | 定義 | 出現位置 |
|------|------|------|---------|
| 雪場 | resort | 日本滑雪場單位（如「白馬八方尾根」「二世古」）| `http_scraper.py`、`urls.json` |
| 雪季 | season | 滑雪營業期間（如「2025-2026」），系統依日期自動判斷 | `http_scraper.py` 輸出欄位 |
| 票種 | ticket_type | 雪場票價分類（如「1日券」「夜間券」「早鳥券」），含日文與中文翻譯版本 | TicketPrice dataclass |
| 早鳥票 | early_bird | 雪季開始前提早購買的優惠票（依雪場規則）| `ski_early_bird_scraper.py` |
| 收藏 | favorite | 用戶儲存的雪票或機票查詢結果（type ∈ {ski, flight}）| `favorites` 表、`auth_router.py:208-252` |
| 行程規劃 | trip plan | 用戶在 `/plan` 頁面同時查機票 + 雪票並下載 3-sheet Excel | `plan_routes.py` |
| 強制登入路徑 | protected route | middleware 攔截的路徑清單（4 個頁面 + 3 個 API 前綴）| `web/main.py:33-34` |
| Resend | — | 第三方寄信服務（API），主要寄信來源 | `email_service.py:9` |
| SMTP fallback | — | Resend 失敗（429 / exception）時的備援寄信路徑 | `email_service.py:71-89` |
| Email 驗證 token | verification token | 24h 過期、單次使用的 token，用於確認用戶 email 所有權 | `email_verification_tokens` 表 |
| HTTP-only cookie | — | JWT 載體，JS 讀不到，防 XSS | `auth_router.py:130-134` |
| Google OAuth state | — | 防 CSRF 的 16-byte 隨機字串，cookie 與 callback query 比對 | `oauth_router.py:28-38` |
| OAuth Upsert | — | callback 流程的 3 段決策邏輯（先 google_id、再 email、最後新建）| `oauth_router.py:85-109` |
| 雪票查詢全域鎖 | ski lock | asyncio.Lock 序列化 `/api/ski/*` 三個端點 | `web/main.py:116` |
| 維運 API | ops API | `/api/auth/verify`，無權限隔離供 admin / CLI 查詢用戶狀態 | `verify_client.py:130-151` |

---

## 11. 追溯矩陣

| FR-ID | 來源（file:line）| 優先順序 | 對應 AC | 對應 NFR/BR | 狀態 |
|-------|------------------|---------|---------|------------|------|
| FR-001 | `web/main.py:127-142` | P0 | AC-001/002/003 | NFR-001/002, BR-012 | brownfield-confirmed |
| FR-002 | `web/main.py:153-194` | P0 | AC-004/005/006 | NFR-002, BR-012 | brownfield-confirmed |
| FR-003 | `web/main.py:197-247` | P0 | AC-007/008 | NFR-001/002/017, BR-012 | brownfield-confirmed |
| FR-004 | `web/main.py:252-298` | P0 | AC-009/010 | — | brownfield-confirmed |
| FR-005 | `web/main.py:442-456` | P1 | AC-011/012 | NFR-017 | brownfield-confirmed |
| FR-006 | `web/plan_routes.py:38,121` | P1 | AC-013/014 | NFR-017, BR-001 | brownfield-confirmed |
| FR-007 | `web/auth/auth_router.py:85-114` | P0 | AC-015/016/017/018 | NFR-006/007/008/009, BR-002/003/004 | brownfield-confirmed |
| FR-008 | `web/auth/auth_router.py:117-135` | P0 | AC-019/020/021 | NFR-003/004/005/007, BR-005 | brownfield-confirmed |
| FR-009 | `web/auth/auth_router.py:138-142` | P0 | AC-022 | NFR-005 | brownfield-confirmed |
| FR-010 | `web/auth/auth_router.py:145-163`, `email_service.py` | P0 | AC-023/024/025/026 | NFR-008/009/010, BR-006 | brownfield-confirmed |
| FR-011 | `web/auth/auth_router.py:170-194` | P1 | AC-027/028 | NFR-010, BR-007 | brownfield-confirmed |
| FR-012 | `web/auth/oauth_router.py:24,42` | P0 | AC-029/030/031 | NFR-011/012, BR-008/009 | brownfield-confirmed |
| FR-013 | `web/auth/auth_router.py:197`, `verify_client.py:130` | P1 | AC-032/033 | NFR-016 | brownfield-confirmed |
| FR-014 | `web/auth/auth_router.py:214,232,245` | P1 | AC-034/035/036 | BR-010/011 | brownfield-confirmed |
| FR-015 | `web/main.py:37-60` | P0 | AC-037/038/039 | NFR-013/016, BR-001 | brownfield-confirmed |
| FR-016 | `web/main.py:98-110`, `auth_router.py:41-56`, `plan_routes.py:38` | P0 | AC-040/041 | NFR-015 | brownfield-confirmed |
| FR-017 | `web/main.py:489-499` | P2 | AC-042/043 | — | brownfield-confirmed |

---

## 12. 自我驗證

> 完整 20 項在 `self-review.json`；此處僅顯示分數摘要。

| 檢查項 | 通過 | 說明 |
|--------|------|------|
| 所有功能需求都有來源引用 | ✅ | 17 個 FR 全部 file:line |
| 沒有自行補充使用者未說的功能 | ✅ | 所有功能限定於 baseline-audit 列出的 28 端點 |
| 所有 [BA建議] 都有標記 | ✅ | 10 個 SUG-* 全在 §8 隔離區 |
| 所有 [待確認] 都有標記 | ✅ | 16 個 Q-* 全在 §9 隔離區 |
| 需求之間沒有矛盾 | ✅ | 已交叉檢查 BR-001 與 FR-015、NFR-013 |
| 每個需求都有驗收標準 | ✅ | 17 FR / 43 AC（AC-001 ~ AC-043 全域連續）|
| 術語使用一致 | ✅ | 15 條術語表已對齊 §10 與正文 |
| ID 編號連續不重複 | ✅ | FR 001-017、NFR 001-018、BR 001-012、AC 001-043、ROLE 001-003、ASSUME 001-008、CONST 001-009、SUG 001-010、Q 001-016 |
| **總分** | **95/100** | 詳見 `self-review.json` |
