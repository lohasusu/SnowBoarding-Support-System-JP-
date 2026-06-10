---
document_id: "CODEARCH-TASK-002-v1.0"
title: "程式碼架構設計 — SQLite → PostgreSQL 持久化遷移"
version: "1.0"
date: "2026-06-10"
author: "SD"
task_id: "TASK-002"
phase: "sd"
mode: "feature"
source_documents:
  - "ARCH-TASK-002-v1.0 (SA system-arch.md — MOD-101..104)"
  - "FUNC-TASK-002-v1.0 (SA functional-flow.md — FUNC-101..107)"
  - "PATTERN-TASK-002-v1.0 (SA pattern-spec.md — PATTERN-101)"
  - "DB-TASK-002-v1.0 (本 SD db-schema.md)"
  - ".sdlc/conventions/code-conventions.md v1.1 (Python snake_case / Google docstring / 檔上限 500 / 函式上限 80)"
  - "deploy/service-contract.yaml (env var 名稱 + 服務依賴)"
  - "deploy/deploy-env.json (4 個 user confirmed decisions)"
  - "web/auth/database.py (重寫目標)"
change_history:
  - version: "1.0"
    date: "2026-06-10"
    changes: "初始版本 — 8 [BLOCKED_ON_SD] 全部解決 + 目錄結構 + MOD-101..104 對應檔案路徑 + Alembic 配置 + advisory lock SQL + Dialect 適配實作策略 + scripts/migrate_sqlite_to_postgres.py 規格 + 14 天 SQLite emergency path 保留策略"
    author: "SD"
approval:
  reviewer: "PM"
  date: ""
  result: "Pending"
  notes: ""
---

# 程式碼架構設計 — SQLite → PostgreSQL 持久化遷移

> **本檔負責**: 將 SA MOD-101..104 + MOD-005 storage 替換 → 對應具體**目錄結構 / 檔案路徑 / 模組職責 / 依賴關係**；解所有 SA test-sa 列出的 8 個 [BLOCKED_ON_SD]；確保 BE 階段拿到本檔可直接動手寫程式碼。
> **CODE_CONVENTIONS 對齊**: 本 TASK 採 Python snake_case 檔名 + Google-style docstring + 檔行 ≤ 500 / 函式 ≤ 80（code-conventions §7 禁止項）

---

## 1. 設計決策摘要（8 [BLOCKED_ON_SD] 全解）

### 1.1 DB Driver 選型 — psycopg3（pure Python）

> **決策**: **psycopg 3.1+**（the official PostgreSQL adapter for Python, `psycopg[binary]` 安裝）
> **拒絕**: psycopg2 / asyncpg / SQLAlchemy ORM

| 候選 | 採納？ | 理由 |
|------|--------|------|
| **psycopg3** | ✅ | (1) PEP 249 DB-API 2.0 標準 — 介面與 sqlite3 module 高度相似（context manager、cursor、execute、fetchone/all/many）— 替換成本最低；(2) `psycopg[binary]` 安裝即用，無需編譯；(3) `psycopg_pool.ConnectionPool` 內建連線池 — 不需要額外 lib；(4) 同步介面與既有 7 檔 FastAPI sync def 對齊（既有實作非 async）；(5) 是 PG 官方持續維護的下一代 driver，psycopg2 進入 maintenance mode |
| psycopg2 | ❌ | maintenance mode；不再加新特性；既然要遷移就一步到位採新版 |
| asyncpg | ❌ | (1) 要求所有既有 FastAPI route 改 async — 範圍超出 NFR-002「外部行為不變」；(2) 沒有 PEP 249 介面 — 既有 7 檔 query 大改造 |
| SQLAlchemy 2.0 (ORM) | ❌ | (1) 引入 ORM 等於 schema 邏輯結構改變（model class）違反 BR-001；(2) 改造範圍超出本 TASK；(3) SA-SUG-102 Repository Pattern 完整 refactor 留後續 TASK |

**Resource**: `psycopg==3.1.18`（或更新）+ `psycopg-binary==3.1.18` + `psycopg-pool==3.2.0`

### 1.2 Migration 工具選型 — Alembic

> **決策**: **Alembic 1.13+**（SQLAlchemy 生態，Python 業界標準）
> **拒絕**: yoyo-migrations / 手寫 runner

| 候選 | 採納？ | 理由 |
|------|--------|------|
| **Alembic** | ✅ | (1) Python ecosystem 業界標準，文件 / Stack Overflow / Claude / 同儕經驗最豐富；(2) Reversible migration 內建（`def upgrade()` + `def downgrade()` 強制配對）— 直接滿足 NFR-006；(3) `op.create_index(..., postgresql_concurrently=True)` 內建支援 NFR-008 後續 CONCURRENTLY 規範；(4) `alembic_version` 表自管版本追蹤 — 不需自寫 schema_migrations；(5) 雖然 Alembic 屬 SQLAlchemy 一部分，但**可獨立於 ORM 使用** — 我們只用 Alembic 的 migration runner，不用 SQLAlchemy Core / ORM；(6) Alembic 內建 advisory lock 支援（透過 `op.execute("SELECT pg_advisory_lock(...)")`）對應 deploy-env.json Q1 決策 |
| yoyo-migrations | ❌ | (1) 純 SQL 但 Python ecosystem 較小；(2) reversibility 需用 `__rollback__` Python 函式包，與 .sql migration 兩棲不直觀；(3) 文件 / community 顯著小於 Alembic |
| 手寫 SQL runner | ❌ | (1) 維護負擔最高 — Reversibility / schema_migrations 自管 / advisory lock 都要自己寫；(2) BE 階段 onboarding 成本高；(3) 不符合「規範行為不規範實作工具」的精神 — 用業界標準工具讓專案有 reusable 經驗 |

**Resource**: `alembic==1.13.1`（或更新）— PEP 621 `pyproject.toml` / `requirements.txt` 新增。

> **注意**: Alembic 內部會 import SQLAlchemy（用於描述 schema metadata），但**不需要**用 SQLAlchemy ORM；我們在 migration 檔內用 `op.create_table()` / `op.add_column()` / `op.execute(raw SQL)` 即可，符合 BR-001 schema 邏輯結構不變。

### 1.3 Connection Pool Library 選型 — psycopg_pool（內建）

> **決策**: **psycopg_pool.ConnectionPool**（psycopg3 官方）
> **拒絕**: SQLAlchemy QueuePool / pgbouncer / 自寫 pool

