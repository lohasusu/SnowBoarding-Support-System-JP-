---
document_id: "DEPGUIDE-{TASK_ID}-v1.0"
title: "環境部署指引"
version: "1.0"
date: "{YYYY-MM-DD}"
author: "Deploy"
status: "Draft"
task_id: "{TASK-ID}"
phase: "deploy"
source_documents:
  - "DEPCONF-{TASK_ID}-v1.0"
  - "CICD-{TASK_ID}-v1.0"
change_history:
  - version: "1.0"
    date: "{YYYY-MM-DD}"
    author: "Deploy"
    changes: "初版建立"
approval:
  reviewer: "PM"
  date: ""
  result: "Pending"
  notes: ""
---

# 環境部署指引

> **用途**: 本文件是給使用者/運維人員的操作手冊。按表填入參數、按指令 copy-paste 即可完成部署。
> **維護者**: Deploy 角色產出，每次部署更新。
> **前置條件**: Docker 已安裝、Git 已安裝、具備目標環境的存取權限。

## 1. 參數總表

> 請將以下表格中「待填」欄位補齊。本地值已由 SDLC 自動設定完畢。

### 1.1 資料庫參數

| 參數名 | 說明 | 本地值（已設好） | Staging（待填） | Production（待填） |
|--------|------|-----------------|----------------|-------------------|
| `DB_CONNECTION_STRING` | 資料庫連線字串 | `{local_db_connection}` | | |
| `POSTGRES_USER` | 資料庫使用者 | `postgres` | | |
| `POSTGRES_PASSWORD` | 資料庫密碼 | `postgres` | | |
| `POSTGRES_DB` | 資料庫名稱 | `{db_name}` | | |

### 1.2 認證參數

| 參數名 | 說明 | 本地值（已設好） | Staging（待填） | Production（待填） |
|--------|------|-----------------|----------------|-------------------|
| `JWT_SECRET` | JWT 簽章密鑰 | `dev-secret-change-me` | | |
| `JWT_ISSUER` | JWT 發行者 | `{project}-local` | | |
{SSO_PARAMS}

### 1.3 應用程式參數

| 參數名 | 說明 | 本地值（已設好） | Staging（待填） | Production（待填） |
|--------|------|-----------------|----------------|-------------------|
| `API_BASE_URL` | 後端 API 路徑 | `http://localhost:{backend_port}/api` | | |
| `NEXT_PUBLIC_API_BASE_URL` | 前端呼叫 API 路徑 | `http://localhost:{backend_port}/api` | | |
{APP_PARAMS}

### 1.4 基礎設施參數

| 參數名 | 說明 | 本地值（已設好） | Staging（待填） | Production（待填） |
|--------|------|-----------------|----------------|-------------------|
| `CONTAINER_REGISTRY` | Container Registry | `local` | | |
| `REGISTRY_ORG` | Registry 組織名 | `{org}` | | |
{INFRA_PARAMS}

### 1.5 CI/CD 參數（GitHub Secrets 設定）

| Secret 名稱 | 說明 | 設定指令 |
|-------------|------|---------|
{CICD_SECRETS}

## 2. 本地部署（一鍵啟動）

> 本地環境已由 SDLC 自動配置完畢，以下指令可直接執行。

```bash
# Step 1: 複製環境變數（若尚未建立）
cp .env.example .env

# Step 2: 建構並啟動所有服務
docker compose up -d --build

# Step 3: 等待服務就緒（約 30 秒）
sleep 30

# Step 4: 確認服務狀態
docker compose ps

# Step 5: 驗證健康檢查
curl -sf http://localhost:{frontend_port}/health && echo "✅ 前端正常"
curl -sf http://localhost:{backend_port}/api/health && echo "✅ 後端正常"
curl -sf http://localhost:{backend_port}/swagger && echo "✅ Swagger 正常"

# Step 6: 開啟瀏覽器
echo "前端: http://localhost:{frontend_port}"
echo "後端 API: http://localhost:{backend_port}/api"
echo "Swagger: http://localhost:{backend_port}/swagger"
```

### 2.1 本地停止

```bash
docker compose down        # 停止服務（保留資料）
docker compose down -v     # 停止服務 + 清除資料庫
```

