---
document_id: "TEST-REPORT-DEPLOY-INIT-TASK-002-v1.0"
title: "Deploy(Init) 階段獨立測試報告 — TASK-002"
version: "1.0"
date: "2026-06-10"
author: "Tester (independent)"
task_id: "TASK-002"
phase: "test-deploy-init"
被測對象:
  - ".sdlc/tasks/TASK-002/deploy/service-contract.yaml"
  - ".sdlc/tasks/TASK-002/deploy/deploy-env.json (PM patched Q0 + Q3)"
  - ".sdlc/tasks/TASK-002/deploy/docker-compose.yml"
  - ".sdlc/tasks/TASK-002/deploy/docker-compose.template.yml"
  - ".sdlc/tasks/TASK-002/deploy/Dockerfile.be"
  - ".sdlc/tasks/TASK-002/deploy/Dockerfile.fe"
  - ".sdlc/tasks/TASK-002/deploy/Dockerfile.template"
  - ".sdlc/tasks/TASK-002/deploy/.env.example"
  - ".sdlc/tasks/TASK-002/deploy/deploy-plan.md"
  - ".sdlc/tasks/TASK-002/deploy/migration-strategy.md (PM patched §2.2-2.4)"
  - ".sdlc/tasks/TASK-002/deploy/parameter-plan.md"
  - ".sdlc/tasks/TASK-002/deploy/self-review.json (Deployer 自評 95)"
驗證基準:
  - ".sdlc/tasks/TASK-002/ba/requirement-spec.md (FR-005/006/007, NFR-003/005/011, CONST-007/009)"
  - ".sdlc/tasks/TASK-002/ba/business-flow.md (BF-002/003)"
  - ".sdlc/tasks/TASK-002/sa/system-arch.md (5 個 [BLOCKED_ON_DEPLOYER])"
  - ".sdlc/tasks/TASK-002/sa/functional-flow.md (FUNC-107 [IRREVERSIBLE])"
  - ".sdlc/tasks/TASK-002/sa/impact-assessment.md §4 + §6.2"
  - ".sdlc/tasks/TASK-002/test-sa/test-report-sa.md"
  - ".sdlc/conventions/api-conventions.md (UPPER_SNAKE_CASE)"
  - ".sdlc/conventions/db-conventions.md"
  - ".sdlc/environments.json"
  - "railway.toml + .github/workflows/* (既有 6 個 sdlc-*.yml)"
  - "docker-compose.yml (既有 root 通用模板)"
驗證方法論:
  - "Tester rules 1-4 (獨立 / 規格優先 / Critical 阻塞 / 100% 追溯)"
  - "Rule 11 (irreversible) + Rule 18 (parameter-registry) + Rule 19 (ci-gate) + Rule 10 (abandoned)"
  - "deploy-init 自訂 5 維度: D1 規格完整性 / D2 與 BA/SA 一致 / D3 使用者決策落地 / D4 FUNC-107 緩解 / D5 Rule 18 預規劃"
status: "Complete"
result: "CONDITIONAL_PASS"
---

# Deploy(Init) 階段獨立測試報告 — TASK-002

> Tester 站在獨立第三方立場：不為 Deployer agent 背書、不為 PM patches 背書。

## 1. 驗證摘要

| 指標 | 結果 |
|------|------|
| 檢查維度 | D1 規格完整性 / D2 BA·SA 一致 / D3 使用者決策落地 / D4 FUNC-107 緩解 / D5 Rule 18 預規劃 + Rule 10/11/18/19 protocol 合規 + 8 個 PM 重點關注項 |
| 檢查項目數 | 42 |
| 通過 | 33 |
| 🔴 Critical | **0** |
| 🟠 Major | **5** |
| 🟡 Minor | **3** |
| 🔵 Info | **4** |
| **結論** | **⚠️ CONDITIONAL PASS**（無 Critical，可前進；但 5 Major 為 PM patch 後其他檔案未同步更新所致，建議在 SD 階段啟動前完成「stale-reference sweep」修補）|

> 嚴格立場註腳: 若採 Rule 3 規格優先 — Warning > 3 + 無 Critical → **CONDITIONAL PASS**。Tester 不阻塞，但**強烈建議 PM 採納 §11 §12 的修補清單**再 approve。若拒絕修補，stale references 會傳遞到 SD 階段並造成下游錯誤實作（特別是 SSL mode default、Railway addon 假設）。

---

## 2. PM patches 充分性獨立判定（核心結論）

### 2.1 PM 已 patch 的範圍

| 檔案 | PM patch 章節 | 內容變更 | 結果 |
|------|--------------|---------|------|
| `deploy-env.json` | `_deploymentDecisions.postgresHosting` + `.backupRollback` + `_blockedOnDeployerResolved.1/3` + `userConfirmedDecisions` | Q0 = `railway-self-hosted-postgres-docker` / Q3 = `sqlite-emergency-only-pg-backup-deferred` / 加入 `_comment` 說明 / Q1 + Q2 confirmed unchanged | ✅ 結構完整 + 內部自洽 |
| `migration-strategy.md` | §2.2 / §2.3 / §2.4 (Staging / Production / Backup 驗證) | Railway daily backup 刪除 → 改為「無自動 PG backup + DEFERRED + 14天 SQLite only」 + test-be 階段不跑 backup restore | ✅ 局部章節邏輯自洽 |

### 2.2 PM 該 patch 但**未 patch** 的檔案（Tester 獨立判定）

Tester 對全部 12 個 deploy artifacts 做 grep 比對「Railway PG addon / verify-full / daily backup / managed-database / both / Hobby plan」等舊假設，發現以下檔案仍引用 Deployer 原始推斷:

| 檔案 | 行號 | 殘留 stale reference | 嚴重度 |
|------|------|---------------------|--------|
| `service-contract.yaml` | 53 | `example: "snowtrip (dev) / postgres (Railway addon default)"` | 🟠 Major-1 |
| `service-contract.yaml` | 79 | `# ========== 替代方案：DATABASE_URL（Railway addon 預設提供）==========` | 🟠 Major-1 |
| `service-contract.yaml` | 81 | `description: "PostgreSQL 連線字串（Railway PG addon 自動注入...)` | 🟠 Major-1 |
| `service-contract.yaml` | 94 | `example: "disable (本機) / require (staging) / verify-full (production)"` | 🟠 Major-2 |
| `service-contract.yaml` | 98 | `default_prod: "verify-full"` | 🟠 Major-2 |
| `service-contract.yaml` | 167 | `database: type: "managed-database"` | 🟠 Major-1 |
| `service-contract.yaml` | 175 | `deployment_mode_prod: "railway-postgres-addon"` | 🔴→🟠 Major-1（與 PM patched deploy-env.json 直接矛盾）|
| `service-contract.yaml` | 178 | `prod: "Railway PG addon 內建持久化儲存（managed）"` | 🟠 Major-1 |
| `service-contract.yaml` | 200 | `prod: "Railway PG addon daily backup (7 天保留 — Hobby plan)"` | 🟠 Major-3（與 PM patched migration-strategy.md §2.3 直接矛盾）|
| `service-contract.yaml` | 268 | `"1. PostgreSQL provision (Railway addon or docker-compose up postgres)"` | 🟠 Major-1 |
| `.env.example` | 26 | `# SSL 模式 — dev=disable, staging=require, prod=verify-full` | 🟠 Major-2 |
| `parameter-plan.md` | 77 | `"value": "(env-specific: snowtrip dev / Railway addon 自動 user)"` | 🟠 Major-1 |
| `parameter-plan.md` | 140 | `"description": "PostgreSQL 連線字串（替代方案 — Railway PG addon 自動注入）...sslmode=require"` | 🟠 Major-1 |
| `parameter-plan.md` | 154 | `"value": "(env-specific: disable dev / require staging / verify-full prod)"` | 🟠 Major-2 |
| `migration-strategy.md` | 289-290 | `staging: require / production (Railway addon): verify-full + 「defense-in-depth 對 SQL injection 攻擊面有額外阻隔」` | 🟠 Major-2（PM 在 §2 patch 了 backup 但漏了 §4 SSL 整段）|
| `migration-strategy.md` | 345 | 追溯矩陣行: `Daily backup (7 天) | Railway PG addon 預設 + SUG-006` | 🟠 Major-3 |
| `migration-strategy.md` | 347 | 追溯矩陣行: `SSL verify-full (prod) | BA SUG-005 + defense-in-depth` | 🟠 Major-2 |
| `migration-strategy.md` | 366 | `→ Deploy(Execute) 階段` 段內仍寫「驗證 backup 流程（§2.4）」(§2.4 已 patch 為不跑) | 🟠 Major-3 |
| `migration-strategy.md` | 373 | `→ Tester (test-deploy) 階段` 段內仍寫「§2.4 backup restore 驗收」 | 🟠 Major-3 |
| `deploy-plan.md` | 43 | `**Backup restore drill**: Staging 部署後執行 migration-strategy.md §2.4 的 backup → DROP → restore 流程` | 🟠 Major-3 |
| `deploy-plan.md` | 81 | 4 層配置表「環境特定配置」: `POSTGRES_SSL_MODE（dev=disable, prod=verify-full）` | 🟠 Major-2 |
| `self-review.json` | 48 | `{"item": "備援機制：14 天 SQLite emergency path 與 Railway PG daily backup 並行", "passed": true, "evidence": "...decision = both"}` | 🟠 Major-4（PM patch 後 evidence stale，但 self-review 是 Deployer 自評產出 — PM 應重跑 verify）|
| `self-review.json` | 49 | `{"item": "SSL mode 3 環境差異化（disable/require/verify-full）", ...}` | 🟠 Major-2 |
| `self-review.json` | 67 | `deploymentDecisions[0].answer: "Railway PostgreSQL addon"` + `rationale: "...內建 SSL + daily backup"` | 🟠 Major-4 |
| `self-review.json` | 70 | `deploymentDecisions[3].answer: "both (Railway daily backup + 14 天 SQLite emergency path)"` | 🟠 Major-4 |
| `self-review.json` | 77 | `blockedOnDeployerResolution.2_ssl_mode: "RESOLVED → disable(dev) / require(staging) / verify-full(prod)"` | 🟠 Major-2 |
| `self-review.json` | 78 | `3_backup_strategy: "RESOLVED → Railway daily backup (7d) + 14d SQLite emergency"` | 🟠 Major-4 |

