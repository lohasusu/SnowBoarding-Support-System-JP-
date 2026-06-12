# Deploy(Init) AskUserQuestion 問題組模板

> Deployer 在 I-2 階段按此模板呼叫 AskUserQuestion。Deployer **不在自己的 agent prompt 內重寫這些 JSON**；依下方「分派邏輯」決定要發哪幾組。

## 分派邏輯（由 Deployer 實作）

| Scope | 必發問題組 | 條件式問題組 |
|-------|-----------|-------------|
| `local` | Q0 + Q1-local | 無（Q2 / Q3 跳過） |
| `local-staging` | Q0 + Q1-full + Q2 | Q3（當 Q1 選 Docker 或 K8s 時） |
| `full` | Q0 + Q1-full + Q2 | Q3（當 Q1 選 Docker 或 K8s 時） |

**回退規則（共用）**:
- 使用者選 Other → 記錄自訂內容
- 使用者跳過 → 根據 `config.json` 推斷預設，標記 `[Deploy 預設 — 使用者未確認]`
- Serverless/PaaS → 自動跳過 Q3，不產出 Dockerfile

---

## Q0 — 部署範圍（所有 scope 都必問；決定 scope 值本身）

```json
AskUserQuestion({
  "questions": [{
    "question": "這個專案的部署範圍是？（決定後續問題數量與產出檔案數量）",
    "header": "部署範圍",
    "options": [
      { "label": "本地 only（最簡模式）", "description": "只跑 localhost，不產 staging/prod 配置。適合 prototype、內部工具、開發學習。僅產出 docker-compose + Dockerfile + .env.example + 最簡 CI。" },
      { "label": "本地 + Staging", "description": "有測試環境但不到 prod。會額外產出 staging 部署配置。⚠️ 本模式目前為 stub（部分檔案要手動補），詳見 STAGING-REQUIRED.md。" },
      { "label": "本地 + Staging + Prod（完整流程）", "description": "正式對外服務。會問完整的 secrets/monitoring/backup/DNS/TLS/prod approval 等問題。⚠️ 本模式目前為 stub（多個檔案要手動補），詳見 FULL-REQUIRED.md。" }
    ],
    "multiSelect": false
  }]
})
```

答案映射: `本地 only → "local"` / `本地+Staging → "local-staging"` / `本地+Staging+Prod → "full"`

---

## Q1-local — 基礎設施（只在 scope=local 時用；2 個問題）

```json
AskUserQuestion({
  "questions": [
    {
      "question": "本地要用 Docker 運行嗎？",
      "header": "本地容器化",
      "options": [
        { "label": "是（Docker + Docker Compose）", "description": "產出 docker-compose.yml + Dockerfile" },
        { "label": "否（直接執行）", "description": "不產 Docker 檔案，使用 npm start / python manage.py 等本機指令" }
      ],
      "multiSelect": false
    },
    {
      "question": "要產出 CI 配置（lint + test + build）嗎？",
      "header": "CI 配置",
      "options": [
        { "label": "GitHub Actions", "description": "產出 .github/workflows/ci.yml（最簡版）" },
        { "label": "略過", "description": "不產 CI 配置" }
      ],
      "multiSelect": false
    }
  ]
})
```

---

## Q1-full — 基礎設施（scope=local-staging / full 時用；4 個問題）

