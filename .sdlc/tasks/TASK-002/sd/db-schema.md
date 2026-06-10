---
document_id: "DB-TASK-002-v1.0"
title: "資料庫 Schema 設計 — SQLite → PostgreSQL 持久化遷移"
version: "1.0"
date: "2026-06-10"
author: "SD"
task_id: "TASK-002"
phase: "sd"
mode: "feature"
source_documents:
  - "REQ-TASK-002-v1.0"
  - "FIELD-TASK-002-v1.0 (SA field-spec.md)"
  - "FUNC-TASK-002-v1.0 (SA functional-flow.md — FUNC-103/104)"
  - "PATTERN-TASK-002-v1.0 (SA pattern-spec.md — PATTERN-101)"
  - ".sdlc/conventions/db-conventions.md v1.1 §2/§3/§4/§5/§6/§8"
  - "web/auth/database.py (既有 SQLite schema — 對照真相基線)"
  - "deploy/service-contract.yaml (env var 名稱)"
  - "deploy/parameter-plan.md (12 個 parameter_added)"
change_history:
  - version: "1.0"
    date: "2026-06-10"
    changes: "初始版本 — 3 TBL [REUSE] 在 PG 完整 DDL + 6 索引 + 2 FK 索引 + 1 schema_migrations + 2 migration 檔規範（FUNC-103/104 拆分為兩個 migration / 選項 B）+ updated_at trigger 應用層策略 + dialect 適配規則 + Expand-Contract 章節 + 索引 CONCURRENTLY 規範"
    author: "SD"
approval:
  reviewer: "PM"
  date: ""
  result: "Pending"
  notes: ""
---

# 資料庫 Schema 設計 — SQLite → PostgreSQL 持久化遷移

> **模式**: feature — 純後端基礎設施重構（SQLite → PostgreSQL 16）；**0 新 TBL**（3 個 [REUSE: from TASK-001]）；**5 新欄位**（updated_at×3 + deleted_at×3 + created_at×1，符合 SA field-spec.md §2）。
> **本檔負責**: 將 SA field-spec.md「規範性語意」轉為**可直接執行的 PostgreSQL 16 DDL**；定義 migration 檔順序 + reversibility + Expand-Contract 章節（NFR-007）+ 後續索引 CONCURRENTLY 規範（NFR-008）。
> **ID 範圍**: TBL 配額 101-200 — **本 TASK 未使用 TBL 範圍**（3 個 TBL 全部 [REUSE: TBL-001/002/003, from TASK-001]）。範圍保留作未來擴充。

---

## 1. 設計決策摘要（[BLOCKED_ON_SD] 解答）

> SA test-sa 提了 8 個 [BLOCKED_ON_SD]，與本 db-schema 直接相關的決策：

| # | 項目 | 決策 | 理由 |
|---|------|------|------|
| 5 | FUNC-103 / FUNC-104 是否拆分 | **拆（選項 B）** | (1) 跨 TASK 修改 TBL-001/002/003 補欄位的事件須獨立追蹤（Rule 6 / Rule 11.1 變體可逆 ALTER COLUMN）；(2) 後續 TASK 引用 deleted_at 時可精準指 `20260610_120100_add_softdelete_columns.sql`；(3) 部署到既有 production（即使 ephemeral 已空）若**將來**有人手動載入 SQLite snapshot 走 FUNC-106，補欄位 migration 可獨立重跑 |
| 6 | updated_at 刷新策略（trigger / app / both）| **App-level（應用層）— 不用 DB trigger** | (1) BR-001 schema 邏輯結構不變（trigger 雖然不算 schema 邏輯但屬於行為層注入，會讓既有 7 檔的 SELECT/UPDATE 行為「不可見地」改變）；(2) MOD-103 auth_repositories 是引入 helper 的天然位置，每次 UPDATE 補 `, updated_at = NOW()`；(3) trigger 對 unit test 不友善（mock DB 時 trigger 不會跑）；(4) [BLOCKED_ON_DEPLOYER] Railway 自建 container 內 trigger 安裝多一道風險；(5) SA-SUG-FS-102 已明示「不預設選 trigger」 |
| 7 | placeholder dialect（`?` → `%s`）| **全替換為 `%s`（psycopg3 風格）** | (1) 不另寫 dialect 適配層 — 7 個檔總計約 30 個 query，IDE 一次性 find-replace 風險可控；(2) 適配層額外抽象增加 cognitive load 對未來新人不友善；(3) `%s` 是 PEP 249（DB-API 2.0）大多數 PG driver 標準；(4) 符合 code-conventions.md §7 「禁止 magic numbers」精神（少一層抽象 = 少一層魔法）|
| 8 | lastrowid 替換策略 | **`RETURNING id` clause** | (1) PG 原生 SQL 支援，零 driver 依賴；(2) 比 driver-specific 屬性（如 psycopg cursor.lastrowid 仿真）顯式、可測；(3) 既有用到 lastrowid 處（`auth_router.py:98` 註冊時取 user_id）可直接 `INSERT ... RETURNING id` 後 `cur.fetchone()[0]` |

> 完整 8 個 [BLOCKED_ON_SD] 在 `code-arch.md` §1 「設計決策摘要」統一回應；本表只列與 schema 直接相關的 4 個。

---

## 2. PostgreSQL Schema DDL（完整可執行）