| 候選 | 採納？ | 理由 |
|------|--------|------|
| **psycopg_pool** | ✅ | (1) 同 driver 生態，零額外抽象；(2) 支援 `min_size` / `max_size` / `timeout`（NFR-005 三個參數對齊）；(3) 同步介面與既有 `with get_conn() as conn:` 完美對齊；(4) Pool 在 application startup 透過 `pool.open()` 啟動，shutdown 透過 `pool.close()` 關閉 — 完整呼應 FUNC-101/102 |
| SQLAlchemy QueuePool | ❌ | 為了 pool 引入 SQLAlchemy 反向擴大依賴 |
| pgbouncer（外部 process）| ❌ | (1) 自建 PG container 加 sidecar 增加複雜度；(2) Railway 自建 container 環境部署 pgbouncer 非 Hobby plan 友善；(3) 應用內 pool 已可達 NFR-005 目標 |
| 自寫 pool | ❌ | 重複造輪子，高風險 |

**Resource**: 包含於 `psycopg-pool==3.2.0`

### 1.4 Migration 觸發策略 — startup-auto + PG advisory lock

> **決策**: 應用 startup 時自動 `alembic upgrade head`（搭配 PG advisory lock 防多 instance 競態）
> **依據**: deploy-env.json `_deploymentDecisions.migrationTrigger = "startup-auto-with-advisory-lock"`（USER CONFIRMED）

**實作流程**:

```python
# web/db_bootstrap.py (MOD-104)
from psycopg import connect
from alembic.config import Config
from alembic import command
import os

ADVISORY_LOCK_KEY = 0xCAFE0102  # 不可改 — 全域唯一 lock identifier；hex CAFE + TASK 編號 0102

def run_migrations() -> None:
    """應用 startup 時自動套用所有未套用的 migration。
    使用 PG advisory lock 確保多 instance / 多 worker 啟動時只有一個跑 migration。
    """
    # 1. 用低層連線取 advisory lock（不依賴 Alembic 的 pool 設定）
    dsn = _build_dsn_from_env()
    with connect(dsn, autocommit=True) as conn:
        with conn.cursor() as cur:
            # pg_try_advisory_lock 是非 blocking — 失敗則代表別人在跑 migration
            cur.execute("SELECT pg_try_advisory_lock(%s)", (ADVISORY_LOCK_KEY,))
            got_lock = cur.fetchone()[0]
            if not got_lock:
                # 別的 instance 在跑 — 等他跑完
                cur.execute("SELECT pg_advisory_lock(%s)", (ADVISORY_LOCK_KEY,))
                # 取到 lock 時對方已寫完 alembic_version；我們直接釋放
                cur.execute("SELECT pg_advisory_unlock(%s)", (ADVISORY_LOCK_KEY,))
                return  # 跳過本次 upgrade

            try:
                alembic_cfg = Config("alembic.ini")
                # 注入 DSN 給 Alembic（避免它再讀 env）
                alembic_cfg.set_main_option("sqlalchemy.url", dsn)
                command.upgrade(alembic_cfg, "head")
            finally:
                cur.execute("SELECT pg_advisory_unlock(%s)", (ADVISORY_LOCK_KEY,))
```

**Advisory Lock 行為**:
| 情境 | 行為 |
|------|------|
| 單 instance 單 worker | 立即取得 lock，跑 upgrade head |
| 多 instance / 多 worker 同時 startup | 第一個取 lock 並跑 upgrade；其餘 `pg_try_advisory_lock` 回 false → block 在 `pg_advisory_lock` 等待 → 解鎖時對方已 upgrade 完成 → 直接釋放並返回 |
| Migration 失敗 | `finally` 釋放 lock；`alembic.command.upgrade` 拋例外 → app startup 失敗 → Railway healthcheck fail → auto rollback to N-1 build（既有平台行為，deploy-env.json `_deploymentDecisions.migrationTrigger.fallback` 已說明） |

**NFR-003 啟動延遲量化**: alembic_version 表查詢 < 100ms（單 row）；若已 up-to-date 則 upgrade head 是 no-op；總增量 < 500ms（startup 含 advisory lock 開銷）。

### 1.5 FUNC-103 / FUNC-104 拆分決策 — 拆（選項 B）

> **決策**: 已在 `db-schema.md` §1 表 #5 詳述（拆為兩個 migration）。
> 此處不重複，僅標 cross-ref：`db-schema.md` §4 Migration 順序表。

### 1.6 updated_at 應用層 vs trigger — 應用層

> **決策**: 已在 `db-schema.md` §1 表 #6 + §7 詳述。
> 此處不重複，僅標 cross-ref：`db-schema.md` §7。

### 1.7 placeholder dialect 適配 — 全替換 `?` → `%s`

> **決策**: 已在 `db-schema.md` §1 表 #7 + §8 詳述。
> 此處不重複，僅標 cross-ref：`db-schema.md` §8。

### 1.8 lastrowid 替換策略 — `RETURNING id`

> **決策**: 已在 `db-schema.md` §1 表 #8 + §8.1 詳述。

---

## 2. 目錄結構（增量視角）

> **基線**: code-conventions.md §3.2「本專案採用」既有結構（brownfield grandfather）；本 TASK 增量說明 ★ NEW / ☆ REWRITE / ✏️ MODIFY。

