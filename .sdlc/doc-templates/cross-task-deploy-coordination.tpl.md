# Cross-TASK Deployment Coordination Guide (PR 18)

> 此檔指引多個並行 TASK 在 deploy 階段如何協調，避免衝突 / race condition / partial-deploy。
> 與 Rule 13 (ID Allocator) / Rule 14 (Journal) / Rule 18 (Parameter Registry) / Rule 19 (CI Gate) 整合。
> Install 後複製到 `.sdlc/doc-templates/cross-task-deploy-coordination.md` 作為專案級客製基線。

## ⚠️ Status: DOCS-ONLY (PR 18)

**本 PR 是純文件**，不修改現有 commands / scripts / agents。

- ✅ **PR 18 範圍**: 補完 multi-TASK 並行部署協調文件 + JSON schema
- ❌ **PR 18 不涵蓋**: 自動 wire-up（PR 18.1+ 後續處理）
- 🔄 **目前部署行為**: 各 TASK 獨立部署，無中央協調機制

## 1. 為什麼需要協調

### 1.1 並行 TASK 的衝突場景

當多個 TASK 並行進入 deploy 階段，會出現：

| 衝突類型 | 場景 | 影響 |
|---------|------|------|
| **DB migration 衝突** | TASK-A 加 column X，TASK-B 加 column X（cross-TASK 撞名）| migration 失敗，後到 deploy 卡住 |
| **Shared parameter race** | TASK-A 改 `MAX_CART_ITEMS=10`，TASK-B 改 `MAX_CART_ITEMS=20` | last-write-wins，可能違反業務邏輯 |
| **Service contract drift** | TASK-A FE 期待 API-101 v1，TASK-B BE 已升級 API-101 v2 | runtime breakage |
| **Deploy order dependency** | TASK-A 新 feature 依賴 TASK-B 的 infra | TASK-A 先 deploy → infra 缺，crash |
| **Rollback cascade** | TASK-A rollback 但 TASK-B 已部署於其上 | 一起 rollback 還是只 rollback A？ |
| **Resource quota exhaustion** | 同時 deploy 5 個 TASK 的 image，registry quota / cluster CPU 用盡 | partial deploy |

### 1.2 黃金規則

> **每個 deploy 必須知道自己上面有什麼下面有什麼** — 不要假設「main 是乾淨的」。

## 2. 協調機制 schema (`.sdlc/deploy-coordination.json`)

```json
{
  "_comment": "Cross-TASK deploy 協調狀態 — 全域單一檔案，由 sdlc-state.sh add-deployment 子命令維護",
  "_invariants": [
    "V2.C4: dependencies field DERIVES from state.json.tasks[ID].git.dependsOn (canonical SoT). PR 18.1 sync helper required.",
    "V2.C5: bidirectional invariant — if A.dependents contains B, then B.dependencies must contain A. PR 18.1 validator required.",
    "V2.C6: migrations.phase MUST be one of expand|backfill|contract (Rule 11 three-phase). expand-only schema is incomplete."
  ],
  "schemaVersion": "deploy-coord-v1",

  "activeDeployments": [
    {
      "taskId": "TASK-001",
      "version": "v1.5.0",
      "environment": "staging",
      "deployedAt": "2026-05-07T10:00:00Z",
      "deployedBy": "alice",
      "status": "monitoring",
      "monitorUntil": "2026-05-08T10:00:00Z",
      "dependencies": [],
      "dependents": ["TASK-002"],
      "migrations": [
        {"id": "20260507_add_column_X", "phase": "expand", "rollbackable": true},
        {"id": "20260507_backfill_column_X", "phase": "backfill", "rollbackable": true},
        {"id": "20260514_drop_old_column", "phase": "contract", "rollbackable": false, "_dependsOn": "20260507_backfill_column_X"}
      ],
      "sharedParametersChanged": [
        {"paramName": "MAX_CART_ITEMS", "from": "5", "to": "10", "registeredAt": "2026-05-07T09:55:00Z"}
      ]
    },
    {
      "taskId": "TASK-002",
      "version": "v1.5.1-pending",
      "environment": "dev",
      "deployedAt": "2026-05-07T11:00:00Z",
      "deployedBy": "bob",
      "status": "pending",
      "dependencies": ["TASK-001"],
      "dependents": [],
      "migrations": [],
      "sharedParametersChanged": []
    }
  ],

  "deployQueue": [
    {
      "taskId": "TASK-003",
      "blockedBy": "TASK-001",
      "blockReason": "depends on TASK-001 staging soak",
      "queuedAt": "2026-05-07T11:30:00Z"
    }
  ],

  "history": [
    {
      "taskId": "TASK-000",
      "version": "v1.4.0",
      "environment": "prod",
      "deployedAt": "2026-05-01T00:00:00Z",
      "completedAt": "2026-05-01T00:15:00Z",
      "outcome": "success",
      "rollbackedAt": null
    }
  ]
}
```