> **目標版本**: PostgreSQL 16（config.json `techStack.database.image = postgres:16-alpine`）
> **規範依據**: db-conventions.md v1.1 §2 (BIGINT IDENTITY / TIMESTAMPTZ) / §3 (索引命名 `uniq_*` `fk_idx_*`) / §4 (FK 顯式命名 + CASCADE 白名單) / §6 (UTF8)
> **既有對照**: `web/auth/database.py:17-43`（13 行既有 SQLite schema）

### 2.1 TBL-001: users（[REUSE: from TASK-001]）

```sql
-- migration: 20260610_120000_create_initial_schema.sql (FUNC-103)
CREATE TABLE users (
    id              BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    email           TEXT NOT NULL,
    username        TEXT NOT NULL,
    hashed_password TEXT NOT NULL DEFAULT '',
    is_verified     BOOLEAN NOT NULL DEFAULT FALSE,
    google_id       TEXT NULL,
    avatar_url      TEXT NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- migration: 20260610_120100_add_softdelete_columns.sql (FUNC-104)
ALTER TABLE users
    ADD COLUMN updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    ADD COLUMN deleted_at TIMESTAMPTZ NULL;

-- 索引（migration: 20260610_120000_create_initial_schema.sql 內聯）
CREATE UNIQUE INDEX uniq_users_email
    ON users (email);

CREATE UNIQUE INDEX uniq_users_username
    ON users (username);

CREATE UNIQUE INDEX uniq_users_google_id
    ON users (google_id)
    WHERE google_id IS NOT NULL;  -- PostgreSQL partial unique index
```

**欄位明細**:

| 欄位 | PG 型別 | NULL | 預設 | 約束 | 索引 | 來源 |
|------|---------|------|------|------|------|------|
| id | `BIGINT GENERATED ALWAYS AS IDENTITY` | NOT NULL | identity | PRIMARY KEY | 隱式 PK | TASK-001 + BR-005 |
| email | `TEXT` | NOT NULL | — | UNIQUE | `uniq_users_email` | TASK-001 + BR-004 |
| username | `TEXT` | NOT NULL | — | UNIQUE | `uniq_users_username` | TASK-001 |
| hashed_password | `TEXT` | NOT NULL | `''` | — | — | TASK-001 |
| is_verified | `BOOLEAN` | NOT NULL | `FALSE` | — | — | TASK-001 |
| google_id | `TEXT` | NULL | NULL | UNIQUE (partial) | `uniq_users_google_id WHERE google_id IS NOT NULL` | TASK-001 |
| avatar_url | `TEXT` | NULL | NULL | — | — | TASK-001 |
| created_at | `TIMESTAMPTZ` | NOT NULL | `NOW()` | — | — | TASK-001 + BR-006 |
| **updated_at** | `TIMESTAMPTZ` | NOT NULL | `NOW()` | — | — | ★ **NEW** FR-004 + BR-006 |
| **deleted_at** | `TIMESTAMPTZ` | NULL | NULL | — | — | ★ **NEW** FR-004 |

### 2.2 TBL-002: favorites（[REUSE: from TASK-001]）

```sql
-- migration: 20260610_120000_create_initial_schema.sql (FUNC-103)
CREATE TABLE favorites (
    id         BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    user_id    BIGINT NOT NULL,
    type       TEXT NOT NULL,
    data       TEXT NOT NULL,
    label      TEXT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_favorites_user_id_users
        FOREIGN KEY (user_id) REFERENCES users(id)
        ON DELETE CASCADE
        ON UPDATE CASCADE
);

-- migration: 20260610_120100_add_softdelete_columns.sql (FUNC-104)
ALTER TABLE favorites
    ADD COLUMN updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    ADD COLUMN deleted_at TIMESTAMPTZ NULL;

-- FK 索引（PG 不自動建 — db-conventions §3 必須顯式）
CREATE INDEX fk_idx_favorites_user_id
    ON favorites (user_id);
```

**欄位明細**:

| 欄位 | PG 型別 | NULL | 預設 | 約束 | 索引 | 來源 |
|------|---------|------|------|------|------|------|
| id | `BIGINT GENERATED ALWAYS AS IDENTITY` | NOT NULL | identity | PRIMARY KEY | 隱式 | TASK-001 |
| user_id | `BIGINT` | NOT NULL | — | FK → users(id) ON DELETE CASCADE | `fk_idx_favorites_user_id` | TASK-001 + BR-010 |
| type | `TEXT` | NOT NULL | — | 應用層白名單 `('ski','flight')` | — | TASK-001 + INV-007 |
| data | `TEXT` | NOT NULL | — | — | — | TASK-001 |
| label | `TEXT` | NULL | NULL | — | — | TASK-001 |
| created_at | `TIMESTAMPTZ` | NOT NULL | `NOW()` | — | — | TASK-001 + BR-006 |
| **updated_at** | `TIMESTAMPTZ` | NOT NULL | `NOW()` | — | — | ★ **NEW** FR-004 |
| **deleted_at** | `TIMESTAMPTZ` | NULL | NULL | — | — | ★ **NEW** FR-004（本 TASK 不啟動軟刪 — SUG-004） |

### 2.3 TBL-003: email_verification_tokens（[REUSE: from TASK-001]）

