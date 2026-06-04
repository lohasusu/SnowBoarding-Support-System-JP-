---
document_id: "TERM-ADD-TASK-001-v1.0"
title: "業務術語新增清單 — TASK-001 brownfield 補追溯"
version: "1.0"
date: "2026-06-03"
author: "BA"
status: "Draft"
task_id: "TASK-001"
phase: "ba"
mode: "brownfield-document"
purpose: "PM 在 next.md Step 2.8 從本檔萃取術語、append 到 .sdlc/shared/terminology.md"
change_history:
  - version: "1.0"
    date: "2026-06-03"
    changes: "初始 — 列入 15 條業務術語（領域概念 + 系統機制）"
    author: "BA"
---

# 業務術語新增清單 — TASK-001

> **用途**: BA 階段新增的業務術語，由 PM 在階段 approved 後萃取到 `shared/terminology.md`。
> **規則**:
> - 中文 + 英文對應雙寫，方便未來 i18n
> - 每條附「定義」+「出現位置」（檔案:行 或 概念來源）
> - 已存在於 `shared/terminology.md` 的術語不重覆登記（本 TASK 是第一個 TASK，shared/terminology.md 為空，全部 15 條都是新增）
> - 系統內部術語（如 `_ski_lock`）也納入，方便後續 SA/SD 對話一致

---

## 一、領域概念（雪場 / 機票業務）

### T-001 雪場（resort）

- **英文**: resort（不用 ski_field，與 `urls.json` 命名一致）
- **定義**: 日本提供滑雪服務的單一營業場所（如「白馬八方尾根」「二世古」），是票價查詢的最小單位
- **出現位置**: `urls.json`、`http_scraper.py` `TicketPrice.resort`、`web/main.py:225` xlsx 欄位、business-flow BF-001
- **複數**: resorts（系統批次查詢多個雪場）

### T-002 雪季（season）

- **英文**: season
- **定義**: 滑雪營業期間（如「2025-2026」），系統依當前日期自動判斷對應雪季
- **出現位置**: `http_scraper.py` `TicketPrice.season`、`web/main.py:230` xlsx 欄位
- **格式**: `<起始年>-<結束年>`

### T-003 票種（ticket_type）

- **英文**: ticket_type
- **定義**: 雪場票價分類，含日文原文與中文翻譯版本（如「1日券」「夜間券」「早鳥券」）
- **出現位置**: `http_scraper.py` `TicketPrice.ticket_type` / `ticket_type_zh`、`web/main.py:227-228`
- **關聯**: 每張票有「ticket_type（日文）」與「ticket_type_zh（中文）」兩個欄位

### T-004 早鳥票（early_bird）

- **英文**: early_bird
- **定義**: 雪季開始前提早購買的優惠票，依各雪場規則訂定截止日期
- **出現位置**: `ski_early_bird_scraper.py`（本地 CLI 工具，非 web 端）
- **註**: 本 TASK 範圍內 `ski_early_bird_scraper.py` 為 MOD-003，提供離線生產資料；web 端不直接呼叫

### T-005 票價頁連結（source_url / ticket_url）

- **英文**: source_url（內部欄位名）/ ticket_url（urls.json 欄位名）
- **定義**: 雪場官方公布票價的 URL，用於使用者驗證價格出處
- **出現位置**: `urls.json` 的 `ticket_url`、`TicketPrice.source_url`、`web/main.py:232`

---

## 二、用戶業務概念（會員系統）

### T-006 收藏（favorite）

- **英文**: favorite
- **定義**: 用戶儲存的查詢結果，type ∈ {ski, flight}，含 data（JSON）+ label（用戶自訂標籤）
- **出現位置**: TBL `favorites`、`auth_router.py:214-252`
- **複數**: favorites

### T-007 行程規劃（trip plan）

- **英文**: trip plan
- **定義**: 用戶在 `/plan` 頁面同時查機票 + 雪票並下載 3-sheet Excel 的整合查詢功能
- **出現位置**: `plan_routes.py`、PAGE-004
- **註**: 「規劃」不是 DB 表，是行為；不要與「行程」（itinerary）混用

### T-008 行程摘要（trip summary）

- **英文**: trip summary
- **定義**: 3-sheet Excel 第 1 個 sheet 名稱，包含出發/目的地機場、雪場地區、日期、人數、結果數
- **出現位置**: `plan_routes.py:62` `ws1.title = "行程摘要"`

### T-009 機票合計票價（total fare）

- **英文**: total fare
- **定義**: 機票 Excel 中「去程票價 + 回程票價」的合計欄，用於排序與前 3 名高亮
- **出現位置**: `web/main.py:375, 405` xlsx「合計票價(TWD)」欄

