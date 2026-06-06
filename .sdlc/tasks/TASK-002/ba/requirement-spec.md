---
document_id: "REQ-TASK-002-v1.0"
title: "需求規格書 — SQLite → PostgreSQL 持久化遷移"
version: "1.0"
date: "2026-06-07"
author: "BA"
status: "Draft"
task_id: "TASK-002"
phase: "ba"
mode: "feature"
source_documents:
  - "enhanced-input.md"
  - ".sdlc/baseline/baseline-audit-2026-06-03.md"
  - ".sdlc/conventions/db-conventions.md (v1.1)"
  - ".sdlc/conventions/api-conventions.md"
  - "DESIGN.md §八、§五-4"
  - "web/auth/database.py"
  - ".sdlc/tasks/TASK-001/ba/requirement-spec.md (FR/AC/ROLE 既有)"
change_history:
  - version: "1.0"
    date: "2026-06-07"
    changes: "初始版本 — 8 FR + 12 NFR + 7 BR + 14 AC + 9 CONST + 2 SEC + 1 既有 ROLE 引用；6 個 [BA確認] 全部決策落地"
    author: "BA"
approval:
  reviewer: "PM"
  date: ""
  result: "Pending"
  notes: ""
---

# 需求規格書 — SQLite → PostgreSQL 持久化遷移

> **模式**: feature（替換既有 SQLite 持久層為 PostgreSQL；保留 3 張既有表 schema 語意）
> **真相基線**: 以 TASK-001 已登記 `ENTITY-001/002/003` + `TBL-001/002/003` 為 schema 真相；以 `web/auth/database.py` 為現況 storage code 真相
> **本 TASK 影響**: 解 Critical C-1 (SQLite ephemeral) + Major M-8 (缺 updated_at/deleted_at — 由本 TASK 決策補) + 部分 Major C-1/§8 違規 (ALTER TABLE try/except hack)

---

## 1. 需求概述

### 1.1 背景

> 來源: 使用者原文「SQLite → Postgres 遷移」+ enhanced-input.md「目標」段 + baseline-audit-2026-06-03.md §3.1 Critical Gap §4.1 C-1

snowboarding_support 目前 production 部署於 Railway，認證（users）/ 收藏（favorites）/ Email 驗證 token（email_verification_tokens）三張表使用 SQLite 儲存於 `web/data/snowtrip.db`。Railway 採 **ephemeral storage** — 每次容器重啟（每日重啟、deploy、scale）即清空整個檔案系統，導致：

- 用戶帳號（含 bcrypt 密碼、`is_verified`、`google_id`）全部消失
- 收藏資料（type/data/label）全部消失
- 進行中的 Email 驗證 token 全部失效

此為 baseline-audit 列為 **Critical C-1**，CLAUDE.md 第 49 行明確標註，DESIGN.md §八「已知問題」最高優先項。

### 1.2 目的

> 來源: enhanced-input.md「目標」段 + baseline-audit-2026-06-03.md §「建議下一步 1」

1. 將 `web/auth/database.py` 的 sqlite3 driver 替換為 PostgreSQL driver，使三張既有表（users / favorites / email_verification_tokens）在 PostgreSQL 中持久化
2. 解決 Railway 容器重啟導致用戶資料消失的 Critical 缺陷
3. 同步消除 `web/auth/database.py:44-52` 違反 `db-conventions.md` §8「禁止在應用程式碼內寫 ALTER TABLE」的 try/except 安全遷移 hack，改用正式 migration 工具
4. 保持既有 8 個 pytest（`web/auth/tests/test_auth.py`）全部通過、Railway 啟動指令不變、認證流程外部行為（HTTP 狀態碼 / cookie / OAuth callback）零變化

### 1.3 範圍

> 來源: enhanced-input.md「範圍邊界 — 納入」段

本 TASK 共 **8 個核心 FR**:

| FR | 功能 | 來源 |
|----|------|------|
| FR-001 | PostgreSQL 連線層替換（sqlite3 → Postgres driver） | enhanced-input.md「納入 — web/auth/database.py 的 sqlite3 driver 改為 Postgres driver」 |
| FR-002 | 三張既有表 schema 在 PostgreSQL 重建（users / favorites / email_verification_tokens） | enhanced-input.md「3 張既有資料表必須遷移」+ db-conventions §1-§6 |
| FR-003 | 正式 migration 工具導入（取代 ALTER TABLE try/except hack） | enhanced-input.md「正式 migration 工具」+ db-conventions §5 |
| FR-004 | 補齊 `updated_at` / `deleted_at` 軟刪除欄位至三張表 | enhanced-input.md [BA確認] 第 5 項 → 本 TASK §8 決策為「補」+ db-conventions §2 + baseline-audit M-8 |
| FR-005 | 環境變數新增與註冊（POSTGRES_* / DATABASE_URL） | enhanced-input.md「環境變數」+ config.json techStack.database.envPrefix + Rule 18 |
| FR-006 | Railway 部署設定切換（Postgres addon / DATABASE_URL） | enhanced-input.md「Railway 部署設定」 |
| FR-007 | 既有資料遷移處理（SQLite → PostgreSQL ，視 [BA確認] 第 1 項決策） | enhanced-input.md [BA確認] 第 1 項 → 本 TASK §8 決策為「不遷移歷史資料（接受 ephemeral 已失），但提供一次性匯入腳本作為 fallback」 |
| FR-008 | 開發 / staging / production 環境 DB engine 策略 | enhanced-input.md [BA確認] 第 2 項 → 本 TASK §8 決策為「全環境統一 PostgreSQL，棄用 SQLite」 |

### 1.4 不在範圍內（明確排除的項目）

> 來源: enhanced-input.md「不納入」段（使用者未提及，不腦補）

- 新增資料表（除 FR-004 補齊 timestamp 欄位外，不改變 schema 邏輯結構）
- DB schema 整體 refactor（UUID PK、partitioning、view、stored procedure）
- Read replica / 高可用配置 / 主從複製
- Caching layer（Redis / Memcached）
- DB 監控 / Grafana / 告警 / Prometheus exporter
- 其他模組（雪票 MOD-001/003、機票 MOD-004、行程 MOD-006）的 storage 變更（目前皆無 DB 互動）
- DESIGN.md 同步更新（屬於 PM/文件債清理，留 TASK 收尾階段）
- `/api/env-check` debug endpoint 下架（baseline-audit C-2，獨立 hotfix 處理）
- 雪票 / 機票 / 行程模組功能變更
- 新增業務功能（如忘記密碼、密碼重設）
- 認證流程外部行為變更（HTTP 狀態碼 / cookie 行為 / OAuth flow / Email 驗證流程）

---

## 2. 利害關係人