### 2.3 Tester 對 PM patches 充分性的最終判定

**判定**: ⚠️ **不充分（partial）**

- ✅ PM 在 `deploy-env.json` 的 _deploymentDecisions / _blockedOnDeployerResolved / userConfirmedDecisions 補了完整紀錄 — 合理
- ✅ PM 在 `migration-strategy.md` §2.2-2.4 (Backup 章節) 改寫合理
- ❌ **PM 沒有把 §2 patch 的副作用傳播到 5 個其他檔案**（service-contract.yaml / .env.example / parameter-plan.md / deploy-plan.md / self-review.json / migration-strategy.md §3.4/§4/§6/§7 等）
- ❌ **PM 沒有 patch SSL mode 章節**（migration-strategy.md §4），仍寫 `production verify-full + 內建 SSL` — 與使用者選自建 container（無自動 SSL）矛盾
- ❌ **`self-review.json` 是 Deployer 產出**，PM 不應該手改；但因 `deploymentDecisions` 內容已 stale（answer=Railway addon），PM 應 require Deployer 重出 self-review

**Tester 判定 PM 越權？**: ❌ **不越權**。在 `deploy-env.json._deploymentDecisions` 加 PM 確認紀錄是合理的；在 `migration-strategy.md` §2 加 PM 修訂 banner + 章節重寫也屬於合理範圍（避免重跑 deploy-init 浪費 token 與時間）。問題是**範圍不夠廣 — 該批次處理但只處理了 2/12 檔**。

**建議行動**:
1. **Option A（推薦）**: PM 啟動「stale-reference sweep」批次 patch 5 個其他檔案（不需重跑 Deployer，PM 自己有上下文，1 次對話完成）
2. **Option B**: `/sdlc:revise` 退回 Deployer 重做（成本較高，但保證所有檔案內部一致）
3. **Option C**: 接受 CONDITIONAL_PASS，在 SD 階段 prompt 中明確注入「實際選擇 = 自建 container + 無 SSL + 無 PG backup + DEFERRED」，由 SD 處理時繞過 stale references

**Tester 推薦**: **Option A**。SD 階段 prompt 注入太脆弱 — SD agent 仍會讀到 service-contract.yaml 寫的 `deployment_mode_prod: railway-postgres-addon`，造成誤導實作（如 SSL connection 預設值、connection string 格式）。

---

## 3. D1 規格完整性

| 檢查項 | 結果 | 證據 |
|--------|------|------|
| service-contract.yaml 結構完整（services / port_allocation / env_vars / dependencies）| ✅ | 5 主章節齊全 |
| service-contract.yaml YAML 語法正確 | ✅ | 無 indentation 異常；可被 yaml 解析器讀取 |
| Port 無衝突 | ✅ | backend=8000 / database=5432 互斥 |
| Env var UPPER_SNAKE_CASE | ✅ | 13 個 env vars 全合規（含 DATABASE_URL 業界慣例特例已標註）|
| Env prefix `POSTGRES_` 對齊 config.json | ✅ | service-contract.yaml line 215 |
| Dockerfile.be 多階段建構 + non-root user | ✅ | builder + runtime 兩階段 + `useradd --uid 1000 appuser` |
| Dockerfile.be entrypoint 鎖定 CLAUDE.md | ✅ | `CMD ["sh", "-c", "uvicorn web.main:app --host 0.0.0.0 --port ${PORT}"]` 一致 |
| Dockerfile.fe 為合規 stub | ✅ | 註解明示 monolith 不啟用；profiles=disabled |
| docker-compose.yml depends_on 條件正確 | ✅ | `condition: service_healthy` |
| docker-compose healthcheck `/api/auth/me` 合理 | ✅ | TASK-001 既有 endpoint，未登入回 401 證明 app + DB 雙活 |
| docker-compose 使用 named volume 持久化 | ✅ | `sdlc-db-data:/var/lib/postgresql/data` |
| .env.example 涵蓋 service-contract 全部 required env | ✅ | 13 個 env vars 全列 |
| .env.example secret 用 CHANGE_ME 占位（不含實際 secret）| ✅ | POSTGRES_PASSWORD / SECRET_KEY / SERPAPI_API_KEY 3 secrets 都用 CHANGE_ME |
| Dockerfile.template 與 Dockerfile.be 一致性 | ⚠️ | 兩者高度重複（Dockerfile.template 是早期版本，Dockerfile.be 較完整）— Minor-1 |
| deploy-plan.md 6 階段 Pipeline | ✅ | Build / Lint / Test / Security Scan / Stage / Deploy + Migration up-down test |
| parameter-plan.md 10 個 parameter spec 完整 | ✅ | paramName / paramKind / paramType / value / scope / ownerService / sourceFR / envPrefix / validation 9 欄位完整 |

**D1 結果**: 14/16 PASS, 1 Minor, 1 待後續 PM patch

---

## 4. D2 與 BA/SA 規格一致性

