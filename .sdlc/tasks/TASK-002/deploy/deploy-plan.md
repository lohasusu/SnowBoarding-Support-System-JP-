---
document_id: "DEPLOYPLAN-TASK-002-v1.0"
title: "部署規劃書 — SQLite → PostgreSQL 持久化遷移"
version: "1.0"
date: "2026-06-09"
author: "Deployer (Init)"
status: "Draft"
task_id: "TASK-002"
phase: "deploy-init"
source_documents:
  - "SYSARCH-TASK-002-v1.0"
  - "CONTRACT-TASK-002-v1.0 (service-contract.yaml)"
  - "deploy-env.json"
  - "doc-templates/deploy-plan.tpl.md"
approval:
  reviewer: "PM"
  date: ""
  result: "Pending"
---

# 部署規劃書 — TASK-002

> Deploy(Init) 產出。Deploy(Execute) 階段以本規劃書為基礎，產出最終 CI workflow / Dockerfile / Railway 配置。
> scope=full（既有 production，CLAUDE.md 確定）；platform=paas (railway)；cicd=github-actions (既定)。

---

## 1. CI/CD Pipeline 骨架（6 階段）

| 階段 | 目的 | 失敗處理 | 本 TASK 適用 |
|------|------|---------|-------------|
| Build | 編譯產出 artifact（pip install + bytecode）| fail → 停止後續 | ✅ |
| Lint | 靜態檢查（ruff / black --check） | fail → 停止後續 | ✅ |
| Test | 既有 8 個 pytest（AC-045）+ 新 migration up-down test | fail → 停止後續 | ✅ |
| Security Scan | verify-security skill（OWASP / 密鑰 / SAST / 依賴掃描） | Critical > 0 → 永遠阻塞；High > 0 → scope=full 阻塞 | ✅ |
| Stage | 部署 staging 驗證（Railway preview environment / branch deploy） | fail → 自動 rollback | ✅ |
| Deploy | 部署 prod（GitHub Environment `production` 審批 gate） | `environment:production` required reviewers 通過後執行 | ✅ |

### 1.1 本 TASK 特殊驗證階段

- **Migration up-down test**: 任何新 migration 必須能 `upgrade head` → `downgrade -1` → `upgrade head` schema 100% 等價（NFR-006 + PATTERN-101）
- **Env consistency check**: Deploy(Execute) E-1.6 跑 `sdlc-env-consistency.sh` 確認 service-contract.yaml 與程式碼 env var 名稱一致
- **Backup restore drill**: Staging 部署後執行 `migration-strategy.md §2.4` 的 backup → DROP → restore 流程

---

## 2. Path-based CI 觸發設計

從 `service-contract.yaml` 的 `ci_path_filters` 展開：

| 檔案路徑變動 | 觸發 pipeline |
|------------|--------------|
| `web/**` / `flight_search/**` / `*.py` / `requirements.txt` / `http_scraper.py` | BE lint + BE test |
| `migrations/**` / `alembic.ini` (假設) / `scripts/run_migrations.py` | Migration up-down test + DDL validation |
| `docker-compose*.yml` / `Dockerfile*` / `.github/workflows/**` / `railway.toml` / `nixpacks.toml` | Infra validation（compose config / Dockerfile lint） |
| `web/static/**` / `web/templates/**` | Static lint（HTML / JS lint 無 build 步驟 — brownfield 原生 JS） |
| `.sdlc/**` | 不觸發應用 CI（純規格變更） |
| Deploy PR（merge to main） | 完整 integration pipeline + Railway 自動 redeploy |

---

## 3. Multi-PR 分支觸發規則

`config.json.gitStrategy.multiPR.enabled = false` → **單分支模式**（小型專案推薦 GitHub Flow）。

| 分支 | 觸發 |
|------|------|
| `sdlc/TASK-002/sqlite-to-postgres` | CI（lint + test + security scan）；不自動 deploy |
| `sdlc/TASK-002/sqlite-to-postgres` → merge to `main` | Full integration + Railway 自動 redeploy（既有 mechanism） |
| `main` 直接 push（緊急 hotfix）| Same as above；但須 PM approval（Rule 6 跨 TASK 修改協議）|

**Worktree**: PM dispatch prompt 指示 `subBranches.enabled=false → 在主 worktree 工作，無需建 .sdlc-worktrees` — 已遵循。

---

## 4. 環境配置 4 層級分離

