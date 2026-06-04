---
document_id: "BDD-TASK-001-v1.0"
title: "BDD 場景 — snowboarding_support brownfield 13 個核心 FR Given/When/Then"
version: "1.0"
date: "2026-06-03"
author: "BA"
status: "Draft"
task_id: "TASK-001"
phase: "ba"
mode: "brownfield-document"
source_documents:
  - "REQ-TASK-001-v1.0"
  - "BF-TASK-001-v1.0"
  - "baseline-audit-2026-06-03.md"
change_history:
  - version: "1.0"
    date: "2026-06-03"
    changes: "初始版本 — 17 個 FR 每個 ≥ 1 個 happy path scenario，含 edge cases 共 35 個"
    author: "BA"
approval:
  reviewer: "PM"
  date: ""
  result: "Pending"
  notes: ""
---

# BDD 場景 — snowboarding_support brownfield Given/When/Then

> **規則**: 每個 FR 至少 1 個 happy path + 重要 edge cases。所有場景對應正式 FR/AC，無虛構行為（brownfield-document 模式所有場景必以 code 為真相）。
>
> **語法**: 標準 Gherkin（Feature / Scenario / Given / When / Then / And）。後續 Tester 可直接從此檔生 `pytest-bdd` 或 `behave` 測試案例。

---

## Feature: FR-001 雪票批次查詢（JSON）

**對應**: `web/main.py:127-142`、AC-001/002/003、NFR-001/002、BR-001/012

```gherkin
Feature: FR-001 雪票批次查詢
  作為已登入用戶
  我希望能用地區或雪場名稱查詢日本雪場票價
  以便快速取得當季所有票價列表

  Background:
    Given 用戶 "alice@test.com" 已註冊且 is_verified=1
    And 用戶 alice 已成功登入，持有效 access_token cookie
    And 雪票查詢全域鎖 _ski_lock 未被佔用
    And `urls.json` 包含 "長野" 地區共 5 個雪場

  Scenario: AC-001 已登入用戶查詢長野地區批次成功
    When 用戶 alice 發送 "GET /api/ski/search?region=長野"
    Then 系統回應 HTTP 狀態碼 200
    And 回應 Content-Type 為 "application/json"
    And 回應 body 為 {"ok": true, "data": [...]}
    And data 陣列中每個元素含欄位 ["resort", "region", "ticket_type", "price", "season", "source_url"]
    And 查詢執行時間不超過 45 秒

  Scenario: AC-002 查詢逾時 (45 秒)
    Given http_scraper.get_ticket_prices_async 模擬延遲 50 秒
    When 用戶 alice 發送 "GET /api/ski/search?region=長野"
    Then 系統回應 HTTP 200（注意：非 504）
    And 回應 body 為 {"ok": false, "error": "查詢逾時（45 秒），請縮小範圍後重試"}

  Scenario: AC-003 雪票查詢鎖被另一查詢佔用
    Given 另一個查詢正持有 _ski_lock
    When 用戶 alice 發送 "GET /api/ski/search?region=長野"
    Then 系統回應 HTTP 200
    And 回應 body 為 {"ok": false, "error": "查詢進行中，請稍後再試"}
    And 系統未呼叫 http_scraper（不執行重複查詢）

  Scenario: 未登入用戶嘗試查詢
    Given 用戶未登入（無 access_token cookie）
    When 用戶發送 "GET /api/ski/search?region=長野"
    Then 系統回應 HTTP 狀態碼 401
    And 回應 body 為 {"ok": false, "error": "請先登入", "redirect": "/login"}
```

---

## Feature: FR-002 雪票串流查詢（SSE）

**對應**: `web/main.py:153-194`、AC-004/005/006、NFR-002、BR-012

