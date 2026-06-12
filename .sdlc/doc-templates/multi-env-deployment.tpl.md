# Multi-Environment Deployment Guide (PR 17)

> 此檔指引專案如何配置與管理多環境部署（dev / staging / prod）。
> 與 `deploy-env.json.scope` 對齊：`scope=full` 預設啟用三環境，`local-staging` 啟用 dev+staging，`local` 僅 dev。
> Install 後複製到 `.sdlc/doc-templates/multi-env-deployment.md` 作為專案級客製基線。

## ⚠️ Status: DOCS-ONLY（PR 17）

**本 PR 是純文件（documentation-only）**，不修改任何現有 command / script / agent 行為：

- ✅ **PR 17 範圍**: 補完 multi-env best practices 文件 + `environments.tpl.json` schema 範例
- ❌ **PR 17 不涵蓋**: 自動 wire-up 到 `commands/release.md` / `commands/hotfix.md` / `scripts/sdlc-config-read.sh` / `scripts/sdlc-render-docker-env.sh`
- 🔄 **目前 deploy 行為**: 仍依 `deploy-env.json.scope`（local / local-staging / full）控制，不讀 `environments.json`

**整合到實際 commands/scripts** 的工作項已記錄在 §9，將分次以追加 PR 處理：
- PR 17.1: `/sdlc:init` Step 4.X 自動產出 `environments.json`
- PR 17.2: `commands/release.md` Step 5 加入 environment-aware 驗證
- PR 17.3: `commands/hotfix.md` 整合 environments.json 取代硬編碼 scope
- PR 17.4: `scripts/sdlc-config-read.sh` 加 `--env` flag
- PR 17.5: `scripts/sdlc-render-docker-env.sh` 產出 `.env.{env}.frontend|backend`

> 在這些後續 PR 完成前，**本文件可作為團隊規範參考**，但 SDLC 工作流不會強制執行。

## 1. 環境定義

| 環境 | 用途 | 流量 | 資料 | Deploy 觸發 |
|------|------|------|------|------------|
| `dev` (development) | 開發者驗證 / PR preview | 內部測試流量（< 1%）| 假資料 / synthetic | 每 PR push 自動 |
| `staging` | E2E 測試 / QA / load test | 模擬 prod 流量（synthetic load）| 完整 schema，定期 anonymized prod snapshot | merge 到 main 後自動 |
| `prod` (production) | 真實使用者 | 100% 真流量 | 真實資料 | 手動 approve（github-environment）+ tag-based |

> **黃金規則**: prod 部署必須先在 staging 驗證至少 24h（gradual rollout）。
> hotfix 例外: P0/P1 可走 hotfix-runbook §5「scope=local-staging 強制」直接從 staging 上 prod，但需 monitor 期 ≥ 15 分鐘。

## 2. 環境配置 schema (`environments.json`)

> 由 `/sdlc:init` Step 4.X 產出（PR 17+ 整合中），目前手動填寫並放在 `.sdlc/environments.json`。

```json
{
  "_comment": "環境配置 — Rule 15 §15.4: per-TASK 不該動這個檔，這是 project-level config，由 Deployer 一次設定",
  "schemaVersion": "multi-env-v1",

  "dev": {
    "baseUrl": "https://dev.example.com",
    "dbHost": "dev-db.internal",
    "dbName": "myapp_dev",
    "secretsRef": "aws-ssm:/myapp/dev/*",
    "deployTrigger": "auto-on-pr-push",
    "monitoring": "datadog-dev-dashboard",
    "smokeTestEndpoints": ["/health", "/api/v1/health"],
    "rollbackPolicy": "immediate-on-fail",
    "comment": "資料每週重置，可隨時 destroy/recreate"
  },

  "staging": {
    "baseUrl": "https://staging.example.com",
    "dbHost": "staging-db.internal",
    "dbName": "myapp_staging",
    "secretsRef": "aws-ssm:/myapp/staging/*",
    "deployTrigger": "auto-on-merge-to-main",
    "monitoring": "datadog-staging-dashboard",
    "smokeTestEndpoints": ["/health", "/api/v1/health", "/api/v1/orders"],
    "rollbackPolicy": "immediate-on-fail",
    "soakTimeHours": 24,
    "comment": "Prod-like 環境，模擬 production load；prod 部署前必經此階段 ≥ 24h"
  },

  "prod": {
    "baseUrl": "https://example.com",
    "dbHost": "prod-db.internal.aws-rds-replica-aware",
    "dbName": "myapp_prod",
    "secretsRef": "aws-ssm:/myapp/prod/*",
    "deployTrigger": "tag-based + github-environment-approval",
    "monitoring": "datadog-prod-dashboard + pagerduty",
    "smokeTestEndpoints": ["/health", "/api/v1/health", "/api/v1/orders", "/api/v1/checkout"],
    "rollbackPolicy": "auto-on-error-rate-1pct",
    "monitorPeriodMinutes": 15,
    "approvalReviewers": ["@cto", "@head-of-eng"],
    "comment": "真實使用者流量，rollback 走 rollback-runbook.tpl.md §3"
  }
}
```

