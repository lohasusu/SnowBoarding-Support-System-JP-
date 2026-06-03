---
document_id: "PAGEIDX-{APP}-SHARED-v1.0"
title: "{App} 頁面索引"
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

# {App} 頁面索引

> **用途**: 記錄該 App 的所有已設計頁面，讓後續 TASK 的 UIUX 知道哪些頁面已存在。
> **維護者**: PM（UIUX 階段 approved 後更新）。
> **角色存取**: UIUX 唯讀（避免重複設計已存在的頁面、確保 PAGE-ID 不碰撞）。
> **每個 App 一份**: 若有多個 App（如 admin + portal），各自維護獨立的 page-index。

## 頁面清單

| PAGE-ID | 名稱 | 路由 | 設計於 TASK | 使用元件 | implements_funcs（反向追溯）| 說明 |
|---------|------|------|-----------|---------|----------------------------|------|

## .pen 頁面對應

| PAGE-ID | .pen Canvas 位置 | 截圖路徑 | 設計於 TASK |
|---------|-----------------|---------|-----------|

> 此表用於 UIUX 在 .pen 中查找已有頁面視覺稿。

## 更新規則

1. **UIUX 職責**: 開始工作前讀取本表 + id-registry.md 的 PAGE 段了解已分配語意；發號走 Rule 8.7 scan-based（scripts/sdlc-id-scan.sh（由 PM 執行））
2. **PM 職責**: UIUX 階段 approved 後，從 wireframes.md 提取新頁面並更新本表
3. **頁面修改**: 若後續 TASK 需修改已有頁面 → UIUX 標記 `[MODIFIED: PAGE-ID, 原 TASK]`