```gherkin
Feature: FR-002 雪票串流查詢（SSE）
  作為已登入用戶
  我希望能用 Server-Sent Events 逐雪場接收結果
  以便在大量雪場查詢時看到即時進度

  Background:
    Given 用戶 alice 已登入
    And 雪票查詢鎖未被佔用

  Scenario: AC-004 SSE 串流回應格式正確
    When 用戶 alice 發送 "GET /api/ski/stream?region=北海道" 帶 Accept "text/event-stream"
    Then 系統回應 Content-Type "text/event-stream"
    And 串流的第一條訊息為 'event: start' 帶 data {"total": N} 其中 N >= 0
    And 串流的最後一條訊息為 'event: done' 帶 data {"total_count": M} 其中 M >= 0

  Scenario: AC-005 串流鎖衝突立即結束
    Given 另一個查詢正持有 _ski_lock
    When 用戶 alice 發送 "GET /api/ski/stream?region=北海道"
    Then 系統立刻 SSE 'event: error' 帶 data {"message": "查詢進行中，請稍後再試"}
    And 串流關閉，不等待鎖釋放

  Scenario: AC-006 每雪場完成發 resort_done 事件
    Given 北海道地區有 3 個雪場且每個雪場至少回傳 1 筆票價
    When 用戶 alice 發送 "GET /api/ski/stream?region=北海道"
    Then 串流中出現 'event: resort_done' 事件 3 次
    And 每個 resort_done event 的 data 含欄位 {"resort": "...", "count": N}
```

---

## Feature: FR-003 雪票 Excel 下載

**對應**: `web/main.py:197-247`、AC-007/008、NFR-001/002/017

```gherkin
Feature: FR-003 雪票 Excel 下載
  作為已登入用戶
  我希望能下載查詢結果為 .xlsx
  以便離線檢視與比價

  Background:
    Given 用戶 alice 已登入
    And 雪票查詢鎖未被佔用

  Scenario: AC-007 成功下載 xlsx
    When 用戶 alice 發送 "GET /api/ski/download?region=長野"
    Then 系統回應 HTTP 200
    And 回應 Content-Type 為 "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    And 回應 header "Content-Disposition" 為 "attachment; filename=ski_prices_長野.xlsx"
    And xlsx 第一列為 8 欄表頭 ["雪場","地區","票種（日文）","票種（中文）","票價","雪季","查詢時間","票價頁連結"]
    And xlsx 表頭 fill color 為 1565C0（藍底白字）

  Scenario: AC-008 下載時鎖佔用回 HTTP 429
    Given 另一個查詢正持有 _ski_lock
    When 用戶 alice 發送 "GET /api/ski/download?region=長野"
    Then 系統回應 HTTP 狀態碼 429（與 /api/ski/search 的 HTTP 200 行為不同）
    And 回應 body 為純文字 "查詢進行中，請稍後再試"

  Scenario: 無 region 參數時下載全部
    When 用戶 alice 發送 "GET /api/ski/download"
    Then 系統回應 HTTP 200
    And filename 為 "ski_prices_all.xlsx"（region or 'all' 預設邏輯）
```

---

## Feature: FR-004 機票查詢（多 backend fallback）

**對應**: `web/main.py:252-298`、AC-009/010

```gherkin
Feature: FR-004 機票查詢
  作為已登入用戶
  我希望輸入出發/到達機場與日期即可查詢機票
  以便比較多家航空公司票價

  Background:
    Given 用戶 alice 已登入

  Scenario: AC-009 SerpAPI 有 key 時使用 SerpAPI
    Given 環境變數 SERPAPI_API_KEY 已設且 SerpApiBackend.is_available() 為 True
    When 用戶 alice 發送 "GET /api/flight/search?origin=TPE&destination=CTS&departure=2026-12-20&adults=1"
    Then 系統回應 HTTP 200
    And 回應 body 為 {"ok": true, "backend": "SerpAPI", "data": [...]}
    And data 陣列中每個元素含 ["dep_time", "arr_time", "duration", "stops", "price", "flights_str"]

  Scenario: AC-009 SerpAPI 無 key 時 fallback 到 fast-flights
    Given 環境變數 SERPAPI_API_KEY 未設或為空字串
    When 用戶 alice 發送 "GET /api/flight/search?origin=TPE&destination=CTS&departure=2026-12-20"
    Then 系統回應 {"ok": true, "backend": "fast-flights (fallback)", "data": [...]}

  Scenario: AC-010 缺 departure 參數
    When 用戶 alice 發送 "GET /api/flight/search?origin=TPE&destination=CTS"（無 departure）
    Then 系統回應 HTTP 200
    And 回應 body 為 {"ok": false, "error": "請輸入出發日期"}
    And 系統未呼叫任何 backend
```