```sql
-- migration: 20260610_120000_create_initial_schema.sql (FUNC-103)
CREATE TABLE email_verification_tokens (
    id         BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    user_id    BIGINT NOT NULL,
    token      TEXT NOT NULL,
    expires_at TIMESTAMPTZ NOT NULL,
    used_at    TIMESTAMPTZ NULL,

    CONSTRAINT fk_email_verification_tokens_user_id_users
        FOREIGN KEY (user_id) REFERENCES users(id)
        ON DELETE CASCADE
        ON UPDATE CASCADE
);

-- migration: 20260610_120100_add_softdelete_columns.sql (FUNC-104)
ALTER TABLE email_verification_tokens
    ADD COLUMN created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),  -- ★ 補 TASK-001 baseline gap
    ADD COLUMN updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    ADD COLUMN deleted_at TIMESTAMPTZ NULL;

-- 索引
CREATE UNIQUE INDEX uniq_email_verification_tokens_token
    ON email_verification_tokens (token);

CREATE INDEX fk_idx_email_verification_tokens_user_id
    ON email_verification_tokens (user_id);
```

**欄位明細**:

| 欄位 | PG 型別 | NULL | 預設 | 約束 | 索引 | 來源 |
|------|---------|------|------|------|------|------|
| id | `BIGINT GENERATED ALWAYS AS IDENTITY` | NOT NULL | identity | PRIMARY KEY | 隱式 | TASK-001 |
| user_id | `BIGINT` | NOT NULL | — | FK → users(id) ON DELETE CASCADE | `fk_idx_email_verification_tokens_user_id` | TASK-001 |
| token | `TEXT` | NOT NULL | — | UNIQUE | `uniq_email_verification_tokens_token` | TASK-001 |
| expires_at | `TIMESTAMPTZ` | NOT NULL | — | — | — | TASK-001 + BR-006 |
| used_at | `TIMESTAMPTZ` | NULL | NULL | — | — | TASK-001 + BR-007 |
| **created_at** | `TIMESTAMPTZ` | NOT NULL | `NOW()` | — | — | ★ **NEW** 補 baseline gap（field-spec §6 標明 TASK-001 缺）|
| **updated_at** | `TIMESTAMPTZ` | NOT NULL | `NOW()` | — | — | ★ **NEW** FR-004 |
| **deleted_at** | `TIMESTAMPTZ` | NULL | NULL | — | — | ★ **NEW** FR-004 |

### 2.4 schema_migrations 追蹤表（Alembic 自管）

```sql
-- Alembic 自動建立（首次 alembic upgrade head 時）
CREATE TABLE alembic_version (
    version_num VARCHAR(32) NOT NULL,
    CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
);
```

> **註**: 此表由 Alembic 工具自管，SD 不需手寫 DDL；列在本檔僅為「事實揭露」+ 供 deploy/test-be 階段檢查存在性。

---

## 3. SQLite → PostgreSQL 既有 schema 對照表（diff 視角）

> **目的**: 給 Code Review / Tester / BE 一份精確的「改了什麼」清單；對照真相 = `web/auth/database.py:17-43`（13 行原始 schema）。

