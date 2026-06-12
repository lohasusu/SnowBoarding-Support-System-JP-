---
document_id: "UIUXIDX-SHARED-v1.0"
title: "UIUX 領域 ID 總表"
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

# UIUX 領域 ID 總表

> **用途**: 彙整 UIUX 階段 FLOW/LAYOUT/TOKEN 類別的 ID。
> **PAGE/COMP**: 請見 `apps/{app}/page-index.md` 與 `apps/{app}/component-index.md`（依 App 分開維護）。
> **維護者**: PM（UIUX approved 後更新）。
> **角色存取**: 所有角色唯讀；SD/FE 實作前需先讀本表。
> **規範依據**: `MASTER-INDEX.md` §2.3、`~/.claude/sdlc/protocols/rule-08-id-naming.md` (Rule 8)。

## 1. FLOW（使用者流程）

| FLOW-ID | 名稱 | 所屬 TASK | 實現 FUNC | 經過 PAGE（有序）|
|---------|------|----------|----------|------------------|

**範圍**: TASK 內編號，跨 TASK 引用用 `TASK-NNN/FLOW-NNN`

## 2. LAYOUT（共用佈局）

| LAYOUT-ID | 名稱 | 首次定義於 TASK | 定義位置 | 適用範圍（App/全域）|
|-----------|------|---------------|---------|---------------------|
| LAYOUT-001 | Header | TASK-001 | sitemap.md §2 | 全域 |
| LAYOUT-002 | Sidebar | TASK-001 | sitemap.md §2 | 全域 |
| LAYOUT-003 | Footer | TASK-001 | sitemap.md §2 | 全域 |

**發號方式**: scan-based（Rule 8.7）— 由 PM 執行 `bash scripts/sdlc-id-scan.sh <PREFIX>` 取 max + 1（全域連續）

## 3. TOKEN（Design Token）

> Token 使用語義化命名，非數字編號。格式: `TOKEN-{category}-{name}`。

### 3.1 色彩 Token

| TOKEN-ID | 值 | 所屬類別 | 引用於 COMP-ID（反向追溯）|
|----------|-----|---------|-------------------------|
| TOKEN-color-primary-500 | `#1976D2` | 主色 | - |
| TOKEN-color-neutral-900 | `#212121` | 文字主色 | - |

### 3.2 間距 Token

| TOKEN-ID | 值 | 用途 | 引用於 COMP-ID |
|----------|-----|------|---------------|
| TOKEN-spacing-sm | `8px` | 小間距 | - |
| TOKEN-spacing-md | `16px` | 中間距 | - |

### 3.3 字型 Token

| TOKEN-ID | 值 | 用途 | 引用於 COMP-ID |
|----------|-----|------|---------------|
| TOKEN-font-body-base | `14px/1.5 sans-serif` | 本文 | - |

### 3.4 其他（Radius / Shadow / Motion）

| TOKEN-ID | 值 | 用途 | 引用於 COMP-ID |
|----------|-----|------|---------------|

## 4. Pencil Variable 綁定（若使用 Pencil）

| Pencil Variable ID | TOKEN-ID | 類別 |
|--------------------|----------|------|

> 此表對應 `.pen` 中的變數定義與 TOKEN 的一對一關係。詳見 `pencil-node-mapping.md`。

## 更新規則

1. **UIUX approved** → PM 從 `design-system.md`、`sitemap.md`、`user-flow.md` 萃取 ID
2. **Token 反向追溯**: 每當 FE 的 component-spec 或 frontend-report 引用某 TOKEN 時，PM 更新 `引用於 COMP-ID` 欄位
3. **LAYOUT 變更**: 修改已存在的 LAYOUT 需走 Rule 6 跨 TASK 修改協議
