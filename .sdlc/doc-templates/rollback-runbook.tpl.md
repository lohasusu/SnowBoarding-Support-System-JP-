# Rollback Runbook (PR 16)

> 此檔由 `/sdlc:hotfix` 命令在執行 Step 6（Deploy + Monitor）失敗時讀取作為決策依據。
> Install 後複製到 `.sdlc/doc-templates/rollback-runbook.md` 作為專案級客製基線。
> 與 `hotfix-runbook.tpl.md` 互補：hotfix 處理「修」，rollback 處理「沒修好怎麼回去」。

## 1. 何時觸發 Rollback

> **黃金規則**: 觀察期（5-15 分鐘）內任一指標惡化就 rollback，不要等。
> "Try to fix forward" 在 prod 是反模式 — 先回到已知良好狀態，事後再診斷。

### 1.1 自動觸發條件（CI/監控應自動 rollback）

| 觸發指標 | 閾值 | Rollback 類型 |
|---------|------|--------------|
| HTTP 5xx error rate | > 1% (P0) / > 0.5% (P1 critical endpoint) | Immediate |
| Latency P95 | > 2× 24h baseline 持續 5 分鐘 | Immediate |
| Smoke test fail | 任一 endpoint fail | Immediate |
| Critical alert（PagerDuty/Sentry）| 任一觸發 | Immediate |
| Database migration error | migration 失敗 / lock timeout | Immediate（含 DB rollback）|

### 1.2 手動觸發條件（人為判斷）

| 場景 | 判定 |
|------|------|
| 業務指標下降（轉換率、交易量）| > 10% 偏離正常 → rollback |
| Customer complaints 集中 | 同類抱怨 ≥ 3 → rollback 並調查 |
| Security 異常（auth 失敗暴增、suspicious traffic）| 任一 → rollback + 通知 security |
| 「感覺怪」（intuition）但無明確指標 | 紀錄到 audit.log，繼續觀察 5 分鐘，仍怪 → rollback |

### 1.3 不應 rollback 的情況

- ✅ 觀察期內**所有**指標正常 → 維持，繼續觀察至 15 分鐘
- ✅ 已知的 `[expected change]` 指標變動（如 hotfix 本來就會降低 latency）→ 維持
- ❌ 「明天再看」/「下班前不要動」→ **錯誤**，prod issue 不等下班

## 2. Rollback 決策樹

```
Production deploy 完成後監控發現異常
    ↓
部署模式確認:
    - Canary / 漸進式（10% / 50%）→ Branch D（Canary Rollback，最便宜）
    - 全量部署 → 看影響面

影響面確認:
    - 全使用者中斷 → P0 Immediate Rollback (Branch A)
    - 部分使用者受影響 → P1 Targeted Rollback (Branch B)
    - 個別 user complain，無監控訊號 → 繼續觀察 + 收集資訊（Branch C）

Branch A: Immediate Rollback (P0)
    ↓
是否涉及 DB migration？
    ├─ NO  → 直接回滾應用程式 (§3.1 Application Rollback)
    └─ YES → 查 fix-spec.md §Rollback Plan
              ├─ Migration 設計為 expand-contract (§3.2.1) → 回滾 app + 留 schema
              └─ Migration 含 DROP/ALTER 不可逆 (§3.2.2) → 災難復原（停服務 + 從備份還原）

Branch B: Targeted Rollback (P1)
    ↓
是否能 feature flag 關閉？
    ├─ YES → flag off 即可，不需重新 deploy (§3.3 Feature Flag Rollback)
    └─ NO  → 同 Branch A 流程
    ↓
是否需 CDN cache invalidation？（前端資產回滾）
    ├─ YES（前端 bundle 改動）→ §3.4 CDN Cache Invalidation
    └─ NO（純後端改動）→ 跳過

Branch C: 觀察階段
    ↓
- 收集 logs / metrics
- 與 hotfix author + on-call 溝通
- 5 分鐘內未升級 → 維持並繼續觀察
- 5 分鐘內升級為 P0/P1 → 切到對應 Branch

Branch D: Canary Rollback（漸進式部署回滾，PR 16 V2.W2 fix）
    ↓
- Kubernetes: kubectl rollout undo deployment/<app>
- 流量權重: aws elbv2 modify-target-group --weight 0  /  istio VirtualService weight: 0
- 若還沒 rollout 到 100% → 直接停止下一階段（save 50% 流量不受影響）
- 較全量 rollback 便宜 10×：只影響 canary 那段流量
- 5 分鐘內升級為 P0/P1 → 切到對應 Branch
```

