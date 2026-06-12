---
document_id: "DEPLOYGUIDE-TASK-002-v1.0"
title: "Production 部署操作手冊 — SQLite → PostgreSQL 持久化遷移"
version: "1.0"
date: "2026-06-12"
author: "Deployer (Execute)"
task_id: "TASK-002"
phase: "deploy"
scope: "full"
target_environment: "Railway production (https://snowboarding-support-system-jp-production.up.railway.app)"
prerequisites:
  - "build-gate v2.0 PASS [92] (5 IMPL_BUGs fixed, 8/8 mandatory tasks PASS)"
  - "code-review CONDITIONAL_PASS [86] approved with user waiver"
  - "MAJ-1 已在 Execute 階段同步修補（Dockerfile.be SoT）"
approval:
  reviewer: "User (PM)"
  date: ""
  result: "Pending"
---

# Production 部署操作手冊 — TASK-002

> 此手冊供使用者（單人專案 owner）執行 SQLite → PostgreSQL production cutover。
> 步驟按時間軸：**前置確認 → Railway 自建 PG container 配置 → 部署觸發 → 健康檢查 → 回滾程序（如需）**

---

## 1. 參數總表（Local + Prod）

| Env Var | Local 值（docker-compose） | Production 值（Railway dashboard） | Secret | Source |
|---------|--------------------------|----------------------------------|--------|--------|
| POSTGRES_HOST | `postgres` (docker service) | `postgres.railway.internal`（自建 container 內網 service name）| ❌ | service-contract.yaml |
| POSTGRES_PORT | `5432` | `5432` | ❌ | 同上 |
| POSTGRES_USER | `snowtrip` | **使用者填**（建議 `snowtrip_prod` 或保持 `snowtrip`） | ❌ | 同上 |
| POSTGRES_PASSWORD | `change_me_locally_only` | **使用者填**（≥ 32 chars 隨機產生）| ✅ | 同上 |
| POSTGRES_DB | `snowtrip` | `snowtrip` | ❌ | 同上 |
| POSTGRES_SSL_MODE | `disable` | `disable`（USER CONFIRMED 2026-06-09 自建 container 預設無 SSL；future hardening 留後續 TASK）| ❌ | deploy-env.json |
| DATABASE_URL（替代）| `postgresql+psycopg://snowtrip:CHANGE_ME@postgres:5432/snowtrip?sslmode=disable` | （可選 — 若設則 POSTGRES_* 5 個可省）| ✅ | service-contract.yaml |
| POSTGRES_POOL_MIN | `2` | `2` | ❌ | NFR-005 |
| POSTGRES_POOL_MAX | `10` | `10` | ❌ | NFR-005 |
| POSTGRES_POOL_TIMEOUT_MS | `5000` | `5000` | ❌ | NFR-005 |
| SECRET_KEY [REUSE] | `dev_secret_change_me_in_local` | **既有 Railway 已設**（[REUSE: TASK-001]） | ✅ | brownfield |
| SERPAPI_API_KEY [REUSE] | （從 .env 載入）| **既有 Railway 已設**（[REUSE: TASK-001]） | ✅ | brownfield |
| PORT [REUSE] | `8000` | **Railway 動態注入** | ❌ | Railway grandfather |

⚠️ **未在 contract 中的 env var**（code-review MIN-4，列 follow-up）:
- `RUN_DB_BOOTSTRAP`：未設則預設 `"1"` 啟用 bootstrap；prod 無需特別設置

---

## 2. 本地部署（dev 環境 — 開發者驗證用）

### 2.1 前置安裝

```bash
# 確認 Docker Desktop 啟動（Windows / macOS）
docker --version          # Expected: Docker version 24+ 
docker compose version    # Expected: v2+
```

### 2.2 本地啟動

