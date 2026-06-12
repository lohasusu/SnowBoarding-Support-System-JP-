# Hotfix Runbook (PR 14)

> 此檔由 `/sdlc:hotfix` 命令在執行時讀取作為決策依據。
> Install 後複製到 `.sdlc/doc-templates/hotfix-runbook.md` 作為專案級客製基線。

## 1. Severity 判定樹

```
Production 出問題了
    ↓
是否影響使用者「現在」操作？
    ├─ YES, 服務完全中斷 → P0
    ├─ YES, 部分功能異常 → P1
    └─ NO, 可延後 → 不是 hotfix（用 /sdlc:start）

是否涉及資料外洩 / 安全漏洞？
    ├─ YES, 已被利用 → P0
    ├─ YES, 但無法利用（理論漏洞）→ P1
    └─ NO → 看上面影響面

是否涉及金錢 / 合規？
    ├─ YES, 已造成損失 → P0
    ├─ YES, 可能造成損失 → P1
    └─ NO → 看上面影響面
```

## 2. 跳階段決策矩陣

| Phase | P0 (服務中斷) | P1 (Critical 業務) | P2 (非 hotfix) |
|-------|--------------|-------------------|----------------|
| BA（需求分析）| ❌ 跳，事後 24h 補 | ⚠️ 縮減（只寫一句根因 + 修復目標）| ✅ 完整 |
| SA（系統架構）| ❌ 跳，事後 24h 補 | ❌ 跳（hotfix 應不涉架構）| ✅ 完整 |
| UIUX（設計）| ❌ 跳，事後 24h 補 | ❌ 跳（若無 UI 變更）| ✅ 完整 |
| Deploy(Init) | ❌ 跳（用既有 contract）| ❌ 跳 | ✅ 完整 |
| **SD（開發前分析）**| ⚠️ **縮減** — 只產 fix-spec.md | ⚠️ 縮減 | ✅ 完整 |
| **FE/BE（開發）**| ✅ **保留** | ✅ 保留 | ✅ 完整 |
| **Build Gate** | ✅ **強制保留** | ✅ 保留 | ✅ 完整 |
| **資安掃描** | ✅ **強制 + Critical 永遠阻塞** | ✅ 強制 | ✅ 完整 |
| **Code Review** | ✅ **強制（即使單人，PR 自我 review）**| ✅ 強制 | ✅ 完整 |
| **Deploy(Execute)** | ✅ scope=local-staging 強制 | ✅ scope=local-staging 強制 | ✅ scope per config |
| **Smoke Test** | ✅ **強制（Rule 19 / E-11）**| ✅ 強制 | ✅ 強制 |
| Tester（測試驗證）| ❌ 跳，事後 24h 補 | ❌ 跳，事後 48h 補 | ✅ 完整 |
| **Monitor 期** | ✅ **15 分鐘觀察 error rate** | ✅ 5 分鐘 | — |

## 3. SD `fix-spec.md` 縮減模板（P0/P1 用）

正常 SD 產出 5 份文件（api-spec/db-schema/code-arch/logic-flow/test-spec）。Hotfix 模式只產一份 `fix-spec.md`：

```markdown
# Hotfix Fix Spec — HOTFIX-{NNN}

## Severity & Incident
- Severity: P0 / P1
- 事件: {一句話描述使用者影響}
- 觸發時間: {ISO}
- 影響範圍: {N 個使用者 / N% 流量 / 全部 / ...}

## Root Cause（必填）
- 根因: {一段話，必須具體 — "因為 X 導致 Y"}
- 證據: {log link / metric snapshot / repro steps}
- 為何之前的 SDLC 沒抓到: {遺漏的測試 / 邊界條件 / 第三方變動 / ...}

## Fix Plan（必填）
- 改動檔案: {列出檔案 + 行號}
- 改動內容: {diff 摘要}
- 為何這個修法: {替代方案 / 取捨}
- 不改動什麼: {明確列出 — 避免 scope creep）

## Rollback Plan（必填）
- 回滾觸發條件: {error rate / latency P95 / smoke test fail / ...}
- 回滾步驟: {git revert / 切回前一個 image / migration down / ...}
- 回滾風險: {migration 不可逆 → 列出 expand-contract 三階段}

## Test Coverage（必填）
- 必須新增 / 修改的測試: {列出 test case}
- （事後補件區）完整測試: {等 Tester phase 補}

## Post-incident TODO（事後補件清單）
- [ ] BA: 補 requirement-spec.md（24h / 48h 內）
- [ ] SA: 補 functional-flow.md
- [ ] UIUX: （若有 UI 變更）補 wireframes
- [ ] Tester: 完整測試報告
- [ ] 更新 `.sdlc/shared/error-codes.md`（若新增 ERR）
```

