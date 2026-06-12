---
document_id: "PATTERN-TASK-002-v1.0"
title: "架構模式規格書 — SQLite → PostgreSQL 持久化遷移"
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
  - ".sdlc/tasks/TASK-001/sa/system-arch.md (PATTERN-001..008 [REUSE])"
  - ".sdlc/conventions/db-conventions.md §5 + §8"
change_history:
  - version: "1.0"
    date: "2026-06-08"
    changes: "初始版本 — 1 個新 PATTERN-101 (Migration Versioning + Reversibility + Expand-Contract)；TASK-001 既有 PATTERN-001..008 全部 [REUSE]"
    author: "SA"
approval:
  reviewer: "PM"
  date: ""
  result: "Pending"
  notes: ""
---

# 架構模式規格書 — SQLite → PostgreSQL 持久化遷移

> **本檔用途**: 補充 system-arch.md §6 對 PATTERN 的描述，提供「跨檔通用模式」的詳細規格 — 包括跨 FUNC / 跨 MOD 引用、實作元素清單、驗證要點，作為 SD 階段實作依據。
> **編號規則**: 凡「跨 ≥2 個 FUNC 或跨 ≥1 個 module」的可識別架構模式才編號。本 TASK 識別 1 個新 PATTERN-101。
> **[REUSE] 部分**: TASK-001 PATTERN-001..008 全部不變（雪票鎖 / middleware 認證 / SSE / 多 backend fallback / 寄信 / OAuth Upsert / Cookie Auth / Per-process Lock）— 不在本檔重述。
> **ID 範圍**: 本 TASK 配額 PATTERN-101..200；本檔分配 **PATTERN-101**（單一新 PATTERN）。範圍 102-200 保留作未來擴充。

---

## 1. PATTERN 清單

### 1.1 本 TASK 新增 PATTERN

| PATTERN ID | 模式名 | 簡述 | 跨 FUNC | 跨 MOD | 觸發 FR | 觸發 NFR |
|------------|--------|------|---------|--------|---------|---------|
| **PATTERN-101** ★ NEW | Migration Versioning + Reversibility + Expand-Contract | DB schema 變更版本化追蹤；每個 migration 必須 reversible；刪欄走三段式避免破壞線上版本 | FUNC-103, FUNC-104 | MOD-102, MOD-104 | FR-003, FR-004 | NFR-006, NFR-007, NFR-008 |

### 1.2 [REUSE: from TASK-001] PATTERN 邊界

TASK-001 PATTERN-001..008 在本 TASK 部署後**機制不變**:

| TASK-001 PATTERN | 本 TASK 影響 | 狀態 |
|------------------|-------------|------|
| PATTERN-001 Lock-protected Endpoint | 與 DB 無關（雪票 lock）| [REUSE] |
| PATTERN-002 Middleware-protected Route | 與 DB 無關（middleware 認證）| [REUSE] |
| PATTERN-003 SSE Streaming Pattern | 與 DB 無關 | [REUSE] |
| PATTERN-004 Multi-backend Fallback Pattern | 機票 backend，與 DB 無關 | [REUSE] |
| PATTERN-005 3-tier Email Delivery | Email 寄送，與 DB 無關 | [REUSE] |
| PATTERN-006 OAuth Upsert Decision Tree | **使用 DB**；本 TASK SQL 適配（FUNC-105）但**決策邏輯不變**；race condition 仍存在（SA-SUG-103 留後續 TASK） | [REUSE] |
| PATTERN-007 HTTP-only Cookie Auth | 與 DB 無關（cookie 認證機制）| [REUSE] |
| PATTERN-008 Lock Scope Constraint | 與 DB 無關（部署層作用域）| [REUSE] |

---

## 2. PATTERN-101 詳細規格 ★ NEW

### 2.1 基本資訊

| 項目 | 內容 |
|------|------|
| ID | PATTERN-101 |
| 名稱 | Migration Versioning + Reversibility + Expand-Contract |
| 適用情境 | 任何持久化 schema 演進場景；尤其多環境部署（dev / staging / production）下需確保 schema 一致 |
| 對應 FR | FR-003 (Migration 工具導入), FR-004 (補軟刪欄位) |
| 對應 NFR | NFR-006 (Migration 可逆性), NFR-007 (三段式刪欄保留), NFR-008 (大表索引 CONCURRENTLY) |
| 對應 BR | BR-002 (移除 ALTER TABLE try/except hack), BR-007 (Migration 檔名格式) |
| 跨 FUNC | FUNC-103 (Schema 初始化 migration), FUNC-104 (補軟刪欄位 migration) |
| 跨 MOD | MOD-102 (migrations) 為實作載體；MOD-101 (postgres_db) 提供連線；MOD-104 (db_bootstrap) 觸發 |
| 來源 | db-conventions.md v1.1 §5（Migration 規範）+ §8（禁止項）|

