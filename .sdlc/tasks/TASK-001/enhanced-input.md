---
task_id: "TASK-001"
mode: "brownfield-document"
created_at: "2026-06-03T13:15:15Z"
base_branch: "sdlc/init"
---

# TASK-001 增強需求

## 原始需求

> 補追溯既有 28 API + 3 ENTITY (users / favorites / email_verification_tokens) + 8 PAGE 到 `.sdlc/shared/`，不寫新代碼，純規格產出（brownfield-document mode）。

## 增強後需求

### 目標

把 snowboarding_support 既有的所有功能反向產出為 SDLC 規格文件，使 `.sdlc/shared/` 與 `.sdlc/tasks/TASK-001/` 內容能描述目前 production 已運作的系統。**完全不修改 `web/` 任何業務代碼**。產出後：

1. id-registry / terminology / error-codes / sa-index / sd-index / be-index / uiux-index / page-index / component-index / api-conventions（引用既有）全部反映現況
2. 後續 TASK-002+ 可以從這份「真相基線」展開新功能（修 bug、加新需求、Postgres 遷移）
3. 最終 merge 到 main 對網站使用者**零行為變化**（純文件加入）

### 範圍邊界

#### 納入（MUST cover）

**28 個 API endpoint**（baseline-audit 2.1 列表）:

頁面路由（6 個）:
- `GET /` index
- `GET /ski` ski_page（強制登入）
- `GET /flight` flight_page（強制登入）
- `GET /plan` plan_page（強制登入）
- `GET /login` login_page
- `GET /register` register_page
- `GET /profile` profile_page（強制登入）

雪票 API（3 個）:
- `GET /api/ski/search` 批次查詢
- `GET /api/ski/stream` SSE 串流
- `GET /api/ski/download` Excel 下載

機票 API（2 個）:
- `GET /api/flight/search`
- `POST /api/flight/download`

整合查詢（1 個）:
- `POST /api/plan/download`

認證 API（9 個）:
- `POST /api/auth/register`
- `POST /api/auth/login`
- `POST /api/auth/logout`
- `GET /api/auth/me`
- `GET /api/auth/verify`
- `GET /api/auth/verify-email`
- `POST /api/auth/resend-verification`
- `GET /api/auth/google/login`
- `GET /api/auth/google/callback`

收藏 API（3 個）:
- `GET /api/favorites`
- `POST /api/favorites`
- `DELETE /api/favorites/{id}`

SEO（2 個）:
- `GET /robots.txt`
- `GET /sitemap.xml`

**3 個 ENTITY/TBL**（baseline-audit 2.2，源自 `web/auth/database.py:18-42`）:
- `users` (id, email UNIQUE, username UNIQUE, hashed_password, is_verified, google_id UNIQUE, avatar_url, created_at)
- `favorites` (id, user_id FK CASCADE, type, data, label, created_at)
- `email_verification_tokens` (id, user_id FK CASCADE, token UNIQUE, expires_at, used_at)

**8 個 PAGE**（baseline-audit 2.3）:
- `PAGE-001` /（index）
- `PAGE-002` /ski
- `PAGE-003` /flight
- `PAGE-004` /plan
- `PAGE-005` /profile
- `PAGE-006` /login
- `PAGE-007` /register
- `LAYOUT-001` base.html（不是 PAGE 而是 LAYOUT — UIUX 階段確認分類）

**6 個 MOD**（baseline-audit 2.5）:
- `MOD-001` http_scraper
- `MOD-002` site_analyzer
- `MOD-003` ski_early_bird_scraper
- `MOD-004` flight_search（含 backends/）
- `MOD-005` auth（含 oauth/verify/email/security/database/dependencies）
- `MOD-006` plan_routes

**核心功能 FUNC 候選**（baseline-audit 2.6，BA 階段精煉為 FR）:
1. 雪票批次/串流/Excel 三種查詢模式
2. 機票查詢 + Excel 下載 + 多 backend fallback（SerpAPI / Travelpayouts / Amadeus / fast-flights）
3. 整合查詢頁 /plan + 3-sheet Excel
4. JWT 註冊（含密碼複雜度檢查 ≥ 8 字元）
5. JWT 登入（HTTP-only cookie, 7 天）
6. Logout
7. Email 驗證（Resend + SMTP fallback）
8. 重寄驗證信
9. Google OAuth 登入 + callback
10. 取得登入狀態（`/api/auth/me` 與 `/api/auth/verify`）
11. 收藏列表 / 新增 / 刪除
12. 強制登入 middleware（保護 `/ski` `/flight` `/plan` `/profile` `/api/ski` `/api/flight` `/api/plan`）
13. SEO（robots / sitemap / OG / JSON-LD）

#### 待確認（BA 階段需釐清）