```bash
# 1. 進入 repo 根目錄
cd D:/SideProject/snowboarding_support

# 2. 複製 env 範本（若尚未做過）
cp .sdlc/tasks/TASK-002/deploy/.env.example .env
# 編輯 .env 填入本機值（POSTGRES_PASSWORD 等）

# 3. 啟動完整環境（PG + Backend）
docker compose -f .sdlc/tasks/TASK-002/deploy/docker-compose.yml up -d

# 4. 等待 healthy
docker compose -f .sdlc/tasks/TASK-002/deploy/docker-compose.yml ps
# Expected: 兩個 container 都 (healthy)

# 5. 驗證健康檢查端點 (API-101)
curl http://localhost:8000/api/db/healthz
# Expected: {"status":"ok","db":{"connected":true,"pool":{...}},"migration":{"current":"20260610_120100","head":"20260610_120100","up_to_date":true}}
```

### 2.3 本地驗證 pytest（與 build-gate v2.0 等同）

```bash
# 創 Python venv
python -m venv .venv
.venv/Scripts/activate   # Windows PowerShell: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
pip install pytest pytest-asyncio 'testcontainers[postgres]'

# 跑全部測試（會用 testcontainers 啟動臨時 PG container）
pytest web/auth/tests/ -v
# Expected: 8 passed in ~7s
```

### 2.4 停止本地

```bash
docker compose -f .sdlc/tasks/TASK-002/deploy/docker-compose.yml down
# 注意：不加 -v 不會刪 volume，下次啟動資料保留
# 若要清空: docker compose ... down -v
```

---

## 3. Production 部署到 Railway（核心流程）

### 3.1 Step 1 — 設定 Railway PostgreSQL container service

> Railway production 採「自建 postgres:16-alpine container」（非 managed addon）— USER CONFIRMED 2026-06-09。

**作業步驟（首次）:**

1. 登入 Railway dashboard：`https://railway.app/dashboard`
2. 進入專案 `snowboarding-support-system-jp-production`
3. 右上角 `+ New` → `Database` → `Add PostgreSQL`
   - **❌ 不要選此選項**（這會建 managed addon，與本 TASK 決策相違）
   - 改選 `+ New` → `Service` → `Deploy from Docker Image` → 輸入 `postgres:16-alpine`
4. 設定 service：
   - **Service name**: `postgres`
   - **Internal port**: `5432`
   - **Public networking**: ❌ 關閉（內網連線即可，避免 PG 對外暴露）
   - **Environment variables**:
     - `POSTGRES_USER` = `snowtrip`
     - `POSTGRES_PASSWORD` = `<產生 ≥32 chars 隨機字串，記錄到 1Password / Keychain / 本地加密筆記>`
     - `POSTGRES_DB` = `snowtrip`
   - **Volumes**: 建立 named volume `sdlc-db-prod` → mount 到 `/var/lib/postgresql/data`
5. Deploy 此 service，等 healthy（Railway dashboard 顯示綠燈）

⚠️ **關鍵**: Volume 必須先設定，否則 redeploy 後資料消失（USER ACKNOWLEDGED 2026-06-09）。

### 3.2 Step 2 — 設定既有 backend service 環境變數

在既有 `snowboarding-support-system-jp` service 的 Variables 頁：

| 新增 Variables | 值 |
|--------------|-----|
| POSTGRES_HOST | `postgres.railway.internal` （Railway 內網 service name） |
| POSTGRES_PORT | `5432` |
| POSTGRES_USER | `snowtrip`（與 PG service 一致） |
| POSTGRES_PASSWORD | `<從 PG service 變數複製同值>` |
| POSTGRES_DB | `snowtrip` |
| POSTGRES_SSL_MODE | `disable` |
| POSTGRES_POOL_MIN | `2` |
| POSTGRES_POOL_MAX | `10` |
| POSTGRES_POOL_TIMEOUT_MS | `5000` |

**既有變數確認保留**:
- SECRET_KEY ✅
- SERPAPI_API_KEY ✅
- PORT（Railway 自動注入，無需手動設） ✅

**儲存**後 Railway 會自動觸發 redeploy。**先別讓它觸發** — 我們要先把 code merge。

### 3.3 Step 3 — 設定 GitHub Environment "production" 審批 gate

> Rule 11 IRREVERSIBLE 要求（FUNC-107 production cutover）+ deploy-env.json.prodApproval.required=true

1. 在 GitHub repo: Settings → Environments → New environment → name = `production`
2. 開啟 **Required reviewers**：加入 `@blacktea881030`（per deploy-env.json.prodApproval.requiredReviewers）
3. Wait timer: 0 minutes（單人專案）
4. Deployment branches: `Selected branches and tags` → 只允許 `main`

