---
document_id: "CICD-TRIGGER-MATRIX-v1.0"
title: "CI/CD 觸發矩陣"
version: "1.0"
date: "{YYYY-MM-DD}"
author: "PM"
status: "Living Document (Layer 2 conventions/)"
phase: "conventions"
locked_at: "{ISO time set by /sdlc:init Step 4.15 — empty / placeholder = unlocked}"
change_history:
  - version: "1.0"
    date: "{YYYY-MM-DD}"
    changes: "PR 12: 初次建立 — 10 觸發事件 × 5 workflow × 7 種 gate 對照表"
    author: "PM"
---

# CI/CD 觸發矩陣（Trigger Matrix）

> **PR 12 引入 — Layer 2 / conventions** — 集中管理「git/PR 事件 → 觸發哪個 workflow → 跑哪些 gate → 是否阻塞 merge」。
> 此檔為 SDLC 模板，install 後複製到 `.sdlc/conventions/cicd-trigger-matrix.md`。
> 本檔為**可閱讀的觸發真相來源**；GitHub Actions tpl 中的 `on:` 區塊應與此表 1:1 對齊。
>
> **Conventions Lock（Rule 16）**: `locked_at` 寫入後必須走 RFC 流程才能變更（提案 → PM + 至少一位 deploy/CI 角色 review → 更新 change_history → bump version）。

---

## 1. 觸發事件對照表

| # | 事件 | workflow | gate 等級 | 阻塞 merge | 主要驗證項 |
|---|------|---------|----------|----------|-----------|
| 1 | feature branch push | `sdlc-ci-pr.yml` | fail-open | ❌ | id-guard / sync --check / parameter-check |
| 2 | PR opened | `sdlc-ci-pr.yml` + `sdlc-cross-task-check.yml` | fail-open | ❌ | 同上 + 跨 TASK 衝突偵測 |
| 3 | PR synchronize | 同 #2 | fail-open | ❌ | 同上（每次 push 重跑） |
| 4 | PR labeled `hotfix` | `sdlc-ci-pr.yml`（縮減版）| fail-open | ❌ | 跳過部分 gate（見 §3.6） |
| 5 | merge_group | `sdlc-merge-gate.yml` | **STRICT** | ✅ | 全部 strict（id-guard / sync --strict / parameter / shared-rebuild --check） |
| 6 | push to main | `sdlc-post-merge.yml` | — | — | shared/ rebuild + auto-commit |
| 7 | tag push `release/*` | `sdlc-deploy-staging.yml`（PR 12 stub） | manual review | ✅ | build + 資安 + smoke + 推 staging |
| 8 | tag push `prod-*` | `sdlc-deploy-prod.yml`（PR 13 stub）| manual approval | ✅ | 同 #7 + manual approval gate |
| 9 | schedule（30 min cron）| `sdlc-ci-integration.yml` | warn-only | ❌ | 兩兩 PR 預合併試錯 |
| 10 | workflow_dispatch | 任一 workflow（手動觸發） | 同對應 workflow | — | 同對應 workflow |

---

## 2. workflow 與 gate 對應表

| workflow | id-guard | sync --check | parameter-check | pencil-sync --check | shared-rebuild --check | smoke-test | 資安掃描 |
|---------|----------|--------------|-----------------|--------------------|-----------------------|-----------|---------|
| `sdlc-ci-pr` | ✅ warn | ✅ warn | ✅ warn | ✅ warn | ✅ warn | — | — |
| `sdlc-merge-gate` | ✅ **STRICT** | ✅ **STRICT** | ✅ **STRICT** | ✅ **STRICT** | ✅ **STRICT** | — | — |
| `sdlc-post-merge` | — | — | — | — | rebuild + commit | — | — |
| `sdlc-cross-task-check` | — | — | — | — | — | — | — |
| `sdlc-ci-integration` | ✅ warn | ✅ warn | ✅ warn | ✅ warn | — | — | — |
| `sdlc-deploy-staging` | — | — | — | — | — | ✅ | ✅ Critical 阻塞 |
| `sdlc-deploy-prod` | — | — | — | — | — | ✅ | ✅ Critical+High 阻塞 |