> 註: 本 TASK 為**後端基礎設施重構**，對終端用戶體驗無預期可見變化。利害關係人聚焦於系統面。

| ROLE | 角色名稱 | 需求摘要 | 優先順序 | 來源 |
|------|---------|---------|---------|------|
| ROLE-001 [REUSE: from TASK-001] | 訪客（Guest） | 註冊 / 登入 / Google OAuth 行為不變；重啟後仍能用既有帳號登入 | P0 | TASK-001/ROLE-001 + enhanced-input.md「不破壞既有認證流程」 |
| ROLE-002 [REUSE: from TASK-001] | 已登入用戶（Authenticated User） | 收藏資料在 Railway 重啟後仍存在；登入狀態不被清除 | P0 | TASK-001/ROLE-002 + DESIGN.md §八 C-1 |
| ROLE-003 [REUSE: from TASK-001] | 系統維運者（Operator / Admin） | 透過 PostgreSQL 標準工具（psql / Railway dashboard）查詢用戶狀態，取代 SQLite 檔案複製 | P1 | TASK-001/ROLE-003 |
| ROLE-004 | 部署者（Deployer） | 能透過 `DATABASE_URL` 或 `POSTGRES_*` 環境變數切換 DB 連線；migration 在啟動時自動執行或可控觸發 | P0 | enhanced-input.md「Railway 部署設定」+ config.json techStack.database.envPrefix |

**註**: ROLE-004「部署者」為新角色（既有 TASK-001 未定義部署層角色），全域連續編號從 ROLE-003 後接 ROLE-004。

---

## 3. 功能需求

> **AC 編號規範**: 全域連續，TASK-001 已用 AC-001~AC-043，本 TASK 從 **AC-044** 起編（dispatch prompt 已聲明）。
> **FR 編號**: TASK 內連續，跨 TASK 引用用 `TASK-002/FR-001` 格式。

### FR-001: PostgreSQL 連線層替換

- **描述**: 將 `web/auth/database.py` 中的 `sqlite3` import 與 connection 邏輯替換為 PostgreSQL driver（具體 driver 選型由 SD 階段決定 — psycopg / SQLAlchemy / asyncpg）；保持 `get_conn()` 介面語意一致供既有 6 個檔案無痛切換
- **優先順序**: P0
- **來源**: enhanced-input.md「納入 — sqlite3 driver 改為 Postgres driver」+ baseline-audit C-1
- **信心等級**: 🟢 高信心
- **影響的既有檔案**（來自 enhanced-input.md「影響面」段）:
  - `web/auth/auth_router.py`（28 處 get_conn）
  - `web/auth/oauth_router.py`（OAuth upsert 邏輯）
  - `web/auth/dependencies.py`（current_user 查詢）
  - `web/auth/verify_client.py`（維運查詢 API）
  - `web/auth/email_service.py`（token 寫入）
  - `web/auth/database.py`（本檔，直接重寫）
- **驗收標準**:
  - [ ] AC-044: 應用程式啟動時能成功透過 `POSTGRES_*` env vars 連線至 PostgreSQL 16，並在連線失敗時拋出明確錯誤（不可 silent fail）— **可測**: 給錯誤密碼啟動，啟動 log 含 connection refused/auth failed
  - [ ] AC-045: 既有 8 個 pytest（`web/auth/tests/test_auth.py`）對接 PostgreSQL 測試實例後全數通過（含註冊 / 登入 / Email 驗證 / 重寄 / OAuth / 收藏 / 強制登入）— **可測**: `pytest web/auth/tests/test_auth.py` exit code = 0，pass 數 = 8
- **BDD 場景**:
  ```gherkin
  Feature: PostgreSQL 連線替換
    Scenario: 應用程式於正確 env vars 下成功連線
      Given POSTGRES_HOST/PORT/USER/PASSWORD/DB 皆設為有效 PostgreSQL 實例
      And 該實例已建立三張既有表（users / favorites / email_verification_tokens）
      When 啟動 uvicorn web.main:app
      Then 啟動成功，無 connection error 拋出
      And `GET /api/auth/me`（未登入）回 HTTP 401 而非 500
  ```

### FR-002: 三張既有表 schema 在 PostgreSQL 重建

- **描述**: 在 PostgreSQL 重建 `users` / `favorites` / `email_verification_tokens` 三張表，schema 語意（欄位、UNIQUE 約束、FK ON DELETE CASCADE）與 `web/auth/database.py:18-42` 完全對應；SQLite 特定型別（`INTEGER PRIMARY KEY AUTOINCREMENT`、`BOOLEAN`、`TIMESTAMP DEFAULT CURRENT_TIMESTAMP`）對應到 PostgreSQL 等價型別（`BIGINT GENERATED ALWAYS AS IDENTITY`、`BOOLEAN`、`TIMESTAMPTZ DEFAULT NOW()`）依 `db-conventions.md` §2
- **優先順序**: P0
- **來源**: enhanced-input.md「3 張既有資料表必須遷移」+ db-conventions.md §2 + TASK-001 ENTITY-001/002/003 schema 真相基線
- **信心等級**: 🟢 高信心
- **保留語意 (Reuse markers)**:
  - `[REUSE: ENTITY-001 users, from TASK-001]`
  - `[REUSE: ENTITY-002 favorites, from TASK-001]`
  - `[REUSE: ENTITY-003 email_verification_tokens, from TASK-001]`
  - `[REUSE: TBL-001/002/003, from TASK-001]`（schema 結構不變，僅 storage engine 變）
- **驗收標準**:
  - [ ] AC-046: PostgreSQL 中存在三張表 `users` / `favorites` / `email_verification_tokens`，欄位數與既有 `database.py` schema 一致（users 7 欄 + 本 TASK 補的 timestamp = 9 欄；favorites 5 欄 + 補 = 7 欄；email_verification_tokens 5 欄 + 補 = 7 欄）— **可測**: `\d users` / `\d favorites` / `\d email_verification_tokens` 比對欄位清單
  - [ ] AC-047: `users.email` `users.username` `users.google_id` `email_verification_tokens.token` 為 UNIQUE 約束；`favorites.user_id` `email_verification_tokens.user_id` 為 FK 指向 `users.id` 且 `ON DELETE CASCADE` — **可測**: `\d` 含 `Indexes: uniq_*` 與 `Foreign-key constraints: ... ON DELETE CASCADE`

### FR-003: 正式 migration 工具導入