---

## Feature: FR-005 機票 Excel 下載

**對應**: `web/main.py:442-456`、AC-011/012

```gherkin
Feature: FR-005 機票 Excel 下載

  Background:
    Given 用戶 alice 已登入

  Scenario: AC-011 / AC-012 下載成功與檔名格式
    Given 用戶持有已查詢的 flights 陣列（含 ≥ 1 個 FlightOption）
    When 用戶發送 "POST /api/flight/download" 帶 body {flights: [...], meta: {origin: "TPE", destination: "CTS", departure: "2026-12-20", adults: 1}}
    Then 系統回應 HTTP 200
    And 回應 Content-Type 為 "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    And 回應 header "Content-Disposition" 為 "attachment; filename=flights_TPE-CTS_2026-12-20.xlsx"
    And xlsx 第 1 列為 banner（合併 A1:M1，含 ✈ + 機場代碼）
    And xlsx 第 4 列為 13 欄表頭
    And 第 5 列開始為依合計票價排序的航班，前 3 名 fill color 為 C6EFCE（淺綠）
```

---

## Feature: FR-006 整合查詢頁 + 3-sheet Excel

**對應**: `web/plan_routes.py:38, 121`、AC-013/014

```gherkin
Feature: FR-006 整合查詢 /plan

  Scenario: AC-013 未登入存取 /plan 觸發 redirect
    Given 用戶未登入
    When 用戶發送 "GET /plan"
    Then 系統回應 HTTP 307（或 302）
    And 回應 Location header 為 "/login?next=/plan"

  Scenario: AC-014 已登入下載 3-sheet xlsx
    Given 用戶 alice 已登入
    And alice 持有已查詢的 flights 與 ski 陣列
    When 用戶發送 "POST /api/plan/download" 帶 body {flights, ski, meta: {origin: "TPE", destination: "CTS", region: "長野", departure: "2026-12-20", adults: 1}}
    Then 系統回應 HTTP 200 + xlsx
    And xlsx 含 3 個 sheets 依序為 ["行程摘要", "機票", "雪票"]
    And "行程摘要" sheet 第 1 欄為標籤、第 2 欄為值
    And "機票" sheet 第 1 列為 6 欄表頭 ["航空公司","出發","抵達","飛行時間","轉機次數","票價(TWD)"]
    And "雪票" sheet 第 1 列為 6 欄表頭 ["雪場","地區","票種","票價","雪季","官網"]
    And filename 為 "snowtrip_TPE-CTS_2026-12-20.xlsx"
```

---

## Feature: FR-007 JWT 註冊

**對應**: `web/auth/auth_router.py:85-114`、AC-015/016/017/018、BR-002/003/004、NFR-006/007/008/009