> **儲存位置**: `.sdlc/deploy-coordination.json`（project-level，與 `state.json` 同層）。
> **Rule 15 §15.8 候選**: 高頻寫入（每 deploy 都動）但跨 TASK 聚合查詢 → 候選白名單，待後續 PR 評估。

## 3. 協調規則

### 3.1 Pre-Deploy Check（每個 deploy 啟動前）

> ### ⚠️ 以下為 **PSEUDOCODE**（PR 18 V1+V2 fix）
>
> PR 18 是 DOCS-ONLY，下列 bash 範例**僅作為 PR 18.1 實作參考**，不可直接執行：
>
> - **PR 24 已實作**: `scripts/sdlc-deploy-precheck.sh`（取代下方 PSEUDOCODE — 6 個 check + --override + audit chain）。下方 bash 範例保留為「設計參考」，實際使用 `bash scripts/sdlc-deploy-precheck.sh $TASK_ID $TARGET_ENV [--override "reason"]`。
> - `scripts/sdlc-journal-read.sh` 仍未存在（PR 18.1 改用 sdlc-deploy-precheck.sh 不需要 journal-read）
> - `migration_added` 不是 sdlc-journal-write.sh 的 ALLOWED_TYPES（需 PR 18.1 擴充 + 新增 `scripts/sdlc-migration-list.sh` 從 TASK 目錄掃 migration）
> - dependencies 應從 `state.json.tasks[ID].git.dependsOn`（PM agent Step 0.6 已用）取得，**不是**從 deploy-coordination.json 自查
> - `sharedParametersChanged` 結構需與 Rule 18 parameter registry schema 對齊（V2.C3 fix 待 PR 18.1 處理）

```bash
# PSEUDOCODE — 由 PR 18.1 實作
# 命令: bash scripts/sdlc-deploy-precheck.sh $TASK_ID $TARGET_ENV
TASK_ID=$1
TARGET_ENV=$2  # dev | staging | prod

# 1. 從 state.json 讀本 TASK 的 dependsOn（V1.W1 fix: 不從 activeDeployments 自查）
DEPS=$(jq -r ".tasks[\"$TASK_ID\"].git.dependsOn[]?" .sdlc/state.json)
for dep in $DEPS; do
    DEP_STATUS=$(jq -r ".activeDeployments[] | select(.taskId==\"$dep\" and .environment==\"$TARGET_ENV\") | .status // \"missing\"" .sdlc/deploy-coordination.json)
    if [ "$DEP_STATUS" = "missing" ]; then
        echo "❌ Dependency $dep 尚未 deploy 到 $TARGET_ENV，本 deploy 阻擋"
        exit 1
    fi
    # V1.C3 fix: 對齊 _supportedStatuses 的 "rolled-back"（不是 "rollbacked"）
    if [ "$DEP_STATUS" = "rolled-back" ]; then
        echo "❌ Dependency $dep 已 rolled-back，本 deploy 阻擋（需先處理 dependency）"
        exit 1
    fi
done

# 2. 檢查 shared parameters 衝突（V2.C3: 須對齊 Rule 18 parameter registry，PR 18.1 處理）
# 跨 TASK parameter 衝突偵測由 sdlc-parameter-check.sh 提供（Rule 18 既有機制）
bash scripts/sdlc-parameter-check.sh --task "$TASK_ID" --against-active-deployments

# 3. 檢查 DB migration 衝突（V1.C2: migration_added 非 journal type，改掃 migration 目錄）
# PR 18.1 將加入 sdlc-migration-list.sh，目前手動 ls migrations/
TASK_MIGRATIONS=$(ls .sdlc/tasks/$TASK_ID/migrations/*.sql 2>/dev/null | xargs -n1 basename)
# V1.W2 fix: 對齊 $TARGET_ENV，不是硬編碼 staging
ACTIVE_MIGRATIONS=$(jq -r ".activeDeployments[] | select(.environment==\"$TARGET_ENV\") | .migrations[].id" .sdlc/deploy-coordination.json)
for m in $TASK_MIGRATIONS; do
    if echo "$ACTIVE_MIGRATIONS" | grep -qxF "$m"; then
        echo "❌ Migration $m 已被其他 TASK 套用，本 deploy 阻擋（撞名）"
        exit 1
    fi
done

# 4. 通過所有檢查 → 可以 deploy
echo "✅ Pre-deploy checks passed for $TASK_ID → $TARGET_ENV"
```

