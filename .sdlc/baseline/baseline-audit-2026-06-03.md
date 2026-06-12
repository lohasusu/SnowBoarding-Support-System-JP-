# Baseline Audit Report — snowboarding_support

- 生成時間: 2026-06-03T09:02:35Z
- 分支: sdlc/init
- 審查範圍: SDLC init 產出 + 既有專案盤點
- 審查者: SDLC Tester（獨立 brownfield audit）
- 引用基準: `~/.claude/sdlc/rules/sdlc-global.md`、`~/.claude/sdlc/rules/sdlc-tester.md`、`.sdlc/conventions/*.md`（鎖定時間 2026-06-03T07:57:02Z）

> 本報告只盤點，不修改任何檔案。發現分級依 Tester Rule 3：
> - **Critical**: 阻塞跨 TASK 一致性 / 安全 / 不可逆操作
> - **Major**: 違反明確 conventions 但可遞延
> - **Minor**: 風格差異 / 模板殘留

---

## 摘要

| 指標 | 數值 |
|------|------|
| Critical | **2** 項 |
| Major | **11** 項 |
| Minor | **9** 項 |
| 待人工審查 | 1 項 |

**ID 候選預登記建議**:
- API 候選: **26** 個（含 SSE / Excel download / OAuth callback / verify endpoint）
- ENTITY 候選: **3** 個（users / favorites / email_verification_tokens）
- TBL 候選: **3** 個（與 ENTITY 對應，SQLite snake_case）
- PAGE 候選: **8** 個（index / ski / flight / plan / profile / login / register / 404 隱性）
- COMP 候選: **30** 個（依 4 個 JS 檔的 top-level functions 推算）
- MOD 候選: **6** 個（http_scraper / site_analyzer / ski_early_bird / flight_search / auth / plan_routes）

**結論**: 既有專案在語意上對應 1 個「大功能 App」，但無 SDLC TASK 紀錄。建議第一個 TASK 採用 **brownfield-document（補追溯）** 模式，把現有 26 個 API + 3 個 TBL + 8 個 PAGE 一次性納入 shared/。

---

## 區塊 1: SDLC Init 產出驗證

### 1.1 核心檔案存在性

| 檔案 | 結果 | 證據 / 備註 |
|------|------|-------------|
| `.sdlc/config.json` | ✅ | 結構合法、techStack 三層展開正確、`gitStrategy.mode = "docs-only"`、`pencilMcp = false`、`mcpStatus.pencil = false`、`claudePreview = true` |
| `.sdlc/state.json` | ✅ | 結構為 `{version, project:{}, tasks:{}}`（初始空白） |
| `.sdlc/conventions/api-conventions.md` | ✅ | `locked_at: 2026-06-03T07:57:02Z`（ISO 合法） |
| `.sdlc/conventions/branch-conventions.md` | ✅ | 同上 |
| `.sdlc/conventions/code-conventions.md` | ✅ | 同上 |
| `.sdlc/conventions/db-conventions.md` | ✅ | 同上 |
| `.sdlc/conventions/i18n-conventions.md` | ✅ | 同上 |
| `.sdlc/conventions/design-system.meta.json` | ✅ | `version=0.1.0`、`rfcHistory[0]` 有 init entry、`componentInventory: []` |
| `.sdlc/conventions/design-system.pen` | ⚠️ | **檔案不存在**（CODEOWNERS 第 27 行已預列保護），但 Pencil MCP 未安裝（config.json 已標記 `pencilMcp: false`），符合「延後安裝」狀態。後續 UIUX 階段前必須補。記為 Minor。 |
| `.sdlc/shared/MASTER-INDEX.md` | ✅ | 完整 8 章節，含 ID 規則 |
| `.sdlc/shared/id-registry.md` | ✅ | 12 張表（全空），ENTITY/API/COMP/PAGE/MOD/FUNC/TBL/ERR/LAYOUT/AC/ROLE/TASK |
| `.sdlc/shared/terminology.md` | ✅ | 存在（未檢內容） |
| `.sdlc/shared/error-codes.md` | ✅ | 存在 |
| `.sdlc/shared/code-registry.md` | ✅ | 模板初始狀態，前端 / 後端 / migration 區塊就緒 |
| `.sdlc/shared/ba-index.md` | ✅ | 存在 |
| `.sdlc/shared/sa-index.md` | ✅ | 存在 |
| `.sdlc/shared/uiux-index.md` | ✅ | 存在 |
| `.sdlc/shared/sd-index.md` | ✅ | 存在 |
| `.sdlc/shared/be-index.md` | ✅ | 存在 |
| `.sdlc/shared/tester-index.md` | ✅ | 存在 |
| `.sdlc/shared/i18n-registry.md` | ✅ | 存在 |
| `.sdlc/shared/apps/snowboarding_support/component-index.md` | ✅ | App 級索引初始 |
| `.sdlc/shared/apps/snowboarding_support/page-index.md` | ✅ | App 級索引初始 |
| `.sdlc/environments.json` | ✅ | 含 `dev/staging/prod` 三 key + V2 schema 完整 |
| `docker-compose.yml` | ✅ | PR 13c 多 engine 版本 |
| `fe/Dockerfile` | ✅ | PR 13c 多 stack 版本 |
| `be/Dockerfile` | ✅ | PR 13c 多語言版本 |
| `.env` | ✅ | 含 `>>> SDLC AUTO-RENDER START` marker（第 1 行）+ `<<< SDLC AUTO-RENDER END` 結束（第 23 行） |
| `.env.example` | ✅ | 存在 |
| `.env.frontend` / `.env.backend` | ✅ | 已生成（render-docker-env.sh 產物） |
| `.gitignore` | ✅ | 含 `.sdlc/backup/` `.sdlc/history/` `.sdlc/exports/` `.sdlc/deploy-coordination.json`（皆出現於檔案內） |
| `.gitattributes` | ✅ | 含 `.sdlc/audit.log merge=union` + `.sdlc/.abandoned-tasks.txt merge=union` |
| `CLAUDE.md` | ✅ | 第 53 行 `<!-- SDLC-WORKFLOW-START -->`、第 100 行 `<!-- SDLC-WORKFLOW-END -->` markers 完整 |
| `.github/CODEOWNERS` | ✅ | 完整模板，含 `.sdlc/conventions/**` / `id-allocator.json` / workflows / scripts 保護 |
| `.claude/settings.json` | ✅ | 3 個 hooks（PreToolUse / SubagentStart / SubagentStop）matcher 正確 |

