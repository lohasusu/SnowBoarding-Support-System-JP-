---
document_id: "MIGSTRAT-TASK-002-v1.0"
title: "Migration 觸發 + Backup + Rollback 策略"
version: "1.0"
date: "2026-06-09"
author: "Deployer (Init)"
status: "Draft"
task_id: "TASK-002"
phase: "deploy-init"
source_documents:
  - "ARCH-TASK-002-v1.0 (SA system-arch.md)"
  - "FUNC-TASK-002-v1.0 (SA functional-flow.md FUNC-103/104/107)"
  - "BF-TASK-002-v1.0 (BA business-flow.md BF-002/003)"
  - "CONTRACT-TASK-002-v1.0 (service-contract.yaml rollback_strategy)"
  - "deploy-env.json _deploymentDecisions"
  - "SA SUG-006 (14 天 SQLite emergency path)"
  - "SA SUG-104 (Migration log 結構化)"
approval:
  reviewer: "PM"
  date: ""
  result: "Pending"
---

# Migration 觸發 + Backup + Rollback 策略

> 解決 5 個 [BLOCKED_ON_DEPLOYER] 中與 migration / backup / rollback 相關的 3 項：
> - #2 SSL 模式
> - #3 Backup 策略
> - 部分 #4 Production SLA dashboard
>
> FUNC-107 [IRREVERSIBLE] production cutover 的緩解措施落地細節

---

## 1. Migration 觸發策略

### 1.1 推斷決策（待 PM/使用者確認）

| 項目 | 決策 | 來源 |
|------|------|------|
| 觸發時機 | **應用啟動時自動跑（startup auto）** | [Deploy 推斷 — 待確認] |
| Race condition 防護 | **PostgreSQL advisory lock**（SD 階段實作） | NFR-005 + 本 TASK 設計 |
| 工具 | [BLOCKED_ON_SD] Alembic / yoyo-migrations / 手寫 SQL runner | SA-BC-3 + AC-049 |

### 1.2 觸發流程（FUNC-101 + FUNC-103 啟動鏈）

```mermaid
sequenceDiagram
    participant App as FastAPI Startup
    participant Lock as PG Advisory Lock
    participant Mig as Alembic (or chosen tool)
    participant DB as PostgreSQL

    App->>App: @app.on_event("startup")
    App->>App: MOD-101 init_pool()
    App->>DB: connect (POSTGRES_*)
    alt 連線失敗
        DB-->>App: OperationalError
        App-->>App: raise → uvicorn 啟動失敗 → Railway healthcheck fail
    else 連線成功
        App->>Lock: SELECT pg_try_advisory_lock(12345)
        alt 已有其他 worker 持鎖
            Lock-->>App: false → skip migration（其他 worker 在跑）
        else 取得 lock
            Lock-->>App: true
            App->>Mig: upgrade head
            Mig->>DB: BEGIN; CREATE TABLE...; INSERT schema_migrations; COMMIT
            alt migration 失敗
                Mig->>DB: ROLLBACK
                App-->>App: raise MigrationError → 啟動失敗
            else 成功
                Mig-->>App: applied: 20260608_120000_create_initial_schema
                App->>Lock: SELECT pg_advisory_unlock(12345)
                App-->>App: 完成 startup → 接流量
            end
        end
    end
```

### 1.3 為什麼選 startup-auto（而非 CI/CD prerun）

| 比較項 | startup-auto | CI/CD prerun |
|--------|--------------|--------------|
| 複雜度 | 低（單一 entrypoint） | 中（CI runner 需連 PG） |
| 自建 PG container 適配 | ✅ docker-compose / Railway 內網（service name=postgres）直連 | ⚠️ 需開公網 + IP whitelist 或 Railway CLI |
| Race condition | 多 worker 風險 → advisory lock 解 | 無 |
| 失敗處理 | App 啟動失敗 → Railway auto rollback | CI fail → 不部署 |
| 部署速度 | startup 多 100-500ms（lock + check schema_migrations） | CI 多一階段 ~30s |
| NFR-003 SLA | ≤ SQLite + 2s（idempotent migration 已套用時極快） | ✅ migration 不計入啟動時間 |
| **本 TASK 結論** | ✅ 選此 | — |