```
snowboarding_support/
├─ web/                                    # FastAPI 應用根 [REUSE]
│  ├─ main.py                              # ASGI app + 主路由 [REUSE]
│  ├─ db_bootstrap.py                      # ★ NEW — MOD-104（startup migration + advisory lock）
│  ├─ plan_routes.py                       # [REUSE]
│  ├─ auth/                                # 認證子系統 [REUSE 目錄]
│  │  ├─ __init__.py                       # [REUSE]
│  │  ├─ auth_router.py                    # ✏️ MODIFY — query 適配 ? → %s + lastrowid → RETURNING id + UPDATE 補 updated_at
│  │  ├─ oauth_router.py                   # ✏️ MODIFY — 同上
│  │  ├─ verify_client.py                  # ✏️ MODIFY — 同上 + 移除 bool() adapter（line 77）
│  │  ├─ email_service.py                  # ✏️ MODIFY — 同上
│  │  ├─ dependencies.py                   # ✏️ MODIFY — 同上
│  │  ├─ security.py                       # [REUSE] — 無 SQL
│  │  ├─ database.py                       # ☆ REWRITE — 從 SQLite 改寫為 PostgreSQL 連線池（MOD-101 實作載體）
│  │  ├─ database_sqlite.py                # ★ NEW — 14 天 emergency rollback 保留路徑（SUG-006）
│  │  ├─ repositories.py                   # ★ NEW — MOD-103 最小封裝 helper（updated_at 注入 + lastrowid 統一）
│  │  └─ tests/
│  │     └─ test_auth.py                   # ✏️ MODIFY — fixture 改 PG（AC-045 既有 8 pytest 100% 通過）
│  ├─ templates/                           # [REUSE]
│  └─ static/js/                           # [REUSE]
├─ flight_search/                          # [REUSE]
├─ http_scraper.py                         # [REUSE]
├─ site_analyzer.py                        # [REUSE]
├─ migrations/                             # ★ NEW — MOD-102 Alembic migration runner
│  ├─ env.py                               # ★ NEW — Alembic 環境配置（DSN 從 env vars 構造）
│  ├─ script.py.mako                       # ★ NEW — Alembic 範本（自動生成）
│  └─ versions/                            # ★ NEW — migration 檔
│     ├─ 20260610_120000_create_initial_schema.py
│     └─ 20260610_120100_add_softdelete_columns.py
├─ alembic.ini                             # ★ NEW — Alembic 配置入口
├─ scripts/                                # ★ NEW — 一次性工具腳本
│  └─ migrate_sqlite_to_postgres.py        # ★ NEW — FUNC-106 SQLite → PG 匯入腳本（fallback）
├─ requirements.txt                        # ✏️ MODIFY — 新增 psycopg / psycopg-binary / psycopg-pool / alembic
├─ docker-compose.yml                      # ✏️ MODIFY — 加 postgres:16-alpine 服務（FR-008 + deploy/service-contract.yaml）
└─ .env.example                            # ✏️ MODIFY — 加 POSTGRES_* + DATABASE_URL + POOL_* 範例值
```

**統計**:
- ★ NEW: 5 個檔（`db_bootstrap.py` / `database_sqlite.py` / `repositories.py` / `migrate_sqlite_to_postgres.py` / `alembic.ini`）+ 1 目錄（`migrations/`）+ 2 migration 檔 + Alembic 框架檔
- ☆ REWRITE: 1 個檔（`database.py`）
- ✏️ MODIFY: 6 個既有檔（`auth_router.py` / `oauth_router.py` / `verify_client.py` / `email_service.py` / `dependencies.py` / `test_auth.py`）+ 3 設定檔（`requirements.txt` / `docker-compose.yml` / `.env.example`）
- [REUSE]: 其他全部不變（雪票 / 機票 / 行程 / 靜態資源）

---

## 3. 模組對應 MOD-ID

### 3.1 MOD-101: postgres_db → `web/auth/database.py`（重寫）

**職責**:
1. 維護 PostgreSQL `psycopg_pool.ConnectionPool`
2. 提供 `get_conn()` context manager（介面語意與既有 SQLite 版本一致）
3. 從 env vars 讀連線資訊建 pool；啟動失敗拋明確 error（AC-044）
4. 提供 `init_pool()` / `close_pool()` 給 FastAPI startup/shutdown event

**檔案內容大綱**（< 200 行，遵守 code-conventions §7 ≤ 500）:

```python
"""PostgreSQL 連線層 — MOD-101 postgres_db.

替換既有 SQLite 實作（TASK-001 brownfield）；介面語意保留：
- get_conn() 仍是 context manager，with 區塊內可 execute SQL
- 唯一可見差異：conn 物件型別為 psycopg.Connection，placeholder 改用 %s
"""
import os
from contextlib import contextmanager
from typing import Iterator

from psycopg import Connection, OperationalError
from psycopg_pool import ConnectionPool

# 模組級 pool — 由 init_pool() 啟動，close_pool() 關閉
_pool: ConnectionPool | None = None


def _build_dsn_from_env() -> str:
    """從 env vars 構造 PostgreSQL DSN。

    優先順序：DATABASE_URL → 個別 POSTGRES_*。
    依 service-contract.yaml + parameter-plan.md 12 個 parameter。

    Raises:
        RuntimeError: 缺必要 env vars 時拋出（不洩漏 password）
    """
    dsn = os.environ.get("DATABASE_URL")
    if dsn:
        return dsn

    host = os.environ.get("POSTGRES_HOST")
    port = os.environ.get("POSTGRES_PORT", "5432")
    user = os.environ.get("POSTGRES_USER")
    password = os.environ.get("POSTGRES_PASSWORD")
    db = os.environ.get("POSTGRES_DB")
    sslmode = os.environ.get("POSTGRES_SSL_MODE", "disable")

    missing = [k for k, v in {
        "POSTGRES_HOST": host,
        "POSTGRES_USER": user,
        "POSTGRES_PASSWORD": password,
        "POSTGRES_DB": db,
    }.items() if not v]
    if missing:
        raise RuntimeError(
            f"Missing required PostgreSQL env vars: {', '.join(missing)}. "
            "Set them in .env (dev) or Railway dashboard (prod)."
        )

    return (
        f"host={host} port={port} user={user} password={password} "
        f"dbname={db} sslmode={sslmode}"
    )


def init_pool() -> None:
    """FastAPI startup 時呼叫 — 啟動 connection pool。

    Raises:
        OperationalError: 連線失敗（PG 未啟動 / auth 錯 / network 錯）— 阻擋 app 啟動（AC-044）
    """
    global _pool
    if _pool is not None:
        return  # 重複初始化保護（FastAPI lifespan reload 場景）

    dsn = _build_dsn_from_env()
    min_size = int(os.environ.get("POSTGRES_POOL_MIN", "2"))
    max_size = int(os.environ.get("POSTGRES_POOL_MAX", "10"))
    timeout_ms = int(os.environ.get("POSTGRES_POOL_TIMEOUT_MS", "5000"))
    timeout_s = timeout_ms / 1000.0

    _pool = ConnectionPool(
        conninfo=dsn,
        min_size=min_size,
        max_size=max_size,
        timeout=timeout_s,  # 從 pool 取連線的最大等待秒數
        kwargs={"row_factory": _row_factory_dict_like},
    )
    _pool.open(wait=True, timeout=30.0)  # 啟動時測試最小連線


def close_pool() -> None:
    """FastAPI shutdown 時呼叫 — 釋放 pool。"""
    global _pool
    if _pool is not None:
        _pool.close()
        _pool = None


@contextmanager
def get_conn() -> Iterator[Connection]:
    """取得一個 PostgreSQL connection（從 pool 借）。

    用法（與既有 SQLite 完全相同）：
        with get_conn() as conn:
            cur = conn.execute("SELECT ... WHERE id = %s", (123,))
            row = cur.fetchone()

    Note:
        - placeholder 為 %s（不再是 ?）— FUNC-105 全替換
        - row 物件為 dict-like（透過 row_factory）
        - 離開 with 自動 commit（psycopg 預設 autocommit=False，with 區塊 exit 觸發 commit）
        - 例外則 ROLLBACK
    """
    if _pool is None:
        raise RuntimeError("pool not initialized — call init_pool() at app startup")
    with _pool.connection() as conn:
        yield conn


def _row_factory_dict_like(cursor):
    """讓 row 行為近似 sqlite3.Row（dict-like 取欄位）以最小化既有 7 檔的破壞。

    既有 code 多處用 row["column_name"] / dict(row)；psycopg 預設回 tuple。
    用 dict_row factory 讓 row 直接是 dict。
    """
    from psycopg.rows import dict_row
    return dict_row(cursor)
```

