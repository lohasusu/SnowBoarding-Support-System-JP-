---
document_id: "SAIDX-SHARED-v1.0"
title: "SA 領域 ID 總表"
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

# SA 領域 ID 總表

> **用途**: 彙整 SA 階段所有產出 ID —「有哪些功能、模組、實體、模式，誰實現/擁有/對應」。
> **維護者**: PM（SA approved 後更新）。
> **角色存取**: 所有角色唯讀；UIUX/SD 實作前需先讀本表。
> **規範依據**: `MASTER-INDEX.md` §2.2、`~/.claude/sdlc/protocols/rule-08-id-naming.md` (Rule 8)。

## 1. FUNC（功能）

| FUNC-ID | 名稱 | 首次定義於 TASK | 聚合 FR（來源）| 所屬 MOD | 實現於（PAGE / API）|
|---------|------|---------------|---------------|---------|---------------------|

**發號方式**: scan-based（Rule 8.7）— 由 PM 執行 `bash scripts/sdlc-id-scan.sh <PREFIX>` 取 max + 1（全域連續 — 跨 TASK 不重置）

## 2. MOD（模組）

| MOD-ID | 名稱 | 首次定義於 TASK | 職責 | 擁有 ENTITY | 提供 API |
|--------|------|---------------|------|-------------|---------|

**發號方式**: scan-based（Rule 8.7）— 由 PM 執行 `bash scripts/sdlc-id-scan.sh <PREFIX>` 取 max + 1

## 3. ENTITY（實體）

| ENTITY-ID | 名稱 | 首次定義於 TASK | 所屬 MOD | 對應 TBL | used_by_apis（反向追溯）|
|-----------|------|---------------|---------|---------|-------------------------|

**發號方式**: scan-based（Rule 8.7）— 由 PM 執行 `bash scripts/sdlc-id-scan.sh <PREFIX>` 取 max + 1

## 4. PATTERN（設計模式）

| PATTERN-ID | 名稱 | 首次定義於 TASK | 適用場景 | 使用於（MOD/FUNC）|
|------------|------|---------------|---------|-------------------|

**發號方式**: scan-based（Rule 8.7）— 由 PM 執行 `bash scripts/sdlc-id-scan.sh <PREFIX>` 取 max + 1

## 5. 依賴關係圖

```
FR (BA)
  └─ 聚合為 → FUNC (SA)
                  ├─ 部署於 → MOD (SA)
                  │             └─ 擁有 → ENTITY (SA)
                  │                          └─ 對應 → TBL (SD)
                  │             └─ 提供 → API (SD)
                  ├─ 設計為 → PAGE (UIUX)
                  └─ 使用 → PATTERN (SA)
```

## 更新規則

1. **SA 階段 approved** → PM 從 `functional-flow.md`、`system-arch.md`、`field-spec.md` 萃取 ID
2. **跨 TASK 新 FUNC**: 依 Rule 8.7 scan-based 取最新 max + 1，自然連續（跨 TASK 不重置）
3. **反向追溯 ENTITY.used_by_apis**: 每當 SD 新增 API 操作某 ENTITY 時，PM 更新此欄位