| 表 / 欄位 | SQLite 既有 (`database.py:17-43`) | PostgreSQL 目標 | 差異類型 |
|----------|----------------------------------|----------------|---------|
| **users.id** | `INTEGER PRIMARY KEY AUTOINCREMENT` | `BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY` | 型別變更（grandfather → BR-005） |
| **users.email** | `TEXT UNIQUE NOT NULL`（隱式索引名）| `TEXT NOT NULL` + `CREATE UNIQUE INDEX uniq_users_email` | 索引顯式命名（修正 baseline M-9） |
| **users.username** | `TEXT UNIQUE NOT NULL`（隱式索引）| `TEXT NOT NULL` + `uniq_users_username` | 同上 |
| **users.hashed_password** | `TEXT NOT NULL DEFAULT ''` | `TEXT NOT NULL DEFAULT ''` | 無變化 |
| **users.is_verified** | `BOOLEAN NOT NULL DEFAULT 0`（SQLite 實存 0/1）| `BOOLEAN NOT NULL DEFAULT FALSE` | PG 原生 BOOLEAN — 應用層移除 `bool()` adapter（FUNC-105 / `verify_client.py:77`） |
| **users.google_id** | `TEXT UNIQUE`（NULL 允許 + UNIQUE 隱式）| `TEXT NULL` + `uniq_users_google_id WHERE google_id IS NOT NULL`（partial）| PG 必須 partial 才能讓多個 NULL 共存 |
| **users.avatar_url** | `TEXT` | `TEXT NULL` | 無變化（NULL 顯式） |
| **users.created_at** | `TIMESTAMP DEFAULT CURRENT_TIMESTAMP`（ISO 字串）| `TIMESTAMPTZ NOT NULL DEFAULT NOW()` | 型別變更 + 加 NOT NULL — 比較不再依賴字串字典序（FUNC-105 / `auth_router.py:157`） |
| **users.updated_at** | ❌ **缺** | `TIMESTAMPTZ NOT NULL DEFAULT NOW()` | ★ **新增**（FR-004 / 解 baseline M-8） |
| **users.deleted_at** | ❌ **缺** | `TIMESTAMPTZ NULL` | ★ **新增**（FR-004） |
| **favorites.id** | `INTEGER PRIMARY KEY AUTOINCREMENT` | `BIGINT IDENTITY PRIMARY KEY` | 型別變更 |
| **favorites.user_id** | `INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE`（inline FK，無顯式索引）| `BIGINT NOT NULL` + `CONSTRAINT fk_favorites_user_id_users FK ON DELETE CASCADE ON UPDATE CASCADE` + `CREATE INDEX fk_idx_favorites_user_id` | FK 顯式命名 + FK 索引顯式建（PG 不自動 — 修正 baseline M-9） |
| **favorites.type** | `TEXT NOT NULL` | `TEXT NOT NULL`（應用層白名單）| 無變化（BR-001 schema 邏輯不變） |
| **favorites.data** | `TEXT NOT NULL` | `TEXT NOT NULL` | 無變化（SA-SUG-FS-101 改 JSONB 留後續 TASK） |
| **favorites.label** | `TEXT` | `TEXT NULL` | 無變化 |
| **favorites.created_at** | `TIMESTAMP DEFAULT CURRENT_TIMESTAMP` | `TIMESTAMPTZ NOT NULL DEFAULT NOW()` | 型別變更 |
| **favorites.updated_at** | ❌ **缺** | `TIMESTAMPTZ NOT NULL DEFAULT NOW()` | ★ **新增**（FR-004） |
| **favorites.deleted_at** | ❌ **缺** | `TIMESTAMPTZ NULL` | ★ **新增**（FR-004，本 TASK 不啟動軟刪 — SUG-004） |
| **email_verification_tokens.id** | `INTEGER PRIMARY KEY AUTOINCREMENT` | `BIGINT IDENTITY PRIMARY KEY` | 型別變更 |
| **email_verification_tokens.user_id** | `INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE` | `BIGINT NOT NULL` + 顯式 FK 命名 + 顯式 FK 索引 | 同 favorites.user_id |
| **email_verification_tokens.token** | `TEXT UNIQUE NOT NULL`（隱式索引）| `TEXT NOT NULL` + `uniq_email_verification_tokens_token` | 索引顯式命名 |
| **email_verification_tokens.expires_at** | `TIMESTAMP NOT NULL`（ISO 字串）| `TIMESTAMPTZ NOT NULL` | 型別變更 — PG 原生時間比較（修正既有 `auth_router.py:157` 字典序 hack） |
| **email_verification_tokens.used_at** | `TIMESTAMP DEFAULT NULL` | `TIMESTAMPTZ NULL` | 型別變更 |
| **email_verification_tokens.created_at** | ❌ **缺**（TASK-001 baseline gap）| `TIMESTAMPTZ NOT NULL DEFAULT NOW()` | ★ **新增**（補 baseline gap） |
| **email_verification_tokens.updated_at** | ❌ **缺** | `TIMESTAMPTZ NOT NULL DEFAULT NOW()` | ★ **新增**（FR-004） |
| **email_verification_tokens.deleted_at** | ❌ **缺** | `TIMESTAMPTZ NULL` | ★ **新增**（FR-004） |
| **`database.py:44-52`** ALTER TABLE try/except hack | 3 行 ALTER TABLE 在 try/except 寬鬆吞例外 | ❌ **完全刪除**（FR-003 + AC-048 + PATTERN-101 §2.5）| 移除（移到 MOD-102 migration 正式管理） |

**Diff 統計**:
- 型別變更: 9 個欄位（PK / FK / TIMESTAMP / BOOLEAN）
- 新增欄位: 7 個（updated_at×3 + deleted_at×3 + created_at×1）
- 索引重命名: 4 個 UNIQUE（隱式 → 顯式）+ 2 個 FK（缺 → 補）
- 刪除 hack: 9 行（`database.py:44-52`）

---

## 4. Migration 檔順序

> **工具**: Alembic（選型理由見 `code-arch.md` §1.2）
> **目錄**: `migrations/versions/`（Alembic 預設 layout）
> **檔名格式**: `{YYYYMMDD_HHMMSS}_{verb}_{noun}.py`（符合 db-conventions §5.1 + BR-007；Alembic 預設用 Python 而非 .sql，semantically 等價）

### 4.1 Migration 順序表

| # | 檔名（Alembic revision）| 觸發 FUNC | 操作 | 觸發 FR |
|---|--------------------------|---------|------|---------|
| 1 | `20260610_120000_create_initial_schema.py` | FUNC-103 | CREATE 3 表 + 4 UNIQUE 索引 + 2 FK 索引 + 2 FK 約束 | FR-002, FR-003 |
| 2 | `20260610_120100_add_softdelete_columns.py` | FUNC-104 | ALTER 3 表 ADD COLUMN（updated_at×3 + deleted_at×3 + created_at×1 = 7 欄）| FR-004 |

### 4.2 Migration 1 範本（FUNC-103）