**對應 SA**: system-arch.md §3 MOD-101 + functional-flow.md FUNC-101 / 102

---

### 3.2 MOD-102: migrations → `migrations/` 目錄 + `alembic.ini`

**職責**:
1. Alembic 配置入口（`alembic.ini`）
2. `migrations/env.py` 描述 Alembic 環境（從 env vars 構造 DSN）
3. `migrations/versions/` 存放 migration 檔（db-schema.md §4 已寫範本）

**alembic.ini 內容**:

```ini
[alembic]
script_location = migrations
# sqlalchemy.url 留空 — 由 env.py 從 env vars 動態構造
sqlalchemy.url =

# Migration 檔名格式（符合 db-conventions §5.1 + BR-007）
file_template = %%(year)d%%(month).2d%%(day).2d_%%(hour).2d%%(minute).2d%%(second).2d_%%(slug)s

# 時區（migration 檔內 created_at 註解用）
timezone = UTC

[loggers]
keys = root,sqlalchemy,alembic

[handlers]
keys = console

[formatters]
keys = generic

[logger_root]
level = WARN
handlers = console
qualname =

[logger_sqlalchemy]
level = WARN
handlers =
qualname = sqlalchemy.engine

[logger_alembic]
level = INFO
handlers =
qualname = alembic

[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic

[formatter_generic]
format = %(levelname)-5.5s [%(name)s] %(message)s
datefmt = %H:%M:%S
```

**migrations/env.py 大綱**（< 100 行）:

```python
"""Alembic env.py — 連線 DSN 從 env vars 構造。"""
import os
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool
from alembic import context

from web.auth.database import _build_dsn_from_env

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# 注入 DSN
config.set_main_option("sqlalchemy.url", _build_dsn_from_env())

target_metadata = None  # 不使用 autogenerate（不依賴 SQLAlchemy ORM）


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url, target_metadata=target_metadata,
        literal_binds=True, dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
```

**對應 SA**: system-arch.md §3 MOD-102 + functional-flow.md FUNC-103 / 104 + pattern-spec.md PATTERN-101

---

### 3.3 MOD-103: auth_repositories → `web/auth/repositories.py`（最小封裝）

> **範圍說明（呼應 test-sa Minor-1）**: SA system-arch.md §3 MOD-103 說明本 TASK 採「最小封裝」原則 — **本 SD 決策為新增單檔 `web/auth/repositories.py`**（非新建 `repositories/` 子目錄），列出 helper function；完整 Repository Pattern refactor（含 `repositories/users.py` / `favorites.py` 分檔）留後續 TASK SA-SUG-102 `auth-layering-refactor`。

**職責**:
1. 統一封裝 `lastrowid` 替換邏輯（`INSERT ... RETURNING id` + `cur.fetchone()[0]`）
2. 統一封裝 UPDATE 注入 `updated_at = NOW()`（決策 #6）
3. 提供 placeholder dialect 適配層（雖然全替換 `?` → `%s`，但 helper 集中讓未來 driver 切換更容易）
4. **不**注入 `WHERE deleted_at IS NULL` filter（SUG-004 + CONST-005 — 本 TASK 不啟動軟刪邏輯）

**檔案內容大綱**（< 150 行）:

```python
"""Repository helpers — MOD-103（最小封裝原則）。

僅集中三類重複動作：
1. INSERT ... RETURNING id
2. UPDATE 補 updated_at = NOW()
3. dict row 取值（與既有 sqlite3.Row 介面相容）

完整 Repository Pattern refactor 留後續 TASK（SA-SUG-102）。
"""
from typing import Any, Sequence

from psycopg import Connection


def insert_returning_id(
    conn: Connection,
    sql: str,
    params: Sequence[Any],
) -> int:
    """執行 INSERT 並回傳新建 row 的 id。

    Args:
        conn: psycopg.Connection（透過 get_conn() 取得）
        sql: 必含 `RETURNING id` clause 的 INSERT 語句
        params: %s placeholder 對應的參數 tuple

    Returns:
        新建 row 的 id（BIGINT）

    Raises:
        psycopg.errors.UniqueViolation: UNIQUE 約束違反（如註冊 email 重複）

    Example:
        user_id = insert_returning_id(
            conn,
            "INSERT INTO users (email, username, hashed_password, is_verified) "
            "VALUES (%s, %s, %s, %s) RETURNING id",
            (email, username, hashed, False),
        )
    """
    cur = conn.execute(sql, params)
    row = cur.fetchone()
    if row is None:
        raise RuntimeError("INSERT did not return an id — check RETURNING clause")
    # row 是 dict（透過 _row_factory_dict_like）
    return row["id"]


def update_with_timestamp(
    conn: Connection,
    table: str,
    set_clause: str,
    where_clause: str,
    params: Sequence[Any],
) -> int:
    """UPDATE 並自動補 updated_at = NOW()。

    決策 #6：應用層手動 SET updated_at（不用 DB trigger）。

    Args:
        conn: psycopg.Connection
        table: 表名（無需 quote — 應由呼叫端確保非使用者輸入）
        set_clause: SET 子句（不含 updated_at — 本函式自動補）
        where_clause: WHERE 子句
        params: SET + WHERE 的 %s 對應參數（按出現順序）

    Returns:
        被影響的 row 數

    Example:
        rows = update_with_timestamp(
            conn,
            table="users",
            set_clause="username = %s",
            where_clause="id = %s",
            params=(new_username, user_id),
        )
    """
    full_sql = (
        f"UPDATE {table} "
        f"SET {set_clause}, updated_at = NOW() "
        f"WHERE {where_clause}"
    )
    cur = conn.execute(full_sql, params)
    return cur.rowcount
```

