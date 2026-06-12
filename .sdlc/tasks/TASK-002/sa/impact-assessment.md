---
document_id: "IMPACT-TASK-002-v1.0"
title: "跨 TASK 影響評估 — SQLite → PostgreSQL 持久化遷移"
version: "1.0"
date: "2026-06-08"
author: "SA"
task_id: "TASK-002"
phase: "sa"
mode: "feature"
source_documents:
  - "ARCH-TASK-002-v1.0"
  - "FUNC-TASK-002-v1.0"
  - "FIELD-TASK-002-v1.0"
  - "PATTERN-TASK-002-v1.0"
  - ".sdlc/tasks/TASK-001/sa/* (TASK-001 SA 全部產出)"
  - ".sdlc/shared/* (共享層當前狀態)"
change_history:
  - version: "1.0"
    date: "2026-06-08"
    changes: "初始 — 對 TASK-001 共 4 個 [CROSS-TASK] 修改項影響評估；7 個 [REUSE] 標記彙整；後續 TASK 影響預告"
    author: "SA"
---

# 跨 TASK 影響評估 — TASK-002

> **本檔用途**: 補充 system-arch.md §9 對跨 TASK 修改的影響評估；列出本 TASK 對 TASK-001 產出的具體修改清單 + 重用清單，供 UIUX/SD/FE/BE/Tester 後續階段參考 Rule 6 跨 TASK 修改協議。

---

## 1. 本 TASK 與 TASK-001 的影響矩陣

### 1.1 [CROSS-TASK: TASK-001] 修改項彙整（4 個 — BA 預警全數落實）

| # | 修改目標 | 修改內容 | 觸發 FR | SA 落實位置 | 下游角色責任 |
|---|---------|---------|---------|------------|------------|
| 1 | **TBL-001 (users)** | 補 `updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()` + `deleted_at TIMESTAMPTZ NULL` | FR-004 | system-arch.md MOD-102 + functional-flow.md FUNC-103/104 + field-spec.md §2 ENTITY-001 | SD: db-schema.md 寫完整 ALTER TABLE / CREATE TABLE DDL；BE: migration 檔實作 |
| 2 | **TBL-002 (favorites)** | 同上補 2 欄 | FR-004 | 同上 + field-spec.md §2 ENTITY-002 | 同上 |
| 3 | **TBL-003 (email_verification_tokens)** | 補 3 欄: `updated_at` + `deleted_at`（FR-004）+ `created_at`（補 TASK-001 baseline gap — field-spec §6 已標明） | FR-004 + baseline gap | 同上 + field-spec.md §2 ENTITY-003 | 同上 |
| 4 | **MOD-005 (auth) storage engine** | sqlite3 driver → PostgreSQL driver；`web/auth/database.py` 直接重寫；6 個依賴檔（auth_router / oauth_router / dependencies / verify_client / email_service / 自身）的 query 適配 PG dialect | FR-001 | system-arch.md §3 MOD-005 "邊界不變、實作替換" + functional-flow.md FUNC-101/105 | SD: api-spec.md 或 logic-flow.md 明確列「儘管 28 個 API 簽名不變（NFR-002），底層 query 全部適配 PG dialect」+ 工具 / driver 選型；BE: 實作；Tester: AC-045 既有 8 pytest + AC-044 連線失敗驗證 |

### 1.2 BA 預警 vs SA 落實對照表

| BA self-review.json `cross_task_modify_warnings` | SA 落實狀態 |
|---------------------------------------------------|-------------|
| `SA 階段必須在 functional-flow.md 標 [CROSS-TASK: TASK-001 / TBL-001 補 updated_at + deleted_at 欄位 / 觸發 FR-004]` | ✅ functional-flow.md §1.1 FUNC-104 標記 + §4.4 |
| `SA 階段必須標 [CROSS-TASK: TASK-001 / TBL-002 補 updated_at + deleted_at 欄位 / 觸發 FR-004]` | ✅ functional-flow.md §1.1 FUNC-104 標記 + §4.4 |
| `SA 階段必須標 [CROSS-TASK: TASK-001 / TBL-003 補 updated_at + deleted_at 欄位 / 觸發 FR-004]` | ✅ functional-flow.md §1.1 FUNC-104 標記 + §4.4 + 補充 TBL-003 created_at |
| `SA 階段必須標 [CROSS-TASK: TASK-001 / MOD-005 auth.database storage engine 替換 / 觸發 FR-001]` | ✅ system-arch.md §3 MOD-005 + functional-flow.md §1.1 FUNC-105 標記 + §4.4 |