```python
"""create initial schema

Revision ID: 20260610_120000
Revises: None
Create Date: 2026-06-10 12:00:00
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = "20260610_120000"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ---- users ----
    op.create_table(
        "users",
        sa.Column("id", sa.BigInteger,
                  sa.Identity(always=True, start=1), primary_key=True),
        sa.Column("email",           sa.Text, nullable=False),
        sa.Column("username",        sa.Text, nullable=False),
        sa.Column("hashed_password", sa.Text, nullable=False, server_default=""),
        sa.Column("is_verified",     sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("google_id",       sa.Text, nullable=True),
        sa.Column("avatar_url",      sa.Text, nullable=True),
        sa.Column("created_at",      sa.TIMESTAMP(timezone=True),
                  nullable=False, server_default=sa.func.now()),
    )
    op.create_index("uniq_users_email",    "users", ["email"],    unique=True)
    op.create_index("uniq_users_username", "users", ["username"], unique=True)
    op.create_index("uniq_users_google_id", "users", ["google_id"],
                    unique=True, postgresql_where=sa.text("google_id IS NOT NULL"))

    # ---- favorites ----
    op.create_table(
        "favorites",
        sa.Column("id", sa.BigInteger,
                  sa.Identity(always=True, start=1), primary_key=True),
        sa.Column("user_id", sa.BigInteger, nullable=False),
        sa.Column("type",    sa.Text, nullable=False),
        sa.Column("data",    sa.Text, nullable=False),
        sa.Column("label",   sa.Text, nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True),
                  nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"],
            name="fk_favorites_user_id_users",
            ondelete="CASCADE", onupdate="CASCADE",
        ),
    )
    op.create_index("fk_idx_favorites_user_id", "favorites", ["user_id"])

    # ---- email_verification_tokens ----
    op.create_table(
        "email_verification_tokens",
        sa.Column("id", sa.BigInteger,
                  sa.Identity(always=True, start=1), primary_key=True),
        sa.Column("user_id",    sa.BigInteger, nullable=False),
        sa.Column("token",      sa.Text, nullable=False),
        sa.Column("expires_at", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("used_at",    sa.TIMESTAMP(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"],
            name="fk_email_verification_tokens_user_id_users",
            ondelete="CASCADE", onupdate="CASCADE",
        ),
    )
    op.create_index("uniq_email_verification_tokens_token",
                    "email_verification_tokens", ["token"], unique=True)
    op.create_index("fk_idx_email_verification_tokens_user_id",
                    "email_verification_tokens", ["user_id"])


def downgrade() -> None:
    # 順序：依 FK 從葉到根
    op.drop_index("fk_idx_email_verification_tokens_user_id",
                  table_name="email_verification_tokens")
    op.drop_index("uniq_email_verification_tokens_token",
                  table_name="email_verification_tokens")
    op.drop_table("email_verification_tokens")

    op.drop_index("fk_idx_favorites_user_id", table_name="favorites")
    op.drop_table("favorites")

    op.drop_index("uniq_users_google_id", table_name="users")
    op.drop_index("uniq_users_username",  table_name="users")
    op.drop_index("uniq_users_email",     table_name="users")
    op.drop_table("users")
```

### 4.3 Migration 2 範本（FUNC-104）

```python
"""add softdelete columns

Revision ID: 20260610_120100
Revises: 20260610_120000
Create Date: 2026-06-10 12:01:00
"""
from alembic import op
import sqlalchemy as sa

revision = "20260610_120100"
down_revision = "20260610_120000"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # users: + updated_at + deleted_at
    op.add_column("users",
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True),
                  nullable=False, server_default=sa.func.now()))
    op.add_column("users",
        sa.Column("deleted_at", sa.TIMESTAMP(timezone=True), nullable=True))

    # favorites: + updated_at + deleted_at
    op.add_column("favorites",
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True),
                  nullable=False, server_default=sa.func.now()))
    op.add_column("favorites",
        sa.Column("deleted_at", sa.TIMESTAMP(timezone=True), nullable=True))

    # email_verification_tokens: + created_at (補 baseline gap) + updated_at + deleted_at
    op.add_column("email_verification_tokens",
        sa.Column("created_at", sa.TIMESTAMP(timezone=True),
                  nullable=False, server_default=sa.func.now()))
    op.add_column("email_verification_tokens",
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True),
                  nullable=False, server_default=sa.func.now()))
    op.add_column("email_verification_tokens",
        sa.Column("deleted_at", sa.TIMESTAMP(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column("email_verification_tokens", "deleted_at")
    op.drop_column("email_verification_tokens", "updated_at")
    op.drop_column("email_verification_tokens", "created_at")
    op.drop_column("favorites", "deleted_at")
    op.drop_column("favorites", "updated_at")
    op.drop_column("users", "deleted_at")
    op.drop_column("users", "updated_at")
```

> **註**: Migration 2 的 downgrade 對 `email_verification_tokens.created_at` 雖然是 hard drop，但因本 TASK 部署到 production 時三表為空（FR-007 §業務影響說明），downgrade 不會丟失歷史資料；本機 / staging 若已 backfill 則 downgrade 會丟欄位 — 屬於合理 trade-off 並由 Expand-Contract（§5）保護未來變更。

### 4.4 Migration Reversibility 自我驗證（NFR-006）

| 驗證項 | 方法 | 期望 |
|--------|------|------|
| Migration 1 up→down→up | `alembic upgrade head && alembic downgrade base && alembic upgrade head` | schema 與第一次 up 後 100% 等價（含欄位 / 索引 / 約束）|
| Migration 2 up→down→up | 同上跑到 head 後 `alembic downgrade -1 && alembic upgrade head` | 同上 |
| 檔名格式合規 | `ls migrations/versions/` + 正則 `^\d{8}_\d{6}_.*\.py$` | 2 個檔皆通過 |
| Reversible 機制 | 每個 migration 都有 `downgrade()` 函式 | 2 個檔皆通過 |
| schema_migrations 表追蹤 | `SELECT version_num FROM alembic_version` | upgrade head 後查詢有對應 row |

---

## 5. Expand-Contract（三段式刪欄協議）章節（NFR-007）