## 3. Staging 部署

> 請先完成第 1 節的 Staging 參數填寫。

### 3.1 設定 GitHub Secrets

```bash
# 將 Staging 參數設定為 GitHub Environment Secrets
{STAGING_SECRET_COMMANDS}
```

### 3.2 觸發部署

```bash
# 方法 A: 透過 Git tag 觸發
git tag v{version}-staging
git push origin v{version}-staging

# 方法 B: 手動觸發 GitHub Actions
gh workflow run deploy-staging.yml
```

### 3.3 驗證部署

```bash
# 確認 CI/CD 執行成功
gh run list --workflow=deploy-staging.yml --limit=1

# 確認服務可達
curl -sf https://{STAGING_HOST}/health && echo "✅ Staging 前端正常"
curl -sf https://{STAGING_HOST}/api/health && echo "✅ Staging 後端正常"
```

## 4. Production 部署

> 請先完成第 1 節的 Production 參數填寫。Production 部署需要額外確認。

### 4.1 前置確認清單

- [ ] Staging 已部署且驗證通過
- [ ] 所有安全掃描 Critical/High = 0
- [ ] 資料庫 migration 已在 Staging 驗證
- [ ] 回滾策略已確認
- [ ] Production 參數已填入第 1 節

### 4.2 設定 GitHub Secrets

```bash
# 將 Production 參數設定為 GitHub Environment Secrets
{PROD_SECRET_COMMANDS}
```

### 4.3 觸發部署

```bash
# Production 部署透過正式 release tag
git tag v{version}
git push origin v{version}
# CI/CD 會自動部署到 Production（需 Environment approval）
```

### 4.4 驗證部署

```bash
curl -sf https://{PROD_HOST}/health && echo "✅ Production 前端正常"
curl -sf https://{PROD_HOST}/api/health && echo "✅ Production 後端正常"
curl -sf https://{PROD_HOST}/swagger && echo "✅ Production Swagger 正常"
```

## 5. 連線資訊

| 環境 | 前端 URL | 後端 API URL | Swagger | 資料庫 |
|------|---------|-------------|---------|--------|
| Local | `http://localhost:{frontend_port}` | `http://localhost:{backend_port}/api` | `http://localhost:{backend_port}/swagger` | `localhost:{db_port}` |
| Staging | `https://{STAGING_HOST}` | `https://{STAGING_HOST}/api` | `https://{STAGING_HOST}/swagger` | {待填} |
| Production | `https://{PROD_HOST}` | `https://{PROD_HOST}/api` | `https://{PROD_HOST}/swagger` | {待填} |

## 6. 回滾程序

> ⚠️ **Deploy(Execute) 依照 `deploy-env.json.platform` 填入對應平台的實指令**，以下為模板各平台選擇（保留你的平台段落，刪除其他）。

### 6.1 自動回滾觸發條件

- 健康檢查連續失敗 > 2 分鐘
- 錯誤率較基線增加 > 5 倍（部署後 10 分鐘內）
- P0 bug 在部署後 30 分鐘內被回報
- 資料完整性檢查失敗

### 6.2 手動回滾指令（依平台）

#### 6.2.A Docker Compose

```bash
# 前置: image tag 必須固定（v{N} 或 git-sha），不可只用 latest
# 1. 查歷史 image tags
docker image ls {project}-fe {project}-be

# 2. 回滾到指定版本
docker compose -f docker-compose.prod.yml down
docker compose pull {project}-fe:{previous_tag} {project}-be:{previous_tag}
# 編輯 docker-compose.prod.yml 的 image 標籤，或透過環境變數 override
IMAGE_TAG={previous_tag} docker compose -f docker-compose.prod.yml up -d

# 3. 驗證
curl -sf https://{PROD_HOST}/health
```

#### 6.2.B Kubernetes

```bash
# 1. 查看 rollout 歷史
kubectl rollout history deployment/{deployment-name} -n {namespace}

# 2. 回滾上一版
kubectl rollout undo deployment/{deployment-name} -n {namespace}

# 或回滾到指定 revision
kubectl rollout undo deployment/{deployment-name} --to-revision={N} -n {namespace}

# 3. 驗證
kubectl rollout status deployment/{deployment-name} -n {namespace}
```

