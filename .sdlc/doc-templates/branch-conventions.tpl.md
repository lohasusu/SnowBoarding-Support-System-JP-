---
document_id: "BRCON-CONVENTIONS-v1.0"
title: "Git 分支慣例規範"
version: "1.0"
date: "{YYYY-MM-DD}"
author: "PM"
status: "Living Document (Layer 2 conventions/)"
phase: "conventions"
locked_at: "{ISO time set by /sdlc:init Step 4.15 — empty / placeholder = unlocked}"
change_history:
  - version: "1.0"
    date: "{YYYY-MM-DD}"
    changes: "init"
    author: "PM"
---

# Git 分支慣例規範（Layer 2 / conventions）

> **用途**: 跨 TASK / 跨 dev 統一 git branch 命名 — 主分支、SDLC TASK 分支、hotfix、release。
>
> **生效時機**: `/sdlc:init` 鎖定後所有 git 操作必須遵守。`sdlc-git-guard.sh` hook 會攔截違規分支建立。
>
> **角色存取**: 全角色唯讀；PM 透過 `/sdlc:start` 自動建立合規分支。

---

## 1. 主分支

| 名稱 | 用途 |
|------|------|
| `main` | 預設受保護分支；merge gate 全綠才能 merge；branch protection rule 啟用 |
| `[CUSTOMIZE: 是否需要 develop？]` | 大型專案有時用 GitFlow 的 `develop` 作 staging 整合層 |

**禁止**: 直接 push 到 `main`（透過 PR + branch protection）

## 2. SDLC TASK 分支（Multi-PR 模型）

格式：`sdlc/{TASK-ID}/{role}`

| role | 用途 | 創建時機 |
|------|------|----------|
| `spec` | BA / SA / UIUX / SD 階段的規格產出 | `/sdlc:start` 自動建 |
| `infra` | Deploy(Init) 階段的 service-contract / Docker / CI | UIUX 與 SD 之間建（與 spec 並行） |
| `fe` | FE 程式碼 | SD approved 後建 |
| `be` | BE 程式碼 | SD approved 後建 |
| `deploy` | Deploy(Execute) 階段的最終 CI/CD | BE/FE 都 approved 後建 |
| `task` | TASK 整合分支（merge spec/infra/fe/be/deploy 進此） | `/sdlc:start` 自動建 |

範例：
```
sdlc/TASK-001/spec
sdlc/TASK-001/infra
sdlc/TASK-001/fe
sdlc/TASK-001/be
sdlc/TASK-001/deploy
sdlc/TASK-001/task    ← 整合 5 個 sub-branch，最終 PR 到 main
```

## 3. Hotfix 分支

格式：`hotfix/{description}`（kebab-case，描述性）

範例：
```
hotfix/login-rate-limit
hotfix/payment-stuck-pending
hotfix/cve-2026-12345
```

直接從 `main` 開分支，修完直接 PR 回 `main`，不走完整 SDLC（緊急修復路徑）。

## 4. Release 分支（若使用 GitFlow）

`[CUSTOMIZE: 啟用此模式才適用]`

格式：`release/v{semver}` 或 `release/{TASK-ID}`

範例：
```
release/v1.2.0
release/v1.2.1-rc1
release/TASK-005    ← 把單一 TASK 包成 release candidate
```

## 5. 命名通則

- 全部 **lowercase kebab-case**
- 禁止字元：空白、中文、`!@#$%^&*()`
- 允許：`a-z`, `0-9`, `-`, `/`
- 長度 ≤ 100 字元（部分 git host 有限制）

## 6. 不允許的分支名稱（git-guard.sh 攔截）

| 違規 | 範例 |
|------|------|
| 大小寫混用 | `Sdlc/TASK-001/FE` |
| 含空白 | `feature my new thing` |
| 含中文 | `feature/使用者登入` |
| 缺 prefix | `task-001` (應為 `sdlc/TASK-001/...`) |
| Prefix 大寫 | `Hotfix/...`, `Release/...` |
| 過長 (>100) | — |

## 7. PR 命名（與分支對應）

PR 標題建議：
- TASK PR: `[TASK-001] {phase}: {description}` （sub-branch PR）
- TASK 整合 PR: `[TASK-001] {task name}` （task 分支 → main）
- Hotfix PR: `[HOTFIX] {description}`
- Release PR: `[RELEASE v{semver}] {description}`

`[CUSTOMIZE: 是否強制此格式？需要 commitlint / PR title bot？]`

## 8. Tag 命名

| 用途 | 格式 |
|------|------|
| Release | `v{semver}`，如 `v1.2.0`, `v1.2.0-rc1` |
| TASK 完成里程碑 | `task/{TASK-ID}` 或 `release/{TASK-ID}` |
| Hotfix | `v{semver}`（patch 版號） |

## 9. RFC 流程

同 db-conventions §7。