### 1.4 NFR-003 啟動時間驗證計畫

| 場景 | 預期延遲 | 驗證方法 |
|------|---------|---------|
| 首次部署（migration 跑） | SQLite baseline + 5-10s（CREATE TABLE + INSERT schema_migrations） | test-be 階段 ab -n 1 量測 cold start |
| 既有部署（migration 已套用） | SQLite baseline + 0.5-1s（只查 schema_migrations） | 同上 |
| Migration 失敗 | 立即失敗（< 5s） | test-be 階段故意給錯 DDL 驗證 fail-fast |

**Acceptable**: SA NFR-003 允許 ≤ SQLite + 2s，本 TASK 首次部署超出但屬一次性事件；既有部署符合 SLA。

---

## 2. Backup 策略（解 [BLOCKED_ON_DEPLOYER] #3）

### 2.1 Dev 環境（本機 docker-compose）

| 項目 | 配置 |
|------|------|
| Backup 機制 | 無（named volume 持久化但不備份） |
| 資料保留 | `docker compose down` 不丟資料；`docker compose down -v` 清空 |
| 災難復原 | 本機開發資料不重要，re-run migration + seed script 重建 |
| 注意事項 | 開發者 .env 含 POSTGRES_PASSWORD 必須 gitignored |

> **⚠️ 2026-06-09 PM 修訂**：使用者實際選擇「自建 postgres:16-alpine container」（非 Railway PG addon）+「先不訂 PG backup，以後再說」。
> 本 §2.2-2.4 的 Railway daily backup 機制**不適用**於自建 container。
> 自建 container 在 Railway 沒有自動 backup — Railway 只會做 container layer 的 snapshot，不會 dump PG 邏輯資料。
> 因此 PG backup 已 **DEFERRED_TO_FUTURE_TASK**（見 deploy-env.json _deploymentDecisions.backupRollback.postgresBackup）。

### 2.2 Staging 環境（修訂後）

| 項目 | 配置 |
|------|------|
| Backup 機制 | **無自動 PG backup**（自建 container 不在 Railway addon 服務範圍） |
| Persistent volume | Railway named volume mount 到 `/var/lib/postgresql/data` — redeploy 不丟資料但無時間點還原能力 |
| 災難復原 | **DEFERRED** — 後續 TASK 評估 `pg_dump` cron 或改回 addon |
| 注意事項 | test-be 階段**不跑** backup restore 流程（無 backup 可測） |

### 2.3 Production 環境（修訂後）

| 項目 | 配置 |
|------|------|
| Backup 機制 | **無自動 PG backup**（USER CONFIRMED — DEFERRED_TO_FUTURE_TASK） |
| Persistent volume | Railway named volume — 提供 container restart 持久化但**不等於 backup** |
| PITR | ❌ 無 |
| 多區域備份 | ❌ 無 |
| 災難復原 RTO/RPO | **無定義** — 無 PG backup 即無 RPO；emergency 走 SQLite path |
| 緊急 path | **唯一可用 backup 機制** — 14 天 SQLite emergency path（SUG-006）— 詳見 §3.4 |
| 使用者已知接受風險 | ✅ 14 天 SQLite path 過期後若 PG 災難無 backup 可回；後續 TASK 評估方案前接受此風險 |

### 2.4 Backup 驗證計畫（修訂後 — test-be 階段不跑）

本 TASK scope 內**不安排** backup restore 驗證測試（因無 PG backup 機制可測）。

**替代驗證項目**（test-be 階段必跑）:
- ✅ 14 天 SQLite emergency rollback drill：模擬 PG 故障 → `git revert <pg-merge-commit>` → Railway 重新部署 SQLite → 確認 app 啟動 + 8 個 pytest 通過
- ✅ Persistent volume 持久化驗證：PG container restart → 資料不丟（透過 mount volume）
- ❌ ~~`railway service postgres backup create/restore`~~ — 移除（自建 container 不適用）

**後續 TASK 規劃（DEFERRED）**：
新開 TASK 評估 backup 方案，候選：
1. cron job 跑 `pg_dump` 輸出到 Railway persistent volume（最低成本，需自寫 scheduler）
2. cron job 跑 `pg_dump` 上傳到 S3 / R2（額外服務但 off-site 安全）
3. 改回 Railway PG addon（內建 daily backup 7 天，月費 $5）— 需評估 trade-off

