---
document_id: "BAIDX-SHARED-v1.0"
title: "BA 領域 ID 總表"
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

# BA 領域 ID 總表

> **用途**: 彙整 BA 階段所有產出 ID —「有哪些需求、規則、角色，由誰使用」。
> **維護者**: PM（BA approved 後更新）。
> **角色存取**: 所有角色唯讀；SA/UIUX/SD 實作前需先讀本表。
> **規範依據**: `MASTER-INDEX.md` §2.1、`~/.claude/sdlc/protocols/rule-08-id-naming.md` (Rule 8)。

## 1. FR（功能需求）

| FR-ID | 名稱 | 所屬 TASK | 來源（使用者原文 / FR 編號）| 實作於（FUNC/API/PAGE）|
|-------|------|----------|------|--------|

**發號方式**: 由各 TASK 獨立編號（TASK-local ID），BA 在單一 TASK 內序列發號；跨 TASK 引用使用 `TASK-NNN/FR-NNN`

## 2. NFR（非功能需求）

| NFR-ID | 名稱 | 所屬 TASK | 量化指標 | 驗證方式 |
|--------|------|----------|---------|---------|

## 3. BR（業務規則）

| BR-ID | 名稱 | 所屬 TASK | 觸發條件 | 實作於 LOGIC |
|-------|------|----------|---------|-------------|

## 4. AC（驗收標準）

| AC-ID | 所屬 FR | 描述 | 所屬 TASK | 測試於（TEST-ID）|
|-------|---------|------|----------|----------------|

**發號方式**: scan-based（Rule 8.7）— 由 PM 執行 `bash scripts/sdlc-id-scan.sh <PREFIX>` 取 max + 1（全域連續編號，跨 FR 不重置）

## 5. BF（業務流程）

| BF-ID | 名稱 | 所屬 TASK | 涉及 ROLE | 涉及 FR |
|-------|------|----------|----------|---------|

## 6. ROLE（角色）

| ROLE-ID | 角色名稱 | 首次定義於 TASK | 權限範圍 |
|---------|---------|---------------|---------|

**發號方式**: scan-based（Rule 8.7）— 由 PM 執行 `bash scripts/sdlc-id-scan.sh <PREFIX>` 取 max + 1（全域連續，定義後跨 TASK 共用）

## 7. CONST（約束）

| CONST-ID | 描述 | 所屬 TASK | 影響範圍 |
|----------|------|----------|---------|

## 8. ASSUME（假設）

| ASSUME-ID | 假設內容 | 所屬 TASK | 驗證狀態 |
|-----------|---------|----------|---------|

## 更新規則

1. **BA 階段 approved** → PM 從 `requirement-spec.md`、`business-flow.md` 萃取 ID 填入本表
2. **其他角色**（SA/UIUX/SD）讀取本表，實作對應的 FR/NFR/BR
3. **衝突處理**: 若新 TASK 的 BA 產出與本表衝突 → PM 仲裁