### 3.2 Post-Deploy Update（deploy 完成後）

```bash
# 寫入 .sdlc/deploy-coordination.json activeDeployments
bash scripts/sdlc-state.sh add-deployment "$TASK_ID" "$VERSION" "$TARGET_ENV" "$STATUS"
# 預期將在 PR 18.2 加入 add-deployment 子命令
```

### 3.3 Rollback Cascade Rules

當 TASK-A rollback 時，依賴關係處理：

```
TASK-A rollback 觸發
    ↓
讀取 TASK-A.dependents
    ↓
（V2.W3 fix: DAG 驗證 — 若 dependents 存在 cycle (A→B→A)，立即 abort 並標 [ROLLBACK_CYCLE]）
（V2.W4 fix: 過濾 abandoned TASK — 讀 .sdlc/.abandoned-tasks.txt，從 dependents 中移除）
（V2.C5 fix: 驗證 bidirectional invariant — 若 B.dependents 含 A，A.dependencies 必須含 B）
    ↓
若 dependents 為空（過濾後）→ 只 rollback A
若有 dependents → 依次序：
     1. 通知所有 dependents owners
     2. 評估每個 dependent 是否需 cascade rollback:
        - dependent 用了 A 新增的 API/feature → MUST cascade rollback
        - dependent 與 A 同層獨立 → 不需 cascade
        - dependent 修改了 A 的 shared parameter → 需協調（depends on conflict）
     3. 從最深層 dependent 開始 rollback（reverse topological order）
     4. 最後 rollback A
```

> **黃金規則**: rollback 順序與 deploy 順序相反（依賴最深的先 rollback）。

### 3.4 Edge Case Handling（PR 18 V2 verifier 補完）

#### 3.4.1 Cycle 偵測（V2.W3）

```bash
# PSEUDOCODE — PR 18.5 cascade walker 實作
detect_dependency_cycle() {
    local start_task=$1
    local visited=()

    walk() {
        local task=$1
        # 在 visited stack 中找到自己 → 偵測到 cycle
        for v in "${visited[@]}"; do
            [ "$v" = "$task" ] && { echo "CYCLE: ${visited[*]} → $task"; return 1; }
        done
        visited+=("$task")
        local deps=$(jq -r ".tasks[\"$task\"].git.dependsOn[]?" .sdlc/state.json)
        for d in $deps; do walk "$d" || return 1; done
        unset 'visited[-1]'
    }
    walk "$start_task"
}
```

#### 3.4.2 Stale TASK-ID 過濾（V2.W4）

```bash
# PSEUDOCODE — Rule 10 abandoned filter
ABANDONED=$(cat .sdlc/.abandoned-tasks.txt 2>/dev/null || echo "")
ACTIVE_DEPENDENTS=$(jq -r ".activeDeployments[] | select(.taskId==\"$TASK_ID\") | .dependents[]" .sdlc/deploy-coordination.json | \
    while read -r dep; do
        echo "$ABANDONED" | grep -qxF "$dep" || echo "$dep"
    done)
```

#### 3.4.3 HOTFIX-NNN 命名空間（V2.W5）