**對應 SA**: system-arch.md §3 MOD-103 + functional-flow.md FUNC-105 + field-spec.md INV-101

---

### 3.4 MOD-104: db_bootstrap → `web/db_bootstrap.py`

**職責**:
1. FastAPI startup hook — 呼叫 `MOD-101.init_pool()` + advisory lock + `alembic upgrade head`
2. FastAPI shutdown hook — 呼叫 `MOD-101.close_pool()`
3. **不**提供 `/healthz` endpoint（SA-SUG-101 明示留後續 TASK；本 TASK 用既有 `/api/auth/me` healthcheck，service-contract.yaml `backend.health_check`）

**檔案內容大綱**（< 150 行）:

```python
"""DB bootstrap — MOD-104。

職責：
1. FastAPI startup → init_pool + advisory lock + alembic upgrade head
2. FastAPI shutdown → close_pool

Migration trigger 策略：startup-auto-with-advisory-lock
(deploy-env.json _deploymentDecisions.migrationTrigger USER CONFIRMED)
"""
import logging
import os
from pathlib import Path

from psycopg import connect

from web.auth.database import init_pool, close_pool, _build_dsn_from_env

logger = logging.getLogger(__name__)

ADVISORY_LOCK_KEY = 0xCAFE0102  # 全域唯一 lock identifier；hex CAFE + TASK 0102；不可改


def run_migrations() -> None:
    """應用 startup 時自動套用所有未套用的 migration。

    使用 PG advisory lock 避免多 instance / 多 worker 同時跑 migration。
    """
    from alembic.config import Config
    from alembic import command

    dsn = _build_dsn_from_env()
    alembic_ini = Path(__file__).resolve().parent.parent / "alembic.ini"

    with connect(dsn, autocommit=True) as lock_conn:
        with lock_conn.cursor() as cur:
            # 非 blocking 嘗試取 lock
            cur.execute("SELECT pg_try_advisory_lock(%s)", (ADVISORY_LOCK_KEY,))
            got_lock = cur.fetchone()[0]

            if not got_lock:
                logger.info("Migration advisory lock busy — waiting for other instance...")
                cur.execute("SELECT pg_advisory_lock(%s)", (ADVISORY_LOCK_KEY,))
                cur.execute("SELECT pg_advisory_unlock(%s)", (ADVISORY_LOCK_KEY,))
                logger.info("Other instance completed migration; skipping.")
                return

            try:
                alembic_cfg = Config(str(alembic_ini))
                alembic_cfg.set_main_option("sqlalchemy.url", dsn)
                logger.info("Running alembic upgrade head...")
                command.upgrade(alembic_cfg, "head")
                logger.info("Migration complete.")
            finally:
                cur.execute("SELECT pg_advisory_unlock(%s)", (ADVISORY_LOCK_KEY,))


def on_startup() -> None:
    """FastAPI app startup hook — 註冊於 web/main.py。"""
    logger.info("Initializing PostgreSQL connection pool...")
    init_pool()
    logger.info("Running migrations...")
    run_migrations()
    logger.info("DB bootstrap complete.")


def on_shutdown() -> None:
    """FastAPI app shutdown hook — 註冊於 web/main.py。"""
    logger.info("Closing PostgreSQL connection pool...")
    close_pool()
```

**整合於 `web/main.py`**:

```python
# web/main.py — 增量改動（既有檔，[REUSE 邊界]）
from contextlib import asynccontextmanager
from web.db_bootstrap import on_startup, on_shutdown

@asynccontextmanager
async def lifespan(app):
    on_startup()
    yield
    on_shutdown()

app = FastAPI(lifespan=lifespan)
# ... 其他既有設定不變
```

**對應 SA**: system-arch.md §3 MOD-104 + functional-flow.md FUNC-101 / 102 / 103 / 104

---

## 4. 14 天 SQLite Emergency Path 保留策略（SUG-006 + CONST-009）

> **依據**: deploy-env.json `_deploymentDecisions.backupRollback.sqliteEmergencyPath`
> **目的**: production 切換到 PG 後**前 14 天**保留 SQLite driver 程式碼於可 revert 的位置；14 天後新開 TASK 正式刪除。

### 4.1 實作方式 — `web/auth/database_sqlite.py`

**內容**: 將既有 `web/auth/database.py` 完整內容**複製**到 `database_sqlite.py`（包含 sqlite3 import + init_db + ALTER TABLE try/except hack 等等 — 完整 14 天保留證據），檔頭加：

```python
"""DEPRECATED: SQLite legacy driver — kept as 14-day emergency rollback path.

DO NOT IMPORT FROM THIS MODULE in new code.

Lifecycle:
- Created: 2026-06-10 (本 TASK 部署當下)
- Retire: 2026-06-24 (T+14 days) — 由後續 TASK 移除
- Purpose: 若 PG 在切換後 14 天內發生不可恢復災難（資料毀損 / 連線完全失能 > 1 hr），
  可走 git revert {pg-migration-merge-commit} 回滾到 SQLite 部署
- Reference: SUG-006 + CONST-009 + deploy-env.json _deploymentDecisions.backupRollback.sqliteEmergencyPath

Rollback steps (14 天 window 內):
1. Railway dashboard → 移除 POSTGRES_* env vars
2. git revert {pg-migration-merge-commit}
3. git push → Railway 自動 redeploy SQLite 版本
4. 接受 SQLite ephemeral 缺陷重現作為 emergency tradeoff
"""
# ↓↓↓ 以下為既有 web/auth/database.py 原內容 ↓↓↓
import sqlite3
from pathlib import Path
# ... (既有 SQLite 實作完整保留)
```

### 4.2 不引入到 production runtime

`database_sqlite.py` **僅作 git history 記錄**；production runtime 不從此檔 import。

