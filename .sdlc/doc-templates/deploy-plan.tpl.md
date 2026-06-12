---
document_id: "DEPLOYPLAN-{TASK_ID}-v1.0"
title: "部署規劃書"
version: "1.0"
date: "{YYYY-MM-DD}"
author: "Deployer (Init)"
status: "Draft"
task_id: "{TASK-ID}"
phase: "deploy-init"
source_documents:
  - "SYSARCH-{TASK_ID}-v1.0"
  - "CONTRACT-{TASK_ID}-v1.0"
approval:
  reviewer: "PM"
  date: ""
  result: "Pending"
---

# 部署規劃書

> Deploy(Init) 產出。Deploy(Execute) 會以本規劃書為基礎，產出最終 CI workflow / Dockerfile / k8s manifests。

## 1. CI/CD Pipeline 骨架

6 階段 Pipeline（Build → Lint → Test → Security Scan → Stage → Deploy）:

| 階段 | 目的 | 失敗處理 |
|------|------|---------|
| Build | 編譯產出 artifact | fail → 停止後續 |
| Lint | 靜態檢查 | fail → 停止後續 |
| Test | 單元 + 整合測試 | fail → 停止後續 |
| Security Scan | 呼叫 verify-security skill | Critical > 0 → 必阻塞；High > 0 → scope=staging/full 阻塞 |
| Stage | 部署 staging 驗證 | fail → 自動 rollback |
| Deploy | 部署 prod（full scope 才有） | `environment:production` 審批後執行 |

## 2. Path-based CI 觸發設計

從 `service-contract.yaml` 的 `ci_path_filters` 展開：

| 檔案路徑變動 | 觸發 pipeline |
|------------|--------------|
| `frontend/**` / `src/frontend/**` / `client/**` | 只跑 FE lint + FE test + FE build |
| `backend/**` / `src/backend/**` / `server/**` / `api/**` | 只跑 BE lint + BE test + BE build |
| `docker-compose*.yml` / `Dockerfile*` / `.github/**` / `nginx*` / `k8s/**` | Docker build + compose config 驗證 |
| `package.json` / `*.lock` / `tsconfig*.json` | 跑 FE + BE 完整 pipeline |
| Deploy PR (`{prefix}/{TASK}/deploy`) | 完整 integration pipeline |

## 3. Multi-PR 分支觸發規則

根據 `config.json.gitStrategy` + `deploy-env.json`。

**授權表**: 見 `doc-templates/path-based-ci-rules.tpl.md §3`（唯一真相：PR 來源分支 × 觸發的 CI Job × 部署環境 6 行對應表）。本節不重複列表；若需調整分支命名或對應 CI Job，改 `path-based-ci-rules.tpl.md §3`。

## 4. 環境配置 4 層級分離

| 層級 | 存放位置 | 範例 |
|------|---------|------|
| Secrets | Secrets Manager（AWS SSM / Vault / Doppler / CI secrets） | DB_PASSWORD, JWT_SECRET |
| 環境特定配置 | CI/CD 環境變數 / ConfigMap | API_BASE_URL, LOG_LEVEL |
| Feature flags | 配置服務（LaunchDarkly / GrowthBook / 自建） | ENABLE_NEW_CHECKOUT |
| Build-time 常量 | `.env` 檔案（不含 secret） | APP_NAME, VERSION |

**規則**: 零機密在程式碼中 / 缺少必要環境變數 = 應用拒絕啟動。

## 5. 回滾策略骨架

| 項目 | 值 |
|------|-----|
| 自動回滾觸發 | 健康檢查失敗 > 2 分鐘 / 錯誤率 > 5 倍基線（部署後 10 分鐘內）/ P0 bug 30 分鐘內 / 資料完整性失敗 |
| 回滾方式 | 依 `deploy-env.json.platform` 選用（見 `doc-templates/deploy-guide.tpl.md §6.2`）|
| 預計回滾時間 | < 5 分鐘（依 platform；Lambda < 30s / Compose < 3min / K8s < 2min） |
| 前置要求 | Image tag 固定（v{N} + git-sha）/ 保留 ≥ 3 個歷史版本 / Migration 向後相容（expand-contract） |

## 6. 健康檢查設計

| Probe | 端點 | 間隔 | 失敗閾值 | 說明 |
|-------|------|------|---------|------|
| Readiness | `/api/health` | 5s | 3 次 | 就緒才接流量 |
| Liveness | `/api/health` | 10s | 5 次 | 不 healthy 則重啟 |
| Startup | `/api/health` | 10s | 30 次 | 允許冷啟動時間 |

**檢查內容**: DB 連線 + 外部服務可達 + 磁碟空間。

## 追溯矩陣

| 規劃項目 | 依據 |
|---------|------|
| Path filter | service-contract.yaml `ci_path_filters` |
| 分支規則 | config.json `gitStrategy.multiPR` + deploy-env.json `scope` |
| 環境列表 | deploy-env.json `environments` |
| 回滾指令 | deploy-guide.tpl.md §6.2 + deploy-env.json `platform` |