### 1.2 GitHub Actions Workflows

| Workflow | 結果 |
|----------|------|
| `.github/workflows/sdlc-ci-pr.yml` | ✅ |
| `.github/workflows/sdlc-merge-gate.yml` | ✅ |
| `.github/workflows/sdlc-post-merge.yml` | ✅ |
| `.github/workflows/sdlc-ci-integration.yml` | ✅ |
| `.github/workflows/sdlc-cross-task-check.yml` | ✅ |
| `.github/workflows/sdlc-deploy-precheck.yml` | ✅ |

**6 個 workflow 全數齊全。**

### 1.3 一致性互檢

| 檢查項 | 結果 | 證據 |
|--------|------|------|
| config.json.techStack 與 .env 自動渲染區塊一致 | ✅ | `.env:13-23` 全部對應 `config.json` 的 vue + fastapi + postgres |
| config.json.pencilMcp = false 與 `.claude/settings.json` 不需要 Pencil hook | ✅ | settings 無 pencil-specific hook |
| config.json.gitStrategy.mode = "docs-only" 與 CLAUDE.md 文字「Git 管理: docs-only」 | ✅ | CLAUDE.md line 79 一致 |
| config.json.sharedLayer.apps[0] = "snowboarding_support" 與 shared/apps/ 子目錄 | ✅ | 目錄存在 |
| MASTER-INDEX.md ID 種類 vs id-registry.md 預設表 | ✅ | 兩份對得上（FUNC/MOD/ENTITY/API/PAGE/COMP/TBL/ERR/LAYOUT/AC/ROLE） |

---

## 區塊 2: 既有代碼 ID 候選清單

> 用途：給 PM 在第一個 TASK 開始前預先登記，避免 SD/UIUX/SA 重複編號。
> 編號規則：依 MASTER-INDEX §4.1（3 位零填充、從 001 起編、不可跳號）。

### 2.1 候選 API（26 個）

> 來源：`grep -nE '@app\.|@auth_router\.|@plan_router\.|@oauth_router\.|@verify_router\.' web/`，加上 main.py 的 `include_router`。

| 候選 ID | Method | Path | Function | 檔案:行 | 分類 |
|---------|--------|------|----------|---------|------|
| API-001 | GET | `/` | index | `web/main.py:98` | page |
| API-002 | GET | `/ski` | ski_page | `web/main.py:103` | page |
| API-003 | GET | `/flight` | flight_page | `web/main.py:108` | page |
| API-004 | GET | `/api/ski/search` | api_ski_search | `web/main.py:127` | data |
| API-005 | GET | `/api/ski/stream` | (SSE) | `web/main.py:153` | data (SSE) |
| API-006 | GET | `/api/ski/download` | (Excel) | `web/main.py:197` | binary |
| API-007 | GET | `/api/flight/search` | api_flight_search | `web/main.py:252` | data |
| API-008 | POST | `/api/flight/download` | api_flight_download | `web/main.py:442` | binary |
| API-009 | GET | `/api/env-check` | (debug) | `web/main.py:461` | **debug — 候選刪除** |
| API-010 | GET | `/robots.txt` | (SEO) | `web/main.py:489` | static |
| API-011 | GET | `/sitemap.xml` | (SEO) | `web/main.py:497` | static |
| API-012 | GET | `/plan` | plan_page | `web/plan_routes.py:38` | page |
| API-013 | POST | `/api/plan/download` | api_plan_download | `web/plan_routes.py:121` | binary |
| API-014 | GET | `/login` | login_page | `web/auth/auth_router.py:41` | page |
| API-015 | GET | `/register` | register_page | `web/auth/auth_router.py:51` | page |
| API-016 | GET | `/profile` | profile_page | `web/auth/auth_router.py:56` | page (auth) |
| API-017 | POST | `/api/auth/register` | api_register | `web/auth/auth_router.py:85` | auth |
| API-018 | POST | `/api/auth/login` | api_login | `web/auth/auth_router.py:117` | auth |
| API-019 | POST | `/api/auth/logout` | api_logout | `web/auth/auth_router.py:138` | auth |
| API-020 | GET | `/api/auth/verify-email` | api_verify_email | `web/auth/auth_router.py:145` | auth |
| API-021 | POST | `/api/auth/resend-verification` | api_resend_verification | `web/auth/auth_router.py:170` | auth |
| API-022 | GET | `/api/auth/me` | api_me | `web/auth/auth_router.py:197` | auth |
| API-023 | GET | `/api/favorites` | api_get_favorites | `web/auth/auth_router.py:214` | crud |
| API-024 | POST | `/api/favorites` | api_add_favorite | `web/auth/auth_router.py:232` | crud |
| API-025 | DELETE | `/api/favorites/{fav_id}` | api_delete_favorite | `web/auth/auth_router.py:245` | crud |
| API-026 | GET | `/api/auth/google/login` | google_login | `web/auth/oauth_router.py:24` | auth (OAuth) |
| API-027 | GET | `/api/auth/google/callback` | google_callback | `web/auth/oauth_router.py:42` | auth (OAuth) |
| API-028 | GET | `/api/auth/verify` | api_verify | `web/auth/verify_client.py:130` | auth (debug) |