## 3. Rollback 執行步驟

### 3.1 Application Rollback（最常見，無 DB 變動）

> 假設使用 git tag-based deploy（與 release.md 對齊）。

```bash
# 1. 確認上一個已知良好版本（前一個正式 release，非 hotfix tag）
# PR 16 V1.W3 註記: 主路徑用 `.[1]` 假設失敗 hotfix 已在 release.md 寫入 release entry
# 若 hotfix deploy 在 release.md 之前就失敗（沒寫到 state.json），可改用 `.[0]`
PREV_TAG=$(jq -r '
  [.tasks[] | .releases // [] | .[] | {v: .version, t: .taggedAt}]
  | map(select(.t != null)) | sort_by(.t) | reverse | .[1].v // empty
' .sdlc/state.json)

# 若 state.json 無記錄，從 git tag 取最新非 hotfix tag
# PR 16 V1.C1 fix: grep -v hotfix 已過濾，最新 prod tag 在 head -1 不是 sed -n 2p
[ -z "$PREV_TAG" ] && PREV_TAG=$(git tag -l 'v*' --sort=-v:refname | grep -v hotfix | head -1)

# PR 16 V2.C3 fix: 若仍空 → 首次 incident 無前一個 tag，直接拒絕並 escalate
if [ -z "$PREV_TAG" ]; then
    echo "FATAL: 找不到前一個 prod release tag — 此為首次 incident（state.json + git tag 都空）" >&2
    echo "  建議: 1) 直接 git revert 闖禍 commit + emergency deploy" >&2
    echo "       2) Disable feature flag 關掉 hotfix 行為（若有）" >&2
    echo "       3) 升級 P0 incident，呼叫 on-call + 評估災難復原" >&2
    exit 1
fi

# 2. 部署上一個 tag（觸發 CI/CD pipeline）
echo "Rolling back to $PREV_TAG"
# (依專案 CI/CD 觸發方式 — 通常 push tag 或 merge revert PR)

# 3. 等待 deployment 完成
# (timeout: 5-10 分鐘，超時 escalate)

# 4. Smoke test 確認回滾成功
bash scripts/deploy-smoke-test.sh "$PROD_BASE_URL"  # PR 12 deploy-smoke-test 模板（跑 critical endpoints）

# 5. audit.log（PR 16 V2.C2 fix: 用 sdlc-audit.sh helper，與其他 audit 寫入格式一致）
bash scripts/sdlc-audit.sh PM "HOTFIX-NNN" "rollback_executed" "from=current to=$PREV_TAG"
```

**回滾後 MANDATORY**:
- 通知 stakeholders（Slack #incidents 或 PagerDuty resolved）
- 開 post-mortem ticket（24h 內必填）
- 把 hotfix branch 標記為 `[ROLLED_BACK]` 不可重用
- fix-spec.md 加註: `## Rollback Outcome\n- 觸發時間: ...\n- 觸發原因: ...\n- 已回滾至: $PREV_TAG`

### 3.2 Database Rollback

#### 3.2.1 Expand-Contract Migration（已正確設計）

依 Rule 11（不可逆操作協議）的 expand-contract 三階段：

```
Phase 1 (expand): 新增欄位/index/table（向下相容）
Phase 2 (migrate): 雙寫 + 資料遷移
Phase 3 (contract): 移除舊欄位/索引（已無 reader）
```

**PR 16 V1.W1 關鍵分支**: 失敗時要看 hotfix 已執行到哪個 phase：

| Phase 已執行到 | App rollback 安全嗎？| 處理 |
|---------------|---------------------|------|
| Phase 1 (expand only) | ✅ 安全 | App rollback 即可，舊 app 仍能讀新 schema（多了欄位但相容）|
| Phase 2 (dual-write) | ✅ 安全（半安全）| App rollback 即可，schema 維持新狀態，下次 hotfix 修正後再 Phase 2/3 |
| **Phase 3 (contract — 舊欄位已 DROP)** | ❌ **不安全** | **App rollback 會 crash**（舊 app 讀 dropped 欄位）→ 走 §3.2.2 災難復原（從備份還原 schema + data）|