### 1.3 [REUSE: from TASK-001] 標記清單

| 物件類別 | TASK-001 ID | 本 TASK 引用位置 | 用途 |
|---------|------------|---------------|------|
| MOD | MOD-001 (http_scraper) | system-arch.md §3 表 | 雪票批次模組 — 完全不變 |
| MOD | MOD-002 (site_analyzer) | system-arch.md §3 表 | dead code 候選 — 不變 |
| MOD | MOD-003 (ski_early_bird_scraper) | system-arch.md §3 表 | 本地 CLI — 不變 |
| MOD | MOD-004 (flight_search) | system-arch.md §3 表 | 機票多 backend — 不變 |
| MOD | MOD-005 (auth) | system-arch.md §3 + functional-flow.md FUNC-105 | **邊界不變、實作替換**（CROSS-TASK 修改項 #4）|
| MOD | MOD-006 (plan_routes) | system-arch.md §3 表 | 整合查詢頁 — 不變 |
| PATTERN | PATTERN-001..008 (8 個) | system-arch.md §6 + pattern-spec.md §1.2 | 鎖機制 / middleware / SSE / fallback / 寄信 / OAuth Upsert / Cookie / Lock scope — 機制不變；PATTERN-006 race condition 仍存在留 SA-SUG-103 |
| ENTITY | ENTITY-001 (users) | field-spec.md §1 + §2 | schema 重建於 PG + 補欄位 |
| ENTITY | ENTITY-002 (favorites) | field-spec.md §1 + §2 | 同上 |
| ENTITY | ENTITY-003 (email_verification_tokens) | field-spec.md §1 + §2 | 同上 |
| TBL | TBL-001/002/003 | field-spec.md §1 | 與 ENTITY 1:1 對應 |
| FUNC | FUNC-001..045 (45 個) | functional-flow.md §1.2 [REUSE 表] | 全部行為不變；FUNC-022..045 底層 query 走 PG（FUNC-105 適配）；FUNC-045 仍硬刪 [IRREVERSIBLE REUSE]（SUG-004） |
| ROLE | ROLE-001/002/003 | BA requirement-spec.md §2 [REUSE] | 既有業務角色 |
| INV | INV-001..012 | field-spec.md §4.1 [REUSE] | 業務不變量（INV-013 WITHDRAWN — PG 原生 BOOLEAN 不需 adapter） |
| 8 個既有 pytest | `web/auth/tests/test_auth.py` | NFR-002 + AC-045 | 必須 100% 通過於 PG fixture |
| 28 個 API endpoint | TASK-001 既有 API-001..028（待 SD 階段正式登記） | NFR-002 22 AC | 外部行為完全不變 |

**[REUSE] 標記計數總計**:
- 物件級 [REUSE]: 6 MOD + 8 PATTERN + 3 ENTITY + 3 TBL + 45 FUNC + 3 ROLE + 12 INV = **80 個物件 [REUSE]**
- 標記出現次數（across SA 4 個文件）：約 30+ 個 [REUSE] 標籤（一個物件可能在多檔出現多次）

---

## 2. 共享層讀取狀態（Rule 7 / 10 / 16 / 18 對照）

