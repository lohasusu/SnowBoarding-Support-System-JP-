# Dockerfile.be — TASK-002 Backend Dockerfile (Execute 階段 v2)
#
# 本 TASK 為 FastAPI monolith（單服務）；此 Dockerfile 供：
#   1. 本機 docker-compose dev 環境
#   2. CI/CD pipeline 建構驗證（GitHub Actions）
#   3. 若未來 Railway 改用自定 Dockerfile（目前 prod 用 nixpacks，本檔不強制）
#
# === Execute 階段 v2 同步紀錄 (2026-06-12) ===
# 本檔在 Execute 階段同步了 build-gate v2.0 在 Dockerfile.task002 中修補的 3 個 IMPL_BUG：
#   IMPL_BUG-1: 缺 COPY alembic.ini → backend 啟動時 alembic 找不到 script_location → exit 3
#   IMPL_BUG-3: HEALTHCHECK 用 /api/auth/me + wget --spider (HEAD) → 405 Method Not Allowed → 永遠 unhealthy
#   ENV_BUG-5: alembic.ini 含中文 + Windows cp950 → UnicodeDecodeError（已在 alembic.ini ASCII 化，此處無修補需要）
#
# Code-Review MAJ-1（信心 95）指出 SoT 模板未含這些修補；Execute 階段已閉環。
# 變更類別記為 cross_phase_sync（非新 IMPL_BUG）— 詳見 deploy-guide.md §8.
# ============================================================

# === Stage 1: builder ===
FROM python:3.12-slim AS builder

WORKDIR /build

# 系統依賴（psycopg / asyncpg 編譯需要 — SD 已選定 psycopg3）
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# === Stage 2: runtime ===
FROM python:3.12-slim AS runtime

WORKDIR /app

# Runtime 依賴（libpq5 for psycopg3 runtime）+ wget for healthcheck（GET 模式）
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    wget \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --create-home --shell /bin/bash --uid 1000 appuser

# 從 builder 複製 packages
COPY --from=builder /install /usr/local

# 複製應用程式碼
COPY --chown=appuser:appuser web/ ./web/
COPY --chown=appuser:appuser flight_search/ ./flight_search/
COPY --chown=appuser:appuser http_scraper.py ./
COPY --chown=appuser:appuser migrations/ ./migrations/

# === [Execute v2 修補 IMPL_BUG-1] COPY alembic.ini ===
# 缺此一行 → /app/alembic.ini 不存在 → migrations/env.py 讀 Config(None) → 'No script_location key' →
# db_bootstrap.run_migrations() 拋 KeyError → FastAPI lifespan startup 失敗 → container exit 3
COPY --chown=appuser:appuser alembic.ini ./

USER appuser

ARG BE_PORT=8000
ENV PORT=${BE_PORT}
EXPOSE ${PORT}

# === [Execute v2 修補 IMPL_BUG-3] HEALTHCHECK 切換到 GET /api/db/healthz ===
# 原問題: /api/auth/me 用 wget --spider (HEAD) 回 405；grep '(401|200)' 永不命中
# 新策略: 使用 API-101 GET /api/db/healthz，回 200 + JSON body 含 "status":"ok"
# 優點: 同時驗證 app + DB pool + alembic migration 三個層次健康
# 失敗時 API-101 回 503 + body "status":"down"，grep "status":\"ok\" 不命中 → exit 1
HEALTHCHECK --interval=10s --timeout=5s --start-period=30s --retries=5 \
    CMD wget --quiet --tries=1 --output-document=- "http://localhost:${PORT}/api/db/healthz" 2>/dev/null | grep -q '"status":"ok"' || exit 1

# Entrypoint — CLAUDE.md 鎖定不可改
CMD ["sh", "-c", "uvicorn web.main:app --host 0.0.0.0 --port ${PORT}"]

# === [DEPLOYER 備註 Execute v2] ===
# 本檔在 Execute 階段已同步 build-gate v2.0 治根修補（解 Code-Review MAJ-1）。
# 後續任何 Docker-based 環境（local docker-compose / CI / 若 Railway 改用自定 Dockerfile）
# 都應以此 SoT 為基底；不再有 Dockerfile.task002（gitignored test-only）與 SoT 不一致的隱憂。
#
# Railway production 目前透過 nixpacks buildpack 部署（不使用此 Dockerfile）；
# 若未來改用自定 Dockerfile，可直接 cp 此檔到 repo 根目錄為 Dockerfile，再於 railway.toml 設 `builder = "DOCKERFILE"`。