> 本 TASK Execute 階段已產出 `.sdlc/tasks/TASK-002/deploy/cicd-workflow.yml`；該 workflow 不直接 deploy（Railway 自動接管），但若未來想增加 `deploy-prod.yml` 走 `environment: production`，可參考 cicd-workflow.yml 註解區。

### 3.4 Step 4 — 在 PR 上 merge 觸發部署

```bash
# 確認 branch 已 push
git push origin sdlc/TASK-002/sqlite-to-postgres

# 在 GitHub UI 開 PR → 等 CI workflow 全綠
# CI workflow 包含: lint / security / test-backend / test-migration / env-consistency / ci-gate

# 觀察 PR check 結果（所有 required job 必須 PASS）
gh pr checks
```

### 3.5 Step 5 — Merge to main → Railway 自動 redeploy

```bash
# 在 GitHub UI 按 Merge（建議 Squash and merge）
# Railway GitHub App 接收 push event → 自動觸發 redeploy
```

Railway redeploy 流程（在 Railway dashboard 觀察）：
1. **Build phase**: railway.toml 執行 `pip install -r requirements.txt`
2. **Deploy phase**: 啟動 `uvicorn web.main:app --host 0.0.0.0 --port $PORT`
3. **Lifespan startup**: `web/main.py` lifespan asynccontextmanager 執行：
   - `init_pool()` → 建立 psycopg_pool 連線到 `postgres.railway.internal:5432`
   - `run_migrations()` → 取 PostgreSQL advisory lock `0xCAFE0102` → 跑 `alembic upgrade head` → 釋放 lock
   - 兩個 migration（`20260610_120000_create_initial_schema` + `20260610_120100_add_softdelete_columns`）執行
4. **Healthcheck**: Railway 對 `/api/auth/me` 發 GET → 預期 401（未登入是正常） → service 標 healthy → 切流量

⚠️ **預期啟動時間**: 比 SQLite 多 ~2 秒（NFR-003 SLA）— 首次 cold start migration 跑 ~1 秒；後續 idempotent check ~100ms。

---

## 4. 健康驗證（部署完成後 5 分鐘內必做）

### 4.1 Smoke Test — 既有業務端點

```bash
PROD_URL="https://snowboarding-support-system-jp-production.up.railway.app"

# 1. 主頁可達
curl -I "$PROD_URL/"
# Expected: 200 OK

# 2. 未登入 /api/auth/me 回 401（既有 healthcheck endpoint）
curl -I "$PROD_URL/api/auth/me"
# Expected: 401 Unauthorized

# 3. 新 API-101 健康檢查端點
curl "$PROD_URL/api/db/healthz"
# Expected: 200 OK + JSON {"status":"ok","db":{"connected":true,"pool":{...}},"migration":{"current":"20260610_120100","head":"20260610_120100","up_to_date":true}}
```

⚠️ **若 `/api/db/healthz` 回 503**: DB 連線異常 → 立即查 Railway logs → 走 §6 rollback 程序。

### 4.2 業務流程驗證

| 流程 | 驗證 |
|------|------|
| 登入 | 用既有 user 登入 — JWT cookie 設置正常 |
| 收藏滑雪場 | 加 → 查 → 刪 三步驟（NFR-002 AC-032~036） |
| 機票搜尋 | 進 /plan 搜尋一次 — SERPAPI 仍正常 |
| Email 驗證信 | 註冊新 test user → 收信 → 點連結驗證 |

→ 完整 22 AC 由 build-gate v2.0 task 6 pytest 8/8 covered，但 prod cutover 後仍建議實際操作 1 次。

### 4.3 Railway Logs 觀察（前 30 分鐘）

```bash
# 用 Railway CLI（若已安裝）
railway logs -n 200 | grep -iE "error|warning|migration|pool"

# 或在 Railway dashboard → Deployments → 該次 deploy → Logs
```