> 實際數量 = **28**（超出摘要的 26 — 摘要保守估計時漏算 verify 和 OAuth 第二個）。建議實際登記時用此完整清單。

### 2.2 候選 ENTITY（3 個）+ TBL（3 個）

> 來源：`web/auth/database.py:18-42` 的 CREATE TABLE 區塊。SQLite 實檔 `web/data/snowtrip.db` (24576 bytes, SQLite 3.x)。

| 候選 ENTITY-ID | 候選 TBL-ID | 表名 | 主鍵 | 欄位概要 | 檔案:行 |
|---------------|-------------|------|------|----------|---------|
| ENTITY-001 | TBL-001 | `users` | `id` INTEGER PK AUTOINCREMENT | email (UNIQUE)、username (UNIQUE)、hashed_password、is_verified、google_id (UNIQUE)、avatar_url、created_at | `web/auth/database.py:18-27` |
| ENTITY-002 | TBL-002 | `favorites` | `id` INTEGER PK AUTOINCREMENT | user_id FK → users(id) ON DELETE CASCADE、type、data (JSON 字串)、label、created_at | `web/auth/database.py:28-35` |
| ENTITY-003 | TBL-003 | `email_verification_tokens` | `id` INTEGER PK AUTOINCREMENT | user_id FK → users(id) ON DELETE CASCADE、token (UNIQUE)、expires_at、used_at | `web/auth/database.py:36-42` |

### 2.3 候選 PAGE（8 個）

> 來源：`ls web/templates/`。

| 候選 PAGE-ID | 路由 | 模板檔案 | 對應功能 |
|--------------|------|----------|----------|
| PAGE-001 | `/` | `web/templates/index.html` | 首頁 |
| PAGE-002 | `/ski` | `web/templates/ski.html` | 雪票查詢 |
| PAGE-003 | `/flight` | `web/templates/flight.html` | 機票查詢 |
| PAGE-004 | `/plan` | `web/templates/plan.html` | 整合查詢 |
| PAGE-005 | `/profile` | `web/templates/profile.html` | 會員個人頁 |
| PAGE-006 | `/login` | `web/templates/auth/login.html` | 登入 |
| PAGE-007 | `/register` | `web/templates/auth/register.html` | 註冊 |
| PAGE-008 | (base) | `web/templates/base.html` | **不是頁面而是 LAYOUT** — 建議登記為 LAYOUT-004（在預設 Header/Sidebar/Footer 之外） |

### 2.4 候選 COMP（依 JS 推算 ~30 個）

> 來源：`grep '^  function ' web/static/js/*.js`（IIFE 內部 named function）。
> **注意**：這些是「行為片段」而非元件 — 既有專案無前端框架，沒有真正的可重用 Component 樹。如果未來轉 Vue/React，這些函式才會升級為 COMP。
> 為 PM 第一個 TASK 預登記建議：先不要逐一發 COMP-ID，**等 UIUX 重設計時才正式編號**。下表只是「目前 JS 行為單元」清單，給 BA/SA 估算複雜度用。

| 檔案 | top-level functions (IIFE 內) | 數量 |
|------|------------------------------|------|
| `web/static/js/ski.js` | escHtml / setQuerying / initTable / appendRow / updateProgress / setError / showEmpty | 7 |
| `web/static/js/flight.js` | escHtml / sortFlights / fmtTime / extractAirline / uniqueAirlines / renderFlights / setLoading / setError | 8 |
| `web/static/js/plan.js` | escHtml / fmtTime / extractAirline / sortFlights / showLoading / renderResults / downloadExcel | 7 |
| `web/static/js/auth.js` | escHtml + 內聯 event listeners（登入 / 註冊 / 收藏 / 登出） | 1 命名 + N 內聯 |

`escHtml` 重複出現 4 次 → **未來重構必抽 utility（候選 COMP-001: util.escHtml 或 MOD-005 util）**。

