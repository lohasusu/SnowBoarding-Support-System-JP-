---
document_id: "PENMAP-{TASK_ID}-v1.0"
title: "Pencil 節點對應表"
version: "1.0"
date: "{YYYY-MM-DD}"
author: "UIUX"
status: "Draft"
task_id: "{TASK-ID}"
phase: "uiux"
source_documents:
  - "WF-{TASK_ID}-v1.0"
  - "DS-{TASK_ID}-v1.0"
change_history:
  - version: "1.0"
    date: "{YYYY-MM-DD}"
    changes: "初始建立"
    author: "UIUX"
---

# Pencil 節點對應表

> **用途**: 建立 Pencil 原生 ID（node / frame / variant / variable）與 SDLC 內部 ID（PAGE / COMP / TOKEN）的一對一對應關係。
> **規範依據**: `rules/sdlc-external-id-binding.md` 規則 1、`MASTER-INDEX.md` §6。
> **維護者**: UIUX（每次 Pencil 變更同步更新）。
> **產出時機**: UIUX 階段 Step 8c 截圖後 MANDATORY 產出。

## 1. Frame → PAGE

| Pencil Frame ID | Frame 名稱 | 對應 PAGE-ID | 所屬 App | 截圖檔名（PAGE-{NNN}-{slug}-{state}.png）|
|-----------------|-----------|--------------|---------|------------------------------------------|
| {frame-abc123} | 使用者列表 | PAGE-001 | {app-name} | PAGE-001-user-list-default.png |

**唯一性規則**: 一個 Pencil Frame 只能對應一個 PAGE；一個 PAGE 的每個狀態對應獨立截圖。

## 2. Component Frame → COMP

| Pencil Frame ID | 元件名稱 | 對應 COMP-ID | 所屬 App | 來源（Source）| 來源版本 |
|-----------------|---------|--------------|---------|--------------|---------|
| {frame-def456} | PrimaryButton | COMP-001 | {app-name} | design-system | 1.2.0 |
| {frame-xyz789} | LoginCard | COMP-008 | {app-name} | local | — |

> 只登記 Design System 區的可複用元件 Frame。頁面中的 instance 不重複登記。
>
> **來源（Source）欄位**（PR 6 / Rule 17）:
> - `design-system`：從 `.sdlc/conventions/design-system.pen` 複製過來（Pencil 不支援跨檔 ref，必須 copy-over）。**來源版本**填當時 DS 的 `version` frontmatter
> - `local`：本 TASK 衍生的 specific 元件，未來可能 promote 到 DS（走 RFC）
> - 詳細追溯（含 customizations）見 `pencil-component-sync.json`

## 3. Variant → COMP.state

| Pencil Variant ID | 父 Frame ID | COMP-ID | 狀態屬性 | 狀態值 |
|-------------------|-------------|---------|---------|-------|
| {variant-ghi789} | {frame-def456} | COMP-001 | state | hover |
| {variant-ghi790} | {frame-def456} | COMP-001 | state | disabled |

**狀態字彙**（與 wireframes.md §4.2 一致）: default / empty / loading / error / create / edit / delete / hover / focus / disabled

## 4. Variable → TOKEN

| Pencil Variable ID | Variable 名稱 | 對應 TOKEN-ID | 類別 |
|--------------------|---------------|---------------|------|
| {var-jkl012} | color-primary-500 | TOKEN-color-primary-500 | 色彩 |
| {var-jkl013} | spacing-md | TOKEN-spacing-md | 間距 |

## 5. 完整性驗證（UIUX 自我驗證必須通過）

- [ ] **所有 Pencil Frame 已登記**: `.pen` 中的每個頁面 Frame 都在第 1 節
  ```bash
  # 用 Pencil MCP snapshot_layout 取得所有 Frame ID，比對本表
  # 差集應為空
  ```
- [ ] **ID 對應唯一**: 無 Pencil ID 對應多個 SDLC ID，也無 SDLC ID 對應多個 Pencil ID（Variant 除外）
- [ ] **截圖檔名一致**: 第 1 節的截圖檔名與 `.sdlc/tasks/{TASK-ID}/uiux/screenshots/` 下實際檔案名相符
  ```bash
  # 表格第 5 欄檔名
  grep -oE 'PAGE-[0-9]{3}[a-z]?-[a-z0-9-]+-[a-z]+\.png' pencil-node-mapping.md | sort -u > /tmp/expected.txt
  ls .sdlc/tasks/{TASK-ID}/uiux/screenshots/*.png | xargs -n1 basename | sort -u > /tmp/actual.txt
  diff /tmp/expected.txt /tmp/actual.txt || echo "FAIL: 對應表與實際檔名不一致"
  ```
- [ ] **PAGE-ID 存在於 wireframes**: 每個第 1 節的 PAGE-ID 必須出現在 `wireframes.md` 第 1 章頁面清單
- [ ] **COMP-ID 存在於 component-spec**: 每個第 2 節的 COMP-ID 必須出現在 `component-spec.md`
- [ ] **TOKEN-ID 存在於 design-system**: 每個第 4 節的 TOKEN-ID 必須出現在 `design-system.md`

> 任一驗證失敗 → UIUX 自我驗證扣 10 分 / 項，分數 < 90 不得交付。

## 6. 變更追蹤

若 Pencil 中的節點被重新命名或重構，須在此記錄：

| 日期 | 舊 ID | 新 ID | 原因 | 操作者 |
|------|-------|-------|------|-------|