> **適用**: 未來 TASK 若需 DROP COLUMN（如後續移除 `is_verified` 改為 `verified_at` 時間戳語意），**必須**走以下三段式；不可單次 migration 直接 `DROP COLUMN`。
> **依據**: db-conventions.md §5.3 + PATTERN-101 §2.3 + NFR-007

### 5.1 三段式定義

| 階段 | 動作 | Migration 檔 | 應用層動作 |
|------|------|------------|----------|
| **Expand** | 新欄位 nullable 加上 + backfill | 1 個 migration（含 `ADD COLUMN` + `UPDATE backfill`）| 應用層仍讀舊欄 |
| **Migrate code** | 應用層改讀寫新欄位 | （無 SQL migration — 純應用層 deploy）| 至少 N 天觀察期 |
| **Contract** | DROP 舊欄位 + RENAME 新欄位 | 1 個 migration（含 `DROP COLUMN` + `RENAME`）| 完成 |

### 5.2 範本（給後續 TASK 參考）

```text
=== Migration A (Expand): 20270101_120000_expand_add_verified_at.py ===
def upgrade():
    op.add_column("users", sa.Column("verified_at",
                  sa.TIMESTAMP(timezone=True), nullable=True))
    op.execute("UPDATE users SET verified_at = NOW() "
               "WHERE is_verified = TRUE AND verified_at IS NULL")

def downgrade():
    op.drop_column("users", "verified_at")


=== Migration B (Migrate code, 應用層 deploy)：無 SQL ===
- 全部 reads 改為 verified_at IS NOT NULL
- 全部 writes 改為 SET verified_at = NOW()
- 至少 14 天觀察期，確認舊欄位無人讀寫
- 監控應用層 log: 無 reads_legacy_is_verified 計數累積


=== Migration C (Contract): 20270201_120000_contract_drop_is_verified.py ===
def upgrade():
    op.drop_column("users", "is_verified")

def downgrade():
    op.add_column("users", sa.Column("is_verified",
                  sa.Boolean, nullable=False, server_default=sa.false()))
    op.execute("UPDATE users SET is_verified = (verified_at IS NOT NULL)")
```

### 5.3 三段式驗證要點

| 驗證項 | 期望 |
|--------|------|
| Expand 階段不破壞既有 reads/writes | 既有所有 query 仍走得通 |
| Migrate 階段無 SQL migration | 純應用層改寫 + N 天監控 |
| Contract 階段執行前確認舊欄位無 reads | grep / log 計數 = 0 持續 N 天 |
| 三個 migration 各自 reversible | up→down→up 等價 |

---

## 6. 索引 CONCURRENTLY 規範（NFR-008）

> **本 TASK 例外**: Migration 1（首個建表 migration）因建表時表內無資料、無讀寫，可 inline 建索引（Alembic `op.create_index` 預設行為），不強制 CONCURRENTLY。
> **後續 TASK 規範**: 任何**非建表 migration**新增索引必須走 CONCURRENTLY 避免鎖表（PostgreSQL 特性）。

### 6.1 後續索引新增範本

```python
# ❌ 禁止: 在 transaction 內鎖表
def upgrade():
    op.create_index("idx_users_created_at", "users", ["created_at"])
    # ↑ Alembic 預設在 transaction 內執行 → 鎖表

# ✅ 正確: CONCURRENTLY + 跳 transaction
def upgrade():
    # Alembic 需顯式關閉 transaction（PG CONCURRENTLY 不能在 transaction 內）
    with op.get_context().autocommit_block():
        op.execute("CREATE INDEX CONCURRENTLY idx_users_created_at ON users (created_at)")

def downgrade():
    with op.get_context().autocommit_block():
        op.execute("DROP INDEX CONCURRENTLY idx_users_created_at")
```

### 6.2 例外清單

| 情境 | CONCURRENTLY 強制 | 理由 |
|------|------------------|------|
| 建表 migration inline 建索引 | ❌ 例外 | 表內無資料、無讀寫，無鎖表風險 |
| Migration 1（FUNC-103）內的 4 個 UNIQUE 索引 + 2 個 FK 索引 | ❌ 例外 | 同上 — 本 TASK 部署時三表為空 |
| 後續 TASK 任何 `CREATE INDEX` | ✅ 強制 | 既有資料可能大量、避免鎖表 |
| `CREATE UNIQUE INDEX CONCURRENTLY` 失敗（重複值）| 強制檢查 | INVALID 索引需手動 DROP + 重建 |

---

## 7. updated_at 應用層刷新規範（決策 #6）

> **決策**: App-level（應用層） — **不用 DB trigger**。每次 UPDATE 都必須在 SET 子句中包含 `updated_at = NOW()`。
> **實作位置**: MOD-103 `auth_repositories.py` 的 helper 函式（詳見 `code-arch.md`）。
> **驗證**: BE/Tester 階段 grep `UPDATE.*SET` 對應 `updated_at`。

### 7.1 範本

```python
# ❌ 錯誤: 漏 SET updated_at
def update_user_username(conn, user_id: int, username: str) -> None:
    conn.execute(
        "UPDATE users SET username = %s WHERE id = %s",
        (username, user_id),
    )

# ✅ 正確: SET updated_at
def update_user_username(conn, user_id: int, username: str) -> None:
    conn.execute(
        "UPDATE users SET username = %s, updated_at = NOW() WHERE id = %s",
        (username, user_id),
    )
```