### 2.2 描述

DB schema 變更不能在應用程式碼內以 `try: ALTER TABLE; except: pass` 模式進行（既有 `web/auth/database.py:44-52` 違反 db-conventions §8 第 1 條）；必須:

1. **版本化追蹤**: 每個 schema 變更為一個 migration 檔，依時間戳排序套用
2. **可逆性**: 每個 migration 必須有對應的 `down` / `rollback` 操作；測試方法：對最新 migration 跑 `up → down → up`，最終 schema 與第一次 `up` 後 100% 等價（含欄位 / 索引 / 約束）— NFR-006 驗收
3. **Expand-Contract（三段式刪欄）**: 刪除欄位**禁止**單次 migration 直接 DROP COLUMN；須走:
   - **Expand**: 新欄位先 nullable 加上 + backfill
   - **Migrate code**: 應用切換到讀寫新欄位
   - **Contract**: 確認無 reads/writes 後才 DROP 舊欄位
4. **大表索引 CONCURRENTLY**: 後續新增索引（非建表 inline）強制 `CREATE INDEX CONCURRENTLY`（PG 特性，避免鎖表）— 本 TASK 首個 migration 因建表無資料可豁免

### 2.3 實作元素

| 元素 | 規範 | [BLOCKED_ON_SD] |
|------|------|-----------------|
| Migration 檔目錄 | `migrations/`（或工具預設 — Alembic `versions/`、yoyo `migrations/`）| ⚠️ 工具決定 layout |
| 檔名格式 | `{YYYYMMDD_HHMMSS}_{verb}_{noun}.{sql\|py}`（db-conventions §5.1 + BR-007）— 範例: `20260608_120000_create_initial_schema.sql` | — |
| Verb 詞彙建議 | `create` / `add` / `drop` / `rename` / `alter`（如 `create_initial_schema`, `add_softdelete_columns`, `drop_legacy_column`）| — |
| schema_migrations 追蹤表 | 由工具自管（Alembic = `alembic_version`，yoyo = `_yoyo_migration`，手寫 = 自訂表） | ⚠️ 工具預設 |
| 工具入口配置檔 | `alembic.ini` / `yoyo.ini` / `scripts/run_migrations.py` | ⚠️ 工具決定 |
| 觸發方式 | A) startup auto-upgrade（MOD-104 啟動時 `upgrade head`）/ B) CI/CD 部署前手動觸發 | ⚠️ SD 決策（NFR-003 啟動延遲考量） |
| Reversibility 機制 | 框架方式: Alembic `def downgrade()` / yoyo `__rollback__` / 手寫 SQL `-- DOWN` 區塊或對應 `*_down.sql` | ⚠️ 工具決定 |
| 三段式刪欄序列 | 三個獨立 migration 檔依序套用（Expand → Code → Contract）| — |
| 大表索引 | 首個 migration inline 建索引（建表無資料）；後續強制 `CREATE INDEX CONCURRENTLY` | — |
| `BEGIN/COMMIT` 包裹 | 每個 migration 在 transaction 內執行（工具預設行為）；失敗 ROLLBACK | — |

### 2.4 規範性 migration 範本（給 SD 階段參考）

#### 範本 A：建表 migration（FUNC-103 對應）

```text
-- 檔名: 20260608_120000_create_initial_schema.sql
-- UP
BEGIN;
CREATE TABLE users (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    email TEXT NOT NULL,
    username TEXT NOT NULL,
    hashed_password TEXT NOT NULL DEFAULT '',
    is_verified BOOLEAN NOT NULL DEFAULT FALSE,
    google_id TEXT NULL,
    avatar_url TEXT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at TIMESTAMPTZ NULL
);
CREATE UNIQUE INDEX uniq_users_email ON users (email);
CREATE UNIQUE INDEX uniq_users_username ON users (username);
CREATE UNIQUE INDEX uniq_users_google_id ON users (google_id) WHERE google_id IS NOT NULL;
-- favorites, email_verification_tokens 類推 + FK 索引
COMMIT;

-- DOWN
BEGIN;
DROP TABLE email_verification_tokens;
DROP TABLE favorites;
DROP TABLE users;
COMMIT;
```

#### 範本 B：補欄位 migration（FUNC-104 — 選項 B 拆分時使用）