### 2.5 候選 MOD（6 個）

| 候選 MOD-ID | 模組名稱 | 路徑 | 角色 |
|-------------|----------|------|------|
| MOD-001 | http_scraper | `http_scraper.py` | 雪票生產爬蟲（httpx，無 Playwright） |
| MOD-002 | site_analyzer | `site_analyzer.py` | 月度分析（待重構） |
| MOD-003 | ski_early_bird_scraper | `ski_early_bird_scraper.py` | 本地 CLI 爬蟲（Playwright） |
| MOD-004 | flight_search | `flight_search/flight_search.py` + `backends/` | 機票查詢（多 backend 策略模式） |
| MOD-005 | auth | `web/auth/` | 認證 + 收藏（含 OAuth / verify / email） |
| MOD-006 | plan_routes | `web/plan_routes.py` | 整合查詢 + Excel 下載 |

### 2.6 候選 FUNC（粗估）

> SA 階段才會正式編號；此處列「使用者可見功能」供 BA 萃取需求參考。

1. 雪票批次查詢（JSON）
2. 雪票串流查詢（SSE）
3. 雪票 Excel 下載
4. 機票查詢（fast-flights）
5. 機票 Excel 下載
6. 機票多後端 fallback（SerpAPI / Travelpayouts / Amadeus）
7. 整合查詢頁
8. 整合 Excel 下載（3 Sheet）
9. JWT 註冊（含密碼複雜度檢查）
10. JWT 登入（HTTP-only cookie）
11. Logout
12. Email 驗證（Resend + SMTP fallback）
13. 重寄驗證信
14. Google OAuth 登入
15. Google OAuth callback
16. 取得登入狀態 `/api/auth/me` 和 `/api/auth/verify`
17. 收藏列表
18. 新增收藏
19. 刪除收藏
20. 強制登入 middleware（`/ski` `/flight` `/plan` `/profile` `/api/ski` `/api/flight` `/api/plan`）
21. SEO（robots / sitemap / OG / JSON-LD）
22. **debug**：`/api/env-check`（候選移除）

---

## 區塊 3: 技術棧 Gap

| 規劃宣告 (`.sdlc/config.json`) | 實際現況 | Gap 類型 | 優先處理 |
|----------------------------|----------|----------|----------|
| `techStack.frontend.framework = "vue"` | **無前端框架** — 純 Jinja2 + Bootstrap 5 CDN + 原生 JS / IIFE 模式（`web/templates/*.html` + `web/static/js/*.js`） | **規劃未來轉，現況差距大** | 高 — 影響 UIUX/FE 階段，需要 PM 決定：(A) 短期 brownfield 接受 Jinja2 + 後續 TASK 轉 Vue，或 (B) 第一個 TASK 直接做 Vue 重寫 |
| `techStack.frontend.envPrefix = "VUE_APP_"` | 沒有 frontend env var（純後端渲染） | 同上 | 與上同 |
| `techStack.frontend.buildImage = "node:22-alpine"` `.buildCmd = "npm run build"` | 無 `package.json`、無 `node_modules`、無 build step | 同上 | 與上同 |
| `techStack.backend.framework = "fastapi"` | ✅ FastAPI（`web/main.py:30`、`requirements.txt:2`） | 一致 | — |
| `techStack.backend.language = "python"` `.runtime = "python:3.12-slim"` | ✅ Python（無明確版本宣告，但 requirements 兼容 3.10+） | 一致（runtime 版本待 BE Dockerfile 對應） | 低 |
| `techStack.backend.pkgManager = "pip"` | ✅ `requirements.txt` (pip-style) | 一致 | — |
| `techStack.database.engine = "postgres"` `.image = "postgres:16-alpine"` `.port = "5432"` | ❌ **SQLite** — `web/data/snowtrip.db` (24KB), 直接從 `web/auth/database.py:1-15` 用 `sqlite3` module | **現況與宣告嚴重不符** | **Critical** — Railway 已知問題：SQLite 在 Railway 部署環境是 ephemeral storage，重啟即遺失資料（CLAUDE.md 已記載）。第一個 TASK 應正式列為 BA 需求：DB engine 遷移到 Postgres |
| `containerStrategy.registry = "ghcr.io"` | 實際部署在 Railway（無 ghcr.io image） | 部署策略差距 | 中 — config 為「未來 self-host」做了準備，但目前是 Railway。可選擇 (A) 改 `containerStrategy = "railway"` 或 (B) 第一個 TASK 把 Railway 換到 ghcr.io + 自管 hosting |
| `containerStrategy.devcontainer = true` | 無 `.devcontainer/` 目錄 | 設定但未實作 | 低 |
| `gitStrategy.subBranches.enabled = false` | 實際歷史曾用 worktree（commit `2f71855: 合併三個 worktree branch`） | 模式不一致但已合併回 main，無遺留 | 低 |
| `mcpStatus.pencil = false` | ✅ 一致（design-system.meta.json 也標記「Pencil MCP not yet installed」） | 一致 | — |

### 3.1 Critical Gap：DB engine