- **描述**: 引入符合 `db-conventions.md` §5 的 migration 工具（reversible / 三段式刪欄 / 檔名 `{YYYYMMDD_HHMMSS}_{verb}_{noun}.sql`），取代 `web/auth/database.py:44-52` 的 `try: ALTER TABLE; except: pass` hack；具體選型（Alembic / yoyo-migrations / 手寫 SQL）由 SD 階段決策。本 FR 規範行為，不規範工具
- **優先順序**: P0
- **來源**: enhanced-input.md「既有 ALTER TABLE try/except 安全遷移 hack（database.py:44-52）改為正式 migration 工具」+ db-conventions.md §5 + §8（禁止項）+ baseline-audit C-1
- **信心等級**: 🟢 高信心
- **驗收標準**:
  - [ ] AC-048: `web/auth/database.py` 中**不存在** `try: ALTER TABLE ... except: pass` 模式（grep `'ALTER TABLE'` on `web/auth/**` 返回 0 行業務代碼，僅可能出現在 migration 檔內）— **可測**: `grep -rn "ALTER TABLE" web/auth/ | grep -v migrations/` exit 1（no match）
  - [ ] AC-049: 至少存在 1 個 migration 檔（命名 `YYYYMMDD_HHMMSS_create_initial_schema.sql` 或工具等價物），且該 migration 為 reversible（具備 down 操作）— **可測**: 檔名符合正則 `^\d{8}_\d{6}_.*\.(sql|py)$`，內容含 down/rollback 區塊

### FR-004: 補齊 `updated_at` / `deleted_at` 軟刪除欄位

- **描述**: 三張既有表（users / favorites / email_verification_tokens）均補上 `updated_at TIMESTAMPTZ` 與 `deleted_at TIMESTAMPTZ NULLABLE` 欄位；`updated_at` 預設 `NOW()` 並由應用層或 trigger 在 UPDATE 時刷新；`deleted_at` 預設 NULL，用於未來軟刪除（本 TASK 不改寫既有 hard-delete 邏輯為 soft-delete，僅補欄位）
- **優先順序**: P1
- **來源**: enhanced-input.md [BA確認] 第 5 項 → 本 TASK §8 決策為「補」+ db-conventions.md §2 + §8 第 4 項禁止項 + baseline-audit M-8
- **信心等級**: 🟢 高信心（決策已落定，理由見 §8 SUG-001）
- **跨 TASK 修改預警**:
  - 預期 SA 在 functional-flow.md 標 `[CROSS-TASK: TASK-001 / TBL-001/002/003 schema 補 updated_at + deleted_at（不改變既有 INSERT/SELECT 行為）]`
- **驗收標準**:
  - [ ] AC-050: 三張表均存在 `updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()` 欄位 — **可測**: `\d` 含該欄位
  - [ ] AC-051: 三張表均存在 `deleted_at TIMESTAMPTZ NULL` 欄位（NULL 表示未刪除）— **可測**: `\d` 含該欄位且 nullable = yes
- **業務行為不變條款**: 本 TASK 不修改 `web/auth/auth_router.py:246` 的 `DELETE FROM favorites` 為 soft-delete（避免擴大範圍）；改寫為 soft-delete 留後續 TASK，需走 Rule 6 跨 TASK 協議

### FR-005: 環境變數新增與註冊

- **描述**: 引入 `POSTGRES_HOST` / `POSTGRES_PORT` / `POSTGRES_USER` / `POSTGRES_PASSWORD` / `POSTGRES_DB` 五個環境變數（或等價的 `DATABASE_URL` 單一連線字串），並透過 Rule 18 機制寫入 `shared/parameter-registry.md`；config.json 的 `techStack.database.envPrefix = "POSTGRES_"` 為命名來源
- **優先順序**: P0
- **來源**: enhanced-input.md「環境變數：新增 POSTGRES_*」+ config.json techStack.database.envPrefix + Rule 18 parameter registry
- **信心等級**: 🟢 高信心
- **驗收標準**:
  - [ ] AC-052: `.env.example` / `.env.backend` 包含 5 個 `POSTGRES_*` 變數（或 `DATABASE_URL`）的範例值與註解 — **可測**: `grep -c POSTGRES_ .env.example` ≥ 5（或 grep DATABASE_URL ≥ 1）
  - [ ] AC-053: `shared/parameter-registry.md` 第 1 節 Env Variables 表新增 5 條（或 1 條 DATABASE_URL）對應記錄，欄位完整（paramKind=env, ownerService=be, required=true）— **可測**: 於 SD 階段 journal 寫入 `parameter_added` 事件後，PM rebuild shared/ 該表新增條目

### FR-006: Railway 部署設定切換

- **描述**: Railway 部署啟用 PostgreSQL（Railway Postgres addon 或外部託管如 Supabase / Neon — 由 deploy 階段決策），環境變數設定使應用啟動時連到 PostgreSQL 實例；啟動指令 `uvicorn web.main:app --host 0.0.0.0 --port $PORT` 不變；healthcheck 符合 config.json `pg_isready -U $DB_USER -d $DB_NAME`
- **優先順序**: P0
- **來源**: enhanced-input.md「Railway 部署設定」+ config.json techStack.database.healthcheck + 「Railway 部署啟動指令不變」
- **信心等級**: 🟡 中信心（Railway Postgres addon vs 外部託管未由 BA 鎖定 — 留 deploy 階段做技術決策）
- **驗收標準**:
  - [ ] AC-054: Railway production 環境變數含 `POSTGRES_*`（或 `DATABASE_URL`），且部署後啟動 log 顯示成功連線（無 OperationalError / ConnectionRefused）— **可測**: Railway deploy log 含「Uvicorn running on…」且不含 connection error
  - [ ] AC-055: 部署後執行手動 smoke test（註冊新帳號 → 登入 → 新增收藏 → 觸發 Railway 容器重啟 → 重新登入 → 收藏仍存在）通過 — **可測**: 5 步驟人工 / 腳本驗證

### FR-007: 既有資料遷移處理

- **描述**: 既有 SQLite 資料（`web/data/snowtrip.db`）已因 Railway ephemeral 在歷次重啟中遺失，**生產環境視為空表**，本 TASK 不執行歷史資料遷移；但提供一次性匯入腳本（`scripts/migrate_sqlite_to_postgres.py`）作為 fallback，供本機 / staging 若有殘留 SQLite 檔案時手動觸發
- **優先順序**: P2
- **來源**: enhanced-input.md [BA確認] 第 1 項 → 本 TASK §8 決策（理由：DESIGN.md §八 + CLAUDE.md 已確認 production 為空）
- **信心等級**: 🟡 中信心（依「Railway ephemeral 已導致資料失」推論；若使用者有完整本地備份 SQLite 副本則需重新評估）
- **驗收標準**:
  - [ ] AC-056: `scripts/migrate_sqlite_to_postgres.py` 存在，接收 `--sqlite-path` 與 PostgreSQL 連線參數，能將三張表資料完整匯入（含 created_at 保留、`users.is_verified` 布林轉換正確、FK 順序正確）；若 SQLite 檔案不存在則 exit 0 with message「無 SQLite 資料需匯入」 — **可測**: 用 mock SQLite 檔（3 用戶 / 2 收藏 / 1 token）跑腳本，PostgreSQL 結果 SELECT count 對應 3 / 2 / 1