---

## 三、認證與安全機制

### T-010 強制登入路徑（protected route）

- **英文**: protected route / protected path
- **定義**: 經過 `_require_auth` middleware 攔截、未登入時拒絕訪問的路徑
- **清單**:
  - 頁面: `/ski`、`/flight`、`/plan`、`/profile`
  - API 前綴: `/api/ski*`、`/api/flight*`、`/api/plan*`
- **出現位置**: `web/main.py:33-34`
- **註**: `/api/auth/*` 與 `/api/favorites*` **不在 middleware 範圍**，由 router 內 `Depends(get_current_user)` 控制

### T-011 HTTP-only cookie（access_token cookie）

- **英文**: HTTP-only cookie
- **定義**: JWT 載體，屬性 `HttpOnly + SameSite=Lax + Max-Age=604800`；JS 讀不到防 XSS
- **出現位置**: `auth_router.py:130-134`、`oauth_router.py:113-117`、api-conventions.md v1.1 §4
- **註**: 本系統 cookie name 固定為 `access_token`

### T-012 Email 驗證 token

- **英文**: email verification token
- **定義**: `secrets.token_urlsafe(32)` 產生的 32-byte URL-safe 字串，24h 過期、單次使用
- **出現位置**: TBL `email_verification_tokens`、`auth_router.py:99-103, 187-191`

### T-013 Google OAuth state cookie

- **英文**: oauth_state cookie
- **定義**: 16-byte 隨機字串，CSRF 防護用；callback 比對 cookie 與 query 必須相同
- **出現位置**: `oauth_router.py:28, 38, 51-52`、有效期 300 秒

### T-014 OAuth Upsert 邏輯

- **英文**: OAuth upsert logic
- **定義**: Google OAuth callback 取得 userinfo 後的 3 段帳號連結決策：① google_id 命中 → 取用；② email 命中 → 綁定 google_id + 強制 is_verified=1；③ 都沒命中 → 新建 user is_verified=1
- **出現位置**: `oauth_router.py:85-109`

### T-015 雪票查詢全域鎖（ski lock / _ski_lock）

- **英文**: ski query lock
- **定義**: `asyncio.Lock` 實例，序列化 `/api/ski/search`、`/api/ski/stream`、`/api/ski/download` 三個端點；同時最多一個查詢執行
- **出現位置**: `web/main.py:116, 129, 158, 202`
- **註**: per-process 範圍；多 worker 部署時失效（已知技術債）

---

## 四、外部服務 / 多後端整合

### T-016 Resend

- **英文**: Resend（產品名）
- **定義**: 第三方 transactional email 服務，主要寄信來源；POST `https://api.resend.com/emails`
- **出現位置**: `email_service.py:9, 48-67`

### T-017 SMTP fallback

- **英文**: SMTP fallback
- **定義**: Resend 失敗（429 / 例外）時的備援寄信路徑；使用 STARTTLS port 587
- **出現位置**: `email_service.py:71-89`、NFR-010

### T-018 dev stderr log fallback

- **英文**: dev stderr log fallback
- **定義**: Resend + SMTP 都失敗時，把驗證 URL 印到 stderr（不阻擋帳號建立）
- **出現位置**: `email_service.py:91-98`

### T-019 SerpAPI backend

- **英文**: SerpApiBackend
- **定義**: 機票查詢主要後端，依賴 `SERPAPI_API_KEY` env；走 Google Flights 資料
- **出現位置**: `web/main.py:275-281`、`flight_search/backends/serpapi_backend.py`

### T-020 fast-flights backend

- **英文**: FastFlightsBackend
- **定義**: 機票查詢 fallback 後端，無 API key 需求；用於 SerpAPI 不可用時
- **出現位置**: `web/main.py:283-285`、`flight_search/backends/fast_flights_backend.py`

---

## 五、運營與維運概念

### T-021 維運 API（ops API）

- **英文**: operations API / ops API
- **定義**: `/api/auth/verify`，無權限隔離供 admin / CLI 查詢用戶 token 有效性或 email 狀態
- **出現位置**: `verify_client.py:130-151`、ROLE-003、SUG-002

### T-022 CLI 驗證工具（verify_client CLI）

- **英文**: verify_client CLI
- **定義**: `python verify_client.py --token <jwt>` 或 `--email <email>`，本地維運用
- **出現位置**: `verify_client.py:155-179`

### T-023 ephemeral storage（Railway 暫存）