| 檢查項 | 結果 | 證據 |
|--------|------|------|
| **FR-001 PG 連線層** | ✅ | service-contract.yaml backend.env_vars 含 POSTGRES_* 5 + DATABASE_URL 6 個 |
| **FR-002 三表 schema 重建** | ✅ | service-contract.yaml `migration_ordering` step 3 涵蓋 |
| **FR-003 Migration 工具** | ✅ | parameter-plan / migration-strategy 全部標 [BLOCKED_ON_SD] 委派合理 |
| **FR-004 補軟刪欄位** | ✅ | service-contract.yaml `migration_ordering` 涵蓋；無越界寫 DDL（規範行為，留 SD 寫實際 ALTER） |
| **FR-005 環境變數** | ✅ | 5 個 POSTGRES_* + DATABASE_URL + 3 個 POOL_* + SSL_MODE 完整登記 |
| **FR-006 Railway 部署** | ✅ | platformDetail=railway + entrypoint LOCKED + railway.toml 沿用既有 |
| **FR-007 既有資料遷移 [IRREVERSIBLE]** | ✅ | service-contract.yaml `rollback_strategy.sqlite_emergency_window = 14 days` |
| **FR-008 全環境統一 PG** | ✅ | docker-compose.yml database service 啟用；deployment_mode_dev/_prod 都標 PG |
| **NFR-001 持久性** | ✅ | named volume + Railway managed volume |
| **NFR-002 行為不變** | ✅ | healthcheck 用既有 `/api/auth/me`（不引入新 endpoint）|
| **NFR-003 啟動延遲 ≤ SQLite + 2s** | ✅ | migration-strategy.md §1.4 量化驗證計畫（首次 5-10s 一次性 / 既有 0.5-1s）|
| **NFR-005 連線池** | ✅ | POSTGRES_POOL_MIN/MAX/TIMEOUT_MS 3 個 env vars + default 對齊 BA 量化指標 |
| **NFR-010 env var UPPER_SNAKE_CASE** | ✅ | service-contract.yaml env_naming_convention |
| **NFR-011 Secret 不洩漏** | ✅ | 4 secrets 在 service-contract.yaml 無 example 值 + .env.example 用 CHANGE_ME |
| **NFR-006 Migration 可逆** | ✅ | deploy-plan.md §1.1 Migration up-down test 列為強制 |
| **NFR-007 三段式刪欄支援** | ✅ | migration-strategy.md §3.3 down 命令明列 |
| **CONST-007 Railway 啟動指令不變** | ✅ | `uvicorn web.main:app --host 0.0.0.0 --port $PORT` 在 service-contract / Dockerfile.be / Dockerfile.template / railway.toml 一致 |
| **CONST-009 rollback plan** | ✅ | service-contract.yaml `rollback_strategy` 完整 |
| **FUNC-107 [IRREVERSIBLE]** | ✅ + 緩解見 D4 | service-contract.yaml `traces_to.irreversible` 明列 |
| **BF-002 5 步驟 smoke test** | ✅ | deploy-plan.md §6 健康檢查設計 + migration-strategy.md §3.1 觸發表 |
| **BF-003 緊急回滾** | ✅ | migration-strategy.md §3.2 + §3.4 |
| **SA SUG-006 14 天 SQLite emergency** | ✅ | migration-strategy.md §3.4 三層落實（程式碼層 / 部署層 / 過期政策）|

**D2 結果**: 22/22 PASS — BA/SA 規格映射完整。但**注意**: 多項是「Deployer 寫對了基本架構」但「PM patch 後其他檔案未同步」造成 D2 內部出現「規格說 A，但其他檔案說 B」的不一致 — 詳見 §11 Major findings。

---

## 5. D3 使用者 4 個決策落地完整性

### 5.1 Q0 PG hosting: railway-self-hosted-postgres-docker

| 檢查項 | 應該長什麼樣 | 實際 | 結果 |
|--------|------------|------|------|
| deploy-env.json `_deploymentDecisions.postgresHosting.decision` | `railway-self-hosted-postgres-docker` | ✅ 已 patch | ✅ |
| `decisionConfirmedBy` 註明使用者 | user (2026-06-09 PM approve session) | ✅ | ✅ |
| 列出 self-hosted 的 implications | volume mount / SSL 自配 / backup 自管 / PG 版本自控 | ✅ 5 條 implications | ✅ |
| **service-contract.yaml `database.type`** | 應該 ≠ "managed-database"（自建 container 不是 managed）| ❌ 仍寫 `type: "managed-database"` | 🟠 Major-1 |
| **service-contract.yaml `database.deployment_mode_prod`** | 應該 ≠ "railway-postgres-addon" | ❌ 仍寫 `railway-postgres-addon` | 🟠 Major-1 |
| **service-contract.yaml `database.persistence.prod`** | 應該 ≠ "Railway PG addon 內建持久化儲存（managed）" | ❌ stale | 🟠 Major-1 |
| **migration_ordering step 1** | 應該不再寫 "Railway addon" | ❌ `"1. PostgreSQL provision (Railway addon or docker-compose up postgres)"` | 🟠 Major-1 |
| **parameter-plan.md POSTGRES_USER** | `"snowtrip dev / postgres (Railway addon default)"` 已不適用 | ❌ stale | 🟠 Major-1 |
| **parameter-plan.md DATABASE_URL** | 連線字串 example `?sslmode=require` 應改為 `?sslmode=disable`（self-hosted 預設無 SSL）| ❌ stale | 🟠 Major-1 + 🟠 Major-2 |

**判定**: ⚠️ Q0 決策**有寫在 deploy-env.json 但未傳播到 5 個關聯檔案** — Major-1（嚴重程度：下游 SD 讀 service-contract.yaml 仍會誤以為是 Railway addon）

### 5.2 Q1 Migration trigger: startup-auto-with-advisory-lock

| 檢查項 | 結果 |
|--------|------|
| deploy-env.json `migrationTrigger.decision` | ✅ `startup-auto-with-advisory-lock` |
| migration-strategy.md §1 觸發策略 | ✅ 完整 mermaid sequence + 利弊比較 + advisory lock pseudocode |
| NFR-003 SLA 評估 | ✅ §1.4 量化驗證計畫（首次 5-10s / 既有 0.5-1s）|
| 委派 SD 階段細節 | ✅ lock id=12345 標示意，留 SD 確認唯一性 |

**判定**: ✅ Q1 落地完整。

### 5.3 Q2 CI/CD: github-actions

| 檢查項 | 結果 |
|--------|------|
| deploy-env.json `cicd = github-actions` | ✅ |
| 既有 6 個 `.github/workflows/sdlc-*.yml` 不破壞 | ✅ deploy-plan.md 提到「既有 mechanism」 |
| 新增 3 個 workflow 規劃 | ✅ `ci-be.yml / deploy-staging.yml / deploy-prod.yml`（deploy-env.json + deploy-plan.md 一致）|
| Production gate (GitHub Environment) | ✅ deploy-env.json `prodApproval` 完整（requiredReviewers / environmentName / mechanism）|
| Path-based CI filter 適配 monolith | ✅ service-contract.yaml `ci_path_filters` 5 groups 對齊 web/ + flight_search/ 實際目錄 |
| Rule 19 CI Gate 合規 | ✅ STRICT merge gate + per-PR fail-open 區分明確 |

**判定**: ✅ Q2 落地完整。

### 5.4 Q3 Backup: sqlite-emergency-only-pg-backup-deferred

| 檢查項 | 應該長什麼樣 | 實際 | 結果 |
|--------|------------|------|------|
| deploy-env.json `backupRollback.decision` | `sqlite-emergency-only-pg-backup-deferred` | ✅ | ✅ |
| `postgresBackup.status = DEFERRED_TO_FUTURE_TASK` | ✅ + rationale + mitigationCandidates | ✅ | ✅ |
| `riskAcceptance.userAcknowledged` 紀錄 | 14 天 SQLite path 過期後若 PG 災難無 backup 可回 | ✅ 明確 | ✅ |
| migration-strategy.md §2.2-2.3 staging/prod backup | 改為「無自動 PG backup + DEFERRED」 | ✅ PM patched | ✅ |
| migration-strategy.md §2.4 backup 驗證 | 改為「test-be 階段不跑」 | ✅ PM patched | ✅ |
| **service-contract.yaml `services.database.backup.prod`** | 不再寫 Railway PG addon daily backup | ❌ 仍寫 `"Railway PG addon daily backup (7 天保留 — Hobby plan)"` | 🟠 Major-3 |
| **migration-strategy.md §6 追溯矩陣** | 不應再列「Daily backup (7 天) - Railway PG addon 預設」 | ❌ line 345 stale | 🟠 Major-3 |
| **migration-strategy.md §7 → Deploy(Execute) / Tester 交接** | line 366「驗證 backup 流程（§2.4）」+ line 373「§2.4 backup restore 驗收」 | ❌ stale (§2.4 已改為不跑) | 🟠 Major-3 |
| **deploy-plan.md §1.1 特殊驗證階段** | 不應再寫「Backup restore drill」 | ❌ line 43 stale | 🟠 Major-3 |
| **self-review.json subjective `備援機制`** | 不應再寫「Railway PG daily backup 並行 / decision = both」 | ❌ stale | 🟠 Major-4 |
| **self-review.json deploymentDecisions[3]** | 不應再寫 `"answer": "both (Railway daily backup ...)"` | ❌ stale | 🟠 Major-4 |
| **self-review.json blockedOnDeployerResolution.3** | 不應再寫「RESOLVED → Railway daily backup (7d) + 14d SQLite emergency」 | ❌ stale | 🟠 Major-4 |