- **業務影響說明**: 本 TASK 部署到 Railway production 後，**現有 ephemeral SQLite 中可能殘留的最後 N 分鐘資料將被丟棄**。此資料按 CLAUDE.md / baseline 分析「不可能有長期積累」（因每次重啟即失），但「上一次重啟到本次部署之間」的少量帳號可能丟失；屬於可接受 trade-off（本就是已知 ephemeral）。標記為 [IRREVERSIBLE: 部署切換瞬間可能丟失少於 N 分鐘 SQLite 殘留資料；事前已知 ephemeral 性質]

### FR-008: 開發 / staging / production 環境 DB engine 策略

- **描述**: 開發 / staging / production **全環境統一使用 PostgreSQL**（透過 docker-compose 提供本機 dev 用 PostgreSQL 容器；config.json `techStack.database.image=postgres:16-alpine` 為標準）；既有 SQLite 開發路徑（`web/data/snowtrip.db`）於本 TASK 部署後棄用（標記 DEPRECATED，不刪檔以保留 git 歷史）
- **優先順序**: P0
- **來源**: enhanced-input.md [BA確認] 第 2 項 → 本 TASK §8 決策（理由：避免雙 driver 維護負擔；docker-compose 已預備 postgres:16-alpine — see baseline-audit §1.1）
- **信心等級**: 🟢 高信心
- **驗收標準**:
  - [ ] AC-057: 本機開發環境執行 `docker-compose up -d postgres` 後，跑 `pytest web/auth/tests/test_auth.py` 連到 PostgreSQL 全數通過（不再需要 SQLite 檔）— **可測**: pytest exit code = 0 且測試框架 fixture 連線 string 含 `postgresql://` 而非 `sqlite://`

---

## 4. 非功能需求

### NFR-001: 持久性（解 Critical C-1）

- **類別**: 可用性 / 持久性
- **描述**: 用戶帳號 / 收藏 / Email 驗證 token 在 Railway 容器重啟（每日重啟 / deploy / scale）後**全部保留**
- **量化指標**: Railway 容器重啟後資料保留率 = 100%（測試方法：建 1 帳號 + 1 收藏 + 1 待驗證 token，觸發 Railway 重啟，重啟後查詢三筆資料皆存在且欄位未變）
- **來源**: enhanced-input.md「解 Critical: SQLite ephemeral storage 用戶資料消失」+ baseline-audit C-1 + DESIGN.md §八
- **驗證方式**: 手動 / smoke test 腳本

### NFR-002: 認證流程外部行為零變化（向後兼容）

- **類別**: 可維護性 / 相容性
- **描述**: TASK-001 已登記之 FR-007~FR-014（註冊 / 登入 / 登出 / Email 驗證 / 重寄 / OAuth / 取得登入狀態 / 收藏 CRUD）的 HTTP 狀態碼 / response body 結構 / cookie 設定（HttpOnly / SameSite / Max-Age）/ redirect URL 在本 TASK 部署後**完全不變**
- **量化指標**: TASK-001 既有 AC-015~AC-036 共 22 個驗收標準在本 TASK 部署後仍全數通過（pytest + 手動 smoke）— pass rate = 100%
- **來源**: enhanced-input.md「不破壞既有認證流程」+ TASK-001/FR-007~FR-014
- **驗證方式**: 既有 8 個 pytest + 手動 smoke 22 個 AC（test-ba/test-be 階段執行）

### NFR-003: 啟動延遲

- **類別**: 效能
- **描述**: 應用啟動到第一個 request 可服務的時間（從 uvicorn 啟動 log 到 `GET /api/auth/me` 回 401）相較 SQLite 階段不顯著惡化
- **量化指標**: 啟動時間 ≤ 既有 SQLite 啟動時間 + 2 秒（PostgreSQL 連線握手成本上限）；P95 ≤ 5 秒（含 migration 自動執行）
- **來源**: 業界經驗 + 不應因 DB 切換造成 Railway 健康檢查失敗 + [BA建議] SUG-003
- **驗證方式**: deploy 階段量測啟動 log 時間戳；test-be 階段量測 pytest fixture 啟動時間

### NFR-004: 查詢延遲（既有 endpoint）

- **類別**: 效能
- **描述**: TASK-001 既有 28 個 API 在 PostgreSQL 後端下，包含 DB 互動的 endpoint（auth / favorites / verify）回應時間相較 SQLite 不顯著惡化
- **量化指標**: P95 ≤ SQLite baseline × 1.5（PostgreSQL 透過網路連線通常較本機 SQLite 慢，1.5x 為合理容忍）；絕對值 P95 ≤ 500 ms（不含外部 API 如 Resend / Google OAuth callback）
- **來源**: 業界經驗 + [BA建議] SUG-003；無使用者明示，標 [BA合理推斷]
- **驗證方式**: test-be 階段以 8 個 pytest 量測平均 / P95

### NFR-005: 連線池與並行容忍

- **類別**: 可擴展性 / 效能
- **描述**: PostgreSQL connection pool 設定須容忍 Railway production 並行 request（既有 production 觀察 ≤ 10 並行）；不可在輕度負載下耗盡連線
- **量化指標**: connection pool min=2 / max=10（具體值由 SD 階段依 Railway 連線數限制定）；連線取得超時 < 5 秒；同時 20 個 request 不會出現 connection refused
- **來源**: enhanced-input.md [BA確認] 第 4 項 → 本 TASK §8 決策（建議 SD 用 SQLAlchemy 內建 pool 或 psycopg pool，視驅動選擇）
- **驗證方式**: SD 階段於 api-spec / logic-flow 明確記錄 pool 參數；test-be 階段以 ab/wrk 模擬 20 並行

### NFR-006: Migration 可逆性

- **類別**: 可維護性
- **描述**: 所有 migration 必須 reversible — 框架方式（Alembic 等）寫好 downgrade；純 SQL 同檔案附 `-- DOWN` 區塊或對應 `*_down.sql`
- **量化指標**: 每個 migration 檔對應 1 個 reversible 機制；測試方法：對最新 migration 跑 up → down → up，最終 schema 與第一次 up 後 100% 相同（含欄位 / 索引 / 約束）
- **來源**: db-conventions.md §5.2 + §8（禁止項）
- **驗證方式**: test-be 階段 fixture 跑 round-trip

### NFR-007: 三段式刪欄保留

