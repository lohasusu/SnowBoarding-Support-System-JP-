# Rollback Drill — YYYY-MM (PR 16)

> 此檔由月度 rollback drill 後填寫，紀錄到 `.sdlc/drills/rollback-YYYY-MM.md`。
> 模板由 `/sdlc:init` 或手動 `cp .sdlc/doc-templates/rollback-drill.tpl.md .sdlc/drills/rollback-{YYYY-MM}.md` 啟用。
> 與 `rollback-runbook.tpl.md` §6 對齊：每月一次，目標 detect-to-rollback < 10 分鐘。

## Drill Metadata

- **日期**: {YYYY-MM-DD HH:MM TZ}
- **演練 owner**: {role + 名字}（建議: PM agent + on-call SRE 輪流）
- **演練環境**: staging（嚴禁在 prod 演練）
- **演練版本**:
  - From: {current staging tag, e.g., v1.5.2}
  - To: {previous tag, e.g., v1.5.1}

## Scenario

> 模擬什麼情境？例如「v1.5.2 deploy 後 5xx error rate 上升至 2%，需 rollback 到 v1.5.1」

- **觸發指標**: {model the trigger condition}
- **預期 rollback 路徑**: {Application Rollback / DB Rollback / Feature Flag / Canary}
- **演練變因**:
  - [ ] PREV_TAG 還能找到（state.json + git tag）
  - [ ] PREV_TAG 已被 GC（強制走 fallback）
  - [ ] DB migration 在 Phase 1（schema-compat）/ Phase 2（dual-write）/ Phase 3（不可逆）

## Timeline

| 時間 (mm:ss) | 事件 | 備註 |
|-------------|------|------|
| 00:00 | Trigger 發送（人為注入 5xx alert）| 起算 |
| 00:?? | Detect — alert 收到 | |
| 0?:?? | 決策完成 — 確認 rollback 路徑 | |
| 0?:?? | 部署上一個 tag | |
| 0?:?? | Smoke test 開始 | |
| 0?:?? | Smoke test 通過 | |
| 0?:?? | 觀察期結束（5 分鐘）| 完成 |

**Detect-to-rollback latency**: ?? 分鐘 ?? 秒（**目標 < 10 分鐘**）

## What Went Well

- {例如: PREV_TAG resolver 一次到位，沒查找問題}
- {例如: deploy-smoke-test 在 30 秒內完成}

## What Went Wrong

- {例如: rollback CI pipeline 卡 5 分鐘，原因是 image registry 拉取慢}
- {例如: 某個 audit.log 寫入 path 配置錯，事件沒紀錄}

## Action Items

- [ ] {具體改善項，含 owner + due}
  - 例如: 「PR-?? 改進 deploy-smoke-test 的並行 endpoint 檢查」owner=Dev，due=2 週內
- [ ] {改善 rollback runbook §X 的某段描述}
- [ ] {更新 CI pipeline 的 image GC 策略}

## Lessons Learned

> 一段話總結，可被未來 drill 引用作為 baseline。

## Audit Trail

```bash
# 演練開始
bash scripts/sdlc-audit.sh PM "DRILL-YYYY-MM" "rollback_drill_started" "scenario=..."

# 演練結束
bash scripts/sdlc-audit.sh PM "DRILL-YYYY-MM" "rollback_drill_completed" "latency_min=?? outcome=pass|fail"
```

## 與其他 runbook 的引用

- 對應 rollback-runbook.tpl.md §{1.1 / 2 / 3.1 / 3.2 / 3.3 / 3.4} 的哪個分支
- 若 drill 揭露 runbook 缺漏 → 開 PR 更新 rollback-runbook.tpl.md