---

## 3. Rollback 策略（FUNC-107 IRREVERSIBLE 緩解）

### 3.1 Rollback 觸發條件

| 觸發 | 自動 / 手動 | 動作 |
|------|------------|------|
| Railway healthcheck fail > 2 分鐘 | 🤖 自動 | rollback to N-1 build |
| BF-002 step 4 smoke test 失敗（5 步驟任一）| 👤 手動 | 走 BF-003 緊急回滾 |
| Production 5xx rate > 5× baseline 持續 10 分鐘 | 👤 手動（PM 決策） | 走 BF-003 |
| DB connection error 持續 > 30 分鐘 | 👤 手動 | 走 BF-003 |
| DB 資料毀損 / 完全失能 > 1 hr 無法恢復 | 👤 手動 | 啟動 14 天 SQLite emergency path（§3.4） |

### 3.2 Application Rollback（< 5 分鐘）

```bash
# Railway dashboard 操作
1. 進入 Service → Deployments
2. 選擇 N-1 build（前一版 PostgreSQL 版本）或 N-K（更早，視情況）
3. 點 "Redeploy"
4. Railway 自動部署該版本 + healthcheck

# Railway CLI 操作（自動化）
railway rollback --deployment-id <prev-deploy-id>
```

**Rollback Time Estimate**: < 3 分鐘（Railway PaaS 平台特性）

### 3.3 Migration Rollback（DB schema 還原）

**前置要求**: 所有 migration 必須 reversible（NFR-006）

```bash
# [BLOCKED_ON_SD: 工具選定後填入]
# 候選命令：
# Alembic:     alembic downgrade -1     # 退一個 migration
# yoyo:        yoyo rollback -1
# Manual:      psql -f migrations/20260608_120000_create_initial_schema_down.sql

# 本 TASK FUNC-103 down 流程（functional-flow.md §FUNC-103 Down/Rollback）：
DROP TABLE email_verification_tokens;
DROP TABLE favorites;
DROP TABLE users;
DELETE FROM schema_migrations WHERE version='20260608_120000_create_initial_schema';
```

**注意**: production migration rollback 會清空所有用戶資料！只在「14 天 emergency path 啟動 + 必須回到 SQLite」場景使用。

### 3.4 14 天 SQLite Emergency Path（SUG-006 + FUNC-107 IRREVERSIBLE 核心緩解措施）

**目的**: 為 FUNC-107 [IRREVERSIBLE] production cutover 提供「在切換後 14 天內仍可回退」的安全網。

**實作細節**（本 TASK Deploy(Execute) 階段必須落實）:

#### 3.4.1 程式碼層

```
1. 保留既有 web/auth/database.py 的 SQLite 實作於 git history
   - 不刪除 commit（git log 可追溯）
   - PR merge 訊息明確記錄「TASK-002 PG migration; SQLite path retained 14 days via git revert」
   - 在 .sdlc/tasks/TASK-002/deploy/deploy-result.md 記錄關鍵 commit SHA

2. database.py 重寫策略（FE/BE 階段必填）：
   - 不是「刪 SQLite + 新增 PG」單一 commit
   - 而是「新增 database_pg.py + 修改 import + 不刪 database.py 舊內容」分階段
   - 直到 14 天 window 過去，再開新 TASK 刪 database.py 舊邏輯
```

#### 3.4.2 部署層 Emergency Rollback 流程（14 天內可執行）