```gherkin
Feature: FR-007 JWT 註冊
  作為訪客
  我希望用 email + 用戶名 + 密碼註冊
  以便建立可登入的帳號

  Scenario: AC-015 密碼短於 8 字元被拒絕
    When 訪客發送 "POST /api/auth/register" 帶 body {email: "alice@test.com", username: "alice", password: "1234567"}
    Then 系統回應 HTTP 狀態碼 400
    And 回應 body 為 {"detail": "密碼至少 8 個字元"}
    And 資料庫 users 表未新增 row

  Scenario: AC-016 Email 格式不符被拒絕
    When 訪客發送 "POST /api/auth/register" 帶 body {email: "not-an-email", username: "alice", password: "validpass123"}
    Then 系統回應 HTTP 400
    And 回應 body 為 {"detail": "Email 格式不正確"}

  Scenario: AC-017 重複 email 註冊被拒絕
    Given users 表已有 row {email: "alice@test.com"}
    When 訪客發送 "POST /api/auth/register" 帶 body {email: "alice@test.com", username: "alice2", password: "validpass123"}
    Then 系統回應 HTTP 409
    And 回應 body 為 {"detail": "Email 或用戶名稱已被使用"}

  Scenario: AC-018 成功註冊建立未驗證帳號 + 24h token
    Given users 表無 alice 相關 row
    And email_verification_tokens 表無 alice 相關 row
    When 訪客發送 "POST /api/auth/register" 帶 body {email: "Alice@Test.com  ", username: " alice ", password: "validpass123"}
    Then 系統回應 HTTP 200
    And 回應 body 為 {"ok": true, "message": "帳號建立成功，驗證信已寄出，請在 24 小時內點擊信中連結"} 或同義訊息
    And users 表新增 1 row 且 email="alice@test.com"（lower+strip）、username="alice"（strip）、is_verified=0
    And users.hashed_password 為 bcrypt hash（以 "$2b$" 開頭）
    And email_verification_tokens 表新增 1 row、token 長度為 43 字元 URL-safe base64、expires_at = now + 24h（UTC ISO 格式）

  Scenario: 寄信失敗仍成功建立帳號
    Given Resend / SMTP / dev fallback 全部失敗
    When 訪客發送 POST /api/auth/register 帶有效資料
    Then 系統回應 HTTP 200
    And 回應 message 為 "帳號建立成功，但寄信失敗，請至登入頁點選「重寄驗證信」"
    And users 表仍新增 row（不因寄信失敗而 rollback）
```

---

## Feature: FR-008 JWT 登入

**對應**: `web/auth/auth_router.py:117-135`、AC-019/020/021、BR-005、NFR-003/004/005

```gherkin
Feature: FR-008 JWT 登入

  Background:
    Given users 表有 row {email: "alice@test.com", hashed_password: bcrypt("validpass123"), is_verified: 1}

  Scenario: AC-019 正確登入設定 cookie
    When 訪客發送 "POST /api/auth/login" 帶 body {email: "alice@test.com", password: "validpass123"}
    Then 系統回應 HTTP 200
    And 回應 body 為 {"ok": true, "message": "登入成功"}
    And 回應 header "Set-Cookie" 包含 "access_token=" + 任意非空字串
    And Set-Cookie 屬性含 "HttpOnly"
    And Set-Cookie 屬性含 "SameSite=Lax"
    And Set-Cookie 屬性含 "Max-Age=604800"
    And access_token 解碼為 JWT (HS256)，payload 含 "sub": "<user.id>"、"exp" 在當下 +7 天

  Scenario: AC-020 密碼錯誤
    When 訪客發送 "POST /api/auth/login" 帶 body {email: "alice@test.com", password: "wrongpass"}
    Then 系統回應 HTTP 401
    And 回應 body 為 {"detail": "Email 或密碼錯誤"}
    And 不設 Set-Cookie header

  Scenario: AC-020 Email 不存在（與密碼錯誤同訊息防 enumeration）
    When 訪客發送 "POST /api/auth/login" 帶 body {email: "ghost@test.com", password: "anything"}
    Then 系統回應 HTTP 401
    And 回應 body 為 {"detail": "Email 或密碼錯誤"}

  Scenario: AC-021 未驗證 email 帳號禁登
    Given users 表有 row {email: "bob@test.com", is_verified: 0}
    When 訪客發送 "POST /api/auth/login" 帶 body {email: "bob@test.com", password: "validpass123"}
    Then 系統回應 HTTP 403
    And 回應 body 為 {"detail": "請先驗證您的 Email 後再登入。未收到信？請點選下方「重寄驗證信」"}
```

---

## Feature: FR-009 登出

**對應**: `web/auth/auth_router.py:138-142`、AC-022

```gherkin
Feature: FR-009 登出

  Scenario: AC-022 登出清除 cookie
    Given 用戶 alice 已登入，持有有效 access_token cookie
    When alice 發送 "POST /api/auth/logout"
    Then 系統回應 HTTP 200
    And 回應 body 為 {"ok": true}
    And 回應 header "Set-Cookie" 含 "access_token=" 且 Max-Age=0 或同義清除指示
```