- `taskId` 欄位允許 `HOTFIX-NNN` 與 `TASK-NNN` 兩種格式
- Hotfix-during-active-deploy 場景:
  - 若 hotfix 與 active TASK 修改同檔案 → 加 entry 到 deployQueue + blockReason="conflict-with-active-task-X"
  - 否則 hotfix 走 fast-path（hotfix-runbook.tpl.md §1）跳 queue
- Hotfix `dependents` 永為 `[]`（hotfix 不應有下游 — 它是 emergency fix）

#### 3.4.4 Manual override / Emergency cancel（V2.W6）

```bash
# 手動忽略 pre-deploy check（emergency 情境）
bash scripts/sdlc-deploy-precheck.sh "$TASK_ID" "$TARGET_ENV" --override "EMERGENCY: $REASON"
# audit.log 強制紀錄: deploy_precheck_overridden | by=$USER reason="..."

# Emergency cancel queued deploy
bash scripts/sdlc-state.sh dequeue-deploy "$TASK_ID" "manual-cancel"
# audit.log: deploy_dequeued | reason=manual-cancel by=$USER
```

> **授權**: `--override` 與 `dequeue` 應限縮至 PM agent / SRE on-call；GitHub PR review 補件強制（即 emergency override 完仍需 24h 內補完整流程）。

## 4. Deploy Queue 機制

### 4.1 何時排隊

| 場景 | 動作 |
|------|------|
| Dependency 尚未 deploy | 加入 queue，blockedBy=dep |
| Shared parameter 衝突 | 加入 queue，blockedBy=other-active-task |
| Resource quota 不足 | 加入 queue，blockedBy="resource:cpu/memory/registry" |
| Maintenance window 不在範圍 | 加入 queue，blockedBy="window:next-Sun-02:00" |

### 4.2 Queue 處理

```bash
# 由 PM agent 在 /sdlc:next deploy 階段執行
QUEUE=$(jq -c '.deployQueue[]' .sdlc/deploy-coordination.json)
for task in $QUEUE; do
    BLOCK_REASON=$(echo "$task" | jq -r '.blockReason')
    BLOCKED_BY=$(echo "$task" | jq -r '.blockedBy')

    # 重新檢查 blocker 是否已解除
    if [ "$BLOCK_REASON" = "depends on dependency" ]; then
        DEP_STATUS=$(jq -r ".activeDeployments[] | select(.taskId==\"$BLOCKED_BY\") | .status" .sdlc/deploy-coordination.json)
        if [ "$DEP_STATUS" = "monitoring" ] || [ "$DEP_STATUS" = "completed" ]; then
            echo "✅ $BLOCKED_BY 已就緒，解除 $TASK_ID queue 阻擋"
            # 移除 queue entry，trigger deploy
        fi
    fi
done
```

### 4.3 Queue 通知

PM agent 應每次 `/sdlc:status` 顯示 queue 狀態：

```
### 🚧 Deploy Queue（PR 18）

  ⏳ TASK-003 — blocked by TASK-001 (staging soak in progress, 18h remaining)
  ⏳ TASK-005 — blocked by resource:registry-quota (will retry in 30min)
```

## 5. 衝突解決矩陣

> **PR 18 V2.W7 註記**: 下表「自動」標記表示 PR 18.1+ 完成後的目標狀態，
> 目前 (DOCS-ONLY) 全部仍是人工執行。

| 衝突 | 目標自動解決（PR 18.x 後）| 目前人工介入 |
|------|---------------------------|---------------|
| Migration ID 撞名 | PR 18.1 pre-deploy check 阻擋 | Rule 6 cross-TASK 協議：標 `[CROSS-TASK]` 由 SA 重新設計 |
| Shared parameter race | PR 18.1 整合 sdlc-parameter-check.sh | Rule 18 parameter registry 協議 |
| API version drift | PR 18.4 CI Gate FE/BE 驗證 | /sdlc:rebase 同步上下游 |
| Deploy order dependency | PR 18.1+18.5 deployQueue 自動排序 | PM agent /sdlc:next 手動依序派發 |
| Rollback cascade | PR 18.5 反向 walker | owner 評估 + 手動執行 |
| Resource quota | PR 18.5 queue + retry（max=3）| 連續 3 次 retry fail → 通知 SRE |