| 層級 | 存放位置 | 本 TASK 範例 |
|------|---------|------------|
| Secrets | Railway dashboard env vars（prod）/ `.env` gitignored（dev）/ GitHub Actions Secrets（CI） | `POSTGRES_PASSWORD`, `SECRET_KEY`, `SERPAPI_API_KEY`, `DATABASE_URL` |
| 環境特定配置 | Railway dashboard 不同 environment | `POSTGRES_HOST`, `POSTGRES_SSL_MODE`（dev=disable, prod=verify-full）|
| Feature flags | 無（本 TASK 不引入 flag — BA §1.4 不納入）| — |
| Build-time 常量 | `nixpacks.toml` / `railway.toml`（已存在）；新增 `.env.example`（範本）| Python 版本、entrypoint command |

**規則**: 零機密在程式碼中 / 缺少必要環境變數 = 應用拒絕啟動（FUNC-101 + AC-044 強制）。

---

## 5. 回滾策略骨架

詳細實作見 `migration-strategy.md §3`。摘要：

| 項目 | 值 |
|------|-----|
| 自動回滾觸發 | Railway healthcheck fail > 2 分鐘 → auto rollback to N-1 build |
| 手動回滾觸發 | Smoke test fail / 5xx > 5× baseline / DB connection error > 30 分鐘 → 走 BF-003 |
| 回滾方式 | Railway dashboard → Deployments → Redeploy 前一版（< 3 分鐘）|
| Migration 回滾 | [BLOCKED_ON_SD] Alembic `downgrade -1` / yoyo `rollback -1`（依工具選定）|
| 14 天 emergency path | 保留 database_sqlite.py 於 git history；14 天內可 git revert + 移除 PG env vars 切回 SQLite |
| 前置要求 | Image tag 固定（Railway nixpacks 自動生成 commit SHA tag）/ 保留 ≥ 3 個歷史 deploys / Migration 向後相容 |

---

## 6. 健康檢查設計

本 TASK 範圍內**不新增 healthz endpoint**（SA-SUG-101 留後續 TASK）；使用既有 endpoint：

| Probe | 端點 | 間隔 | 失敗閾值 | 說明 |
|-------|------|------|---------|------|
| Liveness (Railway) | `/api/auth/me` | 30s | 3 次 | 未登入回 401（既有行為），證明 app + DB 都活 |
| Readiness (本機 docker-compose) | `/api/auth/me` | 10s | 5 次 | 同上 |
| Startup | `/api/auth/me` | 10s | 30 次 | 允許 cold start + migration 時間 |

**檢查內容（隱式）**:
- 401 回應 → app + DB 都 OK
- 500 回應 → DB 連線或業務邏輯異常
- Connection refused → app 未啟動

**[DEPLOYER建議]**: 後續 TASK（不在本 TASK）引入 `/healthz` 應用層 endpoint，回 JSON `{"app":"ok","db":"ok","migration":"applied"}`，可區分 app vs DB 健康狀態 — 詳見 SA-SUG-101 + DEPLOYER建議列表。

---

## 追溯矩陣

| 規劃項目 | 依據 |
|---------|------|
| 6 階段 Pipeline | doc-templates/deploy-plan.tpl.md §1 |
| Path filter | service-contract.yaml `ci_path_filters` |
| 分支規則 | config.json `gitStrategy.multiPR.enabled = false` → 單分支 GitHub Flow |
| 環境列表 | deploy-env.json `environments: ["dev", "staging", "prod"]` |
| 回滾指令 | migration-strategy.md §3 + deploy-guide.tpl.md §6.2.D (Railway 部分) |
| Health check endpoint | 既有 /api/auth/me（NFR-002 行為不變） |
| Prod approval | deploy-env.json.prodApproval.required = true（FUNC-107 IRREVERSIBLE 強制）|

---

## [DEPLOYER建議] 後續 deploy 階段優化（不在本 TASK 範圍）

| 建議 | 理由 | 優先 |
|------|------|------|
| 引入 `/healthz` endpoint 區分 app / DB 健康 | SA-SUG-101；改善監控精度 | P2 |
| 引入 Sentry error tracking | 免費 5k events/月；production 上線後優先 | P1 |
| 引入 UptimeRobot 外部 uptime 監控 | Free tier；補強 Railway healthcheck 盲點 | P1 |
| Migration log 結構化（JSON）| SA-SUG-104；配合 SLA dashboard | P3 |
| Buildx multi-arch 推 ghcr.io | config.json 已規劃；Railway 用 nixpacks 暫無需要 | P3 |
| GitHub Environment `production` reviewers 設定 | Rule 11 + FUNC-107 IRREVERSIBLE 強制 | **P0（本 TASK Execute 階段必須完成）**|