```text
-- 檔名: 20260608_130000_add_softdelete_columns.sql
-- UP
BEGIN;
ALTER TABLE users ADD COLUMN updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW();
ALTER TABLE users ADD COLUMN deleted_at TIMESTAMPTZ NULL;
ALTER TABLE favorites ADD COLUMN updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW();
ALTER TABLE favorites ADD COLUMN deleted_at TIMESTAMPTZ NULL;
ALTER TABLE email_verification_tokens ADD COLUMN created_at TIMESTAMPTZ NOT NULL DEFAULT NOW();
ALTER TABLE email_verification_tokens ADD COLUMN updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW();
ALTER TABLE email_verification_tokens ADD COLUMN deleted_at TIMESTAMPTZ NULL;
COMMIT;

-- DOWN
BEGIN;
ALTER TABLE email_verification_tokens DROP COLUMN deleted_at;
ALTER TABLE email_verification_tokens DROP COLUMN updated_at;
ALTER TABLE email_verification_tokens DROP COLUMN created_at;
ALTER TABLE favorites DROP COLUMN deleted_at;
ALTER TABLE favorites DROP COLUMN updated_at;
ALTER TABLE users DROP COLUMN deleted_at;
ALTER TABLE users DROP COLUMN updated_at;
COMMIT;
```

> **註**: 上述為**規範性範本**，非 SD 階段最終 DDL。Migration 工具若採框架方式（Alembic Python DSL）會以 `op.create_table(...)` / `op.add_column(...)` 表達，語意等價。

#### 範本 C：未來三段式刪欄序列（給後續 TASK 參考）

```text
=== Migration 1 (Expand): 20270101_120000_expand_add_new_field.sql ===
-- UP
ALTER TABLE users ADD COLUMN email_v2 TEXT NULL;  -- nullable
UPDATE users SET email_v2 = LOWER(email);          -- backfill
-- DOWN
ALTER TABLE users DROP COLUMN email_v2;

=== Migration 2 (Migrate code, 應用層 deploy): ===
-- 程式碼修改 — 所有 reads/writes 改用 email_v2；無 SQL migration
-- 至少 N 天運行確認舊 email 欄位無人讀寫

=== Migration 3 (Contract): 20270201_120000_contract_drop_legacy_email.sql ===
-- UP
ALTER TABLE users DROP COLUMN email;
ALTER TABLE users RENAME COLUMN email_v2 TO email;
-- DOWN
ALTER TABLE users RENAME COLUMN email TO email_v2;
ALTER TABLE users ADD COLUMN email TEXT;
UPDATE users SET email = email_v2;
```

### 2.5 既有 brownfield 違反處理（FR-003 / BR-002 / AC-048）

| 既有違反 | 處理動作 |
|---------|---------|
| `web/auth/database.py:44-52` 三行 `try: ALTER TABLE users ADD COLUMN ... except: pass` | **完全移除**（FUNC-105 適配 + MOD-101 重寫時刪除）— grep `'ALTER TABLE'` on `web/auth/**` 應 0 命中（AC-048）|
| 既有「應用啟動時自動 ADD COLUMN」hack | 改由 MOD-102 migration runner 在啟動時（或 CI/CD 前）正式套用 — FUNC-103 / FUNC-104 |
| migration 順序 | 確保時間戳遞增；首個 migration `20260608_xxxxxx_create_initial_schema.sql` 為最早 |

### 2.6 驗證要點（test-be / Tester 階段）

| 驗證項 | 方法 | 期望結果 | AC |
|--------|------|---------|-----|
| Migration reversibility | 對最新 migration 跑 `up → down → up`，比對 schema | 100% 等價（含欄位 / 索引 / 約束）| NFR-006 |
| 檔名格式合規 | `ls migrations/` + 正則 `^\d{8}_\d{6}_.*\.(sql\|py)$` | 全數通過 | AC-049 / BR-007 |
| 應用業務代碼無 ALTER TABLE | `grep -rn 'ALTER TABLE' web/auth/ \| grep -v migrations/` | exit 1（no match）| AC-048 |
| Reversible 機制存在 | 檢查 migration 檔含 `def downgrade()` / `-- DOWN` / `*_down.sql` | 每個 migration 對應 1 個 down 機制 | NFR-006 |
| 三段式刪欄能力 | SD 階段 db-schema.md 明示「未來 DROP COLUMN 走 expand-contract」 | 章節存在 | NFR-007 |
| 後續索引 CONCURRENTLY 規範 | SD 階段 db-schema.md 明示 | 章節存在 | NFR-008 |
| schema_migrations 表追蹤 | 套用後 `SELECT * FROM <tool_tracking_table>` 有對應 row | row 存在 | NFR-006 |

### 2.7 與其他 PATTERN 的關係