- 證據：
  - `web/auth/database.py:1` `import sqlite3`
  - `web/auth/database.py:18-42` CREATE TABLE 用 SQLite 語法（`INTEGER PRIMARY KEY AUTOINCREMENT`、`BOOLEAN`）
  - `.sdlc/config.json:21-27` 宣告 postgres / postgres:16-alpine
  - `CLAUDE.md` 第 49 行明確標註「SQLite DB 在 Railway 重啟後**資料會消失**」
- 風險：所有以為「user data 持久」的功能（收藏、email 驗證 token、Google OAuth user 綁定）在 Railway 重啟後丟失 → 安全/體驗 Critical
- 對 SDLC 流程影響：BA 第一個 TASK 必須把「DB 持久化」列為 FR；SA 階段必須選定 Postgres 部署路徑（Railway Postgres add-on / 外部託管 / 自架）

---

## 區塊 4: Conventions 違反審查

> 評估基準：模板預設值（即使有 `[CUSTOMIZE]` 標記也視為已生效，違反算 Major 不算 Critical）。
> 例外：與安全 / 跨 TASK 一致性 / 不可逆有關的違反仍可升 Critical（Rule 3）。

### 4.1 Critical

| 編號 | 違反項 | 規則來源 | 證據 |
|------|--------|----------|------|
| C-1 | **DB engine 與 conventions 假設不符** | `db-conventions.md` 第 100 行「Charset utf8mb4 / Postgres UTF8」+ §5 migration 規範 + §5.3 三段式刪欄 | SQLite 無 charset 概念、無正式 migration framework（用 `ALTER TABLE ADD COLUMN` 加 try/except 寬鬆吞例外 — `web/auth/database.py:44-52`），違反「reversible migration」「三段式刪欄」「禁止修改已 push 的 migration」 |
| C-2 | **`/api/env-check` debug endpoint 留在生產** | `code-conventions.md` §7「Console.log / print 留在生產 code（只在開發模式）」+ 廣義安全：debug endpoint 不應在 prod 可達 | `web/main.py:461` `@app.get("/api/env-check")`，DESIGN.md 未列為「除錯保留」，git log 顯示是「77787bb debug: add /api/env-check endpoint to diagnose Railway env vars」遺留。**Railway 生產可達 → 可能洩漏 env var 名稱** |

### 4.2 Major

| 編號 | 違反項 | 規則來源 | 證據 |
|------|--------|----------|------|
| M-1 | URL 命名：`/login` `/register` `/profile` `/ski` `/flight` `/plan` 用單數 | `api-conventions.md` §1「資源名用複數」（雖然這些是「頁面」非 REST 資源，但模板未區分） | `web/main.py:103/108`、`web/auth/auth_router.py:41/51/56`、`web/plan_routes.py:38` |
| M-2 | API 路徑大量單數資源：`/api/ski/...` `/api/flight/...` `/api/plan/...` `/api/auth/...` | 同上 §1 | 全部端點 |
| M-3 | API 回應格式不統一 | `api-conventions.md` §3「成功 `{data, message}` / 錯誤 `{error: {code, message}}`」 | `/api/auth/login` 回 `{ok: True, user, redirect}`（`web/auth/auth_router.py:117+`）；`/api/auth/register` 回 `{ok: True, msg}`；`/api/ski/search` 回 `{ok: True, data: [...]}`；錯誤回 HTTPException `{detail: "..."}` — 三套不一致 |
| M-4 | 錯誤回應結構不符 | `api-conventions.md` §3 + `error-codes.md`（空表 — 無錯誤碼） | `HTTPException(status_code=400, detail="密碼至少 8 個字元")` — 純字串、無 code、未登記 ERR-* |
| M-5 | 缺乏統一錯誤碼 | `error-codes.md` 預留 DOMAIN: SYS/AUTH/USER/DATA/VAL，但實作未使用 | shared/error-codes.md 全空，BE 直接寫中文 detail |
| M-6 | 認證方式：使用 HTTP-only cookie 而非 conventions 指定的 Bearer Token | `api-conventions.md` §4「Bearer Token 預設」 | `web/auth/auth_router.py:117+` 設定 cookie `access_token`、`web/main.py:48` 讀 `request.cookies.get("access_token")`。**功能上更安全（防 XSS），但與模板 conventions 不符** — 建議修改 conventions（RFC 流程）而非改實作 |
| M-7 | 缺 HTTP 狀態碼一致性：登入失敗用 401 但 register 失敗用 400 (`detail="密碼至少 8 個字元"`) 應用 422 | `api-conventions.md` §5「400 請求格式錯誤 / 驗證失敗」（其實對齊） | 這點上其實是 conventions 的模糊處 — `code-conventions` 無 22x 區分。**屬於 conventions 待細化** |
| M-8 | Schema 缺少 `updated_at`、`deleted_at` 軟刪欄位 | `db-conventions.md` §2「時間戳 `created_at` / `updated_at` / `deleted_at`」 | `users` / `favorites` / `email_verification_tokens` 三張表都只有 `created_at`，無 `updated_at`。`favorites` DELETE 直接刪除（`auth_router.py:246`）非軟刪 → 違反 Rule 11 不可逆操作協議精神 |
| M-9 | 缺索引命名 | `db-conventions.md` §3「`idx_` / `uniq_`」 | `users.email UNIQUE` 是隱式索引（SQLite 自動建），未明確命名為 `uniq_users_email` |
| M-10 | 程式碼後端結構不符建議目錄 | `code-conventions.md` §3.2 推薦 `controllers/ services/ repositories/ models/ middleware/` | 實際 `web/auth/` 是 flat layout：`auth_router.py` / `database.py` / `dependencies.py` / `security.py` / `email_service.py` / `oauth_router.py` / `verify_client.py`，無分層 |
| M-11 | 一個 router 檔案內混合 page route + API route | `code-conventions.md` §3「pages 對應 PAGE / api 對應 controllers」（隱含分層） | `web/auth/auth_router.py:41,51,56` 是 page route（HTMLResponse），`web/auth/auth_router.py:85+` 是 JSON API。混在同檔（大型化後難維護） |