## 3. Promotion Flow（dev → staging → prod）

### 3.1 標準流程（feature TASK）

```
PR push → CI build → dev deploy (auto)
                       ↓
                       smoke test (dev)
                       ↓
                       SDLC test phase approved（V1.W2 fix: release.md 前置條件）
                       ↓
                       PR review + approve
                       ↓
                       merge to main
                       ↓
                       staging deploy (auto)
                       ↓
                       smoke test (staging) + 24h soak
                       ↓
                       /sdlc:release （驗證 test phase = approved + 版本 tag + GitHub Environment approval）
                       ↓
                       prod deploy
                       ↓
                       monitor 15 min
                       ↓
                       complete
```

> **PR 17 V1.W2 fix**: 加入 SDLC `test` phase approved 步驟。`commands/release.md:27` 強制要求 `state.json.tasks[TASK-ID].phases.test.status = "approved"` 才能 release，不只是 PR review。

### 3.2 Hotfix 加速流程（P0/P1）

```
hotfix branch → CI build → local validation
                            ↓
                            staging deploy (強制 scope=local-staging)
                            ↓
                            smoke test (staging)
                            ↓
                            觀察 5 min（不需 24h soak）
                            ↓
                            手動 trigger prod deploy（不自動）
                            ↓
                            monitor 15 min
                            ↓
                            事後補件 24h (P0) / 48h (P1)
```

> **重要**: hotfix 跳過 dev（避免增加變因），但**不跳過 staging**（最後一道安全網）。

### 3.3 Cherry-pick 補丁流程（已 release 的版本需要修）

```
1. 從 prod tag 切 hotfix 分支（hotfix-runbook §3）
2. 修完 + staging 驗證
3. cherry-pick 到 main（避免下次 prod deploy 蓋掉）
4. 給 hotfix 自己一個 tag（vX.Y.(Z+1)-hotfix-NNN）
5. prod deploy hotfix tag
```

## 4. 環境切換命令

### 4.1 讀取環境配置

```bash
# 讀取特定環境的 baseUrl
ENV_NAME=staging
BASE_URL=$(jq -r ".${ENV_NAME}.baseUrl" .sdlc/environments.json)

# 讀取所有可用環境
jq -r 'to_entries[] | select(.key | startswith("_") | not) | .key' .sdlc/environments.json
```

### 4.2 跑 smoke test 對特定環境

```bash
ENV_NAME=staging
BASE_URL=$(jq -r ".${ENV_NAME}.baseUrl" .sdlc/environments.json)
bash scripts/deploy-smoke-test.sh "$BASE_URL"
```

### 4.3 驗證 promotion 順序（不可跳級）

```bash
# 不可從 dev 直接到 prod
# /sdlc:release 應檢查 staging soak time ≥ environments.staging.soakTimeHours

LAST_STAGING_DEPLOY=$(jq -r '.staging.lastDeploy.timestamp // ""' .sdlc/environments-state.json)
NOW=$(date -u +%s)
LAST=$(date -j -f "%Y-%m-%dT%H:%M:%SZ" "$LAST_STAGING_DEPLOY" +%s 2>/dev/null || \
       date -d "$LAST_STAGING_DEPLOY" +%s 2>/dev/null || echo 0)
SOAK_HOURS=$(jq '.staging.soakTimeHours' .sdlc/environments.json)
ELAPSED=$(( (NOW - LAST) / 3600 ))

if [ "$ELAPSED" -lt "$SOAK_HOURS" ]; then
    echo "❌ Staging soak 不足（已過 ${ELAPSED}h，需要 ${SOAK_HOURS}h）"
    echo "   建議: 等待 $((SOAK_HOURS - ELAPSED))h，或走 hotfix 流程"
    exit 1
fi
```

## 5. 環境隔離原則

### 5.1 強制隔離

- **資料庫**: 每環境獨立實例（不共用 staging-prod cluster）
- **Secrets**: 每環境獨立路徑（`aws-ssm:/myapp/{env}/*`），不可硬編碼
- **DNS**: 每環境獨立 subdomain（dev.example.com / staging.example.com / example.com）
- **CDN**: prod 使用獨立 distribution；dev/staging 可共用 lower-tier
- **Monitoring**: 每環境獨立 dashboard + alert routing（dev 不應觸發 PagerDuty）

### 5.2 允許共享

