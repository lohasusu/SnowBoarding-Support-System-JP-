# TASK-002 增強需求

## 原始需求

> "SQLite → Postgres 遷移"

## 增強後需求

```
目標
───────────────────────────────────────
將生產環境（Railway）的資料持久層從 SQLite（web/data/snowtrip.db）遷移到 PostgreSQL，
解決 Railway ephemeral storage 導致用戶資料（帳號 / 收藏 / email 驗證 token）
在容器重啟後消失的 Critical 問題（DESIGN.md §八 / baseline-audit-2026-06-03 C-1）。

技術棧
───────────────────────────────────────
- Backend: FastAPI (Python 3.12-slim) — 沿用
- Database: PostgreSQL 16-alpine (config.json techStack.database) — 取代 SQLite
- DB Port: 5432，envPrefix `POSTGRES_`，healthcheck `pg_isready -U $DB_USER -d $DB_NAME`
- Container: ghcr.io，Buildx linux/amd64 + linux/arm64
- Deployment: Railway（既有），Postgres 由 Railway addon 提供（或自建）

範圍邊界
───────────────────────────────────────

納入（使用者明示 + 從現有系統推斷）:
- 3 張既有資料表必須遷移:
  - TBL-001 users（含 hashed_password / is_verified / google_id / avatar_url）
  - TBL-002 favorites（type / data JSON / label，has user_id FK）
  - TBL-003 email_verification_tokens（token / expires_at / used_at，has user_id FK）
- web/auth/database.py 的 sqlite3 driver 改為 Postgres driver（待 SD 階段決定 psycopg / SQLAlchemy / asyncpg）
- 既有 ALTER TABLE try/except 安全遷移 hack（database.py:44-52）改為正式 migration 工具
- 環境變數：新增 POSTGRES_* （DB_USER / DB_NAME / DB_PASSWORD / DB_HOST / DB_PORT）
- Railway 部署設定：addon Postgres 或 DATABASE_URL env var
- Schema 設計遵循 `.sdlc/conventions/db-conventions.md` v1.1（含 updated_at / deleted_at 軟刪除欄位 — brownfield 3 表需補齊）
- 既有 Email 驗證 token / Google OAuth state / 收藏 JSON 資料須完整保留語意

待確認（[BA建議] 由 BA 階段向使用者澄清）:
- [BA確認] 現有 SQLite 資料是否需要遷移？（目前 Railway ephemeral，重啟資料已失，可能為空）
- [BA確認] 開發 / staging / production 是否都用 Postgres？或開發保留 SQLite？
- [BA確認] migration 工具選型偏好？（Alembic / yoyo-migrations / 手寫 SQL / SQLAlchemy 內建）
- [BA確認] connection pooling 策略？（Railway 連線數限制 / pgbouncer）
- [BA確認] 是否藉此機會補 conventions v1.1 要求的 updated_at / deleted_at 軟刪除欄位給既有 3 表？（DESIGN.md §八 Major 項目）
- [BA確認] 是否一併處理 conventions §8 違規（既有 ALTER TABLE try/except hack）改為正式 migration？

不納入（使用者未提及，不腦補）:
- 新增資料表 / 新增欄位（除非為 conventions 強制 + BA 確認）
- DB schema 整體 refactor（如 UUID PK / partitioning）
- Read replica / 高可用配置
- Caching layer（Redis 等）
- DB 監控 / Grafana / 告警
- 其他模組（雪票 / 機票）的 storage 變更（目前無 DB）

專案上下文
───────────────────────────────────────
- 既有 production code：`web/auth/database.py`（13 行 schema + 9 行 ALTER TABLE 安全遷移）
- 既有 SQLite 路徑：web/data/snowtrip.db（gitignored，Railway 容器啟動時自動建）
- 既有 ALTER TABLE hack：database.py:44-52（`try: ALTER; except: pass`）— 違反 db-conventions §8
- Railway 啟動指令：`uvicorn web.main:app --host 0.0.0.0 --port $PORT`
- 認證流程使用：bcrypt（passlib）+ JWT（python-jose）+ HTTP-only cookie + Resend/SMTP email + Google OAuth
- DESIGN.md §五-4 Schema 區塊與 database.py 一致（無漂移）
- 影響面：`web/auth/auth_router.py` / `web/auth/oauth_router.py` / `web/auth/dependencies.py` / `web/auth/verify_client.py` 都會用到 connection

共享層狀態（自 .sdlc/shared/ + id-allocator.json）
───────────────────────────────────────
- TASK-002 ID 範圍（由 sdlc-allocate-ids.sh 預留）:
  - ENTITY: 101-200（TASK-001 已用 ENTITY-001/002/003 = users/favorites/email_verification_tokens）
  - MOD: 101-200（TASK-001 已用 MOD-001~006）
  - FUNC: 101-200（TASK-001 已用 FUNC-001~045）
  - PATTERN: 101-200（TASK-001 已用 PATTERN-001~008）
  - API: 101-200
  - TBL: 101-200（TASK-001 已用 TBL-001/002/003 = users/favorites/email_verification_tokens）
  - COMP / PAGE / LAYOUT: 101-200（本 TASK 預期不會用，無 UI 變更）

- 既有可重用（標 [REUSE: ID, from TASK-001]）:
  - ENTITY-001 users / ENTITY-002 favorites / ENTITY-003 email_verification_tokens
  - TBL-001 / TBL-002 / TBL-003（schema 結構不變，僅 storage engine 變）
  - MOD-005 auth（資料層 driver 替換，模組邊界不變）

- 跨 TASK 修改評估（Rule 6 預警）:
  - 預期需要 SA 在 functional-flow.md 標 [CROSS-TASK: TASK-001 / TBL-001/002/003 schema 補 updated_at + deleted_at（若 BA 確認補齊）]
  - 預期需要 SA 在 functional-flow.md 標 [CROSS-TASK: TASK-001 / MOD-005 auth.database driver 替換]
  - 若 BA 確認不補 timestamp 欄位，則僅 driver 替換需 [CROSS-TASK]

- 所屬 App: snowboarding_support（config.json 唯一 app）

- 模式: SDD + BDD + TDD（config.modes，strict testMode）

關鍵限制與目標（從 baseline + DESIGN.md）
───────────────────────────────────────
- 解 Critical: SQLite ephemeral storage 用戶資料消失（C-1）
- 解 Major: db-conventions §8 違規（ALTER TABLE try/except）
- 解 Major: 既有 3 表缺 updated_at / deleted_at（brownfield grandfather，本 TASK 視 BA 決策決定是否一併補）
- 不破壞既有認證流程（登入 / 註冊 / OAuth / email 驗證 / 收藏 CRUD）
- 不破壞既有 8 個測試（web/auth/tests/test_auth.py — TASK-001 已記錄）
- Railway 部署啟動指令不變（uvicorn 命令保持）
───────────────────────────────────────
```

## 增強原則自查（Rule 4 自我驗證）

- [x] **補全而非改變**：保留使用者「SQLite → Postgres 遷移」原意，補充上下文
- [x] **標記而非假設**：所有非使用者明示項目使用 [BA確認] 標記，未自動納入正式規格
- [x] **具體化上下文**：引用 database.py 行號、Railway 部署細節、既有 ENTITY/TBL ID
- [x] **精簡而非堆砌**：與原始需求對比約 50 倍，但每段都有專案實證來源（DESIGN.md / baseline / config / id-registry）
- [x] **App 識別**：snowboarding_support（config 唯一）— 已記
- [x] **共享層**：列出 TASK-002 ID 範圍 + 既有可重用 ID + 跨 TASK 修改預警