## 4. Code Review 強制要求（hotfix 不可省）

即使 P0 緊急，也必須走 PR + 至少一個 reviewer（單人專案：自我 review，明確檢查清單）。

**單人專案 hotfix self-review checklist**:
- [ ] 改動只動 fix-spec.md 列出的檔案，無 scope creep
- [ ] 沒有 hardcode 任何 secret / API key / debug print
- [ ] 沒有 disable 既有測試或繞過 CI
- [ ] Migration（若有）走 expand-contract
- [ ] 提交訊息含 HOTFIX-NNN + severity + 根因摘要
- [ ] PR description 含完整 fix-spec.md 連結
- [ ] Smoke test 至少包含一個業務 endpoint 驗證

## 5. Deploy scope 強制 = local-staging

P0/P1 都強制 scope=`local-staging`（不直接上 prod）：
- Local 跑 docker compose + smoke test 通過
- Staging 部署完跑 smoke test（≥2 endpoints，含 1 個業務）
- 觀察期通過後手動觸發 production deploy（不自動）

> **理由**: hotfix 已縮減驗證流程，staging 是最後一道安全網。

## 6. 事後補件 (Post-incident)

### 6.1 補件時程

| Severity | 補件期限 | 補件範圍 |
|----------|---------|---------|
| P0 | 部署完成後 24 小時內 | BA + SA + UIUX（若有 UI）+ Tester 完整報告 |
| P1 | 部署完成後 48 小時內 | BA（縮減）+ SA（若涉架構）+ Tester 報告 |

### 6.2 補件流程

1. 建立 `.sdlc/tasks/HOTFIX-NNN/post-incident/` 目錄
2. PM 派發 BA agent: `/sdlc:next post-incident-ba`（依 fix-spec.md 反推）
3. PM 派發 SA agent: `/sdlc:next post-incident-sa`
4. （若需）UIUX、Tester
5. 補件完成 → 在 state.json 標記 `hotfixDebt.cleared = true`
6. audit.log: `[ISO] PM | HOTFIX-NNN | post_incident_completed | phases=ba,sa,uiux,tester`

### 6.3 補件未完成的後果

- `/sdlc:status` 會 warn 列出 unresolved hotfix debt
- 累積 3 個未補件 hotfix → 自動阻擋新 `/sdlc:hotfix`（必須先清債務）
- audit.log 持續記錄: `[ISO] PM | check | hotfix_debt | unresolved=N`

## 7. 與其他 Rule 的整合

- **Rule 6（跨 TASK 修改）**: hotfix 修改 in-progress TASK 的 fix 必須走跨 TASK 修改協議（SA 標 `[CROSS-TASK]`）
- **Rule 8（ID 規範）**: 使用 `HOTFIX-NNN` 命名空間（與 TASK 隔離），不用 allocator 配發
- **Rule 10（Abandoned）**: abandoned TASK 的程式碼不能用 hotfix 修，需先 unabandon
- **Rule 11（不可逆）**: DB migration 強制 expand-contract，禁止 P0 也走 hard delete
- **Rule 14（Journal）**: hotfix TASK 也有 `.sdlc/tasks/HOTFIX-NNN/journal.json`
- **Rule 19（CI Gate）**: hotfix 觸發 CI workflow，所有 gate 維持 strict
- **Rule 20（Harness）**: hotfix 不需要 trajectory.md（短週期）但需要 audit.log 完整

## 8. 失敗模式 / Anti-patterns

❌ **不要做的事**:
- 在 main 直接改 + force push（永遠走 PR）
- Disable CI 或繞過 Build Gate
- 跳過資安掃描（即使「只是修字串」也要掃）
- 為 hotfix 改業務邏輯範圍（fix-spec.md 列出什麼就改什麼）
- 用 hotfix 流程做 refactor / 性能優化（那不是 hotfix）

✅ **應該做的事**:
- fix-spec.md 寫清楚根因 + 修復方式 + rollback 計畫
- Smoke test 至少含 1 個業務 endpoint
- Staging 觀察 5-15 分鐘再上 prod
- 部署完立刻通知 stakeholders
- 事後補件 — 永遠補