```bash
# Phase 1/2 流程
1. Application rollback 到 PREV_TAG（§3.1）
2. 確認舊 application 在新 schema 上正常運作（雙向相容）
3. 留 schema 不動，等下次 hotfix 修正後再進 Phase 2/3
4. audit.log: `db_rollback_skip | reason=expand_contract_compatible`

# Phase 3 流程（已 DROP 欄位 → 走 §3.2.2）
0. 立即停 traffic（避免 stale app 寫入錯資料）
1. 從備份還原 schema + 資料（§3.2.2）
2. App rollback 到 PREV_TAG
3. 重新導流
4. Post-mortem 必須檢討為何 hotfix 跑到了 Phase 3 contract（這通常表示流程設計缺陷）
```

#### 3.2.2 Non-Reversible Migration（DROP COLUMN / DROP TABLE / 不可逆 ALTER）

> **理論上不應該存在** — Rule 11 + hotfix-runbook §8 anti-patterns 都禁止 hotfix 使用不可逆 migration。
> 但若意外發生，這是災難復原劇本：

```bash
# Step 1: 立即停應用 traffic（避免持續寫壞資料）— PR 16 V2.W3 fix: 具體命令
# 選一個對應你的 infra，不要混用：

## A. Kubernetes (kubectl scale to 0)
kubectl scale deployment/$APP_NAME --replicas=0 -n $NAMESPACE

## B. Kubernetes (drain node)
kubectl drain $NODE_NAME --ignore-daemonsets --delete-emptydir-data

## C. AWS ALB (target group health-check force fail)
aws elbv2 modify-target-group --target-group-arn $TG_ARN \
    --health-check-path /maintenance --matcher HttpCode=503

## D. Nginx upstream removal (set weight=0 + reload)
sed -i 's|server backend1:8080|server backend1:8080 down|' /etc/nginx/conf.d/upstream.conf
nginx -s reload

## E. Cloud Run / serverless (concurrency=0)
gcloud run services update $SERVICE --max-instances=0 --region=$REGION

# Step 2: 評估資料損失範圍
# - 從上次備份至 incident 時的所有寫入
LAST_BACKUP_TS=$(aws s3 ls s3://my-db-backups/ | sort | tail -1 | awk '{print $1}')
echo "Backup as of: $LAST_BACKUP_TS, incident at: $(date -u)"

# Step 3: 從備份還原
# 注意: 此步驟可能需要 hours，必須通知 stakeholders downtime
## PostgreSQL
pg_restore -h $DB_HOST -U $DB_USER -d $DB_NAME --clean --if-exists $BACKUP_FILE

## MySQL
mysql -h $DB_HOST -u $DB_USER -p$DB_PASSWORD $DB_NAME < $BACKUP_FILE

## MongoDB
mongorestore --host $DB_HOST --db $DB_NAME --drop $BACKUP_DIR

# Step 4: Application rollback 到 PREV_TAG（§3.1）

# Step 5: 重新導流
## A. Kubernetes
kubectl scale deployment/$APP_NAME --replicas=$ORIGINAL_REPLICAS -n $NAMESPACE

## C. AWS ALB
aws elbv2 modify-target-group --target-group-arn $TG_ARN \
    --health-check-path /health --matcher HttpCode=200

# Step 6: 驗證
bash scripts/deploy-smoke-test.sh "$PROD_BASE_URL"  # PR 12 deploy-smoke-test 模板
```

**這是最壞情況** — 發生後必須 post-mortem 強制檢討為何 hotfix 流程允許不可逆 migration。

### 3.3 Feature Flag Rollback（最佳實踐）

> 若 hotfix 透過 feature flag 包覆新邏輯，rollback 變成「flag off」— 秒級復原，不需 redeploy。