關注 keyword:
- `init_pool` — 應出現 1 次成功訊息
- `alembic.runtime.migration` — 應出現 2 個 migration 成功（或 idempotent skip）
- `ERR-DB-001` / `ERR-DB-002` — 任何出現都需立刻調查
- `ERR-SYS-006` — env var 缺失（檢查 Variables 設定）
- `ERR-MIGRATION-001` / `ERR-MIGRATION-002` — migration 失敗

---

## 5. 連線資訊

| 環境 | URL / Endpoint |
|------|----------------|
| Local | http://localhost:8000 |
| Local DB | `localhost:5432` (docker-compose 對外 mapping) |
| Production | https://snowboarding-support-system-jp-production.up.railway.app |
| Production DB | `postgres.railway.internal:5432` (內網 only) |

---

## 6. Rollback 程序（不可逆操作 — Rule 11）

### 6.1 Rollback 觸發條件

| 條件 | 動作 | 緊急度 |
|------|------|-------|
| Railway healthcheck fail > 2 分鐘 | **自動 rollback to N-1 build**（Railway 平台行為） | 自動 |
| API-101 `/api/db/healthz` 回 503 持續 > 5 分鐘 | 手動觸發 §6.2 Railway rollback | 高 |
| 5xx error rate > 5× baseline 持續 10 分鐘 | 手動觸發 §6.2 Railway rollback | 高 |
| DB connection error > 30 分鐘無法恢復 | 啟動 §6.3 14 天 SQLite emergency path | 極高 |
| Production 資料邏輯錯誤需 DB downgrade | §6.4 Alembic downgrade（with caveats）| 中 |

### 6.2 Railway 平台 Rollback

```
1. Railway dashboard → Project → Deployments
2. 找到最後一個健康的 deploy（綠燈 + healthy）
3. 點該 deploy → 右上「⋯」→ Redeploy
4. 等 healthcheck 通過（< 3 分鐘）
5. 驗證 §4.1 smoke test 全綠
```

⚠️ **DB 狀態**: Railway redeploy 只回滾 app code，**不回滾 DB schema**。若新版本已跑 migration 改變 schema，舊版 app 可能在新 schema 上仍可運作（因 NFR-002 行為不變 + expand-contract pattern），但若舊版用到已 DROP 的欄位則會出錯。本 TASK 兩個 migration 全為 ADD COLUMN（無 DROP），舊版兼容。

### 6.3 14 天 SQLite Emergency Path（極端情況）

> 觸發前提：PG 災難（資料毀損 / 連線完全失能 > 1 hr）+ 在 production cutover 後 14 天內。
> deploy-env.json 確認此為**唯一**目前可用的 backup 機制（PG backup DEFERRED_TO_FUTURE_TASK）。

```bash
# Step 1: Railway dashboard 移除 backend service 的 POSTGRES_* env vars
#   （保留 SECRET_KEY / SERPAPI_API_KEY / PORT）
#   注意：POSTGRES_PASSWORD 等可暫存，移除主要是讓 _build_dsn_from_env 走 fallback path

# Step 2: 找到 PG migration merge commit
git log --oneline --grep="TASK-002" --grep="postgres" --all | head -5

# Step 3: revert merge commit
PG_MERGE_SHA=<從上一步找到的 commit hash>
git checkout main
git pull origin main
git revert -m 1 "$PG_MERGE_SHA"
git push origin main

# Step 4: Railway 自動 redeploy SQLite 版本（從 git history 還原）
#   等待 ~3-5 分鐘 build + healthy

# Step 5: 驗證 SQLite app 啟動
curl https://snowboarding-support-system-jp-production.up.railway.app/api/auth/me
# Expected: 401（既有 brownfield 行為）

# Step 6: 接受 SQLite ephemeral 特性 — Railway 重啟資料會丟（CLAUDE.md 明示）
#   開新 TASK 評估永久 backup 策略
```

⚠️ **限制**: SQLite emergency path 不能恢復 PG 上的最新資料；只能讓 app 在 SQLite 重新空白起步。**這是最後手段**。

### 6.4 Alembic DB Schema Downgrade（極謹慎使用）

> Build-gate v2.0 已實證 `alembic upgrade head → downgrade -1 → upgrade head` 冪等。