### 7.2 INV-101 落實機制

| 機制 | 採納？ | 理由 |
|------|--------|------|
| DB trigger（`BEFORE UPDATE`）| ❌ | (1) BR-001 schema 邏輯不變優先；(2) trigger 對單元測試不友善；(3) Railway 自建 container 內裝 trigger 多一道風險；(4) SA-SUG-FS-102 已明示不預設選 trigger |
| 應用層手動 SET（本 TASK 採納）| ✅ | (1) 顯式可審查；(2) Test 階段易 mock；(3) MOD-103 `auth_repositories.py` 集中封裝 — 開發者寫 helper 時注入；(4) lint rule 可後續加 — `[SD建議]` 留 PR 14d 自動檢查 |

### 7.3 受影響的既有 UPDATE 位置（BE 階段必檢查）

| 檔案 | 行 | UPDATE 描述 | 需補 `SET updated_at = NOW()` ？ |
|------|-----|------------|------------------------------|
| `web/auth/auth_router.py` | 重寄驗證信 FUNC-034 (UPDATE email_verification_tokens used_at) | UPDATE email_verification_tokens SET used_at | ✅ |
| `web/auth/auth_router.py` | Email 驗證 FUNC-033 (UPDATE users is_verified + email_verification_tokens used_at) | 2 處 UPDATE 都要補 | ✅ |
| `web/auth/oauth_router.py` | OAuth Upsert FUNC-035 (UPDATE users google_id / avatar_url) | UPDATE users SET google_id, avatar_url | ✅ |

> 完整清單由 BE 階段 grep `UPDATE\s+\w+\s+SET` 萃取補齊。

---

## 8. Dialect 適配規範（決策 #7）

> **決策**: 全替換 `?` → `%s`（psycopg3 風格），不另寫 dialect 適配層。

### 8.1 替換規則

| SQLite 既有 | PG 替換 | 範例 |
|------------|--------|------|
| `?` placeholder | `%s` | `SELECT * FROM users WHERE id = ?` → `SELECT * FROM users WHERE id = %s` |
| `cursor.lastrowid` | `INSERT ... RETURNING id` + `cur.fetchone()[0]` | `cur = conn.execute("INSERT INTO users (...) VALUES (?, ?, ?, ?)"); user_id = cur.lastrowid` → `cur = conn.execute("INSERT INTO users (...) VALUES (%s, %s, %s, %s) RETURNING id"); user_id = cur.fetchone()[0]` |
| `bool(d.get("is_verified", 1))` adapter | 移除 adapter — PG 原生 BOOLEAN | `verify_client.py:77` 直接刪除該行 |
| ISO 字串 `expires_at` 字典序比較 | PG TIMESTAMPTZ 原生比較 | `auth_router.py:157` `row["expires_at"] < now_iso_str` → `row["expires_at"] < datetime.now(timezone.utc)`（psycopg 回傳 `datetime` 物件） |

### 8.2 BE 階段執行清單

| 檔案 | 預估 query 數 | 動作 |
|------|------------|------|
| `web/auth/auth_router.py` | 約 12 | grep `?` → `%s`；lastrowid → RETURNING id |
| `web/auth/oauth_router.py` | 約 5 | 同上 |
| `web/auth/dependencies.py` | 約 1 | 同上 |
| `web/auth/verify_client.py` | 約 1 | 同上 + 移除 `bool()` adapter |
| `web/auth/email_service.py` | 約 2 | 同上 |
| `web/auth/database.py` | 0（直接重寫為 MOD-101）| 全檔重寫 |

---

## 9. CASCADE 白名單對齊（db-conventions §4）

| FK | ON DELETE | ON UPDATE | 白名單合規？ | 理由 |
|----|-----------|-----------|-----------|------|
| `favorites.user_id → users.id` | CASCADE | CASCADE | ✅ | db-conventions §4 已明列；用戶刪除即收藏全失 — 合理 |
| `email_verification_tokens.user_id → users.id` | CASCADE | CASCADE | ✅ | db-conventions §4 已明列；用戶刪除即驗證 token 失效 — 合理 |

**新增 CASCADE 規範**: 後續 TASK 新增 CASCADE 必須在 db-schema.md 標註理由 + 更新 db-conventions §4 白名單（走 RFC）。

---

## 10. 字串編碼 / Collation（db-conventions §6）

| 設定 | 值 | 強制方式 |
|------|-----|--------|
| `server_encoding` | `UTF8` | PostgreSQL 16-alpine image 預設；無需 SD 動作 |
| `lc_collate` | 系統預設 | 不指定（NFR-009） |
| email 唯一性 | 應用層 `.lower().strip()` + DB UNIQUE | 既有實作 [REUSE: TASK-001] |

**驗證**:
```sql
SHOW server_encoding;  -- 應回 UTF8
```

---

## 11. 環境變數合約遵循（ENV_VAR_CONTRACT）

> **依據**: `deploy/service-contract.yaml` 為 env var 名稱的單一真相來源；SD 引用必須使用此檔定義的 key。