```bash
# Step 1: 確認 emergency window 仍有效
TODAY=$(date +%s)
CUTOVER_DATE=$(date -d "2026-06-XX" +%s)  # FUNC-107 完成日，填入實際日期
ELAPSED_DAYS=$(( (TODAY - CUTOVER_DATE) / 86400 ))
if [ $ELAPSED_DAYS -gt 14 ]; then
    echo "ERROR: Emergency window 已過（$ELAPSED_DAYS 天），無法簡單 rollback"
    echo "必須走完整 SDLC 新開 TASK 修正"
    exit 1
fi

# Step 2: 在 Railway dashboard 移除 PG env vars
#   - 刪除 POSTGRES_HOST/PORT/USER/PASSWORD/DB/SSL_MODE/POOL_*
#   - 保留 SECRET_KEY / SERPAPI_API_KEY / PORT

# Step 3: git revert PG migration merge commit
cd /path/to/snowboarding_support
PG_MERGE_COMMIT=$(git log --grep="TASK-002 PG migration" --format=%H | head -1)
git revert -m 1 $PG_MERGE_COMMIT
git push origin main

# Step 4: Railway 偵測 push → 自動 redeploy SQLite 版本
#   - 啟動指令不變：uvicorn web.main:app --host 0.0.0.0 --port $PORT
#   - SQLite db 從 web/data/snowtrip.db 重新初始化（ephemeral，預期空表）

# Step 5: 接受 SQLite ephemeral 缺陷重現
#   - 這是 emergency tradeoff，BA FR-007 已明示業務影響
#   - 此期間新註冊用戶在下次 Railway 重啟時消失
#   - 緊急修正 PG 問題後重新走 SDLC 流程
```

#### 3.4.3 Emergency Path 期間遺失資料風險

| 風險 | 評估 |
|------|------|
| Cutover 後 < 14 天內 PG 寫入的資料 | rollback 後消失（PG dump 可備份但 SQLite 無法匯入；需另開 TASK 處理）|
| SQLite 在 rollback 後接收的新註冊 | 既有 ephemeral 缺陷重現（用戶體驗倒退） |
| 14 天 window 過後仍有 issue | 必須走完整 SDLC 修 PG（不能再 emergency rollback） |

**[DEPLOYER建議] PG → SQLite 緊急資料保留腳本**（不在本 TASK 範圍，留 SUG）:
- 若使用者在 14 天 emergency window 啟動 rollback，建議先跑 `pg_dump --data-only > emergency_backup.sql` 留檔
- 後續修正完 PG 重新部署時，可手動 INSERT 該期間 PG 資料
- 屬於 P2 工具腳本，[SA-SUG-105] 建議列為後續 TASK 候選

#### 3.4.4 Emergency Path 過期後（>14 天）的政策

```
14 天後：
1. 新開 TASK（例如 `task-cleanup-sqlite-path`）
2. 刪除 web/auth/database.py 中的 SQLite 殘留邏輯
3. 從 docker-compose.yml / Dockerfile 移除 SQLite 相關設定
4. 確認 git history 仍可追溯（不 force-push）
5. 在 audit.log 記錄：[ISO] deployer | TASK-XXX | sqlite_path_removed | TASK-002 cutover passed 14-day window
```

---

## 4. SSL 模式策略（解 [BLOCKED_ON_DEPLOYER] #2）

| 環境 | SSL 模式 | 理由 |
|------|---------|------|
| dev (本機 docker-compose) | `disable` | localhost 同 host 通訊；container 間 private network；自簽 cert 增加開發摩擦 |
| staging (Railway preview) | `require` | 加密但不驗 cert；Railway 內部 network 預設提供 SSL cert |
| **production (自建 container — USER CONFIRMED 2026-06-09)** | **`disable`** | 自建 container 預設無 SSL；future hardening（self-signed cert / Let's Encrypt / sidecar proxy）留後續 TASK |

**SD 階段實作要求**:
- `POSTGRES_SSL_MODE` env var 從 `deploy/service-contract.yaml` 讀取
- driver 選定後（psycopg / SQLAlchemy）將此值傳入 connection string
- DATABASE_URL 替代方案：URL 中 `?sslmode=disable`（同優先級；自建 container 預設）

**驗證**:
```bash
# Production 驗證 SSL 真的啟用
railway run -- psql -c "SHOW ssl;"
# 預期: ssl = on
```

---

## 5. Production SLA Dashboard（解 [BLOCKED_ON_DEPLOYER] #4 部分）

### 5.1 本 TASK 涵蓋（Railway built-in）