---

## Feature: FR-010 Email 驗證

**對應**: `web/auth/auth_router.py:145-163`、`web/auth/email_service.py:37-99`、AC-023/024/025/026、BR-006、NFR-010

```gherkin
Feature: FR-010 Email 驗證
  作為剛註冊未驗證的用戶
  我希望點擊驗證信中連結即可驗證 email
  以便取得登入權

  Background:
    Given users 表有 row {id: 1, email: "alice@test.com", is_verified: 0}

  Scenario: AC-023 點擊有效未過期 token 成功驗證
    Given email_verification_tokens 表有 row {user_id: 1, token: "valid_token_xxx", expires_at: now + 23 小時, used_at: NULL}
    When 用戶造訪 "GET /api/auth/verify-email?token=valid_token_xxx"
    Then 系統回應 HTTP 302
    And Location header 為 "/login?verified=1"
    And users 表中 alice 的 is_verified 變為 1
    And email_verification_tokens 表中該 token 的 used_at 不再為 NULL

  Scenario: AC-024 過期 token
    Given email_verification_tokens 表有 row {user_id: 1, token: "expired_xxx", expires_at: now - 1 小時, used_at: NULL}
    When 用戶造訪 "GET /api/auth/verify-email?token=expired_xxx"
    Then 系統回應 HTTP 302
    And Location header 為 "/login?error=token_expired"
    And users.is_verified 仍為 0

  Scenario: AC-025 已使用 token
    Given email_verification_tokens 表有 row {user_id: 1, token: "used_xxx", used_at: now - 1 小時}
    When 用戶造訪 "GET /api/auth/verify-email?token=used_xxx"
    Then 系統回應 HTTP 302
    And Location header 為 "/login?error=token_used"

  Scenario: 不存在的 token
    When 用戶造訪 "GET /api/auth/verify-email?token=nonexistent_token"
    Then 系統回應 HTTP 302
    And Location header 為 "/login?error=invalid_token"

  Scenario: AC-026 Resend 429 自動 fall through 到 SMTP
    Given 環境變數 RESEND_API_KEY 與 SMTP_HOST/USER/PASS 都已設
    And Resend API 模擬回 HTTP 429
    When 系統呼叫 send_verification_email(alice@test.com, "alice", "tok_xxx")
    Then 系統未拋例外
    And SMTP smtplib.SMTP 被呼叫
    And 函式回 True（SMTP 假設成功）
```

---

## Feature: FR-011 重寄驗證信

**對應**: `web/auth/auth_router.py:170-194`、AC-027/028、BR-007

```gherkin
Feature: FR-011 重寄驗證信

  Scenario: AC-027 未驗證帳號重寄
    Given users 表有 row {id: 1, email: "alice@test.com", is_verified: 0}
    And email_verification_tokens 表有 row {user_id: 1, token: "old_xxx", used_at: NULL}
    When 訪客發送 "POST /api/auth/resend-verification" 帶 body {email: "alice@test.com"}
    Then 系統回應 HTTP 200
    And 回應 body 為 {"ok": true, "message": "驗證信已重新寄出"} 或寄信失敗訊息
    And 舊 token "old_xxx" 的 used_at 已更新為 now（廢棄）
    And email_verification_tokens 表新增 1 row 新 token、expires_at = now + 24h

  Scenario: AC-028 已驗證帳號不發新 token
    Given users 表有 row {email: "alice@test.com", is_verified: 1}
    When 訪客發送 "POST /api/auth/resend-verification" 帶 body {email: "alice@test.com"}
    Then 系統回應 HTTP 200
    And 回應 body 為 {"ok": true, "message": "此帳號已完成驗證"}
    And email_verification_tokens 表未新增 row

  Scenario: 不存在 email
    When 訪客發送 "POST /api/auth/resend-verification" 帶 body {email: "ghost@test.com"}
    Then 系統回應 HTTP 404
    And 回應 body 為 {"detail": "找不到此 Email 的帳號"}
```

---

## Feature: FR-012 Google OAuth

**對應**: `web/auth/oauth_router.py:24, 42`、AC-029/030/031、BR-008/009、NFR-011/012

