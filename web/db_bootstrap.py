"""DB bootstrap — MOD-104.

職責：
1. FastAPI startup → init_pool + advisory lock + alembic upgrade head
2. FastAPI shutdown → close_pool

Migration trigger 策略：startup-auto-with-advisory-lock
(deploy-env.json _deploymentDecisions.migrationTrigger USER CONFIRMED)

對應 SD code-arch.md §3.4 MOD-104。
對應 SA functional-flow.md FUNC-101 / FUNC-102 / FUNC-103 / FUNC-104。
"""
from __future__ import annotations

import logging
from pathlib import Path

from psycopg import connect

# IMPORTANT: import absolute "auth.database" (not ".auth.database") so this
# matches the module object that auth_router/oauth_router/verify_client see.
# Otherwise Python treats web.auth.database and auth.database as two distinct
# modules with separate _pool state -> init runs against one, request handlers
# see the other (uninitialized) -> RuntimeError "pool not initialized".
try:
    from auth.database import init_pool, close_pool, _build_dsn_from_env
except ImportError:  # fallback if executed as a package (e.g. unit test)
    from .auth.database import init_pool, close_pool, _build_dsn_from_env  # type: ignore

logger = logging.getLogger(__name__)

ADVISORY_LOCK_KEY = 0xCAFE0102  # 全域唯一 lock identifier；hex CAFE + TASK 0102；不可改


def run_migrations() -> None:
    """應用 startup 時自動套用所有未套用的 migration。

    使用 PG advisory lock 避免多 instance / 多 worker 同時跑 migration。

    Raises:
        alembic.util.exc.CommandError: ERR-MIGRATION-001 / ERR-MIGRATION-002
    """
    from alembic.config import Config
    from alembic import command

    dsn = _build_dsn_from_env()
    # alembic.ini 位於專案根 (web/db_bootstrap.py 的 ../alembic.ini)
    alembic_ini = Path(__file__).resolve().parent.parent / "alembic.ini"

    with connect(dsn, autocommit=True) as lock_conn:
        with lock_conn.cursor() as cur:
            # 非 blocking 嘗試取 lock
            cur.execute("SELECT pg_try_advisory_lock(%s)", (ADVISORY_LOCK_KEY,))
            got_lock = cur.fetchone()[0]

            if not got_lock:
                logger.info(
                    "Migration advisory lock busy — waiting for other instance..."
                )
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
    """FastAPI app startup hook — 註冊於 web/main.py lifespan。"""
    logger.info("Initializing PostgreSQL connection pool...")
    init_pool()
    logger.info("Running migrations...")
    run_migrations()
    logger.info("DB bootstrap complete.")


def on_shutdown() -> None:
    """FastAPI app shutdown hook — 註冊於 web/main.py lifespan。"""
    logger.info("Closing PostgreSQL connection pool...")
    close_pool()