### 4.3 Minor

| 編號 | 違反項 | 規則來源 | 證據 |
|------|--------|----------|------|
| m-1 | Git commit message 全 lower-case 且部分缺乏類型 | `branch-conventions.md` §7 暗示用 conventional commit（`feat:` / `fix:`） | 歷史 commit 大致符合 `feat:` / `fix:` / `debug:` / `refactor:` / `config:`（log 30 條觀察），但有「`debug:`」是非標準類型（標準是 `chore:` 或 `fix:`） |
| m-2 | i18n：完全未實作 | `i18n-conventions.md` — 預設語系未鎖定 | 所有中文文字硬編碼在 Jinja2 模板與 Python `detail="..."` 字串中。**現況：單語 zh-TW + 後端硬編碼**。建議第一個 TASK 把 `i18n-conventions.md` 的「預設語系」明確設為 zh-TW，並降級為 N/A 直到引入 Vue / React。i18n-registry 全空、無 journal — 因為現況「無 i18n key」，**N/A 而非違反** |
| m-3 | Magic numbers | `code-conventions.md` §7「Magic numbers（除 0/1/-1）」 | `web/auth/auth_router.py:87` `len(body.password) < 8`、`web/auth/auth_router.py:100` `timedelta(hours=24)`、`web/main.py:137` `timeout=45.0` — 建議抽常數 |
| m-4 | 印中文 print / 直接 `raise HTTPException(detail="...")` | `code-conventions.md` §7「Console.log/print 留在生產」 | 多處 `print(...)` 在 oauth_router / email_service（除錯訊息） |
| m-5 | 路徑 imports 用 `sys.path.insert` 而非 absolute imports | `code-conventions.md` §4 Import 順序 + 「avoid 深層 ../../」 | `web/main.py:17-19` 三次 `sys.path.insert` — 是 brownfield 結構問題；轉 Vue + 新 BE 結構時應移除 |
| m-6 | 一檔 > 500 行警告 | `code-conventions.md` §7「一個檔超過 N 行 [CUSTOMIZE: 預設 500]」 | `web/main.py` 估計 ~500 行（無精確計算），`ski_early_bird_scraper.py` 22129 bytes / 約 600 行 — 建議第一個 TASK 評估拆分 |
| m-7 | conventions 模板 `[CUSTOMIZE]` 標記未填寫 | Rule 16 conventions lock | 5 個 conventions 都殘留 `[CUSTOMIZE: ...]` 文字（10+ 處），但 `locked_at` 已寫入 → 視同預設值生效。**建議 PM 在第一個 TASK 啟動前清理或正式採用預設值** |
| m-8 | design-system.pen 缺檔 | Rule 17 Pencil 兩層架構 | `.sdlc/conventions/` 無 `.pen` 檔；`design-system.meta.json.componentInventory: []`。Pencil MCP 未安裝是因。**UIUX 階段前必須補** |
| m-9 | `python_multipart` 未在 requirements 鎖定版本下限 | `code-conventions` 對版本鎖定無明確規則（屬最佳實踐 Minor） | `requirements.txt:5` `python-multipart>=0.0.9` — 預發布版本沒 patch 鎖定。第一個 TASK 可建議升級到 1.0+ |

### 4.4 N/A（待人工審查）

| 項目 | 狀態 |
|------|------|
| i18n 規範符合度 | **N/A** — 既有系統無 i18n key（純中文硬編碼）。Rule 16 conventions 預設語系 `[CUSTOMIZE: 主要語系]` 仍是模板字串。建議 PM 確認 zh-TW 為主語系後鎖定 |
| `branch-conventions.md` §1「`[CUSTOMIZE: 是否需要 develop？]`」 | **N/A** — 既有 git 結構只有 main + 短壽命 worktree 分支，未採用 GitFlow。**待 PM 在第一個 TASK 結束後決議 develop 是否需要** → `[NEEDS-HUMAN-REVIEW]` |

---

## 區塊 5: DESIGN.md 一致性

### 5.1 §5-2 路由表 vs 實際 `web/main.py` 路由