| 指標 | 來源 | 警報閾值 |
|------|------|---------|
| HTTP 5xx rate | Railway dashboard → Service Metrics | > 5× baseline 持續 10 分鐘 → 觸發 BF-003 |
| Memory usage | Railway dashboard | > 90% 持續 5 分鐘 → 警告 |
| CPU usage | Railway dashboard | > 80% 持續 10 分鐘 → 警告 |
| Application logs | Railway dashboard → Logs | grep `OperationalError` / `MigrationError` → 警告 |
| Build success/failure | Railway dashboard → Deployments | 失敗即警告 |

### 5.2 本 TASK 規劃但需 SD/BE 階段實作

| 指標 | 實作方式 | 對應 FR/NFR |
|------|---------|------------|
| **DB connection error count** | MOD-101 catch OperationalError → counter += 1 → log structured JSON 到 stdout（Railway 自動收集） | NFR-005 + 新規格 |
| **Migration log 完整性** | MOD-102 Alembic stdout → grep 確認 `applied: <version>` 或 `Target database is not up to date` | FR-003 + AC-049 |
| **Health endpoint** | [SA-SUG-101 留後續 TASK] 目前用 `/api/auth/me` 401 代替 | — |

### 5.3 進階監控（不在本 TASK 範圍，[DEPLOYER建議]）

| 工具 | 用途 | 月費 | 建議 |
|------|------|------|------|
| Sentry | Error tracking + stack trace | Free tier 5k events/月 | **[DEPLOYER建議] 推薦**：production 上線後優先導入 |
| Datadog | APM + Logs + Metrics 一站式 | $15-31/month/host | 不適合單人專案（成本高） |
| Grafana Cloud | Dashboards + Prometheus + Loki | Free tier 50GB logs | 進階使用者選項 |
| UptimeRobot | 外部 uptime 監控 | Free 50 monitors | **[DEPLOYER建議] 推薦**：免費補強 Railway healthcheck |

**[DEPLOYER建議]**: production 上線 + 14 天 emergency window 結束後，開新 TASK 引入 Sentry + UptimeRobot（兩者皆有 free tier，無增加成本壓力）。

---

## 6. 追溯矩陣

| 策略項目 | 對應規格 |
|---------|---------|
| Startup-auto migration | SA FUNC-101 + FUNC-103 + NFR-003 |
| Advisory lock | NFR-005 + 防 race condition |
| ~~Daily backup (7 天)~~ | DEFERRED_TO_FUTURE_TASK — 自建 container 無自動 backup；USER CONFIRMED 2026-06-09 接受此 trade-off；14 天 SQLite emergency 為唯一 backup 機制 |
| 14 天 SQLite emergency path | SA SUG-006 + FUNC-107 IRREVERSIBLE 緩解 |
| ~~SSL `verify-full` (prod)~~ | DOWNGRADED — USER CONFIRMED 2026-06-09 自建 container prod sslmode=disable；BA SUG-005 hardening 留後續 TASK |
| SSL `disable` (dev) | 本機開發摩擦最小化 |
| Railway built-in metrics | test-ba INFO-2 + SA-SUG-104 |
| DB connection error counter | NFR-005 + 新規格 |

---

## 7. 後續階段交接

### → SD 階段
- 選定 migration 工具（Alembic / yoyo / 自寫）後，填補 §3.3 rollback 命令
- 實作 PG advisory lock（§1.2 lock id=12345 為示意，SD 確認唯一性）
- DB connection error counter 寫入 logic-flow.md（§5.2）

### → BE 階段
- web/auth/database.py 重寫策略遵循 §3.4.1：不是單一 commit 全替換，留 14 天 git revert 路徑
- MOD-101 連線失敗訊息**不含 password**（NFR-011）
- MOD-104 startup hook 實作 §1.2 流程圖

### → Deploy(Execute) 階段
- 落實 14 天 emergency window 文件記錄（deploy-result.md 含 cutover 日期 + key commit SHA）
- 驗證 backup 流程（§2.4）
- 設定 Railway Environment reviewers（deploy-env.json.prodApproval）

### → Tester (test-deploy) 階段
- Rule 11 D9 驗證：FUNC-107 IRREVERSIBLE 的 rollback plan 是否完整可執行
- §2.4 backup restore 驗收
- §3.4 14 天 emergency path 文件完整性
- SSL mode 三環境差異驗證