- ❌ `from web.auth.database_sqlite import get_conn`（禁止任何檔 import）
- ✅ 該檔存在於 git 中，僅用於：
  1. PR Review / Tester 確認 emergency rollback path 真的存在
  2. 14 天內若需 emergency revert，git log 可直接看到舊實作
  3. CI lint 可加規則 — 確認無生產 code import 此檔（[SD建議] 留 BE 階段加 `.flake8` 或 ruff config）

### 4.3 移除排程

| 時間 | 動作 | 觸發者 |
|------|------|--------|
| T+0（部署當下）| `database_sqlite.py` 隨本 TASK 一起 merge | 本 TASK BE 階段 |
| T+0 到 T+13 | 觀察期 — production 穩定運行 | Tester + Deployer 監控 |
| T+14（2026-06-24）| 新開 TASK `remove-sqlite-legacy-path` 刪除 `database_sqlite.py` + 14 天 SQLite emergency window 章節 | 後續 TASK SDLC 流程 |

---

## 5. FUNC-106: SQLite → PostgreSQL 匯入腳本

> **路徑**: `scripts/migrate_sqlite_to_postgres.py`
> **觸發**: 手動 — `python scripts/migrate_sqlite_to_postgres.py --sqlite-path xxx.db`
> **AC**: AC-056

### 5.1 規格

| 項目 | 內容 |
|------|------|
| 接受參數 | `--sqlite-path PATH`（必填）+ PG 連線參數（讀 env vars 同 MOD-101）|
| 行為 | 讀 SQLite 三表全部 row → INSERT 到 PG 三表（FK 順序：users → favorites + email_verification_tokens）|
| 欄位對映 | （詳見下表） |
| SQLite 檔不存在 | `exit 0` + 訊息「無 SQLite 資料需匯入」 |
| 失敗處理 | FK 違反 → log warning + skip + 繼續；其他 → exit 1 |

### 5.2 欄位對映表

| SQLite | PG | 轉換 |
|--------|-----|------|
| `users.id` | `users.id` | 保留（用 INSERT 顯式 id 因為 IDENTITY 預設不可寫；用 `OVERRIDING SYSTEM VALUE`）|
| `users.email/username/...` | `users.email/...` | 直接對映 |
| `users.is_verified` (0/1) | `users.is_verified` (BOOLEAN) | `bool()` 轉型 |
| `users.created_at` (ISO 字串) | `users.created_at` (TIMESTAMPTZ) | psycopg 自動 parse |
| `users.updated_at` | （SQLite 無）| **backfill** = `created_at`（meaningful 預設）|
| `users.deleted_at` | （SQLite 無）| **backfill** = `NULL` |
| `favorites.*` | `favorites.*` | 同上 pattern |
| `email_verification_tokens.created_at` | （SQLite 無）| **backfill** = `expires_at - INTERVAL '24 hours'`（從過期時間反推建立時間）|
| `email_verification_tokens.updated_at` | （SQLite 無）| **backfill** = `created_at` |
| `email_verification_tokens.deleted_at` | （SQLite 無）| **backfill** = `NULL` |

### 5.3 INSERT 語法（PG IDENTITY 寫入歷史 id）

```sql
INSERT INTO users (id, email, username, ...)
OVERRIDING SYSTEM VALUE
VALUES (%s, %s, %s, ...);

-- 完成後須 reset IDENTITY 起始值避免後續 INSERT 衝突
SELECT setval(
    pg_get_serial_sequence('users', 'id'),
    (SELECT MAX(id) FROM users)
);
```

### 5.4 完整 stdout 範本

```
$ python scripts/migrate_sqlite_to_postgres.py --sqlite-path /tmp/snowtrip.db
[INFO] SQLite file: /tmp/snowtrip.db
[INFO] PostgreSQL: host=localhost port=5432 user=snowtrip db=snowtrip
[INFO] Reading users... 3 rows
[INFO] Reading favorites... 2 rows
[INFO] Reading email_verification_tokens... 1 row
[INFO] Inserting users (with OVERRIDING SYSTEM VALUE)... 3 ok
[INFO] Inserting favorites... 2 ok
[INFO] Inserting email_verification_tokens... 1 ok
[INFO] Resetting IDENTITY sequences...
[INFO] Verifying counts: SQLite 3/2/1 vs PG 3/2/1 — MATCH
[INFO] Done. exit 0
```

```
$ python scripts/migrate_sqlite_to_postgres.py --sqlite-path /tmp/no-such-file.db
[INFO] SQLite file not found at /tmp/no-such-file.db
[INFO] 無 SQLite 資料需匯入. exit 0
```

---

## 6. requirements.txt 增量

```text
# 既有依賴 [REUSE: TASK-001]
fastapi
uvicorn[standard]
jinja2
python-multipart
pydantic
bcrypt
PyJWT
httpx
openpyxl
beautifulsoup4
requests
google-search-results  # SerpAPI

# ★ NEW (TASK-002)
psycopg[binary]==3.1.18     # MOD-101 driver
psycopg-pool==3.2.0         # MOD-101 connection pool
alembic==1.13.1             # MOD-102 migration runner
# Alembic 會自動拉 SQLAlchemy 作為描述 metadata 的依賴（不用 ORM）

# 開發測試（既有）
pytest
```

> **注意**: `sqlite3` 是 Python stdlib — 不需新增 / 不需移除（`database_sqlite.py` 仍可 import）。

---

## 7. docker-compose.yml 增量

> **依據**: deploy/service-contract.yaml `services.database` + `port_allocation`
> **既有**: docker-compose.yml 已有 postgres 服務範本（baseline §1.1 + service-contract.yaml line 138-140 提及）— SD 確認與本檔對齊。

```yaml
# 完整節錄關鍵增量
services:
  postgres:
    image: postgres:16-alpine
    container_name: snowtrip-postgres
    restart: unless-stopped
    environment:
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_DB: ${POSTGRES_DB}
    ports:
      - "5432:5432"
    volumes:
      - sdlc-db-data:${PG_DATA_PATH:-/var/lib/postgresql/data}
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER} -d ${POSTGRES_DB}"]
      interval: 5s
      timeout: 5s
      retries: 5

  backend:
    # ... 既有
    depends_on:
      postgres:
        condition: service_healthy

volumes:
  sdlc-db-data:
    name: ${PG_VOLUME_NAME:-sdlc-db-data}
```

---

## 8. .env.example 增量