| 共享層檔案 | 讀取狀態 | 內容 | 對本 TASK 影響 |
|-----------|---------|------|--------------|
| `shared/id-registry.md` | ✅ 讀取 | TASK-001 已用 ENTITY/MOD/FUNC/PATTERN/TBL/COMP/PAGE 各 1-100；本 TASK 範圍 101-200 | 本 TASK 從 101 起連續發號（Rule 13）— MOD-101..104 + FUNC-101..107 + PATTERN-101 |
| `shared/terminology.md` | ✅ 讀取 | 既有 26 條 + TASK-002 BA 階段補 8 條（ALTER TABLE try/except hack, Connection pool, DATABASE_URL, Expand-Contract, Migration, PostgreSQL 16, Railway Postgres addon, 軟刪除）| 本 TASK SA 全部 [REUSE] 既有術語 — 無新術語需登記 |
| `shared/parameter-registry.md` | ✅ 讀取 | 當前 6 個區段全空（TASK-001 未引入 env vars 到 registry） | **本 TASK FR-005 將於 SD 階段觸發** `parameter_added` 事件（5 個 POSTGRES_* 或 1 個 DATABASE_URL）— Rule 18 |
| `shared/MASTER-INDEX.md` | ✅ 讀取 | ID 規則 + 文件結構 | 遵循 Rule 8 ID 規範 |
| `shared/api-conventions.md` | ✅ 讀取（locked v1.1）| brownfield 28 endpoint grandfather | 本 TASK 不新增 endpoint；保持既有 grandfather 狀態 |
| `shared/error-codes.md` | ✅ 讀取 | 空白 | **本 TASK 預期** 引入新 ERR-AUTH-NNN 或 ERR-DB-NNN：連線失敗 / migration 失敗 — SD 階段 [BLOCKED_ON_SD] 決定具體錯誤碼語意 |
| `shared/code-registry.md` | ✅ 讀取 | TASK-001 既有 7 檔 auth/* 已登記 | 本 TASK 新增檔案預期：`migrations/`（目錄 + N 個 migration 檔 — SD 決定）+ `scripts/migrate_sqlite_to_postgres.py` |
| `shared/apps/snowboarding_support/component-index.md` | ✅ 讀取 | TASK-001 既有元件 | 本 TASK 無 UIUX 變更（NFR-002）— 不會新增 COMP |
| `shared/apps/snowboarding_support/page-index.md` | ✅ 讀取 | TASK-001 既有 8 頁 | 本 TASK 無 PAGE 變更 |
| `.sdlc/.abandoned-tasks.txt` | ✅ 檢查 | **不存在**（無放棄 TASK）| 無禁讀過濾需求（Rule 10）|

---

## 3. Conventions 對齊狀態

| Convention | 版本 | 本 TASK 對齊狀態 |
|-----------|------|----------------|
| `conventions/db-conventions.md` | v1.1 (locked 2026-06-03) | ✅ §2 (BIGINT IDENTITY / TIMESTAMPTZ) / §3 (`uniq_*` `fk_idx_*` 命名) / §4 (CASCADE 白名單) / §5 (migration 規範) / §6 (UTF8) / §8 (專案特定禁止項 — 解 3 / 4 條，留 hard-delete 給後續 TASK) 全部對齊 |
| `conventions/api-conventions.md` | v1.1 | ✅ NFR-010 env var UPPER_SNAKE_CASE + envPrefix=`POSTGRES_` 對齊；28 endpoint grandfather 不變 |
| `conventions/code-conventions.md` | v1.1 | ✅ MOD-005 內部 flat layout 仍 grandfather（baseline M-10/M-11）— 本 TASK 不重構（SA-SUG-102 留後續 TASK）|
| `conventions/i18n-conventions.md` | v1.1 | ✅ NFR-012 zh-TW 系統語言 [REUSE: TASK-001/NFR-018] — 本 TASK 無新 UI 字串 |
| `conventions/branch-conventions.md` | v1.1 | ✅ 分支 `sdlc/TASK-002/sqlite-to-postgres` base=`sdlc/TASK-001/brownfield-document` 符合命名 |

**RFC 提案**: 本 TASK SA **無** conventions 修改提案；全部 [REUSE]。

---

## 4. Parameter Registry 預期影響（Rule 18）

> **本 TASK SA 階段不直接寫 parameter_added 事件**（Rule 18 規定由 SD 寫入）；以下為 SA 對 SD 階段的預期說明:

| 參數名 | 類型 | 預期值 | Scope | Owner | 來源 FR |
|--------|------|--------|-------|-------|---------|
| `POSTGRES_HOST` | env | `localhost` (dev) / Railway 內部 host (prod) | all | be | FR-005 |
| `POSTGRES_PORT` | env | `5432` | all | be | FR-005 + config.json |
| `POSTGRES_USER` | env | (deployer 決定) | all | be | FR-005 |
| `POSTGRES_PASSWORD` | env (secret) | (Vault / Railway dashboard) | all | be | FR-005 + NFR-011 |
| `POSTGRES_DB` | env | `snowtrip` (建議命名) | all | be | FR-005 |
| `DATABASE_URL` (alt) | env (secret) | `postgresql://user:pass@host:port/db?sslmode=...` | all | be | FR-005 (替代方案 — SD 決定是否採用) |

> **SD 階段 MANDATORY**: 在 api-spec.md / db-schema.md / logic-flow.md 引入這些 env vars 時，必須執行:
> ```
> bash $HOME/.claude/skills/sdlc/scripts/sdlc-journal-write.sh \
>   TASK-002 parameter_added sd \
>   '{"paramName":"POSTGRES_HOST","paramKind":"env","paramType":"string","scope":"all","required":true,"ownerService":"be","description":"PostgreSQL host"}'
> ```
> 並依此模式為 5 個（或 1 個 DATABASE_URL）參數逐一寫入。

---

## 5. 對後續 TASK 的影響預告

> 本 TASK 是基礎設施改造，建立的 PATTERN-101 + MOD-101..104 將被後續 TASK 多次參照。

| 未來 TASK 候選 | 影響 | 標記建議 |
|--------------|------|---------|
| **`soft-delete-favorites`** (建議) | 啟動 `deleted_at` 軟刪邏輯；改寫 FUNC-045 為 `UPDATE SET deleted_at = NOW()`；所有 SELECT 加 `WHERE deleted_at IS NULL` filter | `[DEPENDS: ENTITY-001/002/003 deleted_at columns, from TASK-002]` + Rule 6 `[CROSS-TASK: TASK-001 / FUNC-045]` |
| **`add-password-reset-flow`** | 新增 `password_reset_tokens` 表 — 透過 MOD-102 migration 加表 | `[DEPENDS: PATTERN-101, MOD-102, MOD-101, from TASK-002]` |
| **`oauth-upsert-race-fix`** (SA-SUG-103) | PG `INSERT ... ON CONFLICT` 改寫 PATTERN-006 | `[EXTENDS: PATTERN-006, from TASK-001]` + `[DEPENDS: PostgreSQL backend, from TASK-002]` |
| **`auth-layering-refactor`** (SA-SUG-102) | MOD-005 內部 `{routers,services,repositories,...}` 分層 | `[EXTENDS: MOD-005, from TASK-001]` + `[BUILD-ON: MOD-103 部分封裝, from TASK-002]` |
| **任何新增 schema 變更的 TASK** | 必須走 PATTERN-101 — 不可在應用程式碼內 ALTER TABLE | 標 `[USES: PATTERN-101, from TASK-002]` |
| **任何 DROP COLUMN 的 TASK** | 必須走 Expand-Contract 三段式 | 標 `[USES: PATTERN-101 Expand-Contract, from TASK-002]` |
| **`distributed-lock-redis`** (TASK-001 SA-SUG-005) | Redis 分散式鎖取代 PATTERN-008 | 本 TASK 不影響 |
| **`hotfix/auth-security-hardening`** (TASK-001 HOTFIX-A/B/C) | Cookie Secure / SECRET_KEY fail-fast / verify admin gate | 本 TASK 不影響（範圍隔離 CONST-004）|
| **`v2-api-pluralization`** (TASK-001 BACKLOG-009) | v2 API endpoint 複數命名 | 本 TASK 不影響 |
| **`remove-flight-backend-deadcode`** (TASK-001 BACKLOG-010) | 移除 Travelpayouts/Amadeus | 本 TASK 不影響 |

---

## 6. SDLC 跨階段交付清單（給 UIUX/Deploy-init/SD 角色）

### 6.1 → UIUX 階段

| 需要本 TASK 哪些產出 | 用途 |
|-------------------|------|
| `system-arch.md` | 確認本 TASK 無 UI 變更（NFR-002 + 28 endpoint 行為不變）|
| `functional-flow.md` | 確認 FUNC-101..107 全部為基礎設施 / 部署動作，無使用者觸發的 UI 流程 |
| `impact-assessment.md`（本檔）| §5 預告：本 TASK 不會新增 PAGE / COMP |

**UIUX 行動建議**: 因本 TASK 為純後端重構，UIUX 階段可能極簡（或 PM 評估後 skip — 視 PM 決策）。若執行 UIUX，產出 `wireframes.md` / `component-spec.md` / `design-system.md` 只需聲明 `[NO_UI_CHANGE: TASK-002 為基礎設施重構，無 UI 變更 — NFR-002 強制 28 endpoint 外部行為不變]`。

### 6.2 → Deploy-init 階段

| 需要本 TASK 哪些產出 | 用途 |
|-------------------|------|
| `system-arch.md` §4 技術選型 + §7 Docker Compose | 確認 docker-compose postgres 服務啟用（FR-008）+ Railway PG provisioning 規劃（FR-006） |
| `functional-flow.md` FUNC-107 | Production cutover IRREVERSIBLE — rollback plan 必填 |
| `impact-assessment.md` §4 Parameter Registry | 5 個 env vars 預期 |
| `pattern-spec.md` §2.6 驗證要點 | 部署層測試項：smoke test 5 步驟（FR-006 AC-055）|

**Deploy-init 行動清單**:
1. `deploy/service-contract.yaml` 寫明:
   - service: snowboarding_support （現有）+ postgres （新增）
   - env vars: 5 個 POSTGRES_* + 1 個 DATABASE_URL 候選
   - rollback plan: 14 天 SQLite emergency path 保留承諾（SUG-006）
2. `deploy/deploy-env.json` 區分 dev / staging / production 的 PG 連線資訊
3. 解 [BLOCKED_ON_DEPLOYER]: Railway PG addon vs 外部託管（Supabase / Neon）

### 6.3 → SD 階段

| 需要本 TASK 哪些產出 | 用途 |
|-------------------|------|
| `system-arch.md` MOD-101..104 + PATTERN-101 | 寫 `api-spec.md` / `db-schema.md` / `code-arch.md` / `logic-flow.md` 的設計依據 |
| `functional-flow.md` 7 個 FUNC | 每個 FUNC 對應到 SD 階段的 endpoint / DB query / 程式碼路徑 |
| `field-spec.md` 三表完整欄位規格 | SD `db-schema.md` 寫完整 PostgreSQL CREATE TABLE DDL |
| `pattern-spec.md` §2.3 + §2.4 | SD 完成 migration 工具配置 + 寫 migration 檔範本 |
| `impact-assessment.md` §4 Parameter Registry | SD 執行 `sdlc-journal-write.sh parameter_added` |

**SD 階段必解 [BLOCKED_ON_SD] 清單（系統性）**:
1. Postgres driver 選型（psycopg3 / psycopg2 / asyncpg / SQLAlchemy）— BA-BC-3 + ASSUME-001 + NFR-005
2. Migration 工具選型（Alembic / yoyo-migrations / 手寫 SQL runner）— BA-BC-3 + AC-049 + PATTERN-101
3. Connection pool library + 參數調整（NFR-005 min=2/max=10 為起點）
4. Migration 觸發策略（A: startup auto / B: CI/CD 預先）— NFR-003
5. `updated_at` 刷新策略（應用層 SET vs DB trigger）— INV-101
6. SQL placeholder dialect 適配策略（`?` → `%s` 全替換 vs 適配層 helper）— FUNC-105
7. `lastrowid` 替換策略（`RETURNING id` 或 driver-specific）— FUNC-105
8. FUNC-103 / FUNC-104 是否分拆為兩個 migration（選項 A vs B）— PATTERN-101

**SD 階段必執行**:
1. `sdlc-journal-write.sh parameter_added` 寫入 5 個 POSTGRES_* （或 DATABASE_URL）
2. `db-schema.md` 寫完整 PostgreSQL CREATE TABLE + 索引 DDL
3. `api-spec.md` 確認 28 個 endpoint 簽名不變 + 標明底層 query 適配（FR-001）
4. `logic-flow.md` 寫 FUNC-101..107 完整實作流程
5. `code-arch.md` 描述 `migrations/` 目錄結構 + `scripts/migrate_sqlite_to_postgres.py` 規格

### 6.4 → Tester (test-sa) 階段

| 必驗證項 | AC / NFR / 規則 |
|---------|----------------|
| 4 個 [CROSS-TASK: TASK-001] 標記齊全 | Rule 6 |
| FUNC-107 [IRREVERSIBLE] 標記正確 + mitigation 完整 | Rule 11 |
| FUNC-045 [REUSE 嚴格邊界] 仍標 [IRREVERSIBLE] | SUG-004 + CONST-005 |
| ID 範圍合規（101-200 內 + TASK 內連續）| Rule 13 + Rule 8 |
| 6 + 8 + 3 + 3 = 80 個物件 [REUSE] 標記 | Rule 7 |
| 無腦補（每 FUNC / MOD / PATTERN 對應到 FR）| Rule 1 |
| [SA建議] 物理隔離 | Rule 2 |
| db-conventions 對齊（3 / 4 條解，1 條留後續 TASK） | Rule 16 |
| Parameter Registry 預期影響清晰 | Rule 18 |

---

## 7. 自我驗證

| 檢查項 | 通過 | 說明 |
|--------|------|------|
| 4 個 [CROSS-TASK: TASK-001] 全數落實 | ✅ | §1.1 + §1.2 |
| BA 預警 4 項 100% 對應 SA 落實 | ✅ | §1.2 |
| 80 個物件 [REUSE: from TASK-001] 標記 | ✅ | §1.3 |
| 共享層讀取狀態完整 | ✅ | §2 涵蓋 10 個共享層檔案 |
| Conventions 對齊（5 個 v1.1）| ✅ | §3 |
| Parameter Registry 預期影響清晰 | ✅ | §4 + SD 階段 mandatory 動作 |
| 後續 TASK 影響預告（10+ 候選 TASK）| ✅ | §5 |
| SDLC 跨階段交付清單（UIUX / Deploy-init / SD / Tester）| ✅ | §6 |
| **總分** | **95/100** | 詳見 `self-review.json` |
