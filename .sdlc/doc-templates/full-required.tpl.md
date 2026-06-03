# Full 模式 — 手動補齊清單

本 TASK 選擇了 `full` scope（含 Production）。以下自動化尚未就緒。

## ⚠️ 需要手動建立

### 上述 STAGING-REQUIRED 所有項目

（見 local-staging 的 staging deploy workflow、docker-compose.prod.yml、deploy-guide §3，或參考 `doc-templates/staging-required.tpl.md`）

### 額外 Production 項目

#### 1. `.github/workflows/deploy-prod.yml`

- 必含 `environment: production`（GitHub Environment protection）
- 必含 `docker buildx build --push`、deploy、post-deploy health check、`if: failure()` rollback
- 最簡 CI 結構可參考 `doc-templates/ci-local-minimal.tpl.yaml`；Prod deploy 的審批 gate + rollback step 需依平台自填（指令見 `doc-templates/deploy-guide.tpl.md §6.2`）
- Deployer agent 規範見 `agents/deployer.md` §E-8.3 的 8a-full 要求清單

#### 2. K8s manifests（若 platform=K8s）

```
k8s/
├── namespace.yml
├── frontend-deployment.yml + service.yml
├── backend-deployment.yml + service.yml
├── ingress.yml
├── configmap.yml
└── secrets.yml (placeholder)
```

#### 3. Serverless 配置（若 platform=Serverless）

- `vercel.json` / `serverless.yml` / `wrangler.toml` 之一
- 需補: runtime、region、memory、timeout、env bindings

#### 4. Monitoring Alerts（若 monitoring != none）

- Datadog: `monitors/*.json`
- Grafana: `dashboards/*.json` + alerting rules
- Prometheus: `alertmanager.yml` + rules
- 告警通道 secrets: `SLACK_WEBHOOK_URL` / `PAGERDUTY_KEY` / `ALERT_EMAIL`

#### 5. Backup 策略

- Cron / scheduled task 設定
- 備份目的地（S3 bucket / GCS / 其他）
- 還原測試計畫

#### 6. DNS / TLS

- 正式域名 A/CNAME 記錄
- TLS 憑證（Let's Encrypt via cert-manager / AWS ACM / 商業憑證）

## 🔧 GitHub Environment protection 設定（MANDATORY 若 prodApproval.required = true）

Repository Settings → Environments → New environment → `production`:

- **Required reviewers**: 至少 1 個 team lead
- **Deployment branches**: 只允許 tag `v*`
- **Wait timer**: 可選（推薦 prod deploy 前等 5 分鐘）

## 📋 完成後刪除本檔案

以上全部補齊後，將此檔案刪除並在 `audit.log` 記錄 `full_manual_setup_complete`。

## 或者

若你決定先不要 prod，執行 `/sdlc:revise deploy-init` 把 scope 改回 `local-staging` 或 `local`。