---

## 3. 觸發決策樹（人類判讀）

### 3.1 平日開發（feature branch push）

```
push feature branch
    ↓
sdlc-ci-pr 跑 → fail-open warning（不阻塞）
    ↓
如果有 warning → dev 自行決定是否修復
    ↓
push 更多 commits → 自動再跑（synchronize）
```

### 3.2 PR 開啟

```
gh pr create
    ↓
sdlc-ci-pr + sdlc-cross-task-check 同時跑
    ↓
跨 TASK 衝突？
    ├─ YES → bot 在 PR 留言（可選協調）
    └─ NO  → 繼續
    ↓
進入 review
```

### 3.3 進入 merge queue

```
PR approved → 排入 merge queue
    ↓
sdlc-merge-gate STRICT 跑
    ↓
任一 gate 失敗？
    ├─ YES → 從 queue 退出，PR 標 conflict
    └─ NO  → merge → 觸發 sdlc-post-merge
```

### 3.4 Merge 後

```
push to main 完成
    ↓
sdlc-post-merge 跑
    ↓
sdlc-shared-rebuild 從 journal 重建 shared/
    ↓
若有變更 → auto-commit "chore(shared): rebuild from journals"
    ↓
通知 open PRs 需 rebase（可選）
```

### 3.5 部署 staging（tag `release/*`）

```
git tag release/TASK-001 && git push --tags
    ↓
sdlc-deploy-staging 跑
    ↓
build & push image
    ↓
跑資安掃描（OWASP / 依賴 / 密鑰）
    ↓
Critical 漏洞？
    ├─ YES → 阻塞 + 通知
    └─ NO  → 部署到 staging
    ↓
sdlc-deploy-smoke-test 跑（curl health/critical paths）
    ↓
失敗 → auto-rollback (前一版 image)
成功 → 繼續監控 5 分鐘
```

### 3.6 Hotfix（PR 標 `hotfix` label）

```
PR 標 hotfix label
    ↓
sdlc-ci-pr 跑（縮減 gate）
    ↓
跳過: parameter-check（避免阻塞緊急修復）
保留: id-guard / sync / 資安
    ↓
sdlc-merge-gate 仍 STRICT（merge 不放水）
```

---

## 4. 與 GitHub Actions 同步

每次修改本表時，必須**同步**:

| 本表內容 | 對應 workflow 檔案 | 區塊 |
|---------|-------------------|-----|
| 事件 #1-#4 | `.github/workflows/sdlc-ci-pr.yml` | `on:` |
| 事件 #5 | `.github/workflows/sdlc-merge-gate.yml` | `on: merge_group:` |
| 事件 #6 | `.github/workflows/sdlc-post-merge.yml` | `on: push: branches: [main]` |
| 事件 #7 | `.github/workflows/sdlc-deploy-staging.yml`（PR 12 stub） | `on: push: tags: ['release/*']` |
| 事件 #8 | `.github/workflows/sdlc-deploy-prod.yml`（PR 13） | `on: push: tags: ['prod-*']` |
| 事件 #9 | `.github/workflows/sdlc-ci-integration.yml` | `on: schedule:` |
| 事件 #10 | 任一 workflow | `on: workflow_dispatch:` |

**驗證腳本**: `bash scripts/sdlc-trigger-matrix-check.sh`（PR 12 — 比對本表與 workflow 檔案 `on:` 區塊一致性）

---

## 5. 失敗時的 fallback

- 若觸發矩陣與實際 workflow 不一致 → `sdlc-trigger-matrix-check.sh` 退出碼 1，CI 標 Warning
- 若 dev 在沒有 GitHub Actions 的環境（GitLab / Jenkins / 純本地）→ 本表仍可作為人類執行流程的指南；CI 自動化部分自行對應
- 若 hotfix 標籤誤標 → merge-gate 仍 STRICT 把關，避免錯誤縮減擴散

---

## 6. 變更記錄

| 日期 | 變更 | PR |
|------|------|-----|
| {YYYY-MM-DD} | 初次建立（10 個事件 / 7 個 workflow / 7 種 gate） | PR 12 |