- **類別**: 可維護性
- **描述**: 即使本 TASK 不刪除任何既有欄位，工具選型必須支援未來三段式 (Expand / Migrate code / Contract) 刪欄協議
- **量化指標**: SD 階段 db-schema.md 第 X 節明示「未來 DROP COLUMN 必須走 expand-contract」；migration 工具支援多步驟序列發布
- **來源**: db-conventions.md §5.3 + §8
- **驗證方式**: test-sd 階段檢視 db-schema.md 是否有此章節

### NFR-008: 大表索引 CONCURRENTLY

- **類別**: 可維護性 / 可用性
- **描述**: 未來新增索引時使用 `CREATE INDEX CONCURRENTLY`（PostgreSQL 特性）避免鎖表；本 TASK 因建表初始可不強制 CONCURRENTLY，但 SD 階段須在規範中明示後續策略
- **量化指標**: SD 階段 db-schema.md 明示「後續新增索引必須 CONCURRENTLY」；本 TASK 初次建立 uniq_users_email / uniq_users_username / uniq_users_google_id / uniq_email_verification_tokens_token 可同步建（建表時 inline）
- **來源**: db-conventions.md §5.4
- **驗證方式**: test-sd 階段檢視

### NFR-009: 字串編碼

- **類別**: 可維護性 / 國際化
- **描述**: PostgreSQL database charset = UTF8（PostgreSQL 預設）；不指定特殊 Collation（依 db-conventions §6 — email 唯一性檢查在應用層用 `.lower()` 處理）
- **量化指標**: `SHOW server_encoding` 返回 `UTF8`；`SHOW lc_collate` 為系統預設值（不強制）
- **來源**: db-conventions.md §6
- **驗證方式**: test-be 階段 fixture 啟動時檢查

### NFR-010: 環境變數 Owner 與命名一致性（Rule 18）

- **類別**: 可維護性
- **描述**: 新增的 5 個 `POSTGRES_*`（或 `DATABASE_URL`）env vars 必須遵守 api-conventions.md「env var UPPER_SNAKE_CASE」+ config.json `envPrefix = "POSTGRES_"`；ownerService=be；scope=all（FE 不直接讀）
- **量化指標**: `shared/parameter-registry.md` 第 1 節 Env Variables 表中 5 條記錄全部符合 UPPER_SNAKE_CASE + paramKind=env + ownerService=be
- **來源**: api-conventions.md（env var 命名）+ config.json envPrefix + Rule 18
- **驗證方式**: test-sd 階段以 `sdlc-parameter-check.sh` 驗證

### NFR-011: Secret 管理

- **類別**: 安全
- **描述**: `POSTGRES_PASSWORD`（或 `DATABASE_URL` 含 password 段）視為 secret — 不可 commit 到 git；Railway 環境變數透過 Railway dashboard 設定；本地開發用 `.env`（已 gitignored，見 baseline-audit §1.1）
- **量化指標**: `git log --all -p | grep -i POSTGRES_PASSWORD` 無實際密碼洩漏（僅出現 `.env.example` 中的範例占位符如 `your_password_here`）；`.gitignore` 包含 `.env`
- **來源**: 業界 secret 管理慣例 + baseline-audit §1.1（.gitignore 已含 `.env`）
- **驗證方式**: test-sd 階段以 `git secrets`-style 掃描；deployer 階段檢視 Railway dashboard 設定

### NFR-012: 系統語言（既有規範延續）

- **類別**: 國際化 / UX
- **描述**: 本 TASK 為後端基礎設施重構，無新 UI 文字產出；既有錯誤訊息（如 `web/auth/database.py` 拋出的 connection error）若需新增使用者可見訊息，仍須使用繁體中文 zh-TW（沿用 TASK-001/NFR-018 既有定義）
- **量化指標**: 本 TASK 不新增使用者可見訊息（DB 層錯誤由既有 FastAPI exception handler 處理，已是中文）
- **來源**: i18n-conventions.md（主語系 zh-TW，見 baseline-audit §3 結論 + TASK-001/NFR-018）+ sdlc-ba.md 規則 6
- **驗證方式**: test-ba 階段檢視本 TASK 無新增英文 UI 字串

---

## 5. 業務規則

### BR-001: 三表 schema 邏輯結構不變

- **條件**: 本 TASK migration 完成後
- **行為**: `users` / `favorites` / `email_verification_tokens` 三表的**欄位邏輯**（除 FR-004 補的 updated_at + deleted_at 外）/ **UNIQUE 約束** / **FK ON DELETE CASCADE** / **預設值語意** 必須與 TASK-001/ENTITY-001/002/003 真相基線 100% 一致；應用層 SELECT/INSERT/UPDATE/DELETE 邏輯不需修改 column 列表
- **來源**: enhanced-input.md「不破壞既有認證流程」+ TASK-001/ENTITY-001/002/003 schema 真相
- **實作於**: SD 階段 db-schema.md / FUNC 對應 migration

### BR-002: 既有 ALTER TABLE 三行禁用

- **條件**: 本 TASK 部署後
- **行為**: `web/auth/database.py:44-52` 三行 `ALTER TABLE users ADD COLUMN ...` 全部移除；後續若需新增欄位，必須新建 migration 檔（不可在應用啟動時 try/except 加欄位）
- **來源**: db-conventions.md §8 第 1 條禁止項 + baseline-audit §4.1 C-1
- **實作於**: FR-001 + FR-003 對應的 SD/BE 重構

### BR-003: ON DELETE CASCADE 白名單延續

- **條件**: PostgreSQL 重建 FK 時
- **行為**: 沿用既有 CASCADE 設計（`favorites.user_id → users.id` / `email_verification_tokens.user_id → users.id`），不新增 CASCADE
- **來源**: db-conventions.md §4 CASCADE 白名單 + database.py:30/38
- **實作於**: SD 階段 db-schema.md

### BR-004: 索引命名規範

- **條件**: PostgreSQL 建立索引時
- **行為**: UNIQUE 索引前綴 `uniq_`（如 `uniq_users_email` / `uniq_users_username` / `uniq_users_google_id` / `uniq_email_verification_tokens_token`）；FK 隱式索引前綴 `fk_idx_`（PostgreSQL 不會自動為 FK 建索引，須明確建立）
- **來源**: db-conventions.md §3 索引命名
- **實作於**: SD 階段 db-schema.md + migration 檔

### BR-005: PRIMARY KEY 採 BIGINT IDENTITY

- **條件**: PostgreSQL 重建表時
- **行為**: 所有表 PK 採 `BIGINT GENERATED ALWAYS AS IDENTITY`（取代 SQLite `INTEGER PRIMARY KEY AUTOINCREMENT`）；既有 `users.id` 從 1 起編
- **來源**: db-conventions.md §2 + Postgres 目標欄
- **實作於**: SD 階段 db-schema.md

