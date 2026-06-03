# Staging 模式 — 手動補齊清單

本 TASK 選擇了 `local-staging` scope。本模式的完整自動化尚未就緒，以下檔案需要使用者手動補齊或調整。

## ⚠️ 需要手動建立

### 1. Staging deploy workflow

- 檔案: `.github/workflows/deploy-staging.yml`
- 目的: merge 到 main 或 tag `staging-*` 時觸發 staging 部署
- 參考: `ci.yml` 現有結構 + 加 deploy 步驟
- 需補: staging 主機資訊、SSH/kubeconfig secrets、部署指令

### 2. Docker Compose Production 配置

- 檔案: `docker-compose.prod.yml`
- 目的: 生產模式的 override（resource limits、restart policy、健康檢查頻率等）
- 範本: 見 https://docs.docker.com/compose/production/

### 3. Deploy Guide Staging 區塊

- 檔案: `deploy/deploy-guide.md` §3
- 需填: Staging 主機 URL、GitHub Environment secrets 設定指令、觸發方式

## 🔧 需要手動設定（不在本地檔案）

### GitHub Secrets（Settings → Secrets and variables → Actions）

- `STAGING_SSH_KEY` / `STAGING_HOST` / `STAGING_USER`
- 或 `STAGING_KUBECONFIG`（若 K8s）
- DB 連線字串、JWT secret 等

### DNS 設定

- staging.{your-domain}.com 指向 staging 主機

## 📋 完成後刪除本檔案

以上全部補齊後，將此檔案刪除並在 `audit.log` 記錄 `staging_manual_setup_complete`。

## 或者

若你決定不需要 staging，執行 `/sdlc:revise deploy-init` 把 scope 改回 `local`，Deploy(Execute) 會重新產出乾淨的 local-only 配置。
