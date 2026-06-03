---
document_id: "DEPLOY-{TASK_ID}-v1.0"
title: "部署配置"
version: "1.0"
date: "{YYYY-MM-DD}"
author: "Deploy"
status: "Draft"
task_id: "{TASK-ID}"
phase: "deploy"
source_documents:
  - "CICD-{TASK_ID}-v1.0"
  - "CODEARCH-{TASK_ID}-v1.0"
change_history:
  - version: "1.0"
    date: "{YYYY-MM-DD}"
    changes: "初始版本"
    author: "Deploy"
approval:
  reviewer: "PM"
  date: ""
  result: "Pending"
  notes: ""
---

# 部署配置

## 1. 環境矩陣

| 環境 | 用途 | URL | 部署方式 |
|------|------|-----|---------|
| development | 本地開發 | localhost:{port} | 手動 |
| staging | 測試驗證 | {staging_url} | CI 自動 |
| production | 正式環境 | {prod_url} | CI 自動（需審核） |

## 2. 環境變數配置

### 2.1 Layer 1: Secrets（Secrets Manager）

| 變數名 | 用途 | 管理方式 |
|--------|------|---------|
| DATABASE_URL | 資料庫連線字串 | Vault / AWS SSM |
| JWT_SECRET | JWT 簽章金鑰 | Vault / AWS SSM |
| API_KEY | 外部服務 API Key | Vault / AWS SSM |

### 2.2 Layer 2: 環境特定配置（CI/CD 環境變數）

| 變數名 | Development | Staging | Production |
|--------|------------|---------|-----------|
| API_URL | http://localhost:{port} | {staging_api} | {prod_api} |
| LOG_LEVEL | debug | info | warn |
| CORS_ORIGIN | * | {staging_domain} | {prod_domain} |

### 2.3 Layer 3: Feature Flags

| Flag | 說明 | Development | Staging | Production |
|------|------|------------|---------|-----------|
| {feature_flag} | {說明} | true | true | false |

### 2.4 Layer 4: Build-time 常量（.env）

| 變數名 | 值 | 說明 |
|--------|-----|------|
| NODE_ENV | {environment} | 環境標識 |
| PORT | {port} | 服務埠號 |

## 3. 健康檢查

### 3.1 Readiness Probe
```
GET /health/ready
期望: 200 OK
檢查: DB 連線 + 外部服務
超時: 5s
間隔: 10s
```

### 3.2 Liveness Probe
```
GET /health/live
期望: 200 OK
檢查: 應用程序存活
超時: 3s
間隔: 15s
```

### 3.3 Startup Probe
```
GET /health/startup
期望: 200 OK
檢查: 初始化完成（DB migration, cache warm-up）
超時: 30s
間隔: 5s
最大失敗次數: 12（= 60s 啟動時間）
```

## 4. 容器化配置（MANDATORY）

> **規則**: 必須使用 Docker Buildx Multi-Stage 構建 + Container Registry 推送。
> 禁止使用傳統 `docker build`。配置從 `.sdlc/config.json` 的 `containerStrategy` 讀取。

### 4.1 Container Registry 配置

| 項目 | 值 |
|------|-----|
| Registry | {從 config.json containerStrategy.registry} |
| Registry URL | {從 config.json containerStrategy.registryUrl} |
| Image 命名 | `{registry}/{org}/{service}:{tag}` |
| Tag 策略 | `latest`（main）+ `{git-sha-short}`（每次 build）+ `v{semver}`（release） |
| 認證方式 | {CI/CD 環境變數} |

### 4.2 Docker Buildx 配置

| 項目 | 值 |
|------|-----|
| 平台 | {從 config.json containerStrategy.buildxPlatforms} |
| Cache | `--cache-from type=gha --cache-to type=gha,mode=max` |
| Builder | `docker buildx create --use --name multiarch-builder` |

### 4.3 CI/CD Build + Push 步驟（MANDATORY）

```yaml
# GitHub Actions 範例
- name: Set up Docker Buildx
  uses: docker/setup-buildx-action@v3

- name: Login to Registry
  uses: docker/login-action@v3
  with:
    registry: {registry}
    username: {username}
    password: {password_secret}

- name: Build and Push
  uses: docker/build-push-action@v5
  with:
    context: .
    file: ./Dockerfile
    platforms: {platforms}
    push: true
    tags: |
      {registry}/{org}/{service}:latest
      {registry}/{org}/{service}:${{ github.sha }}
    cache-from: type=gha
    cache-to: type=gha,mode=max
```

### 4.4 Dev Container 驗證

| 檢查項 | 預期 |
|--------|------|
| `.devcontainer/devcontainer.json` 存在 | ✅ |
| `devcontainer.json` 可被 JSON parse | ✅ |
| `forwardPorts` 包含所有服務埠 | ✅ |
| `postCreateCommand` 存在 | ✅ |

### 4.5 Dockerfile 驗證

| 檢查項 | 預期 |
|--------|------|
| 使用 Multi-Stage（含 `AS builder` 或 `AS deps`） | ✅ |
| 含 `HEALTHCHECK` 指令 | ✅ |
| 含 `USER` 指令（非 root） | ✅ |
| 無 `docker build` 命令（必須用 buildx） | ✅ |

## 5. 啟動安全規則

| 規則 | 說明 |
|------|------|
| 零機密在程式碼中 | 所有敏感資訊通過環境變數注入 |
| 缺少必要變數 = 拒絕啟動 | 應用啟動時驗證所有必要環境變數 |
| 預設值安全 | 預設值不會造成安全風險 |