```json
AskUserQuestion({
  "questions": [
    {
      "question": "專案要部署到哪個平台？",
      "header": "部署平台",
      "options": [
        { "label": "Docker + Docker Compose", "description": "容器化部署，適合小型到中型專案" },
        { "label": "Kubernetes (K8s)", "description": "容器編排，適合需要自動擴展的專案" },
        { "label": "Serverless (AWS Lambda / Vercel / Cloudflare)", "description": "無伺服器架構，按需計費" },
        { "label": "PaaS (Heroku / Railway / Render)", "description": "平台即服務，最簡單的部署方式" }
      ],
      "multiSelect": false
    },
    {
      "question": "CI/CD 使用哪個平台？",
      "header": "CI/CD 平台",
      "options": [
        { "label": "GitHub Actions", "description": "與 GitHub 深度整合，免費額度充裕" },
        { "label": "GitLab CI", "description": "與 GitLab 深度整合，支援自建 Runner" },
        { "label": "Jenkins", "description": "自建 CI/CD 伺服器，高度可自訂" }
      ],
      "multiSelect": false
    },
    {
      "question": "部署策略偏好？",
      "header": "部署策略",
      "options": [
        { "label": "Rolling Update", "description": "逐步替換舊版本，零停機，最常見" },
        { "label": "Blue-Green", "description": "雙環境切換，可瞬間回滾，需雙倍資源" },
        { "label": "Canary", "description": "漸進式流量切換，先導 10% 驗證，適合大流量系統" }
      ],
      "multiSelect": false
    },
    {
      "question": "Git 託管平台？（用於設定分支保護規則）",
      "header": "Git 託管",
      "options": [
        { "label": "GitHub", "description": "Branch protection rules + PR reviews" },
        { "label": "GitLab", "description": "Protected branches + Merge request approvals" },
        { "label": "Bitbucket", "description": "Branch permissions + Pull request approvals" }
      ],
      "multiSelect": false
    }
  ]
})
```

---

## Q2 — 環境與 Secrets（scope ≠ local 時必問）

```json
AskUserQuestion({
  "questions": [
    {
      "question": "需要哪些部署環境？",
      "header": "部署環境",
      "options": [
        { "label": "dev + prod", "description": "最小配置：開發 + 正式環境" },
        { "label": "dev + staging + prod", "description": "標準配置：開發 + 測試驗證 + 正式環境（推薦）" },
        { "label": "dev + staging + uat + prod", "description": "完整配置：開發 + 測試 + 用戶驗收 + 正式環境" }
      ],
      "multiSelect": false
    },
    {
      "question": "機密管理方式？（API Keys、DB 密碼等）",
      "header": "Secrets 管理",
      "options": [
        { "label": "CI/CD 平台內建 Secrets", "description": "GitHub Secrets / GitLab Variables，適合小型專案" },
        { "label": "AWS SSM Parameter Store", "description": "AWS 原生方案，適合 AWS 生態系" },
        { "label": "HashiCorp Vault", "description": "企業級 Secrets 管理，支援動態 Secrets" },
        { "label": "Doppler", "description": "雲端 Secrets 管理 SaaS，多環境同步" }
      ],
      "multiSelect": false
    },
    {
      "question": "是否有現有的監控/可觀測性工具？",
      "header": "監控工具",
      "options": [
        { "label": "無，需要建議", "description": "尚未設定監控，請推薦適合的方案" },
        { "label": "Datadog", "description": "已使用 Datadog 進行 APM + Logs + Metrics" },
        { "label": "Grafana + Prometheus", "description": "已使用開源監控堆疊" },
        { "label": "AWS CloudWatch / GCP Cloud Monitoring", "description": "使用雲端供應商原生監控" }
      ],
      "multiSelect": false
    }
  ]
})
```

---

## Q3 — Container Registry（條件式：scope ≠ local 且 Q1 選 Docker/K8s）

```json
AskUserQuestion({
  "questions": [{
    "question": "Container Image 要推送到哪個 Registry？",
    "header": "Registry",
    "options": [
      { "label": "GitHub Container Registry (GHCR)", "description": "與 GitHub Actions 整合最佳" },
      { "label": "Docker Hub", "description": "最老牌的 Registry，公開 Image 免費" },
      { "label": "AWS ECR", "description": "AWS 原生，與 ECS/EKS 整合最佳" },
      { "label": "Google Artifact Registry", "description": "GCP 原生，與 GKE 整合最佳" }
    ],
    "multiSelect": false
  }]
})
```
