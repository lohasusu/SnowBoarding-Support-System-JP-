---
document_id: "TESTIDX-SHARED-v1.0"
title: "Tester / Code Review / 資安 領域 ID 總表"
version: "1.0"
date: "{YYYY-MM-DD}"
author: "PM"
status: "Living Document"
phase: "shared"
change_history:
  - version: "1.0"
    date: "{YYYY-MM-DD}"
    changes: "初始建立"
    author: "PM"
---

# Tester / Code Review / 資安 領域 ID 總表

> **用途**: 彙整 Tester / Code Review / Deployer 階段的發現與測試案例 ID。
> **維護者**: PM（各相應階段 approved 後更新）。
> **角色存取**: 所有角色唯讀；PM 仲裁 Critical 發現。
> **規範依據**: `MASTER-INDEX.md` §2.6、`rules/sdlc-tester.md`。

## 1. TEST（測試案例）

| TEST-ID | 名稱 | 所屬 TASK | @traces_to | 類型（正向/負向/邊界）| 狀態 |
|---------|------|----------|-----------|---------------------|------|

**狀態值**: `pass` / `fail` / `skip` / `blocked`
**追溯**: 100% 必須有 `@traces_to(SPEC-ID)`（FR/NFR/API/PAGE/LOGIC 等）

### 1.1 覆蓋率統計

| 類型 | 總數 | 已覆蓋 | 覆蓋率 |
|------|------|-------|-------|
| FR | 0 | 0 | 0% |
| NFR | 0 | 0 | 0% |
| API | 0 | 0 | 0% |
| PAGE | 0 | 0 | 0% |

**合格標準**: 每類覆蓋率 ≥ 95%；負向測試比率 ≥ 30%。

## 2. CR（Code Review 發現）

| CR-ID | 所屬 TASK | 分級 | 標題 | 檔案：行 | 狀態 |
|-------|----------|------|------|---------|------|

**分級**: `Critical` / `Warning` / `Info`
**狀態**: `open` / `fixed` / `wontfix`

### 2.1 分級統計

| 分級 | 總數 | 已修正 | open |
|------|------|-------|------|
| Critical | 0 | 0 | 0 |
| Warning | 0 | 0 | 0 |
| Info | 0 | 0 | 0 |

**合格標準**: Critical = 0, Warning ≤ 3（否則 CONDITIONAL PASS）

## 3. SEC（資安發現）

格式: `SEC-{LEVEL}-NNN`

| SEC-ID | 所屬 TASK | 等級 | 標題 | CVE / CWE | 狀態 |
|--------|----------|------|------|----------|------|

**等級**: `CRIT` / `HIGH` / `MED` / `LOW`
**狀態**: `open` / `mitigated` / `accepted`

### 3.1 等級統計

| 等級 | 總數 | 已緩解 | open |
|------|------|-------|------|
| CRIT | 0 | 0 | 0 |
| HIGH | 0 | 0 | 0 |
| MED | 0 | 0 | 0 |
| LOW | 0 | 0 | 0 |

**合格標準**: CRIT = 0, HIGH = 0（依 OWASP Top 10）

## 4. 追溯矩陣

| TEST-ID | 追溯 | CR-ID（若有相關）| SEC-ID（若有相關）|
|---------|------|-----------------|-------------------|

## 更新規則

1. **Tester approved** → PM 從 `test-report.md` 萃取 TEST-ID 更新本表
2. **Code Review approved** → PM 從 `code-review-report.md` 萃取 CR-ID
3. **Deployer 資安掃描完成** → PM 從 `security-report.md` 萃取 SEC-ID
4. **Critical 阻塞**: 任何 Critical 發現未 fixed/mitigated → 不可進入下一階段