- **Container registry**: 同一 image registry，**同一 tag** 跨環境（V1.W1 fix: 不要用 env-suffix tag，會違反 §6 promote-not-rebuild）
- **Code repository**: 同一 main branch，不同 deploy target
- **Build artifacts**: 同一 build，不同 deploy 環境（promote-not-rebuild 原則 — values-{env}.yaml 提供 env-specific config，image 本身不變）

### 5.3 反模式

❌ **不要做**:
- 從 staging 環境連 prod 資料庫做 join query
- 用同一個 secret 在 dev/staging/prod
- 在 dev 部署可疑的 third-party SDK 後直接 promote 到 prod（dev 應 soak ≥ 1 day）
- 跳過 staging 直接從 dev 到 prod（hotfix 例外，但仍經 staging）

## 6. Promote-Not-Rebuild 原則

> 同一個 image artifact 在三個環境都應該是**位元相同**的，只有 config（env vars / secrets）不同。

```bash
# Build 一次（CI 在 PR merge 後）
docker build -t myapp:v1.5.0 .
docker push myapp:v1.5.0

# Promote 到 dev
helm upgrade myapp-dev --set image.tag=v1.5.0 -f values-dev.yaml

# Promote 到 staging（同 image，不同 values）
helm upgrade myapp-staging --set image.tag=v1.5.0 -f values-staging.yaml

# Promote 到 prod（同 image，不同 values）
helm upgrade myapp-prod --set image.tag=v1.5.0 -f values-prod.yaml
```

**理由**: 確保「在 staging 驗證的 binary 等於 prod 上線的 binary」，避免 build-once-deploy-different-binary 的環境不一致。

## 7. 環境特定的 CI/CD 配置

> 詳見 `doc-templates/github-actions/` — 三種 workflow：
> - `pr-validation.yml`（dev deploy + smoke test）
> - `merge-to-main.yml`（staging deploy + soak）
> - `release.yml`（prod deploy with manual approval）

### 7.1 PR 25 — Per-env .env files 消費方式

> **PR 25 V2.C1 fix**: 補上 per-env `.env.{env}.frontend` / `.env.{env}.backend` 的實際使用方式。

`bash scripts/sdlc-render-docker-env.sh --env staging` 產出的檔案，需在 docker-compose / Kubernetes / Helm 配置中明確消費：

#### 方式 A: docker-compose 多 env_file

```yaml
# docker-compose.staging.yml
services:
  frontend:
    env_file:
      - .env.frontend           # 共用 vars (legacy mode)
      - .env.staging.frontend   # per-env override (PR 25)
  backend:
    env_file:
      - .env.backend
      - .env.staging.backend
```

啟動: `docker compose -f docker-compose.yml -f docker-compose.staging.yml up`

#### 方式 B: 環境變數覆蓋

```bash
# 將 per-env file 載入 shell，再啟 docker compose
set -a; source .env.staging.frontend; source .env.staging.backend; set +a
docker compose up
```

#### 方式 C: Kubernetes ConfigMap from env file

```bash
kubectl create configmap myapp-staging-fe --from-env-file=.env.staging.frontend -n staging
kubectl create configmap myapp-staging-be --from-env-file=.env.staging.backend -n staging
# 然後在 Deployment.spec.containers.envFrom.configMapRef 引用
```

#### 方式 D: Helm values from env file

```bash
# 將 .env.{env} 轉為 helm values:
helm install myapp ./chart \
  --set-file env_file=.env.staging.backend \
  -n staging
```

### 7.2 整合 sdlc-render-docker-env.sh 到 CI/CD

```yaml
# .github/workflows/staging-deploy.yml
- name: Render staging .env files
  run: bash scripts/sdlc-render-docker-env.sh "$TASK_ID" --env staging

- name: Deploy to staging
  run: docker compose -f docker-compose.yml -f docker-compose.staging.yml up -d
```

## 8. 與其他 Rule 的整合

- **Rule 11（不可逆操作）**: prod deploy 前 staging 必驗證 expand-contract 三階段
- **Rule 14（Journal）**: 每環境 deploy 都寫 `.sdlc/journals/deploy-{env}.json`
- **Rule 15 §15.8**: `tasks.{ID}.deployments[]` 候選白名單（含 env, deployedAt, version）
- **Rule 19（CI Gate）**: GitHub Environment 是 prod approval 機制
- **Rule 20.2（Browser Verify）**: staging + prod 都要跑 browser smoke test
- **rollback-runbook §6（Drill）**: 月度 drill 在 staging 跑

## 9. 補件 / 改善 TODO

- [ ] `/sdlc:init` Step 4.X 自動生成 `environments.json` 模板（PR 17 後續）
- [ ] `/sdlc:status` 顯示各環境最新 deploy 版本 + soak 進度
- [ ] `scripts/sdlc-state.sh add-deployment` helper（per-env deploy 記錄）
- [ ] 每環境的 rollback drill 紀錄分開（rollback-drill-{env}-{YYYY-MM}.md）