**判定**: ⚠️ Q3 決策**有寫在 deploy-env.json + migration-strategy.md §2.2-2.4 但未傳播到 6 個關聯位置** — Major-3 + Major-4。

### 5.5 4 個使用者決策落地總結

| 決策 | 完整性 |
|------|-------|
| Q0 PG hosting | ⚠️ 50%（核心檔對但 service-contract / parameter-plan stale）|
| Q1 Migration trigger | ✅ 100% |
| Q2 CI/CD | ✅ 100% |
| Q3 Backup | ⚠️ 60%（核心檔對但 service-contract / migration-strategy §4/§6/§7 / deploy-plan / self-review stale）|

**D3 結果**: 2/4 完整，2/4 部分落地 — **這是 Major findings 的主要根因**。

---

## 6. D4 FUNC-107 [IRREVERSIBLE] 緩解充足性（Rule 11.1 四要素）

> 特別關注：使用者選 Q3 後，14 天 SQLite emergency path 是**唯一** backup 機制（不再有 Railway daily backup 雙保險）。Tester 嚴格評估緩解是否仍充足。

| Rule 11 四要素 | 內容 | 結果 |
|---------------|------|------|
| **description** | FUNC-107 production cutover；deploy/migration-strategy.md §3 詳細 6 步驟流程 | ✅ |
| **business impact** | functional-flow.md FUNC-107 §IRREVERSIBLE 理由：資料層 + 業務層雙重影響說明 | ✅ |
| **when triggered** | functional-flow.md FUNC-107 前置條件 5 項 | ✅ |
| **mitigation** | 14 天 SQLite emergency path + rollback plan + BF-003 緊急回滾 三層 | ⚠️ 見下方 |

### 6.1 14 天 SQLite emergency path 落實檢驗

**migration-strategy.md §3.4 5 步驟**: 
- §3.4.1 程式碼層: 保留 `database_sqlite.py` 於 git history + PR merge msg 記錄 + 分階段 commit 策略 ✅
- §3.4.2 部署層 5 步驟 emergency rollback: Step 1 確認 window / Step 2 移除 PG env / Step 3 git revert / Step 4 Railway auto redeploy / Step 5 接受 SQLite ephemeral ✅
- §3.4.3 期間遺失資料風險評估表 ✅
- §3.4.4 14 天後政策（新開 cleanup TASK 移除 SQLite path）✅

**判定**: ✅ §3.4 5 步驟流程清楚可執行。

### 6.2 PG backup 移除後緩解是否仍充足？

| 風險場景 | 14 天內 | 14 天後 |
|---------|---------|---------|
| PG 連線異常 | ✅ git revert 切回 SQLite + 接受 ephemeral | ❌ 無 SQLite path，無快速回退 |
| PG container 持久化資料毀損 | ⚠️ 14 天 SQLite 切換可恢復服務但**該期間 PG 寫入資料全部遺失** | ❌ 無 backup 可回 |
| PG schema migration 寫壞 | ✅ Alembic downgrade -1（NFR-006 強制 reversible） | ✅ 同上 |
| Railway container 重啟 | ✅ named volume 持久化 | ✅ |
| Railway 平台層異常（容器無法啟動）| ✅ rollback to N-1 build | ✅ |

**Tester 判定**: ⚠️ **14 天內充足，14 天後不充足，但這是使用者明示接受的 trade-off**（deploy-env.json `riskAcceptance.userAcknowledged`）

**緩解措施改進建議（Info-1）**:
- 既然 PG backup DEFERRED，14 天內的「PG 寫入資料保留」是極大風險。建議 deploy-init 在 §3.4 加一段：「**14 天 window 啟動 emergency rollback 前的『最後 5 分鐘 pg_dump』命令範本」**（Tester 觀察 [DEPLOYER建議] 已提及 pg_dump 但屬 SUG，建議升級為 BLOCKING 動作）
- 此屬範圍外 Info 建議，不阻塞

### 6.3 Rule 11.2 SD/UIUX/FE/BE/Tester 下游責任

functional-flow.md FUNC-107 line 400-405 明確列出。✅ Rule 11.2 落實完整。

### 6.4 service-contract.yaml `traces_to.irreversible`

```yaml
irreversible:
  - "FUNC-107 production cutover [IRREVERSIBLE] — rollback_strategy 完整覆蓋"
```
✅ Trace 完整。

**D4 結果**: ✅ 緩解充足（無 Critical / Major）；但有 1 Info 建議（pg_dump 命令範本）。

---

## 7. D5 Rule 18 Parameter Registry 預規劃完整性

| 檢查項 | 結果 | 證據 |
|--------|------|------|
| parameter-plan.md 列出 10 個 parameter_added 命令 | ✅ | §1.1-1.10 完整 bash 命令 + JSON payload |
| 每個 param 含 paramKind / paramType / scope / ownerService / required / sourceFR / envPrefix / validation 9 欄位 | ✅ | 10 個 param 全部完整 |
| paramKind 分類正確 | ✅ | 5 env (HOST/PORT/USER/DB/SSL_MODE) + 2 secret (PASSWORD/DATABASE_URL) + 3 limit (POOL_MIN/MAX/TIMEOUT) |
| ownerService = be 一致 | ✅ | 10/10 |
| 命名 UPPER_SNAKE_CASE + 服務前綴 | ✅ | POSTGRES_* + DATABASE_URL（業界慣例特例）|
| Conflict Detection 預期狀態 | ✅ | parameter-plan.md §3 明示「全部第一次引入，無衝突」 |
| **使用者選自建後是否需新增 parameter？**（PM 重點 4）| ❌ Major-5 | 自建 container 需 mount 持久化 volume 給 `/var/lib/postgresql/data`；現有 docker-compose.yml 用 `sdlc-db-data` 但無 `DOCKER_VOLUME_NAME` 或 `PG_DATA_PATH` env var 化 — 後續 Execute / SD 階段需要規範時會發現缺漏 |
| **POSTGRES_SSL_MODE 預設值是否該從 verify-full 改為 disable**（PM 重點 4）| ❌ 部分 Major-2 | parameter-plan.md §1.7 value 仍是 `"(env-specific: disable dev / require staging / verify-full prod)"` — 未反映 Q0 後 prod 應該也是 `disable`（或標 DEFERRED）|
| **Retroactive registry 建議（TASK-001 3 個 env vars）** | ✅ | parameter-plan.md §2 [DEPLOYER建議] 列出 + 留 PM 決策 |

**D5 結果**: 8/10 PASS, 2 Major(1 之前已記 Major-2; 1 新 Major-5 = volume parameter 缺漏)

---

## 8. Rule Protocol 合規檢查

### 8.1 Rule 11 不可逆操作

詳見 §6。✅ FUNC-107 標記合規，14 天 emergency path 落實完整。

### 8.2 Rule 18 Parameter Registry

詳見 §7。✅ 預規劃充足。SSL mode default value 待 Major-2 修正。

### 8.3 Rule 19 CI Gate

| 檢查項 | 結果 |
|--------|------|
| 既有 6 個 sdlc-*.yml workflow 不破壞 | ✅ deploy-env.json 標既定事實 |
| 新 3 個 workflow 規劃合理 | ✅ ci-be / deploy-staging / deploy-prod 對齊 Rule 19.1 4 個工作流分工 |
| Production gate STRICT | ✅ deploy-env.json `prodApproval.required=true + mechanism=github-environment` |
| Per-PR fail-open vs Merge-gate STRICT | ✅ deploy-plan.md §1 表已區分 |
| sdlc-merge-gate.yml 整合 | ⚠️ Minor-2 | deploy-plan.md 提到 3 個新 workflow 但**未明示要不要在 sdlc-merge-gate.yml 加 strict gate 步驟**整合 |