| PATTERN | 互動 |
|---------|------|
| TASK-001 PATTERN-001..008 | **無互動**（PATTERN-101 是基礎設施模式，與業務 PATTERN 隔離）|
| 未來可能引入的 Connection Pool Pattern | **[SA建議]** PATTERN-101 不涵蓋連線池策略；本 TASK 連線池由 MOD-101 內部實作（NFR-005 量化），未編為獨立 PATTERN — 理由：連線池是單一 MOD-101 內部實作細節，不跨 ≥2 FUNC 或 ≥1 MOD（PATTERN 編號規則 §1）|
| 未來可能引入的 Soft-Delete Query Rewrite Pattern | **[SA建議]** 本 TASK 補 `deleted_at` 欄位但**不啟動軟刪邏輯**（SUG-004 / CONST-005）；當後續 TASK 啟動軟刪時（如改寫 FUNC-045 為 `UPDATE SET deleted_at`），所有 SELECT 必須加 `WHERE deleted_at IS NULL` filter — 這是一個跨檔通用 query 改寫模式，建議當時編號為 PATTERN-NNN（待後續 TASK SA 決定） |

---

## 3. 候選但**未編號**為 PATTERN 的設計（SA 範圍隔離）

> **編號規則**: 跨 ≥2 FUNC 或 ≥1 MOD 才編號。以下設計**未達門檻**，故記錄於本節但不發 PATTERN-NNN。

| 候選設計 | 為何不編號 | 替代登記位置 |
|---------|----------|-------------|
| **Connection pool 策略** | 單一 MOD-101 內部實作；跨 FUNC 數 = 1（FUNC-101）| system-arch.md §5.2 NFR-005 + MOD-101 規格 |
| **健康檢查 endpoint** | 不在本 TASK FR 範圍；[SA建議] SA-SUG-101 | system-arch.md §11 |
| **`updated_at` auto-trigger** | [BLOCKED_ON_SD] 應用層手動 SET vs DB trigger — 不跨 ≥2 FUNC | field-spec.md §4.2 INV-101 |
| **Migration 觸發策略 A/B** | 部署層決策；屬 MOD-104 內部行為 | system-arch.md §3 MOD-104 + 此檔 §2.3 |
| **PG dialect 適配（`?` → `%s`）** | FUNC-105 內部實作細節；不跨 ≥2 FUNC | functional-flow.md FUNC-105 |

---

## 4. 跨 TASK 影響（PATTERN-101 對未來 TASK 的影響）

PATTERN-101 是本 TASK 引入的**基礎設施模式**，後續 TASK 涉及 schema 變更時必須遵守:

| 未來 TASK 行為 | 必須遵守 PATTERN-101 |
|--------------|-------------------|
| 新增欄位 | 新建 migration 檔，不可在 `database.py` 內 ALTER TABLE |
| 刪除欄位 | 走三段式 Expand-Contract，不可單次 DROP COLUMN |
| 新增索引 | `CREATE INDEX CONCURRENTLY`（大表）|
| Refactor schema | 每個變更 reversible（up + down 對稱）|
| Soft-delete 啟用（建議的 `soft-delete-favorites` TASK） | 配 migration 改寫 FUNC-045 + 應用層 SELECT 加 filter；PATTERN-101 仍適用 |

---

## 5. 自我驗證（摘要）

| 檢查項 | 通過 | 說明 |
|--------|------|------|
| PATTERN-101 跨 ≥2 FUNC ✅ | ✅ | FUNC-103 + FUNC-104 |
| PATTERN-101 跨 ≥1 MOD ✅ | ✅ | MOD-102 + MOD-104 |
| PATTERN-101 有對應 FR / NFR / BR | ✅ | FR-003/004 / NFR-006/007/008 / BR-002/007 |
| 編號正確（範圍 101-200 內 + TASK 內連續）| ✅ | PATTERN-101 是第一個 |
| TASK-001 PATTERN [REUSE] 邊界明示 | ✅ | §1.2 8 個 PATTERN 表 |
| 規範性範本與 db-conventions §5 對齊 | ✅ | §2.4 範本 A/B/C 對齊 §5.1/5.2/5.3 |
| brownfield 違反處理明示（FR-003 / AC-048）| ✅ | §2.5 |
| 候選但未編號的設計記錄 | ✅ | §3 5 個候選說明 |
| 範圍邊界（不選工具 / 不寫完整 DDL）| ✅ | §2.3 多處 [BLOCKED_ON_SD]；§2.4 標「規範性範本」 |
| 與 TASK-001 PATTERN 互動明示 | ✅ | §2.7 |
| **總分** | **93/100** | 詳見 self-review.json |
