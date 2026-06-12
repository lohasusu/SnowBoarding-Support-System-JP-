---
document_id: "VISCOMP-{TASK_ID}-v1.0"
title: "畫面視覺比對報告"
version: "1.0"
date: "{YYYY-MM-DD}"
author: "FE"
status: "Draft"
task_id: "{TASK-ID}"
phase: "fe"
source_documents:
  - "WF-{TASK_ID}-v1.0"
  - "DS-{TASK_ID}-v1.0"
  - "COMP-{TASK_ID}-v1.0"
change_history:
  - version: "1.0"
    date: "{YYYY-MM-DD}"
    changes: "初始版本"
    author: "FE"
approval:
  reviewer: "PM"
  date: ""
  result: "Pending"
  notes: ""
---

# 畫面視覺比對報告

## 1. 比對摘要

| 項目 | 結果 |
|------|------|
| 比對頁面數 | {N} |
| 通過頁面數 | {N} |
| 整體還原度 | {X}% |
| 通過門檻 | >= 90% |
| 結論 | PASS / FAIL |

## 2. 比對方法

| 項目 | 說明 |
|------|------|
| FE 截圖工具 | Claude Preview MCP (`preview_screenshot`) |
| 設計稿來源 | Pencil MCP (`get_screenshot`) / wireframes.md ASCII |
| 響應式斷點 | {列出斷點，如 375px, 768px, 1024px, 1440px} |

## 3. 逐頁比對結果

### PAGE-001: {頁面名稱}

| 檢查項 | 比對內容 | 結果 |
|--------|---------|------|
| 佈局結構 | 區塊位置、排列順序 | ✅/❌ |
| 元件配置 | 元件種類、數量、位置 | ✅/❌ |
| 色彩使用 | 背景色、文字色、邊框色 vs Design Token | ✅/❌ |
| 字體使用 | 字型、大小、行高 vs Design Token | ✅/❌ |
| 間距 | 元素間距 vs spacing Token | ✅/❌ |
| 互動元素 | 按鈕、輸入框、連結的狀態 | ✅/❌ |
| 響應式 | 各斷點佈局是否與 UIUX 設計一致 | ✅/❌ |
| 空/載入/錯誤狀態 | 是否有實作 UIUX 定義的狀態畫面 | ✅/❌ |

**頁面還原度**: {通過項}/{總項} = {X}%
**偏差**: {無 / [DEVIATION: 描述]}

### PAGE-002: {頁面名稱}

（同上格式，每頁一個區塊）

## 4. 截圖對照表

| 頁面 | 斷點 | FE 截圖 | UIUX 設計稿 | 差異描述 |
|------|------|---------|------------|---------|
| PAGE-001 | Desktop | {截圖路徑} | {設計稿路徑/ASCII 參考} | {差異描述或「一致」} |
| PAGE-001 | Mobile | {截圖路徑} | {設計稿路徑/ASCII 參考} | {差異描述或「一致」} |

## 5. 還原度總表

| 頁面 | 通過項 | 總項 | 還原度 | 偏差 |
|------|--------|------|--------|------|
| PAGE-001 | {n} | {N} | {X}% | {偏差描述或「無」} |
| PAGE-002 | {n} | {N} | {X}% | {偏差描述或「無」} |
| **整體** | {n} | {N} | **{X}%** | |

## 6. 判定結論

| 條件 | 結果 |
|------|------|
| 整體還原度 >= 90% | ✅ PASS / ❌ FAIL |
| 任何頁面還原度 < 80% | 無 / {列出頁面} → FAIL |
| 80% <= 整體 < 90% | CONDITIONAL PASS（PM 決定）|

## 7. 追溯矩陣

| 頁面 | 對應 wireframes.md | 對應 component-spec.md | 對應 design-system.md |
|------|-------------------|----------------------|---------------------|
| PAGE-001 | PAGE-001 | COMP-001, COMP-002 | color.primary, spacing.md |