### 5.1 Max-Retry 政策（V2.W2 fix）

```
retry < 3                 → 自動 retry，退避 30 分鐘
retry == 3                → 升級為 BLOCKED + 通知 SRE on-call
queued > 24 小時未解除    → 自動移到 deployQueue.history + 標 [STARVED]
                            owner 必須 manual override 或 abandon TASK
```

## 6. 與其他 Rule / PR 的整合（V1.W3 fix: 補完 PR 14/16/17 cross-refs）

### 6.1 Rule 整合

- **Rule 6（跨 TASK 修改協議）**: 跨 TASK migration / parameter 修改必須走標記 + 審核流程
- **Rule 10（Abandoned TASKs）**: cascade walker 必須過濾 abandoned dependents（V2.W4 fix）
- **Rule 11（不可逆操作）**: migrations.phase 必為 expand|backfill|contract 三階段（V2.C6 fix）
- **Rule 13（ID Allocator）**: API/TBL ID 預分配避免撞名（已解 migration 大多數衝突）
- **Rule 14（Journal）**: cross-TASK 衝突偵測由 journal aggregation 提供（migration / parameter 變動都寫 journal）
- **Rule 15 §15.8**: deploy-coordination.json 候選白名單（待 PR 18+ 評估）
- **Rule 18（Parameter Registry）**: shared parameter 衝突的單一 SoT；PR 18 schema 對齊（V2.C3 fix）
- **Rule 19（CI Gate）**: GitHub Actions 在 PR merge 前跑 cross-TASK 檢查（PR 18.4 加入）
- **Rule 20.2（Browser Verify）**: cross-TASK deploy 後 verify 不止本 TASK，還要看 dependents

### 6.2 PR 整合（與 hotfix / rollback / multi-env 配合）

- **PR 14 hotfix-runbook.tpl.md**: hotfix 流程獨立於本 PR 的 queue（hotfix-runbook §1 fast-path），但 hotfix 部署仍寫 deploy-coordination.json activeDeployments（taskId="HOTFIX-NNN"，V2.W5 fix）
- **PR 16 rollback-runbook.tpl.md**: rollback 失敗時走 rollback-runbook §3-4；本 PR §3.3 cascade 邏輯 + rollback-runbook §3 具體命令互補
- **PR 17 multi-env-deployment.tpl.md**: PR 17 縱向（dev→staging→prod 各 env soak）+ PR 18 橫向（同 env 多 TASK 並行）正交。pre-deploy check 同時讀 environments.json (PR 17) 與 deploy-coordination.json (PR 18)

## 7. Anti-Patterns

❌ **不要做**:
- 假設 main 是乾淨的（main 可能有其他 TASK 部分 deploy 中）
- 跳過 pre-deploy check 直接 deploy（race condition 機率 > 0%）
- 不通知 dependents 直接 rollback（cascade 失序）
- 用 cron 自動 retry 阻塞的 deploy（應由 PM 人工檢查 blocker 已解）
- 把 deploy-coordination.json commit 到 git（這是 runtime state，不是 source code — 加到 .gitignore）

✅ **應該做**:
- 每個 deploy 前跑 §3.1 pre-deploy check
- 寫 deploy 時標清 dependencies / dependents
- Rollback 前通知所有 dependents
- Queue 觀察期到了還沒解除 → escalate to PM

## 8. 補件 / 改善 TODO

- [ ] PR 18.1: `commands/deploy.md` 加入 §3.1 pre-deploy check 步驟
- [ ] PR 18.2: `scripts/sdlc-state.sh add-deployment` / `rollback-deployment` helpers
- [ ] PR 18.3: PM agent §5.4 status report 加 deploy queue 顯示
- [ ] PR 18.4: GitHub Action workflow 跑 cross-TASK check（merge to main 前阻擋）
- [ ] PR 18.5: rollback cascade 自動化（讀 dependents → 反向 rollback）
- [ ] PR 18.6: `.gitignore` 自動加入 `.sdlc/deploy-coordination.json`