```gherkin
Feature: FR-012 Google OAuth 登入

  Scenario: AC-029 未設 GOOGLE_CLIENT_ID 時 503
    Given 環境變數 GOOGLE_CLIENT_ID 為空
    When 用戶發送 "GET /api/auth/google/login"
    Then 系統回應 HTTP 503
    And 回應 body 為 {"ok": false, "error": "Google 登入尚未設定，請聯繫管理員"}

  Scenario: AC-030 callback state 不符（CSRF 防護）
    Given 用戶 cookie oauth_state="A"
    When 用戶造訪 "GET /api/auth/google/callback?code=valid_code&state=B"
    Then 系統回應 HTTP 302
    And Location header 為 "/login?error=oauth_state_mismatch"
    And 系統未呼叫 Google token endpoint

  Scenario: AC-031 既有 email 用戶 OAuth 登入自動綁定
    Given users 表有 row {id: 5, email: "alice@gmail.com", google_id: NULL, is_verified: 0}
    And cookie oauth_state="abc"
    And Google token endpoint 模擬回 200 {"access_token": "ga_xxx"}
    And Google userinfo endpoint 模擬回 200 {"sub": "g_111", "email": "alice@gmail.com", "name": "Alice", "picture": "url"}
    When 用戶造訪 "GET /api/auth/google/callback?code=valid_code&state=abc"
    Then 系統回應 HTTP 302
    And Location header 為 "/plan"
    And users 表中 id=5 的 google_id 變為 "g_111"
    And users 表中 id=5 的 is_verified 變為 1
    And users 表中 id=5 的 avatar_url 為 "url"
    And users 表未新增 row（自動綁定既有帳號）
    And 回應 Set-Cookie 含 "access_token=" + 任意 JWT、HttpOnly、Max-Age=604800

  Scenario: 新用戶首次 Google OAuth 自動建立帳號
    Given users 表無 google_id="g_222" 且無 email="newuser@gmail.com" 的 row
    And cookie oauth_state="xyz"
    And Google userinfo 模擬回 200 {"sub": "g_222", "email": "newuser@gmail.com", "name": "NewUser", "picture": "url2"}
    When 用戶造訪 "GET /api/auth/google/callback?code=valid_code&state=xyz"
    Then users 表新增 1 row 含 {email: "newuser@gmail.com", username: "NewUser", google_id: "g_222", is_verified: 1, hashed_password: ""}
    And 系統 302 redirect "/plan"

  Scenario: 用戶在 Google 端拒絕授權
    When 用戶造訪 "GET /api/auth/google/callback?error=access_denied"
    Then 系統回應 HTTP 302
    And Location header 為 "/login?error=google_denied"
```

---

## Feature: FR-013 取得登入狀態

**對應**: `web/auth/auth_router.py:197`、`web/auth/verify_client.py:130-151`、AC-032/033

```gherkin
Feature: FR-013 取得登入狀態與用戶驗證查詢

  Scenario: AC-032 已登入用戶 GET /api/auth/me
    Given 用戶 alice 已登入
    When alice 發送 "GET /api/auth/me"
    Then 系統回應 HTTP 200
    And 回應 body 為 {"ok": true, "user": {"id": 1, "username": "alice", "email": "alice@test.com"}}

  Scenario: 未登入存取 /api/auth/me
    Given 用戶未登入
    When 用戶發送 "GET /api/auth/me"
    Then 系統回應 HTTP 401（由 Depends(get_current_user) 拋出）

  Scenario: AC-033 維運 API 用 email 查用戶狀態
    Given users 表有 row {email: "alice@test.com", username: "alice", is_verified: 1, google_id: NULL, created_at: "2026-06-01T00:00:00Z"}
    When 任何呼叫者發送 "GET /api/auth/verify?email=alice@test.com"
    Then 系統回應 HTTP 200
    And 回應 body 為 {"found": true, "user": {"id": ..., "email": "alice@test.com", "username": "alice", "is_verified": true, "auth_method": "password", "created_at": "..."}, "error": null}
    And 此 API 不需要登入（已知安全 [BA建議] SUG-002）
```