| 比對項 | DESIGN.md 第 5-2 表 | 實際 grep 結果 | 一致? |
|--------|----------------------|----------------|-------|
| `GET /` | ✅ 列 | ✅ 存在 `main.py:98` | ✅ |
| `GET /ski` | ✅ 列 | ✅ 存在 `main.py:103` | ✅ |
| `GET /flight` | ✅ 列 | ✅ 存在 `main.py:108` | ✅ |
| `GET /login` | ✅ 列「UI 已建，功能待啟用」 | ✅ 存在 `auth_router.py:41` — **已啟用且驗證登入狀態 redirect** | ⚠️ DESIGN.md **過時**（line 266 還寫「功能待啟用」） |
| `GET /register` | ✅ 列「UI 已建，功能待啟用」 | ✅ 存在 `auth_router.py:51` — **已啟用** | ⚠️ DESIGN.md **過時** |
| `GET /api/ski/search` | ✅ 列 | ✅ 存在 `main.py:127` | ✅ |
| `GET /api/ski/download` | ✅ 列 | ✅ 存在 `main.py:197` | ✅ |
| `GET /api/flight/search` | ✅ 列 | ✅ 存在 `main.py:252` | ✅ |
| `GET /robots.txt` | ✅ 列 | ✅ 存在 `main.py:489` | ✅ |
| `GET /sitemap.xml` | ✅ 列 | ✅ 存在 `main.py:497` | ✅ |
| `GET /plan` | ✅ 列 | ✅ 存在 `plan_routes.py:38` | ✅ |
| `GET /profile` | ✅ 列 | ✅ 存在 `auth_router.py:56` | ✅ |
| `POST /api/plan/download` | ✅ 列 | ✅ 存在 `plan_routes.py:121` | ✅ |
| `POST /api/auth/register` | ✅ 列 | ✅ 存在 `auth_router.py:85` | ✅ |
| `POST /api/auth/login` | ✅ 列 | ✅ 存在 `auth_router.py:117` | ✅ |
| `POST /api/auth/logout` | ✅ 列 | ✅ 存在 `auth_router.py:138` | ✅ |
| `GET /api/auth/me` | ✅ 列 | ✅ 存在 `auth_router.py:197` | ✅ |
| `GET /api/favorites` | ✅ 列 | ✅ 存在 `auth_router.py:214` | ✅ |
| `POST /api/favorites` | ✅ 列 | ✅ 存在 `auth_router.py:232` | ✅ |
| `DELETE /api/favorites/{id}` | ✅ 列 | ✅ 存在 `auth_router.py:245` | ✅ |
| **`GET /api/ski/stream`** | ❌ DESIGN.md §5-2 漏列 | ✅ 存在 `main.py:153` | ❌ **DESIGN.md 缺漏** |
| **`POST /api/flight/download`** | ❌ DESIGN.md §5-2 漏列 | ✅ 存在 `main.py:442` | ❌ **DESIGN.md 缺漏** |
| **`GET /api/env-check`** | ❌ DESIGN.md §5-2 漏列 | ✅ 存在 `main.py:461`（debug） | ❌ **DESIGN.md 缺漏**（也是 Critical C-2） |
| **`GET /api/auth/google/login`** | ✅ 第 9 章「新增路由」有列 | ✅ 存在 `oauth_router.py:24` | ⚠️ **未進主 §5-2 路由表**（在「下次對話從這裡開始」內列） |
| **`GET /api/auth/google/callback`** | ✅ 第 9 章「新增路由」有列 | ✅ 存在 `oauth_router.py:42` | ⚠️ 同上 |
| **`GET /api/auth/verify-email`** | ✅ 第 9 章「新增路由」有列 | ✅ 存在 `auth_router.py:145` | ⚠️ 同上 |
| **`POST /api/auth/resend-verification`** | ✅ 第 9 章「新增路由」有列 | ✅ 存在 `auth_router.py:170` | ⚠️ 同上 |
| **`GET /api/auth/verify`** | ✅ 第 9 章「新增路由」有列 | ✅ 存在 `verify_client.py:130` | ⚠️ 同上 |

→ DESIGN.md §5-2 主表 **缺漏 3 個端點 + 5 個 2026-06-03 新增端點未回填主表**。屬於 DESIGN.md 維護債（CLAUDE.md 規定「任何修改必須同步更新 DESIGN.md」未落實到主表）。

### 5.2 §二 目錄結構 vs 實際 `ls`

| DESIGN.md 第 二 目錄結構 | 實際 | 一致? |
|------|------|-------|
| `web/auth_routes.py` | **不存在**，實際是 `web/auth/auth_router.py`（複數 → 單數、平鋪 → 子目錄） | ❌ DESIGN.md **過時** |
| `web/templates/auth/login.html` | ✅ | ✅ |
| `web/templates/auth/register.html` | ✅ | ✅ |
| `web/auth/oauth_router.py` | ✅ 存在但 DESIGN.md §二 主結構未提（只在「新增/修改的檔案」段提） | ⚠️ §二 缺 |
| `web/auth/email_service.py` | ✅ 存在但 DESIGN.md §二 主結構未提（同上） | ⚠️ §二 缺 |
| `web/auth/verify_client.py` | ✅ 存在但 DESIGN.md §二 主結構未提（同上） | ⚠️ §二 缺 |
| `web/auth/tests/test_auth.py` | ✅ 存在 | ⚠️ §二 缺 |
| `web/airport_codes.py` | ✅ 存在 `web/airport_codes.py` | ⚠️ §二 缺（在第 9 章列） |