**Rule 19 結果**: 4/5 PASS, 1 Minor。

### 8.4 Rule 10 Abandoned TASKs

| 檢查項 | 結果 |
|--------|------|
| `.sdlc/.abandoned-tasks.txt` 不存在 → 無禁讀過濾 | ✅ |
| 無引用 abandoned TASK 的 ID | ✅ |

### 8.5 與 conventions 對齊

| Convention | 對齊狀態 |
|-----------|---------|
| api-conventions.md (Layer 2 lock) | ✅ env var UPPER_SNAKE_CASE 全合規 |
| db-conventions.md | ✅ 未越界改 conventions |
| branch-conventions.md | ✅ 分支 sdlc/TASK-002/sqlite-to-postgres |

---

## 9. PM 8 個重點關注項獨立評估

### 9.1 Stale references 是否充分傳播

詳見 §2 + §5。**不充分** — Tester 列出 25 個 stale 行需 PM 補修。

### 9.2 PM patches 自身合理性

詳見 §2.3。**不越權**（範圍合理）但**範圍不夠廣**。

### 9.3 FUNC-107 緩解充足性（PG backup 移除後）

詳見 §6。**14 天內充足**；14 天後依賴使用者明示接受的 trade-off。Tester 不阻塞。

### 9.4 Rule 18 完整性 + volume parameter 缺漏

詳見 §7。**SSL default value 未更新（Major-2 重複）+ volume name / data path 未 env var 化（Major-5）**。

### 9.5 CI/CD plan 合規（Rule 19）

詳見 §8.3。✅ 合規。1 Minor 關於 sdlc-merge-gate.yml 整合未明示。

### 9.6 5 個 [BLOCKED_ON_DEPLOYER] 解決狀態獨立驗證

| # | SA test-sa 提項 | Deployer self-review 聲稱 | PM patch 後實際 | Tester 獨立判定 |
|---|----------------|--------------------------|----------------|----------------|
| 1 | postgres-hosting | RESOLVED → Railway addon | PM patched → RESOLVED → self-hosted container | ✅ 合理（使用者明示） |
| 2 | ssl-mode | RESOLVED → disable/require/verify-full | PM patched _blockedOnDeployerResolved.2_ssl_mode → DEFERRED_TO_DEPLOY_EXECUTE | ⚠️ **問題：自建 container 預設 disable 是部署層配置問題，可在 deploy-init 直接決定 — DEFERRED 屬於拖延**。詳見 Info-2 |
| 3 | backup-strategy | RESOLVED → Railway daily + 14d SQLite | PM patched → PARTIAL（14d SQLite only + PG DEFERRED）| ✅ 合理（使用者明示），但 PARTIAL 是合理分類 |
| 4 | production-sla-dashboard | PARTIAL (Railway built-in + SD/BE 補 DB error counter + Sentry 留 SUG) | 未變 → PARTIAL | ✅ 合理（與 deploy-init 階段適配）|
| 5 | docker-compose-volume | RESOLVED → named volume `sdlc-db-data` | 未變 → RESOLVED | ⚠️ 但 named volume 未 env var 化 — 詳見 §7 Major-5 |

**Tester 判定**:
- #1: ✅ RESOLVED
- #2: ⚠️ DEFERRED_TO_DEPLOY_EXECUTE 合理嗎？— **Tester 認為部分合理**。對自建 container 而言，SSL setup 涉及 cert 管理（self-signed / Let's Encrypt / sidecar proxy）— 不是 deploy-init 階段可決定的（需基礎設施實驗）。**但 SD 寫程式時必須要有 SSL_MODE 預設值** — 此值應該在 deploy-init 就決定為 `disable`，否則 SD 看到 service-contract.yaml 仍寫 `default_prod: verify-full` 會誤導實作（Major-2）
- #3: ✅ PARTIAL (DEFERRED) 是使用者明示
- #4: ✅ PARTIAL 合理
- #5: ⚠️ 雖然 named volume 已存在但未 env var 化（PG_VOLUME_NAME / PG_DATA_PATH）— 屬於 Major-5 補完範圍

### 9.7 與既有 production 的相容性

| 檢查項 | 結果 |
|--------|------|
| Railway 啟動指令不可改（CLAUDE.md）| ✅ entrypoint_lock = LOCKED 在 service-contract / Dockerfile.be / Dockerfile.template / railway.toml 一致 |
| 既有 6 個 sdlc-*.yml CI workflow 不破壞 | ✅ deploy-plan.md / deploy-env.json 標既定事實，新 workflow 為加法 |
| 既有 docker-compose.yml (root, PR 13c 通用模板) 不破壞 | ✅ docker-compose.template.yml 用 override 策略（profile=disabled + 重命名 env vars）|
| 既有 .env.example / .env.backend / .env.frontend 不衝突 | ✅ deploy/.env.example 為 TASK-002 範本，不取代 root |
| 既有 web/data/snowtrip.db SQLite path | ✅ 在 git history 保留作為 14 天 emergency |

### 9.8 不腦補檢查

| 檢查項 | 結果 |
|--------|------|
| 無腦補 multi-region | ✅ 全部單 region |
| 無腦補 read replica | ✅ |
| 無腦補 message queue / Redis | ✅ 對齊 BA §1.4「不納入」 |
| 無腦補 Sentry / Datadog 為強制 | ✅ migration-strategy.md §5.3 標 [DEPLOYER建議] 留後續 TASK |
| 無腦補 K8s namespace / PV | ✅ 純 Railway + docker-compose |
| 14 天 emergency 是 BA SUG-006 + 使用者確認 | ✅ 不是腦補 |

**Tester 判定**: ✅ 無腦補。Deployer 對「未授權的部署架構」克制良好。

---

## 10. 追溯矩陣

| 規格 | 對應 deploy 元素 | 結果 |
|------|----------------|------|
| FR-001 PG 連線層 | service-contract.yaml backend.env_vars POSTGRES_* | ✅ @traces_to(FR-001) |
| FR-002 三表 schema | migration_ordering step 3 | ✅ @traces_to(FR-002) |
| FR-003 Migration 工具 | parameter-plan + migration-strategy [BLOCKED_ON_SD] | ✅ @traces_to(FR-003) |
| FR-004 補欄位 | migration_ordering step 3 | ✅ @traces_to(FR-004) |
| FR-005 環境變數 | parameter-plan.md §1.1-1.10 | ✅ @traces_to(FR-005) |
| FR-006 Railway 部署 | deploy-env.json.platformDetail + entrypoint LOCKED | ✅ @traces_to(FR-006) |
| FR-007 [IRREVERSIBLE] | 14 天 SQLite emergency + rollback_strategy | ✅ @traces_to(FR-007) |
| FR-008 全環境統一 PG | docker-compose.yml database service | ✅ @traces_to(FR-008) |
| NFR-002 行為不變 | healthcheck 用既有 /api/auth/me | ✅ @traces_to(NFR-002) |
| NFR-003 啟動 SLA | migration-strategy.md §1.4 量化計畫 | ✅ @traces_to(NFR-003) |
| NFR-005 連線池 | POSTGRES_POOL_* 3 個 env vars | ✅ @traces_to(NFR-005) |
| NFR-010 命名 | env_naming_convention | ✅ @traces_to(NFR-010) |
| NFR-011 Secret | 4 secrets 不含 example 值 | ✅ @traces_to(NFR-011) |
| FUNC-107 [IRREVERSIBLE] | 14 天 SQLite emergency 三層落實 | ✅ @traces_to(FUNC-107) |
| BF-002/003 | migration-strategy §3.1-§3.4 | ✅ @traces_to(BF-002, BF-003) |
| 4 [CROSS-TASK: TASK-001] | service-contract.yaml `traces_to.cross_task_modify` 4 條 | ✅ @traces_to([CROSS-TASK]) |

**全部 16 規格元素三向追溯完整**。

---

## 11. 發現清單

### 🔴 Critical
- **無**

### 🟠 Major