```bash
# 範例：使用 GrowthBook / LaunchDarkly / 自家 flag 系統
# (depends on flag system)

# 1. Disable flag in production
# growthbook flags set NEW_CHECKOUT_FLOW false --env production

# 2. 等待 flag SDK 拉新值（PR 16 V1.W2 fix: 是 SDK polling/streaming，不是 CDN）
# - LaunchDarkly streaming: ~毫秒級（websocket）
# - LaunchDarkly polling: 30s 預設（fallback）
# - GrowthBook SDK: cacheTTL 預設 60s（POST /features 重抓）
# - 自家 flag 系統: 視 polling interval / pub-sub 設計而定
# 保守等 60s，必要時等 SDK config 中的 cacheTTL × 2
sleep 60

# 3. Smoke test
bash scripts/deploy-smoke-test.sh "$PROD_BASE_URL"  # PR 12 deploy-smoke-test 模板

# 4. audit.log
bash scripts/sdlc-audit.sh PM "HOTFIX-NNN" "rollback_via_flag" "flag=NEW_CHECKOUT_FLOW value=false"
```

**這是 hotfix 的首選模式** — 設計時若可加 flag 就加，rollback 成本最低。

### 3.4 CDN Cache Invalidation（前端資產 rollback，PR 16 V2.I 補完）

> **盲點**: App rollback 到 v1.5.2，但 CDN edge 仍 cache v1.5.3 的 JS bundle →
> 使用者瀏覽器抓到舊 bundle 但呼叫新版 API（不存在）→ 全網 404/500。
> Rollback 必須 invalidate CDN cache 才完整。

```bash
# 1. 列出本次 hotfix 改過的前端資產（fix-spec.md §Fix Plan 應已列出）
ASSETS=("/static/js/main.*.js" "/static/css/main.*.css" "/index.html")

## A. CloudFront
DIST_ID=$(aws cloudfront list-distributions --query 'DistributionList.Items[?Comment==`prod`].Id' --output text)
aws cloudfront create-invalidation --distribution-id $DIST_ID --paths "${ASSETS[@]}"

## B. Cloudflare
for path in "${ASSETS[@]}"; do
    curl -X POST "https://api.cloudflare.com/client/v4/zones/$ZONE_ID/purge_cache" \
        -H "Authorization: Bearer $CF_API_TOKEN" \
        -d "{\"files\":[\"https://example.com$path\"]}"
done

## C. Fastly
fastly purge --service-id=$FASTLY_SERVICE_ID --soft "${ASSETS[@]}"

# 2. 驗證 cache invalidated（通常 1-5 分鐘）
sleep 60
for path in "${ASSETS[@]}"; do
    curl -I "https://example.com$path" | grep -i "x-cache:.*MISS" && echo "OK: $path cache cleared"
done

# 3. audit.log
bash scripts/sdlc-audit.sh PM "HOTFIX-NNN" "cdn_invalidated" "assets=${#ASSETS[@]}"
```

> **設計建議**: 前端資產用 hash-suffix 命名（`main.abc123.js`）→ rollback 即換不同檔名，
> CDN 自然 cache miss，不需手動 invalidate。這是減少 rollback 變數的最佳實踐。

## 4. Rollback Failure Recovery

### 4.1 Rollback 本身失敗

| 失敗模式 | 處理 |
|---------|------|
| PREV_TAG image 不存在 / 已被 GC | 取再前一個 tag，逐步往前嘗試 |
| Rollback CI 卡住 (> 30 分鐘) | **Escalation timeline**: 10 分卡→ ping author，20 分卡→ 強制 cancel + SSH 直接 deploy，30 分卡 → P0 incident + 呼叫 SRE on-call |
| Smoke test 在 PREV_TAG 也 fail | **異常** — PREV_TAG 之前是好的，可能 infra 共用元件出問題（e.g., DB schema、Redis、外部 API）。先停服務、分離 infra issue 再決定 |
| DB 從備份還原失敗 | **災難** — 升級 P0 incident，呼叫 DBA + 啟用備援 cluster |
| Concurrent incident（rollback 中又出新 incident）| 嚴禁同時 rollback 兩個 hotfix；處理優先序: 1) 先 stabilize（drain traffic）2) 完成手上 rollback 3) 再處理新 incident |
| Env drift（staging 通過但 prod 失敗）| 比對 env 變數差異 → diff staging.env vs prod.env，找未同步配置；同步後重試 |

### 4.2 Rollback 後再次失敗

> Rollback 完還是 fail → 通常表示 **infra 問題**，不是 code 問題。

1. 停應用 traffic（drain）
2. 檢查 infra:
   - DB 連線數 / lock
   - Redis / cache 服務
   - 外部 API（payment / SMS / etc.）
   - DNS / CDN
3. infra 確認正常後再 enable traffic

## 5. Post-Rollback Audit Trail