---

## Feature: FR-014 收藏 CRUD

**對應**: `web/auth/auth_router.py:214, 232, 245`、AC-034/035/036、BR-010/011

```gherkin
Feature: FR-014 收藏管理
  作為已登入用戶
  我希望儲存查詢結果為收藏
  以便日後回顧

  Background:
    Given 用戶 alice (id=1) 與 bob (id=2) 都已登入

  Scenario: AC-034 alice 新增 ski 收藏
    When alice 發送 "POST /api/favorites" 帶 body {"type": "ski", "data": {"resort": "白馬八方尾根", "price": 6500}, "label": "今年聖誕"}
    Then 系統回應 HTTP 200
    And 回應 body 為 {"ok": true, "id": <new_fav_id>}
    And favorites 表新增 row {user_id: 1, type: "ski", label: "今年聖誕"}
    And favorites.data 欄為 JSON string '{"resort": "白馬八方尾根", "price": 6500}'

  Scenario: AC-035 alice 列表只看到自己的收藏
    Given favorites 表有 row {user_id: 1, type: "ski", label: "A"}
    And favorites 表有 row {user_id: 2, type: "flight", label: "B"}
    When alice 發送 "GET /api/favorites"
    Then 系統回應 HTTP 200
    And 回應 body 為 {"ok": true, "data": [{type: "ski", label: "A", ...}]}
    And 回應不含 user_id=2 的任何 row（label "B" 不應出現）

  Scenario: AC-036 alice 嘗試刪除 bob 的收藏不報錯但不影響資料
    Given favorites 表有 row {id: 100, user_id: 2, type: "flight"}
    When alice 發送 "DELETE /api/favorites/100"
    Then 系統回應 HTTP 200
    And 回應 body 為 {"ok": true}
    And favorites 表中 id=100 的 row 仍存在（DELETE WHERE id=100 AND user_id=1 命中 0 rows）

  Scenario: type 非合法值
    When alice 發送 "POST /api/favorites" 帶 body {"type": "hotel", "data": {}}
    Then 系統回應 HTTP 400
    And 回應 body 為 {"detail": "type 必須是 ski 或 flight"}

  Scenario: 未登入嘗試收藏
    Given 用戶未登入
    When 用戶發送 "POST /api/favorites" 帶任意 body
    Then 系統回應 HTTP 401（由 Depends(get_current_user) 拋出）
```

---

## Feature: FR-015 強制登入 middleware

**對應**: `web/main.py:37-60`、AC-037/038/039、NFR-013、BR-001

```gherkin
Feature: FR-015 強制登入 middleware

  Background:
    Given 受保護頁面清單為 ["/ski", "/flight", "/plan", "/profile"]
    And 受保護 API 前綴為 ["/api/ski", "/api/flight", "/api/plan"]

  Scenario Outline: AC-037 未登入存取保護頁面 redirect
    Given 用戶未登入（無 access_token cookie）
    When 用戶發送 "GET <path>"
    Then 系統回應 HTTP 307 或 302
    And Location header 為 "/login?next=<path>"

    Examples:
      | path     |
      | /ski     |
      | /flight  |
      | /plan    |
      | /profile |

  Scenario Outline: AC-038 未登入存取保護 API 回 401 JSON
    Given 用戶未登入
    When 用戶發送 "GET <path>"
    Then 系統回應 HTTP 狀態碼 401
    And 回應 body 為 {"ok": false, "error": "請先登入", "redirect": "/login"}
    And 回應 Content-Type 為 "application/json"

    Examples:
      | path                  |
      | /api/ski/search       |
      | /api/ski/stream       |
      | /api/ski/download     |
      | /api/flight/search    |
      | /api/plan/download    |

  Scenario: AC-039 非保護路徑不需登入
    Given 用戶未登入
    When 用戶發送 "GET /"
    Then 系統回應 HTTP 200
    And 回應 Content-Type 為 "text/html; charset=utf-8"

  Scenario: 認證 API 不在 middleware 保護但用 Depends 控制
    Given 用戶未登入
    When 用戶發送 "GET /api/auth/me"
    Then 系統回應 HTTP 401（由 router 內的 Depends(get_current_user) 拋出，非 middleware）
```