- **非功能需求**（NFR）：以下從現況推測，BA 階段請與既有實作對照確認:
  - 雪票查詢 timeout = 45 秒（`web/main.py:137`）
  - JWT 有效期 = 7 天（`web/auth/security.py`）
  - Resend 上限觸發 429 後切 SMTP（`web/auth/email_service.py`）
  - SQLite path = `web/data/snowtrip.db`（**已知 Critical：Railway ephemeral**）
  - 密碼 hash = bcrypt 直接呼叫（不用 passlib，因相容性問題）
  - 認證載體 = HTTP-only cookie `access_token`（SameSite=Lax, Secure 在 prod）
- **業務術語表**: BA 階段建立至少這些術語的官方定義:
  - 雪場（resort）、雪季（season）、票種（ticket_type）、早鳥票（early_bird）
  - 收藏（favorite）、行程規劃（trip plan）
  - 強制登入路徑（protected route）
- **BDD 場景**: 模式啟用 BDD，BA 階段必附 Given/When/Then 場景（每個核心 FR 至少 1 個）

#### 不納入（OUT OF SCOPE — Tester 會驗證沒越界）

- ❌ **不寫任何新 web/ 代碼** — 純規格產出
- ❌ **不改 conventions** — 已 lock v1.1
- ❌ **不做 Postgres 遷移**（留 TASK-002）
- ❌ **不修 brownfield 技術債**（DESIGN.md §八 列的 8 項 brownfield 標記 — 留後續 TASK）
- ❌ **不補齊 urls.json 剩餘雪場**（這是內容工作，不是程式工作，留另外 TASK 或人工流程）
- ❌ **不安裝 Pencil MCP**（前置工作，使用者負責）
- ❌ **不規劃 Vue 重構**（留更後面 TASK）

### 專案上下文

**技術棧（config.json，含 brownfield reality）**:
- Backend: FastAPI + Python 3.12 + Jinja2 + bcrypt + python-jose
- Frontend: **Jinja2 SSR + Bootstrap 5 CDN + vanilla JS**（config 宣告 Vue 是未來目標，brownfield grandfather）
- Database: **SQLite**（config 宣告 Postgres 是未來目標，brownfield grandfather）
- Deploy: Railway（uvicorn ASGI）
- 認證: JWT + HTTP-only cookie + Google OAuth

**全域 ID 狀態（id-registry 空白，這是第一個 TASK）**:
- ID Allocator 將在 Step 4.3 配發 TASK-001 範圍（預計 ENTITY/MOD/FUNC/PATTERN/API/TBL/COMP/PAGE/LAYOUT 各 [1, 100]）
- 既有 28 API + 3 ENTITY + 8 PAGE 都從 TASK-001 範圍依序分配
- ERR-* 由 SD 階段建立（baseline 已標 error-codes 全空）

**已有共享層**:
- `.sdlc/shared/*.md` 12 個 + apps/snowboarding_support/{component,page}-index.md 全部從模板初始（無實質內容）
- `.sdlc/conventions/*.md` 5 個 v1.1 已 lock — BA/SA/SD 必須遵守

**Baseline 報告**: `.sdlc/baseline/baseline-audit-2026-06-03.md`（420+ 行）— 完整列出既有功能、ID 候選、conventions 違反、DESIGN.md 一致性。BA agent **必讀**。

**外部關鍵文件**:
- `D:\SideProject\DESIGN.md`（576 行，已 sync）— 既有功能說明
- `D:\SideProject\snowboarding_support\CLAUDE.md`（102 行）— 專案守則

**所屬 App**: `snowboarding_support`（單一 App）

---

## BA 階段交付物（agent 自行決定具體章節）

1. `ba/requirement-spec.md` — 把上述 13 個核心功能轉成 FR-001..FR-NNN（含來源引用：`來源: 既有實作 web/...`）+ NFR-001..NFR-NNN（從 baseline + 現況推測，BA 階段詢問用戶確認）+ 業務角色 ROLE-001..NNN
2. `ba/business-flow.md` — 雪票查詢 / 機票查詢 / 整合查詢 / 註冊登入 / 收藏 / Email 驗證 / Google OAuth 七大流程的業務級流程圖（mermaid 或 ASCII）
3. （BDD 模式）`ba/bdd-scenarios.md` — Given/When/Then 每核心 FR 至少 1 個
4. `ba/self-review.json` — 20 項驗證清單 ≥ 90 分
5. `ba/terminology-additions.md`（可選）— BA 階段新增的業務術語給 PM 收進 journal

## 重要原則（給 BA agent）

1. **反腦補**：所有 FR/NFR 必須有來源引用（`來源: 使用者原文` / `來源: 既有實作 file:line` / `[INFERRED: 推理依據]` / `[BA建議]`）
2. **Brownfield 真相優先**：當 baseline / DESIGN.md / 既有 code 三者不一致時，以 code 為真相，標 `[CODE-AS-TRUTH: file:line]`
3. **不擴大範圍**：上述「不納入」清單是硬邊界，越界由 Tester 標 Critical
4. **詢問用戶 NFR**：所有 [INFERRED] 的 NFR（timeout、cookie 屬性、Resend rate limit 等）BA 階段必須整理成「待用戶確認」清單，方便用戶一次回答