| Migration 操作所用 env var | service-contract.yaml 定義 | 用途 |
|---------------------------|---------------------------|------|
| `POSTGRES_HOST` | services.backend.env_vars[0] | Alembic 連線 host |
| `POSTGRES_PORT` | services.backend.env_vars[1] | Alembic 連線 port |
| `POSTGRES_USER` | services.backend.env_vars[2] | Alembic 連線 user |
| `POSTGRES_PASSWORD` | services.backend.env_vars[3]（secret）| Alembic 連線 password |
| `POSTGRES_DB` | services.backend.env_vars[4] | Alembic 連線 database |
| `POSTGRES_SSL_MODE` | services.backend.env_vars[6] | sslmode 連線參數（dev/prod 預設 disable — USER CONFIRMED 自建 container）|
| `DATABASE_URL`（替代）| services.backend.env_vars[5]（secret）| 單一連線字串替代 5 個 POSTGRES_* |

**Alembic 連線方式**: `migrations/env.py` 從 env var 構造 connection string；詳見 `code-arch.md` §3.4。

---

## 12. 追溯矩陣

### 12.1 TBL ↔ ENTITY ↔ FUNC ↔ FR

| TBL | ENTITY | 修改類型 | FUNC | FR |
|-----|--------|---------|------|-----|
| TBL-001 [REUSE] | ENTITY-001 (users) | 補欄 + 型別變更 | FUNC-103, FUNC-104, FUNC-105 | FR-001, FR-002, FR-004 |
| TBL-002 [REUSE] | ENTITY-002 (favorites) | 同上 | FUNC-103, FUNC-104, FUNC-105 | FR-001, FR-002, FR-004 |
| TBL-003 [REUSE] | ENTITY-003 (email_verification_tokens) | 同上 + 補 created_at | FUNC-103, FUNC-104, FUNC-105 | FR-001, FR-002, FR-004 |

### 12.2 反向: 每個 FR 涉及的 TBL

| FR | 涉及 TBL | 證據 |
|----|---------|------|
| FR-001 連線層替換 | TBL-001/002/003（全部 — 統一新 driver）| §3 對照表 |
| FR-002 三表 schema 重建 | TBL-001/002/003 | §2 完整 DDL |
| FR-003 Migration 工具 | TBL-001/002/003（DDL 透過 Alembic）| §4 Migration 順序 |
| FR-004 補 timestamp 欄位 | TBL-001/002/003 | §2 + §3 |
| FR-005 env vars | 無直接 TBL 互動（MOD-101 配置）| §11 |
| FR-006 Railway 部署 | 無直接 TBL（部署層）| code-arch.md |
| FR-007 既有資料遷移 | TBL-001/002/003（FUNC-106 匯入）| code-arch.md FUNC-106 |
| FR-008 全環境 PG | TBL-001/002/003 | §2 |

### 12.3 跨 TASK 標記彙整

| 標記 | 落實位置 |
|------|---------|
| `[REUSE: TBL-001 users, from TASK-001]` | §2.1 + §3 + §12.1 |
| `[REUSE: TBL-002 favorites, from TASK-001]` | §2.2 + §3 + §12.1 |
| `[REUSE: TBL-003 email_verification_tokens, from TASK-001]` | §2.3 + §3 + §12.1 |
| `[CROSS-TASK: TASK-001 / TBL-001 (users) 補 updated_at + deleted_at 欄位 / 觸發 FR-004]` | §2.1 + §3 + §4.3 Migration 2 |
| `[CROSS-TASK: TASK-001 / TBL-002 (favorites) 補 updated_at + deleted_at 欄位 / 觸發 FR-004]` | §2.2 + §3 + §4.3 Migration 2 |
| `[CROSS-TASK: TASK-001 / TBL-003 (email_verification_tokens) 補 updated_at + deleted_at 欄位 / 觸發 FR-004]` | §2.3 + §3 + §4.3 Migration 2 |
| 補充 `[CROSS-TASK: TBL-003 補 created_at — TASK-001 baseline gap]` | §2.3 + §3 + §4.3 Migration 2 |

---

## 13. 自我驗證（摘要）

| 檢查項 | 通過 | 說明 |
|--------|------|------|
| 3 TBL [REUSE] 完整 PG DDL | ✅ | §2.1-2.3 三表 |
| 5 + 1 + 1 新欄位完整列出 + ★ NEW 標記 | ✅ | updated_at×3 + deleted_at×3 + TBL-003 created_at |
| 6 索引（4 UNIQUE + 2 FK）+ 命名符合 db-conventions §3 | ✅ | uniq_* / fk_idx_* |
| SQLite → PG 對照表完整 | ✅ | §3 |
| Migration 拆 2 個檔（FUNC-103 + FUNC-104）| ✅ | §4 |
| Reversibility（downgrade）完整 | ✅ | 2 個 migration 都有 downgrade |
| Expand-Contract 章節（NFR-007）| ✅ | §5 |
| 後續索引 CONCURRENTLY 規範（NFR-008）| ✅ | §6 |
| updated_at 應用層刷新規範 | ✅ | §7 |
| Dialect 適配規範（決策 #7/#8）| ✅ | §8 |
| CASCADE 白名單對齊 | ✅ | §9 |
| UTF8 編碼 | ✅ | §10 |
| ENV_VAR_CONTRACT 遵循 | ✅ | §11 service-contract.yaml 對齊 |
| 追溯矩陣完整 | ✅ | §12 |
| TBL ID 範圍正確（本 TASK 0 新 TBL）| ✅ | §1 |
| 不腦補 schema 結構（BR-001）| ✅ | 嚴格 [REUSE] 三表 + 補 7 欄 |
| **總分** | **95/100** | 詳見 self-review.json |