#### 6.2.C Vercel

```bash
# 1. 查歷史 deployments
vercel ls --prod

# 2. Promote 指定 deployment 為 production（真正的 rollback）
vercel rollback <deployment-url>
# 或 Vercel Dashboard 選 deployment → "Promote to Production"
```

#### 6.2.D AWS ECS

```bash
# 1. 查歷史 task definitions
aws ecs list-task-definitions --family-prefix {project} --sort DESC --max-items 5

# 2. 更新 service 使用上一版
aws ecs update-service \
  --cluster {cluster-name} \
  --service {service-name} \
  --task-definition {previous-task-def-arn} \
  --force-new-deployment

# 3. 監控
aws ecs describe-services --cluster {cluster-name} --services {service-name}
```

#### 6.2.E AWS Lambda（Alias + Versioning）

```bash
# 1. 列出版本
aws lambda list-versions-by-function --function-name {function-name}

# 2. 把 live alias 指向上一版
aws lambda update-alias \
  --function-name {function-name} \
  --name live \
  --function-version {previous-version-number}
```

#### 6.2.F Heroku

```bash
heroku releases -a {app-name} | head -5
heroku releases:rollback v{N} -a {app-name}
```

#### 6.2.G Cloudflare Workers

```bash
wrangler deployments list
wrangler rollback --message "reason for rollback" <deployment-id>
```

### 6.3 資料庫回滾

> ⚠️ **只有向後相容（expand-contract）的 migration 才能安全回滾**。若 migration 刪除 column / 改 type，請用 fix forward（寫新 migration 修正），不要 down。

#### 6.3.A Prisma
```bash
npx prisma migrate resolve --rolled-back {migration-name}
npx prisma migrate status
```

#### 6.3.B TypeORM
```bash
npm run typeorm migration:revert
```

#### 6.3.C Alembic (Python)
```bash
alembic current
alembic downgrade -1        # 回滾上一個
alembic downgrade {revision}  # 回滾到指定版本
```

#### 6.3.D Flyway
```bash
flyway info
flyway undo  # 需要 Teams Edition
```

#### 6.3.E golang-migrate
```bash
migrate -path migrations -database "{DB_URL}" down 1
```

#### 6.3.F EF Core
```bash
dotnet ef database update {PreviousMigrationName}
```

### 6.4 前置要求（必須事先建立，才能回滾）

- [ ] Image tag 使用 `v{version}` 或 `{git-sha}`，**絕不只用 `latest`**
- [ ] 保留至少 **3 個歷史版本**（Image registry / K8s replicas / Vercel / ECS task definitions）
- [ ] Migration 採 **expand-contract 模式**，向後相容
- [ ] Rollback 程序**在 staging 演練過**（首次 production 部署前，BE Rule 3 要求）

## 7. 故障排除

| 問題 | 可能原因 | 解決方式 |
|------|---------|---------|
| 服務啟動失敗 | 環境變數缺失 | 檢查 `.env` 檔案，確認所有 `required` 參數已填寫 |
| 資料庫連線失敗 | 連線字串錯誤 | 確認 `DB_CONNECTION_STRING` 格式和主機可達 |
| Health check 失敗 | 服務尚未就緒 | 等待 30 秒後重試；檢查 `docker compose logs` |
| Swagger 不可達 | Nginx 未轉發 | 確認 nginx.conf 包含 `/swagger` proxy 規則 |
| CI/CD 失敗 | Secrets 未設定 | 確認 GitHub Secrets 已按第 1.5 節設定 |
| Port 衝突 | 本地 port 被佔用 | 執行 `lsof -i :{port}` 查看佔用程序 |

## 追溯矩陣

| 章節 | 對應規格 |
|------|---------|
| §1 參數總表 | deploy-config.md §2 環境變數 |
| §2 本地部署 | deploy-result.md §4 本地驗證 |
| §3 Staging | cicd-spec.md §2.5 Stage 階段 |
| §4 Production | cicd-spec.md §2.6 Deploy 階段 |
| §5 連線資訊 | deploy-result.md §5 健康檢查 |
| §6 回滾 | deploy-config.md 回滾策略 |