#### Major-1: Q0 PG hosting 決策未傳播至 service-contract.yaml + parameter-plan.md

- **位置**: 
  - `service-contract.yaml` line 53, 79, 81, 167, 175, 178, 268
  - `parameter-plan.md` line 77, 140
- **描述**: PM 已在 `deploy-env.json._deploymentDecisions.postgresHosting` 標明使用者選 self-hosted container，但其他檔案仍寫 `type: "managed-database"` / `deployment_mode_prod: "railway-postgres-addon"` / `persistence.prod: "Railway PG addon 內建持久化儲存（managed）"` / DATABASE_URL example 用 `postgresql://user:pass@host:5432/snowtrip?sslmode=require` 等舊假設
- **影響**: 
  1. SD 階段讀 service-contract.yaml 會誤以為是 Railway addon 而設計連線假設
  2. service-contract.yaml 的 `database.type` 是 SD/BE 階段的「真相來源」— 內部矛盾
  3. DATABASE_URL example 含 `sslmode=require` 但實際 self-hosted 無 SSL → 連線 string 預設值錯誤
- **建議修補**: PM 批次 patch 9 個 stale 行 → 改寫為:
  - `type: "self-hosted-container"`
  - `deployment_mode_prod: "railway-self-hosted-docker"`
  - `persistence.prod: "Railway named volume mount 到 /var/lib/postgresql/data (PG_VOLUME_NAME env var TBD)"`
  - DATABASE_URL example: `postgresql://user:pass@host:5432/snowtrip?sslmode=disable`（移除 Railway addon 字眼）
  - parameter-plan.md POSTGRES_USER value: `(env-specific: snowtrip dev / snowtrip prod — 使用者自訂)`
- **嚴重度**: Major（不阻塞但下游 SD 會誤導實作 → 進入 test-sd 才會被抓到，浪費迭代成本）

#### Major-2: POSTGRES_SSL_MODE 預設值未配合 Q0 更新

- **位置**:
  - `service-contract.yaml` line 94 `example: "disable (本機) / require (staging) / verify-full (production)"`
  - `service-contract.yaml` line 98 `default_prod: "verify-full"`
  - `.env.example` line 26-27 註解 `prod=verify-full` + 預設 `POSTGRES_SSL_MODE=disable`（註解與實際值不一致）
  - `parameter-plan.md` line 154 value `"(env-specific: disable dev / require staging / verify-full prod)"`
  - `migration-strategy.md` line 286-290 SSL 模式表 prod 仍寫 verify-full
  - `migration-strategy.md` line 347 追溯矩陣 `SSL verify-full (prod) | BA SUG-005 + defense-in-depth`
  - `deploy-plan.md` line 81 4 層配置表 `POSTGRES_SSL_MODE（dev=disable, prod=verify-full）`
  - `self-review.json` line 49 subjective evidence
  - `self-review.json` line 77 blockedOnDeployerResolution.2_ssl_mode
- **描述**: PM 在 `deploy-env.json._blockedOnDeployerResolved.2_ssl_mode.status = DEFERRED_TO_DEPLOY_EXECUTE` 標 「自建 container 預設不啟用 SSL；本 TASK 階段 sslmode=disable」，但**7 個其他檔案仍寫 verify-full 為 production 預設** + migration-strategy.md §4 整段沒被 PM patch
- **影響**: 
  1. SD 階段在 db-schema.md / logic-flow.md 寫 connection string 時會用 verify-full（誤導）
  2. .env.example 註解與實際預設值不一致（人類部署者困惑）
  3. parameter-plan.md 命令到 SD 階段執行時會 emit `parameter_added` 帶 verify-full default — 寫進 shared/parameter-registry.md 形成永久錯誤
- **建議修補**: PM 批次 patch 9 行 → SSL_MODE 改寫為:
  - `default_prod: "disable"` + 註解「使用者選自建 container 預設不啟用 SSL；SSL setup 留 Deploy(Execute) 階段視需要強化（self-signed / Let's Encrypt / sidecar proxy）」
  - migration-strategy.md §4 整段重寫（環境 SSL 表 prod 改為 `disable + TODO: future TASK 強化`）
- **嚴重度**: Major（嚴重度等同 Major-1，因為 SSL_MODE 預設值直接影響 SD 設計 + BE 實作）

#### Major-3: Q3 Backup DEFERRED 未傳播至 service-contract / deploy-plan / migration-strategy 多處引用

- **位置**:
  - `service-contract.yaml` line 200 `prod: "Railway PG addon daily backup (7 天保留 — Hobby plan)"`
  - `migration-strategy.md` line 345 追溯矩陣 `Daily backup (7 天) - Railway PG addon 預設 + SUG-006`
  - `migration-strategy.md` line 366 → Deploy(Execute) 交接「驗證 backup 流程（§2.4）」
  - `migration-strategy.md` line 373 → Tester (test-deploy) 交接「§2.4 backup restore 驗收」
  - `deploy-plan.md` line 43 「Backup restore drill: Staging 部署後執行 migration-strategy.md §2.4 的 backup → DROP → restore 流程」
- **描述**: PM 已 patch migration-strategy.md §2.2-2.4 但**§3.4 / §4 / §6 追溯矩陣 / §7 交接清單** 等 4 處仍引用「Railway PG daily backup + §2.4 backup restore」— 與 PM patch 後實際狀態（無 PG backup + DEFERRED）直接矛盾
- **影響**:
  1. Deploy(Execute) 階段讀 §7 交接清單會嘗試「驗證 backup 流程」但找不到（§2.4 已改為不跑）
  2. Tester (test-deploy = §5.9 D9) 讀 §7 會嘗試 backup restore 驗收但無 backup 可測
  3. deploy-plan.md §1.1 「特殊驗證階段」列為強制但實際無法執行 → Build Gate 階段會出現 confusing failures
- **建議修補**: PM 批次 patch 5 行 → 改為:
  - service-contract.yaml line 200: `prod: "[DEFERRED_TO_FUTURE_TASK] 無自動 PG backup — 唯一 backup 機制為 14 天 SQLite emergency path（SUG-006）"`
  - migration-strategy.md §6 追溯矩陣行: `Daily backup` 行**刪除**
  - migration-strategy.md §7 line 366: 改為「驗證 14 天 SQLite emergency path 可執行性（§3.4 5 步驟）」
  - migration-strategy.md §7 line 373: 改為「§3.4 SQLite emergency rollback drill」
  - deploy-plan.md line 43: 改為「14 天 SQLite emergency rollback drill: Staging 部署後執行 migration-strategy.md §3.4 模擬」
- **嚴重度**: Major（驗證計畫與實際 scope 矛盾 → Build Gate / test-deploy 階段會 failed）

#### Major-4: self-review.json 多處 stale，但這是 Deployer 產出，PM 不該手改

- **位置**:
  - `self-review.json` line 48 subjective.checklist「備援機制：14 天 SQLite emergency path 與 Railway PG daily backup 並行」passed=true
  - `self-review.json` line 67 deploymentDecisions[0].answer = "Railway PostgreSQL addon"
  - `self-review.json` line 70 deploymentDecisions[3].answer = "both (Railway daily backup + 14 天 SQLite emergency path)"
  - `self-review.json` line 78 blockedOnDeployerResolution.3_backup_strategy = "RESOLVED → Railway daily backup (7d) + 14d SQLite emergency"
- **描述**: self-review.json 是 Deployer agent 的自評產出，Deployer 寫的時候使用者尚未確認 Q0/Q3。PM 不能/不該直接手改 self-review（會破壞 SDLC 自我驗證機制的真實性），但 self-review 內容已與最新事實脫節
- **影響**:
  1. Tester（本人）讀 self-review 時看到 evidence 與實際不符 — 已抓到
  2. 後續任何 audit / review 讀 self-review 會看到「decision = both」與實際的 `sqlite-emergency-only-pg-backup-deferred` 矛盾