```
[ISO] PM | HOTFIX-NNN | rollback_started | trigger={metric_name} threshold={value}
[ISO] PM | HOTFIX-NNN | rollback_method | type={app|db|flag}
[ISO] PM | HOTFIX-NNN | rollback_target | from=v1.5.3-hotfix-001 to=v1.5.2
[ISO] PM | HOTFIX-NNN | rollback_smoke_test | status={pass|fail} duration={N}s
[ISO] PM | HOTFIX-NNN | rollback_completed | total_downtime={N}min
[ISO] PM | HOTFIX-NNN | post_mortem_scheduled | for=YYYY-MM-DD
```

## 6. Rollback Drill（演練）

> 最好的 rollback 是練過的 rollback。

### 6.1 Drill 規格（PR 16 V2.W1 fix: 補完 ownership + template）

- **Owner**: PM agent + on-call SRE 輪流（PM agent 排月度 reminder，SRE 執行）
- **頻率**: 每月一次
- **環境**: 嚴禁在 prod 演練；只在 staging
- **Template**: `~/.claude/sdlc/doc-templates/rollback-drill.tpl.md` (PR 16 新增)

### 6.2 演練流程

```bash
# 1. 從模板建立本月 drill 紀錄
mkdir -p .sdlc/drills
DRILL_FILE=".sdlc/drills/rollback-$(date +%Y-%m).md"
[ ! -f "$DRILL_FILE" ] && cp .sdlc/doc-templates/rollback-drill.tpl.md "$DRILL_FILE"

# 2. 在 staging 做一次 rollback 演練（用最新 release tag，回到上一個）
# (實際操作 — 跑 §3.1 Application Rollback 流程於 staging)

# 3. 量測 Detect-to-rollback latency（從 alert 到 rollback complete）
#    目標: < 10 分鐘

# 4. 填寫 drill record（依 rollback-drill.tpl.md 結構）
# - Timeline
# - What Went Well / Wrong
# - Action Items（含 owner + due）
# - Lessons Learned

# 5. audit.log
bash scripts/sdlc-audit.sh PM "DRILL-$(date +%Y-%m)" "rollback_drill_completed" "latency_min=?? outcome=pass"
```

### 6.3 Drill 違規處理

- 連續 2 個月沒 drill → `/sdlc:status` 顯示 ⚠️ DRILL DEBT
- 連續 3 個月沒 drill → 阻擋下一次 `/sdlc:hotfix`（強制先補 drill）
- 此機制由 PM agent §5.4 status report 監控（PR 16+ 強化）

## 7. Anti-Patterns（不要做的事）

❌ **不要做**:
- Try to fix forward in prod（直接在 prod 改 code 試圖修）
- 跳過 smoke test 直接結束 rollback
- 用 hotfix 來 rollback（rollback 應該用既有 release tag，不是新做一個 hotfix）
- 「等明天再看」（rollback 不應有 SLA debt）
- Rollback 後不開 post-mortem（永遠要 post-mortem，即使 rollback 順利）
- 對 staging / canary 跳過驗證直接 rollback prod

✅ **應該做**:
- 觀察期內任一惡化 → 立即 rollback
- Rollback 後立刻通知 stakeholders
- Post-mortem 24h 內必填
- Rollback drill 每月跑（演練得快才能真正快）
- 設計時優先加 feature flag（rollback 成本最低）

## 8. 與其他 Rule 的整合

- **Rule 11（不可逆操作）**: hotfix 設計時就強制 expand-contract，避免落入 §3.2.2 災難復原
- **Rule 14（Journal）**: rollback 也是 journal 事件，TASK / HOTFIX 的 journal.json 加 `rollback_executed`
- **Rule 15 §15.8（全域索引）**: rollback 完成後 `tasks.HOTFIX-NNN.rollbackedAt` 是低頻聚合欄位（候選白名單，待 PR 16+ 評估）
- **Rule 19（CI Gate）**: 自動 rollback 觸發條件（§1.1）由 CI workflow 監控；CI 認定 fail 直接觸發 rollback workflow
- **Rule 20.2（Browser Verify）**: rollback 後也要跑 browser smoke test（不只 endpoint）
- **hotfix-runbook §3 Rollback Plan**: fix-spec.md 必填欄位「Rollback Plan」要寫具體步驟（用本 runbook §3 對應子章節）