```bash
# ===== PostgreSQL（TASK-002 新增）=====
# 自建 container 連線（本機 docker-compose）
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=snowtrip
POSTGRES_PASSWORD=changeme_dev_password
POSTGRES_DB=snowtrip
POSTGRES_SSL_MODE=disable  # 自建 container 預設 disable（USER CONFIRMED 2026-06-09）

# 替代方案：DATABASE_URL（若使用此 var 則 POSTGRES_* 5 個變 optional）
# DATABASE_URL=postgresql://snowtrip:changeme_dev_password@postgres:5432/snowtrip?sslmode=disable

# Connection pool（NFR-005）
POSTGRES_POOL_MIN=2
POSTGRES_POOL_MAX=10
POSTGRES_POOL_TIMEOUT_MS=5000

# Docker volume 名稱（Tester Major-5 補登記）
PG_VOLUME_NAME=sdlc-db-data
PG_DATA_PATH=/var/lib/postgresql/data

# ===== 既有環境變數 [REUSE: from TASK-001] =====
SECRET_KEY=...
SERPAPI_API_KEY=...
# PORT 由 Railway 動態注入
```

---

## 9. 模組依賴圖（無循環）

```mermaid
flowchart TD
    Main["web/main.py [REUSE]<br/>(FastAPI lifespan)"]
    DBBoot["MOD-104 web/db_bootstrap.py ★NEW"]
    MOD101["MOD-101 web/auth/database.py ☆REWRITE<br/>(postgres_db + pool)"]
    MOD102["MOD-102 alembic.ini + migrations/ ★NEW<br/>(Alembic runner)"]
    MOD103["MOD-103 web/auth/repositories.py ★NEW<br/>(helper: INSERT RETURNING / UPDATE w/ updated_at)"]
    AuthRouter["web/auth/auth_router.py ✏️MODIFY"]
    OAuthRouter["web/auth/oauth_router.py ✏️MODIFY"]
    Deps["web/auth/dependencies.py ✏️MODIFY"]
    VerifyClient["web/auth/verify_client.py ✏️MODIFY"]
    EmailSvc["web/auth/email_service.py ✏️MODIFY"]
    PG[("PostgreSQL 16")]
    DBSQLite["web/auth/database_sqlite.py ★NEW<br/>(14 天 emergency, 不被 import)"]
    Script["scripts/migrate_sqlite_to_postgres.py ★NEW"]

    Main -.startup lifespan.-> DBBoot
    DBBoot --> MOD101
    DBBoot --> MOD102
    MOD102 -.直接連 psycopg.-> PG
    MOD101 --> PG

    AuthRouter --> MOD101
    AuthRouter -.選擇性.-> MOD103
    OAuthRouter --> MOD101
    OAuthRouter -.選擇性.-> MOD103
    Deps --> MOD101
    VerifyClient --> MOD101
    EmailSvc --> MOD101
    MOD103 --> MOD101

    Script -.獨立執行.-> PG
    DBSQLite -.deprecated git 歷史保留.-> DBSQLite

    classDef new fill:#e6ffe6,stroke:#006600,stroke-width:2px
    classDef rewrite fill:#fff3cd,stroke:#856404,stroke-width:2px
    classDef modify fill:#ffe0b3,stroke:#cc6600
    classDef reuse fill:#f0f0f0,stroke:#666
    classDef storage fill:#e6f3ff,stroke:#0066cc
    classDef deprecated fill:#ffe6e6,stroke:#cc0000,stroke-dasharray:5 5

    class DBBoot,MOD102,MOD103,Script new
    class MOD101 rewrite
    class AuthRouter,OAuthRouter,Deps,VerifyClient,EmailSvc modify
    class Main reuse
    class PG storage
    class DBSQLite deprecated
```

**依賴方向驗證**:
- `web/main.py` → MOD-104（startup）→ MOD-101 / MOD-102（單向）
- MOD-102 → PostgreSQL（直接，Alembic 自管連線）
- MOD-101 → PostgreSQL
- 6 個 MOD-005 既有檔 → MOD-101（直接 `get_conn()`）
- MOD-103（最小封裝）→ MOD-101（部分 MOD-005 既有檔可選用 MOD-103 helper）
- **無循環依賴** ✅

---

## 10. 錯誤處理策略

> **依據**: code-conventions.md §6（不允許靜默忽略 / 不允許 catch 後拋資訊更少的 Error / 統一使用 error-codes.md）

### 10.1 連線層錯誤（MOD-101）

| 錯誤 | 處理 | ERR 引用 |
|------|------|---------|
| env vars 缺失 | `raise RuntimeError(...)` — 明確列缺哪些（不含 password value） | ERR-SYS-006（詳見 error-codes.md）|
| psycopg.OperationalError（auth fail / connection refused）| 不吞例外；`logger.error` + re-raise | ERR-DB-001 |
| `psycopg_pool.PoolTimeout` | 呼叫端決定（既有 7 檔 try/except 不變）| ERR-DB-002 |

### 10.2 Migration 錯誤（MOD-102 / MOD-104）

| 錯誤 | 處理 | ERR 引用 |
|------|------|---------|
| Alembic upgrade SQL 失敗 | Alembic 自動 ROLLBACK transaction；上拋 → app startup fail → Railway healthcheck fail → auto rollback to N-1 build | ERR-DB-003 |
| Advisory lock 取不到（極端 — 等了 30s 還 block）| logger warning + 仍嘗試（PG 預設無限等待）| — |
| Migration 已套用 | Alembic no-op | — |

### 10.3 既有應用層錯誤（MOD-005 既有 7 檔）

[REUSE: from TASK-001] — 既有 HTTPException / FastAPI exception handler 不變（NFR-002 強制）。

---

## 11. 共用工具 / Helper 清單

| Helper | 位置 | 用途 |
|--------|------|------|
| `get_conn()` context manager | `web/auth/database.py` (MOD-101) | 取 pool 連線；既有 7 檔已用 |
| `init_pool()` / `close_pool()` | `web/auth/database.py` (MOD-101) | Lifespan hook |
| `_build_dsn_from_env()` | `web/auth/database.py` (MOD-101) | DSN 構造（含 fallback DATABASE_URL）|
| `insert_returning_id(conn, sql, params)` | `web/auth/repositories.py` (MOD-103) | INSERT 取新 id 統一寫法 |
| `update_with_timestamp(conn, table, set_clause, where_clause, params)` | `web/auth/repositories.py` (MOD-103) | UPDATE 自動補 updated_at |
| `run_migrations()` | `web/db_bootstrap.py` (MOD-104) | Startup 時跑 Alembic + advisory lock |

---