- **建議修補**: 
  - **不要 PM 手改**（破壞 SDLC 真實性）
  - **Option A**: PM 在 self-review.json 加一個 `_pmPatchedNotice` 區塊明示「2026-06-09 PM approve session：使用者最終決策 Q0=self-hosted, Q3=sqlite-only-deferred；本 self-review 內容由 Deployer 於確認前寫入，正確真相見 deploy-env.json + migration-strategy.md PM patches」
  - **Option B**: PM `/sdlc:revise` 退回 Deployer 重出 self-review
  - **Tester 推薦**: Option A（成本低 + 保留 audit trail）
- **嚴重度**: Major（不影響部署正確性，但破壞 SDLC self-review 真實性 + 後續 retro 難追溯真相）

#### Major-5: 使用者選自建後缺漏 PG_VOLUME_NAME / PG_DATA_PATH parameter

- **位置**: parameter-plan.md（10 個 parameter 都不含 volume）+ service-contract.yaml line 177 (`dev_volume: "sdlc-db-data (named volume — 既有 docker-compose.yml line 138-140)"`) + deploy-env.json line 45-46 implications 第 1 條
- **描述**: 使用者選 self-hosted container 後，docker-compose.yml + Railway 都需要 mount persistent volume 給 `/var/lib/postgresql/data`。當前 docker-compose.yml 寫死 `sdlc-db-data:/var/lib/postgresql/data`（line 62-63）。
  - 若不 env var 化：dev / staging / prod 三環境的 volume 名稱無法區分 → docker compose down -v 會清空所有環境
  - 若不 env var 化：Railway dashboard 的 persistent volume mount 路徑配置（implications 第 1 條明示需要）無法和 docker-compose 同步
- **影響**: SD 階段在 logic-flow.md / db-schema.md 不需要這些 parameters，但 Execute 階段啟動 PG container 時會碰到「Railway volume mount 路徑 vs docker-compose volume 名稱」的環境特定差異 → 部署失敗
- **建議修補**: parameter-plan.md 新增 2 個 parameter（從 10 → 12）:
  ```bash
  # PG_VOLUME_NAME (env, dev only)
  paramName: "PG_VOLUME_NAME"
  paramKind: "env"
  paramType: "string"
  value: "(env-specific: sdlc-db-data dev / postgres-data-prod prod)"
  scope: "deploy"
  ownerService: "deploy"
  description: "PostgreSQL data volume 名稱（docker-compose / Railway 配置一致用）"
  
  # PG_DATA_PATH (limit/env, all envs)
  paramName: "PG_DATA_PATH"  
  paramKind: "env"
  paramType: "string"
  value: "/var/lib/postgresql/data"
  scope: "all"
  ownerService: "deploy"
  description: "PostgreSQL data 目錄（容器內路徑 — postgres:16-alpine 預設）"
  ```
- **嚴重度**: Major（不阻塞 deploy-init approve，但 Execute 階段會發現缺漏）

### 🟡 Minor

#### Minor-1: Dockerfile.template 與 Dockerfile.be 高度重複

- **位置**: `Dockerfile.template` (76 行) + `Dockerfile.be` (63 行)
- **描述**: 兩檔案幾乎相同（runtime base / packages / multi-stage / healthcheck / entrypoint 都一樣）；Dockerfile.template 是早期模板版本，Dockerfile.be 是最終版。保留兩檔造成「哪個是 source of truth?」歧義
- **建議**: 刪除 Dockerfile.template（保留 Dockerfile.be 作 source of truth）；或在 Dockerfile.template 加 banner「[REPLACED BY Dockerfile.be — kept for SDLC template lineage]」
- **嚴重度**: Minor（不影響部署）

#### Minor-2: sdlc-merge-gate.yml 是否要加 strict gate 未明示

- **位置**: deploy-plan.md / deploy-env.json
- **描述**: deploy-plan.md 提到 3 個新 workflow (`ci-be.yml / deploy-staging.yml / deploy-prod.yml`)，Rule 19.1 規定 merge-gate 是 STRICT，但**未明示要不要在既有 `sdlc-merge-gate.yml` 加入新的 strict-validate 步驟**（如 verify env-consistency / verify migration up-down）
- **建議**: deploy-plan.md §1 補一節「sdlc-merge-gate.yml 加入步驟：(1) sdlc-env-consistency.sh TASK-002 (2) migration up-down test must pass」明示
- **嚴重度**: Minor（Execute 階段可補）

#### Minor-3: SUG-007 DESIGN.md 同步更新未在任一 deploy artifact 中提及

- **位置**: BA requirement-spec.md SUG-007 + CLAUDE.md
- **描述**: BA SUG-007「DESIGN.md §八 同步更新（解 C-1 後從『已知問題』移到『已解決』）」屬於 PM 文件債清理 — Deployer 沒義務在 deploy 階段處理。但 deploy-plan.md / deploy-result.md (Execute 階段才有) 都沒提到 trigger 點
- **建議**: deploy-plan.md 「後續 deploy 階段優化」表加一行「FUNC-107 cutover 完成 → PM trigger DESIGN.md §八 更新」
- **嚴重度**: Minor（文件債，不阻塞）

### 🔵 Info

#### Info-1: PG 寫入資料的 14 天 emergency window 期間保護建議

- **建議**: 既然 PG backup DEFERRED，14 天內若需 emergency rollback 切回 SQLite，**該期間在 PG 寫入的所有資料會立刻遺失**。建議 §3.4.2 Step 1 + Step 2 之間新增 Step 1.5「執行 `pg_dump --data-only > emergency_pg_snapshot_{timestamp}.sql` 保存到 Railway volume / 本機」— 屬於低成本（< 5min）的災難前保護
- **不阻塞**

#### Info-2: SSL mode DEFERRED_TO_DEPLOY_EXECUTE 半推半就

- **觀察**: PM patch 後 `_blockedOnDeployerResolved.2_ssl_mode.status = DEFERRED_TO_DEPLOY_EXECUTE`，但 deploy-env.json `_deploymentDecisions.postgresHosting.sslMode` 又標「本 TASK 階段 sslmode=disable 為預設」— **「DEFERRED 但有預設值」邏輯衝突**
- **建議**: status 應改為 `RESOLVED_AS_DISABLE_WITH_FUTURE_HARDENING_TASK` 而不是 DEFERRED — 因為實際上「disable」就是當前的決策，留後續強化才是 DEFERRED 的 scope
- **不阻塞**（語意問題，不影響行為）

#### Info-3: Retroactive Parameter Registry 提案合理

- **觀察**: parameter-plan.md §2 [DEPLOYER建議] 列 TASK-001 既有 SECRET_KEY / SERPAPI_API_KEY / PORT 未登記 — Deployer 不擴大本 TASK 範圍合理
- **建議**: PM 在 SD approve TASK-002 後 + Tester 同意此安排後，**列為 SDLC backlog 待後續處理**（不在本 TASK）
- **不阻塞**

#### Info-4: docker-compose.template.yml [DELTA] 章節 LOC 偏多

- **觀察**: docker-compose.template.yml line 80-97 [DELTA] 章節列 5 條既有 docker-compose.yml 對本 TASK 的差異 — 屬於分析性質而非可執行配置，混在 yaml 檔內降低可讀性
- **建議**: 將 [DELTA] 章節抽到 deploy-plan.md 的「§7 既有 docker-compose 相容性分析」獨立章節
- **不阻塞**

---

## 12. 修補清單（給 PM 採納用）

### 12.1 Major 修補（建議在 deploy-init approve 前完成）

