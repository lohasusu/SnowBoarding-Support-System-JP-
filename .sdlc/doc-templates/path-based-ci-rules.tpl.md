# Path-based CI + Multi-PR 觸發規則 — 單一真相來源

> 所有 Path-based CI 設計與 Multi-PR → CI Job 對應表集中於此。Deploy(Init) 的 deploy-plan.md §2/§3 以及 Deploy(Execute) 的 cicd-spec.md 都**引用本檔**，禁止在 agent prompt 或其他產出中重複撰寫。

## 1. 六階段 CI Pipeline

```
Build → Lint → Test → Security Scan → Stage → Deploy
```

各階段失敗處理:

| 階段 | 失敗行為 | 重試 | 通知 |
|------|---------|------|------|
| Build | 停止 | 否 | 作者 + 團隊 |
| Lint | 停止 | 否 | 作者 |
| Test | 停止 | 1 次（記錄 flaky） | 作者 + 測試擁有者 |
| Security | Critical 永遠停止；High 在 scope=staging/full 停止 | 否 | 安全團隊 + 作者 |
| Stage | 停止 | 1 次 | DevOps + 作者 |
| Deploy | 停止 + 自動回滾 | 否 | 全團隊 |

## 2. Path-based 觸發骨架（展開自 service-contract.yaml `ci_path_filters`）

| 檔案路徑變動 | 觸發 pipeline |
|------------|--------------|
| `frontend/**` / `src/frontend/**` / `client/**` | FE lint + FE test + FE build |
| `backend/**` / `src/backend/**` / `server/**` / `api/**` | BE lint + BE test + BE build |
| `docker-compose*.yml` / `Dockerfile*` / `.github/**` / `nginx*` / `k8s/**` | Docker build + compose validate |
| `package.json` / `*.lock` / `tsconfig*.json` | FE + BE 完整 pipeline |
| `.sdlc/**` | 不觸發應用 CI（純文件） |

## 3. Multi-PR → CI Job 對應

| PR 來源分支 | 觸發的 CI Job | 部署環境 |
|-----------|-------------|---------|
| `{prefix}/{TASK}/spec` → main | 無（純文件 PR） | 不部署 |
| `{prefix}/{TASK}/infra` → main | `validate:infra`（Docker build 驗證 + compose config） | 不部署 |
| `{prefix}/{TASK}/fe` → main | `fe-pipeline`（lint + test + build） | 不部署 |
| `{prefix}/{TASK}/be` → main | `be-pipeline`（lint + test + build） | 不部署 |
| `{prefix}/{TASK}/deploy` → main | `integration`（完整 pipeline） | staging |
| Release tag `v*` → main | 完整 pipeline + prod deploy | prod（需審批） |

## 4. 實作語法對照（依 CI/CD 平台）

| 平台 | Path filter 實作 | 範例 |
|------|-----------------|------|
| GitHub Actions | `dorny/paths-filter@v3` action，或 `on.pull_request.paths` / `on.push.paths` | 見下方 4.1 |
| GitLab CI | `rules: changes:` 陣列 | 見下方 4.2 |
| Jenkins | `changeset('**/*.ext')` pipeline directive | 見下方 4.3 |

### 4.1 GitHub Actions 骨架

```yaml
on:
  pull_request:
    branches: [main]

jobs:
  detect-changes:
    runs-on: ubuntu-latest
    outputs:
      fe: ${{ steps.filter.outputs.fe }}
      be: ${{ steps.filter.outputs.be }}
      infra: ${{ steps.filter.outputs.infra }}
    steps:
      - uses: actions/checkout@v4
      - uses: dorny/paths-filter@v3
        id: filter
        with:
          filters: |
            fe:
              - 'frontend/**'
              - 'src/frontend/**'
              - 'client/**'
            be:
              - 'backend/**'
              - 'src/backend/**'
              - 'server/**'
              - 'api/**'
            infra:
              - 'docker-compose*.yml'
              - 'Dockerfile*'
              - '.github/**'
              - 'k8s/**'

  fe-pipeline:
    needs: detect-changes
    if: needs.detect-changes.outputs.fe == 'true'
    # lint:fe + test:fe + build:fe

  be-pipeline:
    needs: detect-changes
    if: needs.detect-changes.outputs.be == 'true'
    # lint:be + test:be + build:be

  integration:
    # deploy PR 或 release tag 觸發
    if: startsWith(github.head_ref, 'sdlc/') && endsWith(github.head_ref, '/deploy') || startsWith(github.ref, 'refs/tags/v')
    needs: [fe-pipeline, be-pipeline]
    # security-scan + docker-build + integration-test + deploy
```

### 4.2 GitLab CI 骨架

```yaml
fe-pipeline:
  rules:
    - changes:
        - frontend/**/*
        - src/frontend/**/*
        - client/**/*
  script: [lint:fe, test:fe, build:fe]

be-pipeline:
  rules:
    - changes:
        - backend/**/*
        - src/backend/**/*
        - server/**/*
        - api/**/*
  script: [lint:be, test:be, build:be]

deploy-prod:
  when: manual
  environment: production
  allow_failure: false
  rules:
    - if: $CI_COMMIT_TAG =~ /^v/
```

### 4.3 Jenkins 骨架

```groovy
pipeline {
  agent any
  stages {
    stage('FE Pipeline') {
      when { changeset pattern: 'frontend/**' }
      steps { sh 'npm run lint:fe && npm test -- --projects=fe && npm run build:fe' }
    }
    stage('BE Pipeline') {
      when { changeset pattern: 'backend/**' }
      steps { sh 'npm run lint:be && npm test -- --projects=be && npm run build:be' }
    }
    stage('Deploy Prod') {
      when { tag 'v*' }
      input message: 'Deploy to production?'
      environment name: 'production'
      // deploy step
    }
  }
}
```

## 5. Prod Deploy 審批 Gate（scope=full 必要）

| 平台 | 審批機制 |
|------|---------|
| GitHub Actions | `environment: { name: production, url: ... }` + repo 設 Required reviewers |
| GitLab CI | `when: manual` + `environment: production` + Protected environment reviewers |
| Jenkins | `input` directive 要求使用者點選 |

詳細設定見 `doc-templates/full-required.tpl.md`。