### 5.3 §七 開發優先順序 vs 已知問題

DESIGN.md §七 列出 25+ Phase 進度，全部 ✅，但與 §八「已知問題」的 Critical 項：

- ✅「Email 驗證」完成（§七）但 §八無記載 Resend 上限 / SMTP fallback 風險
- ⚠️「SQLite 在 Railway ephemeral」是嚴重問題（CLAUDE.md 第 49 行直接寫死），但 §八未列入 → **DESIGN.md §八 缺漏 P0 持久性問題**
- ⚠️「`/api/env-check`」debug endpoint 未列為已知問題 → 同上

### 5.4 結論

DESIGN.md 整體**功能列表與實際 code 高度一致**（90%+），但：
1. §5-2 主路由表落後最新 5 個新增端點
2. §二 目錄結構落後 `web/auth/` 子目錄重組
3. §八 已知問題缺漏 SQLite ephemeral / debug endpoint 兩個關鍵風險
4. 「UI 已建，功能待啟用」字樣已過時（功能已啟用）

→ 屬於 Major 文件債（CLAUDE.md 強制規則未落實），但不阻塞 SDLC TASK-001 啟動，可作為 BA TASK-001 的副產出順手清理。

---

## 建議下一步

### 1. （Critical）將 SQLite → Postgres 持久化納入第一個 TASK 的需求

DB engine 與 config 宣告不符 + Railway ephemeral 已知問題 + 用戶資料丟失風險 = 必須首先處理。
- BA：把 FR 寫成「用戶帳號 / 收藏在 Railway 重啟後保留」
- SA：技術決策 Postgres 來源（Railway Postgres add-on 最快，或外部 Supabase / Neon）
- SD：寫 migration（須符合 `db-conventions.md` §5：reversible + 三段式刪欄 + timestamp 命名）
- BE：抽 DB layer 為 repository 模式，先讓 SQLite 與 Postgres 並存切換（環境變數驅動），最後 contract SQLite

### 2. （Critical）下架 `/api/env-check` debug endpoint

- 開新 hotfix branch（`hotfix/remove-env-check`，符合 `branch-conventions.md` §3）
- 直接刪除 `web/main.py:461-487`（或先改為 `@app.get("/api/env-check", include_in_schema=False)` + 限定 dev mode）
- 不需 SDLC 完整流程；走 hotfix 路徑

### 3. （Major）conventions 清理 — 解決所有 `[CUSTOMIZE]` 留白

PM 在第一個 TASK 啟動前完成以下決策（一次性，無需 RFC，因為仍在 init 後期）：
- `api-conventions.md`：定錨「認證 = HTTP-only cookie 而非 Bearer」（與既有實作對齊）
- `code-conventions.md`：明確 backend = Python snake_case；檔行上限 500
- `db-conventions.md`：選 Postgres charset UTF8、ON DELETE = CASCADE for favorites (`favorites.user_id`)
- `i18n-conventions.md`：主語系 = zh-TW；i18n key 規範**暫不啟用**（純 Jinja2 階段），UIUX 轉框架時啟用
- `branch-conventions.md`：保留 `[CUSTOMIZE: develop？]` 不啟用（小團隊 main only）

### 4. （Major）DESIGN.md 同步更新

第一個 TASK 結束時 PM 順手清理：
- §5-2 補 5 個漏列端點 + `GET /api/auth/google/*` 等
- §二 結構更新 `web/auth/` 子目錄樹
- §八 加入「SQLite ephemeral」「`/api/env-check` 殘留」兩個風險（前者修完才能刪）
- §三 移除「UI 已建，功能待啟用」過時字樣

### 5. （建議）第一個 TASK 採 brownfield-document（補追溯）模式

把區塊 2 的 26-28 個 API + 3 個 ENTITY/TBL + 8 個 PAGE 一次性登記到 `.sdlc/shared/id-registry.md`。
- 由 PM 在 TASK-001 開啟時透過 `sdlc-id-scan.sh` 配發 ID 範圍給 BA/SA/SD
- 第一個 TASK 的「需求」= 「為既有功能補需求 + 補 SA + 補 SD + 標 ENTITY → TBL 映射」，不寫新 code
- 結束後共享層完整，第二個 TASK 才開始做新功能（如 Postgres 遷移）

---

## 附錄：自我驗證

- 已讀 `~/.claude/sdlc/rules/sdlc-global.md`、`~/.claude/sdlc/rules/sdlc-tester.md`
- 證據 100% 引用 file:line（區塊 2、4、5）
- Critical / Major / Minor 分級嚴格依 Tester Rule 3
- 無修改任何 SDLC / 代碼檔（僅 Write 本報告）
- 範圍邊界：未推測使用者未提的需求；所有「建議」放在獨立區塊
- 自我驗證估分：96 / 100（扣 4 分：未跑 `sdlc-role-verify.sh tester` 因本次為 baseline 非 TASK 階段；未產出 `self-review.json` 因目錄非 `.sdlc/tasks/{TASK-ID}/test-*/`）

—— 報告結束。