```bash
# 1. 連到 production PG（透過 Railway CLI 開 tunnel）
railway run --service postgres -- psql

# 2. 在 psql 內檢視當前 head
SELECT version_num FROM alembic_version;

# 3. 退出 psql，本地跑 alembic downgrade
#    需設好 POSTGRES_HOST / POSTGRES_PASSWORD 等指向 prod
export DATABASE_URL='postgresql+psycopg://...prod conn string...'
alembic downgrade -1

# 4. 注意：downgrade 會 DROP COLUMN！
#    本 TASK 兩個 migration:
#      - 0001 create_initial_schema (downgrade = DROP all tables)
#      - 0002 add_softdelete_columns (downgrade = DROP 7 columns)
#    Downgrade 0002 安全（資料保留，只去 softdelete 欄位）
#    Downgrade 0001 = 整庫 DROP — 等同 §6.3 SQLite emergency
```

### 6.5 前置要求（已就緒）

| 項目 | 狀態 |
|------|------|
| Image tag 固定 | ✅ Railway nixpacks 自動生成 commit SHA tag |
| 保留 ≥ 3 個歷史 deploys | ✅ Railway 預設保留 50 個 deploy 紀錄 |
| Migration 向後相容（expand-contract） | ✅ 兩個 migration 全為 ADD COLUMN，舊版 app 兼容 |
| 14 天 SQLite emergency path | ✅ `web/auth/database_sqlite.py` 已保留於 git |

---

## 7. 故障排除

### 7.1 啟動失敗：`ERR-SYS-006 Missing required PostgreSQL env vars`

**原因**: Railway backend service 漏設 POSTGRES_HOST / USER / PASSWORD / DB 任一個
**解法**: 重新檢查 §3.2 表格，全部填齊；儲存後 Railway 會自動 redeploy

### 7.2 啟動失敗：`alembic.command.upgrade ... advisory lock timeout`

**原因**: 兩個 worker 同時搶 advisory lock 0xCAFE0102（本應由 single-worker Railway 不發生）
**解法**: Railway dashboard 確認只啟動 1 個 replica；若 logs 顯示 `Got lock = false` → 等 60s 重試（advisory lock 設計如此）

### 7.3 healthz 回 503: `{"status":"down","db":{"connected":false,"error":"ERR-DB-001"}}`

**原因**: PG container 未就緒 / 網路問題 / POSTGRES_HOST 錯字
**解法**:
1. Railway dashboard 確認 `postgres` service 狀態 healthy
2. 確認 backend service `POSTGRES_HOST` 是 `postgres.railway.internal`（精確拼字）
3. 若 PG 真的 down → 走 §6.3 SQLite emergency path

### 7.4 healthz 回 200 但 `up_to_date: false`

**原因**: alembic_version 表中的 current 與 migrations/versions/ 內的 head 不一致
**解法**:
1. 連 production PG: `railway run --service postgres -- psql`
2. `SELECT version_num FROM alembic_version;`
3. 比對 `migrations/versions/*.py` 檔名前綴最大值
4. 若 stale → 手動 `alembic upgrade head`

### 7.5 業務功能異常但 healthz 顯示 ok

**原因**: 應用層 bug（非 DB 層）
**解法**: 走 §6.2 Railway rollback 到 N-1 build；本 TASK NFR-002 強制行為不變，異常通常代表 cutover 過程踩雷

---

## 8. MAJ-1 處置紀錄（Code-Review 信心 95 — 已閉環）

> Code-Review 報告指出 `.sdlc/tasks/TASK-002/deploy/Dockerfile.be` SoT 模板未同步 build-gate v2.0 修補的 2 個 IMPL_BUG（缺 `COPY alembic.ini` + healthcheck 用錯誤 spider 法）。User 同意 waive 因為 Railway prod 用 nixpacks 不會踩雷。

**Execute 階段處置（cross_phase_sync）**:

1. ✅ **已同步** `.sdlc/tasks/TASK-002/deploy/Dockerfile.be`:
   - 加入 `COPY --chown=appuser:appuser alembic.ini ./`（解 IMPL_BUG-1）
   - HEALTHCHECK 改為 `wget --quiet --output-document=- "/api/db/healthz" | grep -q '"status":"ok"'`（解 IMPL_BUG-3）