- **英文**: ephemeral storage
- **定義**: Railway 部署環境的容器層暫存空間，每次重啟即清空；不適合放 SQLite db 檔
- **出現位置**: CLAUDE.md「Railway 部署注意事項」、NFR-014、baseline C-1
- **註**: 已知 Critical 問題，留 TASK-002 解決

---

## 六、SDLC 流程術語（本 TASK 為 brownfield-document）

### T-024 brownfield 真相基線（brownfield truth baseline）

- **英文**: brownfield truth baseline
- **定義**: 反向萃取既有 production code 形成的 SDLC 規格基線；當 DESIGN.md / baseline / code 不一致時以 code 為真相
- **出現位置**: enhanced-input.md、`requirement-spec.md` §1.1、所有 `[CODE-AS-TRUTH: file:line]` 標記
- **用途**: 後續 TASK-002+ 從此基線增量開發

### T-025 [CODE-AS-TRUTH] 標記

- **英文**: code-as-truth marker
- **定義**: 在規格文件中標示「此處以既有 code 為真相，DESIGN.md / baseline 可能落後」的標籤
- **格式**: `[CODE-AS-TRUTH: <檔案>:<行號>]`
- **出現位置**: `requirement-spec.md` 多處（FR-001 鎖 / OAuth redirect / 機票 backend list 等）

### T-026 [BA建議]

- **英文**: BA recommendation
- **定義**: BA 專業判斷的改善建議，必須與正式規格物理分離；用戶未確認前不採納
- **出現位置**: `requirement-spec.md` §8、本 TASK 共 10 條 SUG-001 ~ SUG-010

---

## 七、術語表合併規則（給 PM）

PM 萃取本檔到 `shared/terminology.md` 時：

1. **直接合併**: 全部 26 條都是新增（shared/terminology.md 目前為空）
2. **格式對齊 shared/terminology.md 的「術語定義」表頭**:
   | 術語 | 定義 | 來源 TASK | 備註 |
3. **「備註」欄填入**: 對應的 file:line 或 FR-/NFR- ID（最重要的關聯點）
4. **多語**: 中文為 key，英文為 value 的一部分（不要拆兩列；繁中為唯一支援語系見 NFR-015）
5. **避免重複**: 後續 TASK 若提及這些術語，直接引用、不重定義

PM 萃取後寫入 `shared/terminology.md` 範例：

```markdown
## 術語定義

| 術語 | 定義 | 來源 TASK | 備註 |
|------|------|----------|------|
| 雪場（resort） | 日本提供滑雪服務的單一營業場所（如「白馬八方尾根」「二世古」），是票價查詢的最小單位 | TASK-001 | TicketPrice.resort, urls.json |
| 雪季（season） | 滑雪營業期間（如「2025-2026」），系統依當前日期自動判斷 | TASK-001 | TicketPrice.season |
| 票種（ticket_type） | 雪場票價分類，含日文與中文翻譯版本 | TASK-001 | TicketPrice.ticket_type/ticket_type_zh |
| 收藏（favorite） | 用戶儲存的查詢結果，type ∈ {ski, flight} | TASK-001 | TBL favorites |
| 強制登入路徑（protected route） | middleware 攔截的路徑（4 頁面 + 3 API 前綴）| TASK-001 | web/main.py:33-34 |
| HTTP-only cookie | JWT 載體，HttpOnly+SameSite=Lax+604800s | TASK-001 | api-conventions §4 |
| 雪票查詢全域鎖（_ski_lock） | asyncio.Lock 序列化 3 個雪票端點 | TASK-001 | NFR-002 |
| Resend | 第三方 transactional email 服務（主要） | TASK-001 | email_service.py:9 |
| SMTP fallback | Resend 失敗（429/例外）的備援寄信路徑 | TASK-001 | email_service.py:71-89 |
| Email 驗證 token | 32-byte URL-safe 字串，24h 過期、單次使用 | TASK-001 | TBL email_verification_tokens |
| OAuth state cookie | 16-byte 隨機字串，CSRF 防護，300 秒過期 | TASK-001 | oauth_router.py:28 |
| 維運 API（ops API） | /api/auth/verify，無權限隔離供 admin 查詢 | TASK-001 | ROLE-003, SUG-002 |
| brownfield 真相基線 | 反向萃取 production code 形成的規格基線 | TASK-001 | 本 TASK 模式 |
| [CODE-AS-TRUTH] 標記 | 「以 code 為真相」標籤格式 | TASK-001 | 多處 |
| [BA建議] | BA 專業改善建議，與正式規格隔離 | TASK-001 | requirement-spec §8 |
| ...（其餘 11 條同格式）| ... | ... | ... |
```
