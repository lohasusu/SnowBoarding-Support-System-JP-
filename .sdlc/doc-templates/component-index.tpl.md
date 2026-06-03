---
document_id: "COMPIDX-{APP}-SHARED-v1.0"
title: "{App} 元件索引"
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

# {App} 元件索引

> **用途**: 記錄該 App 的所有已設計元件，讓後續 TASK 的 UIUX 知道哪些元件已存在。
> **維護者**: PM（UIUX 階段 approved 後更新）。
> **角色存取**: UIUX 唯讀（避免重複設計已存在的元件、確保 COMP-ID 不碰撞）。
> **每個 App 一份**: 若有多個 App（如 admin + portal），各自維護獨立的 component-index。

## 元件清單

| COMP-ID | 名稱 | 類型 | 設計於 TASK | 變體 | used_by_pages（反向追溯）| used_tokens（引用的 TOKEN）| 說明 |
|---------|------|------|-----------|------|-------------------------|---------------------------|------|

**類型說明**:
- `ui`: 基礎 UI 元件（Button, Input, Modal...）
- `layout`: 佈局元件（Header, Sidebar, Footer...）
- `feature`: 功能元件（SearchBar, DataTable...）

## .pen 元件對應

| COMP-ID | .pen 節點 ID | Canvas 位置 | 說明 |
|---------|-------------|------------|------|

> 此表用於 UIUX 在 .pen 中查找已有元件，避免重複繪製。

## 更新規則

1. **UIUX 職責**: 開始工作前讀取本表 + id-registry.md 的 COMP 段了解已分配語意；發號走 Rule 8.7 scan-based（scripts/sdlc-id-scan.sh（由 PM 執行））
2. **PM 職責**: UIUX 階段 approved 後，從 component-spec.md 提取新元件並更新本表
3. **重用規則**: 若已有元件滿足需求，UIUX 直接引用不重新設計