2. ✅ 記錄在 Dockerfile.be 註解區（明示 cross_phase_sync 性質，非新 IMPL_BUG）
3. ✅ 本 deploy-guide.md 此章節留證據鏈

**影響範圍**:
- ✅ 後續任何 Docker-based 環境（local docker-compose / CI / 若 Railway 改用自定 Dockerfile）不再踩 IMPL_BUG-1/3
- ℹ️ Railway production 目前用 nixpacks（不讀 Dockerfile.be）→ 不影響當前 prod
- ℹ️ MAJ-2（MOD-103 dead code）+ MAJ-3（test-be framework gap）仍如 user waiver 為 follow-up，不在本 Execute 範圍

**Audit log 將記為**: `[ISO] deployer | TASK-002 | cross_phase_sync | Dockerfile.be | sync build-gate IMPL_BUG-1+3 fixes`

---

## 9. 部署完成後追蹤項

| 項目 | 時機 | 動作 |
|------|------|------|
| 14 天 SQLite emergency window | Production cutover 後 14 天 | 開新 TASK 正式移除 `database_sqlite.py` + 評估永久 backup |
| MAJ-2 MOD-103 dead code | 下次 SDLC TASK | 移除或重構 `web/auth/repositories.py` |
| MAJ-3 test-be framework gap | SDLC framework PR | 強化 test-be 對 Dockerfile / SQLAlchemy driver / DSN 的靜態驗證 |
| MIN-4 RUN_DB_BOOTSTRAP 未登記 | 下次 TASK 順手 | 補到 service-contract.yaml + parameter-registry |
| deep-translator 漏洞追蹤（PYSEC-2022-252） | 下次 TASK 順手 | 升級版本或替換套件 |
| pip 25.0.1 → 26.1 | CI/CD 環境維護 | workflow setup-python action 內加 `pip install --upgrade pip` |
| **MAJ-AC1** docker-compose.yml Init 模板 healthcheck 殘留 | 下次 TASK 順手（同 MAJ-1 處置 pattern）| 把 `/api/auth/me --spider grep '(401\|200)'` 改成 `/api/db/healthz` 並 grep `"status":"ok"`；Railway prod 不受影響（nixpacks 不讀 compose）|
| **MIN-AC1** deploy-guide §3 缺 cicd-workflow.yml manual cp 指引 | 下次 SDLC TASK | 在 §3 加 step：`cp .sdlc/tasks/TASK-002/deploy/cicd-workflow.yml .github/workflows/ci-be.yml` |
| **MIN-AC2** §6.4 Alembic prod downgrade 缺 `railway run` 指引 | 下次 SDLC TASK | 加註：「prod PG 在 Railway internal network，需用 `railway run alembic downgrade -1`」|
| **MIN-AC3/AC4** implementation-report 文字微差 + API-101 operationId 偏差 | 下次 SDLC TASK 順手 | report 校正 + operationId 標準化 |

> 以上 4 個新項目來自最終驗收測試（test acceptance 2026-06-12，CONDITIONAL_PASS 91/100，agentId a4891009efe441ec0）。User 同意 follow-up 不阻塞本 TASK closure。

---

## 10. 追溯矩陣

| 操作步驟 | 來源規格 |
|---------|---------|
| §3.1 自建 PG container | deploy-env.json._deploymentDecisions.postgresHosting (USER CONFIRMED 2026-06-09) |
| §3.2 13 env vars | service-contract.yaml services.backend.env_vars |
| §3.3 GitHub Environment production | Rule 11 IRREVERSIBLE + deploy-env.json.prodApproval |
| §3.5 advisory lock 0xCAFE0102 | sd/code-arch.md MOD-104 + be/implementation-report.md |
| §4.1 healthz 端點 | API-101 sd/api-spec.md §2 |
| §6.2 Railway rollback | deploy-plan.md §5 + deploy-env.json.deployStrategy=rolling |
| §6.3 SQLite emergency 14 天 | SA SUG-006 + FUNC-107 IRREVERSIBLE mitigation |
| §6.4 Alembic downgrade | build-gate v2.0 task 7 idempotency PASS |
| §8 MAJ-1 處置 | code-review MAJ-1 + user waiver + deploy-execute cross_phase_sync |