## 12. ENV_VAR_CONTRACT 遵循驗證

> 本檔引用的所有 env vars **必須**對應 `deploy/service-contract.yaml` 中定義的 key 名稱。

| 本檔引用位置 | env var | service-contract.yaml 對應 | ✓ |
|--------------|---------|-----------------------------|---|
| §3.1 `_build_dsn_from_env` | `POSTGRES_HOST` | services.backend.env_vars[0] | ✅ |
| §3.1 | `POSTGRES_PORT` | services.backend.env_vars[1] | ✅ |
| §3.1 | `POSTGRES_USER` | services.backend.env_vars[2] | ✅ |
| §3.1 | `POSTGRES_PASSWORD` | services.backend.env_vars[3] | ✅ |
| §3.1 | `POSTGRES_DB` | services.backend.env_vars[4] | ✅ |
| §3.1 | `POSTGRES_SSL_MODE` | services.backend.env_vars[6] | ✅ |
| §3.1 | `DATABASE_URL`（替代）| services.backend.env_vars[5] | ✅ |
| §3.1 | `POSTGRES_POOL_MIN/MAX/TIMEOUT_MS` | services.backend.env_vars[7-9] | ✅ |
| §7 docker-compose | `PG_VOLUME_NAME` | parameter-plan.md §1.11（PM 補）| ✅ |
| §7 docker-compose | `PG_DATA_PATH` | parameter-plan.md §1.12（PM 補）| ✅ |

**結論**: 100% 對齊；無需 [SD建議: 需新增 env var]。

---

## 13. 追溯矩陣

### 13.1 MOD ↔ 檔案 ↔ FUNC ↔ FR

| MOD | 檔案路徑 | FUNC | FR |
|-----|----------|------|-----|
| MOD-101 postgres_db ☆REWRITE | `web/auth/database.py` | FUNC-101, FUNC-102, FUNC-105 | FR-001, FR-005 |
| MOD-102 migrations ★NEW | `alembic.ini` + `migrations/` | FUNC-103, FUNC-104 | FR-002, FR-003, FR-004 |
| MOD-103 auth_repositories ★NEW | `web/auth/repositories.py` | FUNC-105 | FR-001 |
| MOD-104 db_bootstrap ★NEW | `web/db_bootstrap.py` | FUNC-101, FUNC-102, FUNC-103 | FR-001, FR-003, FR-006 |
| MOD-005 auth [REUSE 邊界、實作替換] | `web/auth/{auth,oauth,verify_client,email,dependencies}_*.py` | FUNC-105 + TASK-001 FUNC-022..045 | FR-001 |
| scripts/ ★NEW | `scripts/migrate_sqlite_to_postgres.py` | FUNC-106 | FR-007 |

### 13.2 跨 TASK 標記

| 標記 | 落實 |
|------|------|
| `[CROSS-TASK: TASK-001 / MOD-005 storage engine 替換 / FR-001]` | §2 目錄結構 ✏️ MODIFY 6 個既有檔 + §3.1 MOD-101 重寫 |

### 13.3 14 天 emergency 保留追蹤

| 工件 | 路徑 | T+0 | T+14 |
|------|------|-----|------|
| SQLite legacy driver | `web/auth/database_sqlite.py` | 隨本 TASK merge | 後續 TASK 刪除 |

---

## 14. [SD建議] 區（與正式規格隔離）

### SD-SUG-101: 加 Migration log 結構化

- **建議**: Alembic `upgrade` 完成時 emit JSON log（含 revision_id / direction / duration / success）供 Railway log 收集
- **理由**: 配合 SA-SUG-104 + production SLA dashboard
- **不採納於本 TASK 理由**: Alembic 預設 stdout log 已足夠本 TASK 範圍；結構化 log 屬 SA-SUG-008 大架構，留後續 TASK

### SD-SUG-102: 加 lint rule 禁止 import database_sqlite

- **建議**: `.flake8` / ruff config 加規則：任何 `from web.auth.database_sqlite import` 報錯
- **理由**: 防止 14 天 emergency 期間有人誤用 SQLite path
- **不採納於本 TASK 理由**: BE 階段加 lint config 即可；本檔 §4.2 已明示策略，由 PR Reviewer 把關

### SD-SUG-103: Repository Pattern 完整 refactor 排程

- **建議**: 14 天 SQLite emergency 移除 TASK 完成後，緊接開 TASK 走 SA-SUG-102 `auth-layering-refactor`，將 `repositories.py` 拆 `repositories/users.py` / `favorites.py` / `tokens.py`
- **理由**: 配合本 TASK MOD-103 最小封裝奠定的基礎
- **不採納於本 TASK 理由**: 本 TASK 範圍 = SQLite → PG 持久層遷移；refactor 留後續 TASK 走 Rule 6 跨 TASK 修改協議

---

## 15. 自我驗證（摘要）

| 檢查項 | 通過 | 說明 |
|--------|------|------|
| 8 [BLOCKED_ON_SD] 全部解決 | ✅ | §1 |
| 4 MOD（101..104）+ MOD-005 替換對應檔案 | ✅ | §3 |
| Alembic 配置完整（alembic.ini + env.py + versions/）| ✅ | §3.2 |
| Advisory lock SQL + Python wrapper | ✅ | §1.4 + §3.4 |
| repositories.py 最小封裝（明確不含 deleted_at filter）| ✅ | §3.3 |
| 14 天 SQLite emergency path 明確策略 | ✅ | §4 |
| FUNC-106 完整規格（包含欄位 backfill 對映表）| ✅ | §5 |
| requirements.txt 增量 | ✅ | §6 |
| docker-compose.yml 增量 | ✅ | §7 |
| .env.example 增量 | ✅ | §8 |
| 模組依賴圖無循環 | ✅ | §9 |
| 錯誤處理策略 | ✅ | §10 |
| 共用 Helper 清單 | ✅ | §11 |
| ENV_VAR_CONTRACT 對齊 service-contract.yaml | ✅ | §12 |
| 追溯矩陣完整 | ✅ | §13 |
| [SD建議] 物理隔離 | ✅ | §14 |
| Mermaid 語法正確 | ✅ | §9 |
| 檔大小 ≤ 500 行（程式碼）/ 函式 ≤ 80 行 | ✅ | §3.1 ~190 行 / §3.3 ~120 行 / §3.4 ~80 行；皆內含 docstring，函式皆 < 80 行 |
| **總分** | **95/100** | 詳見 self-review.json |