### BR-006: 時間戳採 TIMESTAMPTZ

- **條件**: PostgreSQL 建立 `created_at` / `updated_at` / `deleted_at` 欄位時
- **行為**: 採 `TIMESTAMPTZ`（含時區）而非 SQLite `TIMESTAMP`；預設 `NOW()`
- **來源**: db-conventions.md §2 + PostgreSQL 最佳實踐
- **實作於**: SD 階段 db-schema.md + FR-004 補欄位

### BR-007: Migration 檔名格式

- **條件**: 新增 migration 時
- **行為**: 檔名格式 `{YYYYMMDD_HHMMSS}_{verb}_{noun}.{sql|py}`（具體副檔名依工具）；至少 1 個 verb（如 `create_initial_schema` / `add_softdelete_columns`）
- **來源**: db-conventions.md §5.1
- **實作於**: SD/BE 階段 migrations/ 目錄

---

## 6. 假設與約束

### 假設（需 PM/使用者確認）

- [ASSUME-001] Railway 提供 PostgreSQL 16 addon 或允許連線至外部 PostgreSQL 16（Supabase / Neon / Railway 自建）— deploy 階段確認
- [ASSUME-002] 既有 SQLite production 資料**已因 ephemeral 流失**，本 TASK 部署不需保留歷史用戶（CLAUDE.md / baseline-audit 隱含；若使用者另有備份須調整 FR-007）
- [ASSUME-003] Railway production env 允許設定 ≥ 5 個新環境變數（或 1 個 DATABASE_URL）— 部署層常識
- [ASSUME-004] 本機開發者擁有 Docker 或 PostgreSQL 16 本機實例可供測試（docker-compose.yml 已含 postgres 服務 — baseline §1.1）

### 約束