---

## Feature: FR-016 頁面路由

**對應**: `web/main.py:98-110`、`web/auth/auth_router.py:41-56`、`web/plan_routes.py:38`、AC-040/041、NFR-015

```gherkin
Feature: FR-016 7 個 HTML 頁面

  Scenario Outline: AC-040 公開頁面回 200 HTML
    Given 用戶未登入
    When 用戶發送 "GET <path>"
    Then 系統回應 HTTP 200
    And 回應 Content-Type 開頭為 "text/html"

    Examples:
      | path      |
      | /         |
      | /login    |
      | /register |

  Scenario: AC-041 已登入用戶造訪 /login 重導向 /profile
    Given 用戶 alice 已登入
    When alice 發送 "GET /login"
    Then 系統回應 HTTP 302
    And Location header 為 "/profile"

  Scenario: 已登入用戶造訪 /profile 載入收藏
    Given 用戶 alice 已登入
    And favorites 表有 alice 的 3 個收藏
    When alice 發送 "GET /profile"
    Then 系統回應 HTTP 200
    And 回應 HTML 內可解析出 3 個收藏（template 已嵌入 user 與 favorites 上下文）
```

---

## Feature: FR-017 SEO

**對應**: `web/main.py:489-499+`、AC-042/043

```gherkin
Feature: FR-017 SEO 端點

  Scenario: AC-042 robots.txt 內容
    When 搜尋引擎爬蟲發送 "GET /robots.txt"
    Then 系統回應 HTTP 200
    And 回應 Content-Type 為 "text/plain"
    And 回應 body 包含 "User-agent: *"
    And 回應 body 包含 "Disallow: /api/"
    And 回應 body 包含 "Sitemap: https://snowboarding-support-system-jp-production.up.railway.app/sitemap.xml"

  Scenario: AC-043 sitemap.xml 內容
    When 搜尋引擎爬蟲發送 "GET /sitemap.xml"
    Then 系統回應 HTTP 200
    And 回應 body 為合法 XML
    And 回應 body 含至少 3 個 <url> 區段，loc 分別為 "/"、"/ski"、"/flight"
```

---

## 場景統計

| FR | Scenario 數 | Edge 案例 |
|----|-------------|----------|
| FR-001 | 4 | timeout、lock 衝突、未登入 |
| FR-002 | 3 | lock 衝突、resort_done 多筆 |
| FR-003 | 3 | lock 衝突 → 429、無 region 預設值 |
| FR-004 | 3 | SerpAPI / fast-flights / 缺參數 |
| FR-005 | 1 | filename + xlsx 排序 |
| FR-006 | 2 | redirect、3-sheet 結構 |
| FR-007 | 5 | 密碼短 / email 錯 / 重複 / 成功 + 寄信失敗 |
| FR-008 | 4 | 成功 / 密碼錯 / 不存在 / 未驗證 |
| FR-009 | 1 | 清除 cookie |
| FR-010 | 5 | 有效 / 過期 / 已用 / 不存在 / Resend 429 fallback |
| FR-011 | 3 | 未驗證 / 已驗證 / 不存在 |
| FR-012 | 5 | 未設定 / state 不符 / 既有用戶綁定 / 新用戶 / 拒絕 |
| FR-013 | 3 | /me 成功 / 401 / verify email |
| FR-014 | 5 | 新增 / 列表隔離 / 跨用戶刪除 / type 錯 / 未登入 |
| FR-015 | 4 (Outline) + 2 | 頁面 4 條 / API 5 條 / 公開頁 / auth API |
| FR-016 | 3 (Outline) + 2 | 公開頁 / login redirect / profile 含收藏 |
| FR-017 | 2 | robots / sitemap |

**總計**: 17 個 FR × 平均 3.3 個 scenario = **約 56 條 Gherkin scenario**（含 Scenario Outline 展開），可直接餵給 Tester pytest-bdd / behave 生成測試案例。
