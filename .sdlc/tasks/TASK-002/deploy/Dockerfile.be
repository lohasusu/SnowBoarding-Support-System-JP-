# Dockerfile.be — TASK-002 Backend Dockerfile 模板（Deploy Init）
#
# 本 TASK 為 FastAPI monolith（單服務）；此 Dockerfile 模板供：
#   1. 本機 docker-compose dev 環境
#   2. Execute 階段視需求推 ghcr.io（多 arch buildx — config.json 已規劃）
#   3. Railway production 仍可繼續用 nixpacks buildpack（不強制使用此 Dockerfile）
#
# 模板原則（Rule 4 — Init 模式不寫實值）：版本號、port、entrypoint 用 ARG/ENV

# === Stage 1: builder ===
FROM python:${PYTHON_VERSION:-3.12}-slim AS builder

WORKDIR /build

# 系統依賴（psycopg / asyncpg 編譯需要 — SD 階段選定 driver 後可微調）
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# === Stage 2: runtime ===
FROM python:${PYTHON_VERSION:-3.12}-slim AS runtime

WORKDIR /app

# Runtime 依賴（libpq5 for PG driver runtime）+ wget for healthcheck
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

USER appuser

ARG BE_PORT=8000
ENV PORT=${BE_PORT}
EXPOSE ${PORT}

# Healthcheck — service-contract.yaml 規定 /api/auth/me
HEALTHCHECK --interval=10s --timeout=5s --start-period=30s --retries=5 \
    CMD wget --no-verbose --tries=1 --spider "http://localhost:${PORT}/api/auth/me" 2>&1 | grep -qE '(401|200)' || exit 1

# Entrypoint — CLAUDE.md 鎖定不可改
CMD ["sh", "-c", "uvicorn web.main:app --host 0.0.0.0 --port ${PORT}"]

# === [DEPLOYER 備註] ===
# 本檔為模板（Init 模式），實際 Execute 階段可能：
# - 推 ghcr.io 用：docker buildx build --platform linux/amd64,linux/arm64 -t ghcr.io/.../snowboarding_support-backend:TASK-002 --push
# - Railway 用 nixpacks：本檔不啟用，railway.toml 控制