| # | 檔案 | 行號 | 動作 |
|---|------|------|------|
| M1.1 | service-contract.yaml | 53 | 改 `example: "snowtrip"` （移除 Railway addon default）|
| M1.2 | service-contract.yaml | 79 | 註解改為 `# 替代方案：DATABASE_URL` |
| M1.3 | service-contract.yaml | 81 | 改 description 移除 "Railway PG addon 自動注入" |
| M1.4 | service-contract.yaml | 167 | 改 `type: "self-hosted-container"` |
| M1.5 | service-contract.yaml | 175 | 改 `deployment_mode_prod: "railway-self-hosted-docker"` |
| M1.6 | service-contract.yaml | 178 | 改 `prod: "Railway named volume mount (PG_VOLUME_NAME env)"` |
| M1.7 | service-contract.yaml | 268 | 改 `"1. PostgreSQL provision (docker-compose up postgres for dev / Railway docker volume mount for prod)"` |
| M2.1 | service-contract.yaml | 94 | 改 example 移除 verify-full（self-hosted 預設 disable）|
| M2.2 | service-contract.yaml | 98 | 改 `default_prod: "disable"` + 註明 future TASK 強化 |
| M2.3 | .env.example | 26 | 改註解 `# SSL 模式 — 全環境預設 disable（自建 container 無自動 SSL）` |
| M2.4 | parameter-plan.md | 154 | value 改為 `"(env-specific: disable all envs — future TASK enable SSL)"` |
| M2.5 | migration-strategy.md | 284-303 §4 整段 | 重寫 SSL 模式表：3 環境都 disable + 後續強化候選方案 |
| M2.6 | migration-strategy.md | 347 | 追溯矩陣 SSL 行改為 `SSL disable (全環境) | Q0 self-hosted decision + future hardening TASK` |
| M2.7 | deploy-plan.md | 81 | 改 `POSTGRES_SSL_MODE（all envs=disable, future hardening TASK）` |
| M3.1 | service-contract.yaml | 200 | 改 `prod: "[DEFERRED_TO_FUTURE_TASK] 無自動 PG backup — 唯一 backup 機制為 14 天 SQLite emergency path"` |
| M3.2 | migration-strategy.md | 345 | 追溯矩陣刪除「Daily backup (7 天)」行 |
| M3.3 | migration-strategy.md | 366 | 改 `驗證 14 天 SQLite emergency path 可執行性（§3.4 5 步驟）` |
| M3.4 | migration-strategy.md | 373 | 改 `§3.4 14 天 SQLite emergency rollback drill` |
| M3.5 | deploy-plan.md | 43 | 改 `14 天 SQLite emergency rollback drill（§3.4）`+ 移除 backup restore drill |
| M4.1 | self-review.json | 全檔 | 加入 `_pmPatchedNotice` 區塊（PM 寫，非改 Deployer 原文）|
| M5.1 | parameter-plan.md | 新增 §1.11 + §1.12 | PG_VOLUME_NAME (env) + PG_DATA_PATH (env) 兩個 parameters |
| M5.2 | service-contract.yaml | 177 | dev_volume 改為使用 `${PG_VOLUME_NAME}` |
| M5.3 | docker-compose.yml | 63 | volume mount 改為 `${PG_VOLUME_NAME:-sdlc-db-data}:${PG_DATA_PATH:-/var/lib/postgresql/data}` |

### 12.2 Minor 修補（可在 SD/Execute 階段一併處理）

| # | 動作 |
|---|------|
| Min-1 | 刪除 Dockerfile.template 或加 banner 「REPLACED BY Dockerfile.be」 |
| Min-2 | deploy-plan.md §1 補「sdlc-merge-gate.yml 加 strict-validate 步驟」說明 |
| Min-3 | deploy-plan.md 「後續優化」表加「FUNC-107 完成 → PM trigger DESIGN.md §八 更新」 |

### 12.3 Info 採納建議

| # | 動作 |
|---|------|
| Info-1 | migration-strategy.md §3.4.2 Step 1 後加 Step 1.5 (pg_dump emergency snapshot) |
| Info-2 | deploy-env.json `_blockedOnDeployerResolved.2_ssl_mode.status` 改為 `RESOLVED_AS_DISABLE_WITH_FUTURE_HARDENING_TASK` |
| Info-3 | PM 將 retroactive parameter registry 列為 SDLC backlog |
| Info-4 | docker-compose.template.yml [DELTA] 章節移至 deploy-plan.md §7 |

---

## 13. 結論

| 項目 | 結果 |
|------|------|
| **Tester 獨立分數** | **76/100** |
| **deploy-init 階段獨立判定** | **⚠️ CONDITIONAL PASS** |
| Critical 數 | **0** |
| Major 數 | **5** |
| Minor 數 | **3** |
| Info 數 | **4** |
| PM patches 充分性 | **不充分** — patches 集中在 deploy-env.json + migration-strategy.md §2 但未傳播到其他 5 個檔案的 25 個 stale references |
| PM patches 越權? | **不越權** — patch 範圍合理但**廣度不夠**；建議 PM 啟動 "stale-reference sweep" 補修而非 revise 退回 |
| 使用者 4 個決策落地完整性 | Q0=50% / Q1=100% / Q2=100% / Q3=60% — 2/4 完整落地 |
| FUNC-107 緩解充足性（PG backup 移除後）| **14 天內充足**（使用者明示接受 trade-off）；建議 Info-1 補強 pg_dump emergency snapshot |
| 5 個 [BLOCKED_ON_DEPLOYER] 獨立驗證 | 1 RESOLVED / 1 半推半就 DEFERRED（SSL mode — 實際是 disable）/ 1 PARTIAL（合理）/ 1 PARTIAL（合理）/ 1 RESOLVED 但未 env var 化（Major-5）|
| 與既有 production 相容性 | ✅ Railway entrypoint LOCKED / 6 個既有 sdlc-*.yml 不破壞 / 既有 docker-compose 用 override 不破壞 |
| 不腦補檢查 | ✅ 無腦補 multi-region / read replica / message queue / Sentry 強制 |
| Rule 11 / 18 / 19 合規 | ✅ 全部合規（Rule 18 缺 2 個 volume parameter — Major-5；Rule 19 sdlc-merge-gate 整合 - Minor-2）|

**建議行動**:

1. **PM**（強烈推薦）: 啟動「stale-reference sweep」批次 patch 25 個 stale 行（§12.1 Major 修補清單）— 預估 1 個對話完成。完成後 deploy-init 階段升級為 **PASS**。
2. **PM**（次選）: 接受 CONDITIONAL_PASS，在 SD dispatch prompt 中**明確注入**「實際選擇 = self-hosted container + sslmode=disable + 無 PG backup DEFERRED + PG_VOLUME_NAME + PG_DATA_PATH 需新增 parameter」防止 SD 被 stale references 誤導 — Tester 保留意見：此 fallback 仍會留下 audit confusion，但勉強可行
3. **PM**: 採納 Info-1（pg_dump emergency snapshot 命令範本）— 強化 14 天 emergency path 內的資料保護
4. **PM**: 採納 Info-2（_blockedOnDeployerResolved.2_ssl_mode status 語意修正）
5. **Deployer**: 不需重出產出（Tester 不發現 Critical / 結構性錯誤）；但若 PM 選 Option B（revise）則重出 self-review.json + parameter-plan.md 補 volume + service-contract.yaml 統一傳播
6. **SD 階段**: 必須**先讀 deploy-env.json `_deploymentDecisions` + `userConfirmedDecisions` 作為真相來源**，再讀 service-contract.yaml；當兩者衝突時以 deploy-env.json 為準

---

## 14. [BLOCKED] 項目

無 Critical 阻塞項。5 Major 不阻塞但**強烈建議在進入 SD 階段前修補**（避免 stale 假設傳播到 SD/BE 實作）。

---

> **附註**:
> - 本報告由 Tester 在獨立上下文中執行（未存取 Deployer agent 開發對話歷史、未存取 PM approve 對話歷史）
> - 對照基準: BA requirement-spec / BA business-flow / SA system-arch / SA functional-flow / SA impact-assessment / test-sa report / conventions/* / environments.json / railway.toml / .github/workflows/* / 既有 root docker-compose.yml
> - 驗證工具: Read / Grep / Bash（無腳本式 verify，因 test-deploy-init 非常規 verify-* skill 涵蓋階段）
> - Tester 立場: 對抗心態 — 找 bug 即成功；Deployer score 95 自評 + L1 90 PASS 不採信，獨立評分 76（CONDITIONAL_PASS）— 與 Deployer 差 19 分主因 PM patches 後 25 個 stale references 未同步更新
> - 5 Major 全部源於同一根因「PM patch 範圍不夠廣」— 修補成本低（1 對話完成）
> - Tester 強烈不建議「靠 SD prompt 注入繞過 stale」— 真相來源（service-contract.yaml）若與決策（deploy-env.json）矛盾，會在後續 audit / Build Gate / Tester 階段反覆出現困惑