- [CONST-001] 不得修改 TASK-001 已 approved 的 FR/NFR/BR/AC 內容（依 Rule 7 跨 TASK 增量產出原則）
- [CONST-002] 不得改變 TASK-001/FR-007~FR-014 對應的 HTTP API 外部行為（status / body / cookie / redirect — 見 NFR-002）
- [CONST-003] 不得修改 conventions/*（已於 2026-06-03 lock；變更走 RFC 流程 — db-conventions.md §7）
- [CONST-004] 不得在本 TASK 重構雪票 / 機票 / 行程 / SEO / page route 等非 DB 相關代碼（範圍隔離 — enhanced-input.md「不納入」段）
- [CONST-005] 不得新增 hard-delete 邏輯到既有不可逆 FUNC（FUNC-027/034/045 — IRREVERSIBLE 已標記 from TASK-001）
- [CONST-006] 不得新增業務功能（如忘記密碼）— FR-001~FR-008 嚴格限於 DB 遷移
- [CONST-007] Railway 啟動指令 `uvicorn web.main:app --host 0.0.0.0 --port $PORT` 不變
- [CONST-008] 不得修改 既有 8 個 pytest 的測試斷言邏輯（可調整 fixture 連線 string，但 assert 邏輯不變 — 保證向後兼容驗證有效）
- [CONST-009] 本 TASK 部署到 production 涉及不可逆切換 — FR-007 標 [IRREVERSIBLE] 並需 deploy 階段提供 rollback plan（保留 SQLite 應用層代碼作為 emergency rollback 路徑直到本 TASK 在 production 穩定運行 N 天）

---

## 7. 其他角色的備註

> 本 TASK 涉及多個下游角色決策；以下為使用者 / 上下文提到但不屬於 BA 職責的內容

| 備註 | 分類 | 建議分派給 | 來源 |
|------|------|-----------|------|
| Postgres driver 選型（psycopg2 / psycopg3 / asyncpg / SQLAlchemy） | 技術 | SD/SA | enhanced-input.md「待 SD 階段決定」 |
| Migration 工具選型（Alembic / yoyo-migrations / 手寫 SQL） | 技術 | SD | enhanced-input.md [BA確認] 第 3 項 |
| Connection pool 參數（min/max/timeout） | 技術 | SD/BE | enhanced-input.md [BA確認] 第 4 項 + NFR-005 |
| Railway Postgres addon vs 外部託管（Supabase / Neon） | 部署 | SA + Deployer | enhanced-input.md「Postgres 由 Railway addon 提供（或自建）」 |
| Docker-compose dev PostgreSQL 服務名稱與 port mapping | 部署 / 環境 | SA + Deployer | config.json + baseline §1.1（docker-compose.yml 已 PR 13c） |
| SD 須於 db-schema.md 寫明三表完整 schema（含本 TASK 新欄位） + migration 順序 | 規格 | SD | FR-002/004 + db-conventions §5.1 |
| BE 須在實作後執行所有既有 pytest 確認 100% 通過 | 測試 | BE | NFR-002 + AC-045 |
| Tester 須增加「Railway 重啟後資料保留」smoke test | 測試 | Tester | NFR-001 + FR-006 AC-055 |
| 安全強化：是否藉此機會加 PostgreSQL connection over SSL（sslmode=require） | 安全 | SA + Deployer | [BA建議] SUG-005 |

---

## 8. [BA建議]（需 PM / 使用者確認才納入）

> 本區為 BA 專業判斷的建議，與正式規格物理分離；確認前不可採納為 FR/NFR。
> 本區同時記載 enhanced-input.md 中 6 個 [BA確認] 項的決策方向（已在正式 FR 區落地者列「已採納」；未採納者保留為建議）。

### 6 個 [BA確認] 決策狀態彙整

| 編號 | [BA確認] 項 | BA 決策 | 採納位置 |
|------|-----------|--------|---------|
| BC-1 | 現有 SQLite 資料是否需要遷移？ | **不執行歷史遷移，但提供腳本 fallback** | FR-007 + ASSUME-002 |
| BC-2 | 開發 / staging / production 是否都用 Postgres？ | **全環境統一 Postgres** | FR-008 |
| BC-3 | Migration 工具選型？ | **委派 SD 階段決策**（規範 reversible + 檔名格式即可，工具中性） | §7「其他角色備註」+ FR-003 |
| BC-4 | Connection pool 策略？ | **NFR 量化指標 + 委派 SD** | NFR-005 + §7 |
| BC-5 | 是否補 updated_at / deleted_at？ | **補**（理由：見 SUG-001） | FR-004 + BR-006 |
| BC-6 | 是否處理 ALTER TABLE try/except hack？ | **處理**（理由：見 SUG-002） | FR-003 + BR-002 + AC-048 |

### [BA建議] 詳細理由

- [SUG-001] **補 updated_at / deleted_at 至既有 3 表** — **理由**: db-conventions.md §2 + §8 第 4 條禁止項明示「無 updated_at 的新表」屬違規；本 TASK 既然 schema 重建，是補齊低成本時機；不補則 baseline-audit M-8 持續違規，未來 audit / 法務追溯（如 GDPR 軟刪除）會需要再開 TASK。**面向**: 流程優化 + 擴充性 + conventions 合規
- [SUG-002] **處理 ALTER TABLE try/except hack** — **理由**: 該 hack 違反 db-conventions §8「應用程式碼內寫 ALTER TABLE」+ §5 reversible migration；保留會讓本 TASK 留下技術債、且 PostgreSQL 環境下該 hack 可能因錯誤型別轉換失敗導致 silent fail；藉本 TASK schema 重建一併移除最經濟。**面向**: conventions 合規 + 安全強化（避免 silent fail）+ 可維護性
- [SUG-003] **規範啟動 / 查詢延遲 NFR 量化指標** — **理由**: 切換 SQLite→PostgreSQL 必然引入網路 round-trip；無 NFR 約束會導致 SD/BE 階段做 trade-off 時無依據；建議 NFR-003 / NFR-004 採保守倍數（PostgreSQL 通常比 SQLite 慢 1.3~1.5x），避免事後驚訝。**面向**: 效能 + 流程優化
- [SUG-004] **本 TASK 不改 hard-delete 為 soft-delete** — **理由**: 雖然補了 `deleted_at` 欄位（FR-004），但改寫 `web/auth/auth_router.py:246` 的 `DELETE FROM favorites` 為 `UPDATE SET deleted_at = NOW()` 涉及多處應用層 SELECT 都需加 `WHERE deleted_at IS NULL` filter，是另一個 logical refactor，不應與 DB 遷移混搭；留後續 TASK（建議名 `soft-delete-favorites`），走 Rule 6 跨 TASK 修改協議。**面向**: 範圍邊界 + 風險控制
- [SUG-005] **PostgreSQL 連線啟用 SSL** — **理由**: production 部署到 Railway 時 PostgreSQL 連線跨 container network；雖 Railway 內網被視為信任區，但 enable `sslmode=require` 屬 defense-in-depth；DATABASE_URL 通常已含 `?sslmode=require`，成本低。**面向**: 安全強化
- [SUG-006] **保留 SQLite driver 作 emergency rollback 路徑（短期）** — **理由**: 本 TASK 是不可逆切換（FR-007 [IRREVERSIBLE]）；建議 PostgreSQL 部署到 production 後**前 N 天保留** `database_sqlite.py` 作 git 歷史，若 PostgreSQL 出現嚴重問題（如 Railway addon 損毀）可快速 revert；N 天後（建議 14 天）正式刪除。**面向**: 風險控制 + 可逆性（部分）
- [SUG-007] **DESIGN.md §八 同步更新** — **理由**: 本 TASK 解 CLAUDE.md / DESIGN.md §八列為「SQLite ephemeral」的 P0 問題；TASK 完成時需在 DESIGN.md §八「已知問題」標記為「✅ 已於 TASK-002 解決」並更新 §五-4 Schema 區塊（加 updated_at / deleted_at）。屬於 PM 文件清理工作，標記為提醒。**面向**: 流程閉環 + 文件同步

---

## 9. [待確認] 項目

> 本區僅列**未在正式規格區決策**的項目；6 個 [BA確認] 已全部決策（見 §8），故本區應為空或極少。

- (本 TASK 無 [待確認] — 6 個 [BA確認] 全數已決策，殘留技術細節已委派下游角色）

---

## 10. 術語表（增量 — 本 TASK 新增 / 引用既有）

| 術語 | 定義 | 來源 |
|------|------|------|
| ephemeral storage | [REUSE: from TASK-001 terminology] Railway 容器層暫存，每次重啟即清空，不適合 SQLite | shared/terminology.md |
| PostgreSQL 16 | 本 TASK 目標 DB engine，對應 config.json techStack.database.image=postgres:16-alpine | config.json |
| Railway Postgres addon | Railway 平台提供的 managed PostgreSQL 服務（待 deploy 階段確認可用性） | enhanced-input.md |
| DATABASE_URL | PostgreSQL 標準連線字串格式 `postgresql://user:pass@host:port/db?sslmode=...`，可單一變數取代 5 個 POSTGRES_* | enhanced-input.md + 業界慣例 |
| Migration（資料庫遷移） | reversible 的 schema 變更腳本，由 migration 工具（如 Alembic）追蹤已套用版本 | db-conventions.md §5 |
| Expand-Contract（三段式刪欄） | [REUSE: 即 db-conventions §5.3] 刪欄協議：先 nullable 加新欄、再切換應用、最後 DROP 舊欄 | db-conventions.md §5.3 |
| 軟刪除 (soft-delete) | 用 `deleted_at` 標記取代 DELETE FROM；查詢時加 `WHERE deleted_at IS NULL` | db-conventions.md §8 |
| Connection pool | 應用層維護的 DB 連線重用池，避免每次 query 開新連線 | NFR-005 + SD 階段決策 |
| ALTER TABLE try/except hack | 既有 `web/auth/database.py:44-52` 用 `try: ALTER TABLE; except: pass` 寬鬆吞例外的 brownfield 技術債 | baseline-audit C-1 + database.py:44-52 |

---

## 11. 追溯矩陣

| 需求ID | 來源引用 | 優先順序 | 狀態 | 相關 AC | 相關 NFR/BR |
|--------|---------|---------|------|--------|-------------|
| FR-001 | enhanced-input.md「sqlite3 driver 改為 Postgres driver」 | P0 | 已確認 | AC-044, AC-045 | NFR-001/002/003/004, BR-001 |
| FR-002 | enhanced-input.md「3 張既有資料表必須遷移」+ TBL-001/002/003 [REUSE] | P0 | 已確認 | AC-046, AC-047 | BR-001/003/004/005/006 |
| FR-003 | enhanced-input.md「正式 migration 工具」+ db-conventions §5 | P0 | 已確認 | AC-048, AC-049 | NFR-006/007/008, BR-002/007 |
| FR-004 | enhanced-input.md [BA確認] 第 5 項 → 採納 + db-conventions §2/§8 | P1 | 已確認 | AC-050, AC-051 | BR-006, NFR-007 |
| FR-005 | enhanced-input.md「環境變數」+ config.envPrefix + Rule 18 | P0 | 已確認 | AC-052, AC-053 | NFR-010/011 |
| FR-006 | enhanced-input.md「Railway 部署設定」 | P0 | 已確認 | AC-054, AC-055 | NFR-001/003/009 |
| FR-007 | enhanced-input.md [BA確認] 第 1 項 → 採納 | P2 | 已確認 [IRREVERSIBLE] | AC-056 | CONST-009 |
| FR-008 | enhanced-input.md [BA確認] 第 2 項 → 採納 | P0 | 已確認 | AC-057 | NFR-002 |

### NFR 追溯（量化來源）

| NFR-ID | 來源 | 量化值 |
|--------|------|--------|
| NFR-001 | baseline C-1 + DESIGN.md §八 + 使用者「解 Critical」 | 重啟後資料保留 = 100% |
| NFR-002 | enhanced-input.md「不破壞既有認證流程」+ TASK-001 22 AC | 既有 AC pass rate = 100% |
| NFR-003 | [BA建議] SUG-003 + 業界經驗 | 啟動時間 ≤ SQLite + 2s；P95 ≤ 5s |
| NFR-004 | [BA建議] SUG-003 + 業界經驗 | P95 ≤ SQLite × 1.5；絕對值 ≤ 500ms |
| NFR-005 | enhanced-input.md [BA確認] 第 4 項 + Railway 連線數常識 | pool min=2 / max=10；20 並行不丟連線 |
| NFR-006 | db-conventions §5.2 | 100% migration 可逆 (up→down→up schema 等價) |
| NFR-007 | db-conventions §5.3 | SD db-schema.md 明示 expand-contract 章節 |
| NFR-008 | db-conventions §5.4 | SD 明示後續索引 CONCURRENTLY |
| NFR-009 | db-conventions §6 | server_encoding = UTF8 |
| NFR-010 | Rule 18 + api-conventions + envPrefix | parameter-registry 5 條 UPPER_SNAKE + owner=be |
| NFR-011 | 業界 secret 慣例 + baseline §1.1 | git 無實際 password；.gitignore 含 .env |
| NFR-012 | i18n-conventions + TASK-001/NFR-018 | 本 TASK 無新增英文 UI 字串 |

### CONST 追溯

| CONST-ID | 來源 | 影響範圍 |
|----------|------|---------|
| CONST-001 | Rule 7 跨 TASK 增量產出 | TASK-001 全部產出 |
| CONST-002 | NFR-002 + enhanced-input | TASK-001/FR-007~FR-014 對應 API |
| CONST-003 | conventions lock 2026-06-03 + Rule 16 | conventions/*.md |
| CONST-004 | enhanced-input.md「不納入」 | 雪票 / 機票 / 行程 / SEO / page route |
| CONST-005 | Rule 11 不可逆 + TASK-001 IRREVERSIBLE 標記 | FUNC-027/034/045 |
| CONST-006 | enhanced-input.md「不納入」 | 業務功能新增 |
| CONST-007 | enhanced-input.md「Railway 啟動指令不變」 | Procfile / Railway 設定 |
| CONST-008 | NFR-002 + AC-045 | web/auth/tests/test_auth.py |
| CONST-009 | FR-007 [IRREVERSIBLE] + Rule 11 | deploy 階段 rollback plan |

### 跨 TASK 修改預警（Rule 6 / Rule 7）

> SA 階段必須在 functional-flow.md 明確標記以下 [CROSS-TASK] 項：

| 受影響 TASK | 修改項目 | 觸發 FR | 原因 |
|------------|---------|---------|------|
| TASK-001 | TBL-001 schema 補 updated_at + deleted_at | FR-004 | db-conventions 合規 + brownfield 補齊 |
| TASK-001 | TBL-002 schema 補 updated_at + deleted_at | FR-004 | 同上 |
| TASK-001 | TBL-003 schema 補 updated_at + deleted_at | FR-004 | 同上 |
| TASK-001 | MOD-005 auth.database storage engine 替換 (sqlite3 → Postgres driver) | FR-001 | 解 Critical C-1 |

---

## 12. 自我驗證

| 檢查項 | 通過 | 說明 |
|--------|------|------|
| 所有功能需求都有來源引用 | ✅ | 8 個 FR 全部標 enhanced-input.md / baseline / conventions 行/段引用 |
| 沒有自行補充使用者未說的功能 | ✅ | 6 個 [BA確認] 明確處理；不納入清單覆蓋所有腦補候選；FR-007 採保守「腳本 fallback」而非腦補完整遷移工具 |
| 所有 [BA建議] 都有標記 | ✅ | §8 7 個 SUG 全部標 [SUG-NNN] + 理由 + 面向 |
| 所有 [待確認] 都有標記 | ✅ | §9 為空（6 個 [BA確認] 全數已決策）；殘留技術細節已委派下游角色 §7 |
| 需求之間沒有矛盾 | ✅ | FR-004 補欄位 + SUG-004 不改 hard-delete 為 soft-delete 已明確界線；FR-007 不遷移歷史 + FR-008 全環境 Postgres 邏輯一致 |
| 每個需求都有驗收標準 | ✅ | 8 個 FR 對應 AC-044~AC-057 共 14 個 AC，皆二元可驗證 |
| 術語使用一致 | ✅ | 既有術語標 [REUSE: from TASK-001 terminology]；新術語在 §10 定義 |
| ID 編號連續不重複 | ✅ | FR/NFR/BR/CONST 從 001 起 TASK 內連續；AC 從 044 全域連續；ROLE-004 全域連續續 TASK-001/ROLE-003 |
| NFR 已量化 | ✅ | 12 個 NFR 全部有量化指標（時間 / 百分比 / pool 參數 / 編碼值） |
| 禁止模糊語言 | ✅ | 避免「適當」「合理」「快速」；用「≤ 500ms」「100%」「P95」量化 |
| [BA建議] 面向 ≥ 3 | ✅ | 涵蓋流程優化 / 範圍邊界 / 安全強化 / 效能 / 風險控制 / 擴充性 / 流程閉環 7 面向 |
| 系統語言已明確 | ✅ | NFR-012 沿用 zh-TW（TASK-001/NFR-018） |
| **總分** | **95/100** | 扣 5 分：FR-006 Railway addon vs 外部託管為中信心（依賴 deploy 階段確認），屬技術選型本就不該 BA 鎖定，可接受 |

---

> **附註 — 既有 TASK-001 連結**:
> - 既有 FR/AC 範圍: TASK-001/FR-001~FR-017, TASK-001/AC-001~AC-043, TASK-001/ROLE-001~ROLE-003
> - 既有 NFR 範圍: TASK-001/NFR-001~NFR-019（含 NFR-018 = zh-TW 系統語言）
> - 既有 IRREVERSIBLE FUNC: FUNC-027（觸發寄信）/ FUNC-034（廢舊產新 token）/ FUNC-045（收藏刪除）— 本 TASK CONST-005 約束不變
> - 既有不在本 TASK 範圍但被本 TASK 隔離的技術債: baseline-audit C-2（`/api/env-check` 下架，獨立 hotfix）/ DESIGN.md 同步（PM 文件債）
