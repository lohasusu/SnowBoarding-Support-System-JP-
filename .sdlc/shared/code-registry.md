---
document_id: "CODEREG-SHARED-v1.0"
title: "程式碼檔案索引"
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

# 程式碼檔案索引

> **用途**: 記錄已實作的程式碼檔案位置，讓後續 TASK 的 FE/BE 知道哪些檔案已存在。
> **維護者**: PM（FE/BE 階段 approved 後更新）。
> **角色存取**: FE/BE 唯讀（避免重複建立已存在的檔案、知道哪些共用元件可重用）。

## 1. 前端檔案

### 共用元件（src/components/ui/）

| 檔案路徑 | 對應 COMP-ID | 建立於 TASK | 說明 |
|----------|-------------|-----------|------|

### 功能元件（src/components/features/）

| 檔案路徑 | 對應 COMP-ID | 建立於 TASK | 說明 |
|----------|-------------|-----------|------|

### 頁面（src/pages/ 或 src/app/）

| 檔案路徑 | 對應 PAGE-ID | 建立於 TASK | 說明 |
|----------|-------------|-----------|------|

### 樣式 / Token

| 檔案路徑 | 用途 | 建立於 TASK | 說明 |
|----------|------|-----------|------|

## 2. 後端檔案

### Entity / Model

| 檔案路徑 | 對應 ENTITY-ID | 建立於 TASK | 說明 |
|----------|---------------|-----------|------|

### Controller / Route

| 檔案路徑 | 對應 API-ID 範圍 | 建立於 TASK | 說明 |
|----------|-----------------|-----------|------|

### Service / Business Logic

| 檔案路徑 | 對應 LOGIC-ID 範圍 | 建立於 TASK | 說明 |
|----------|-------------------|-----------|------|

### Migration

| 檔案路徑 | 對應 TBL | 建立於 TASK | 說明 |
|----------|---------|-----------|------|

## 3. 共用配置

| 檔案路徑 | 用途 | 建立於 TASK | 說明 |
|----------|------|-----------|------|

## 4. 更新規則

1. **PM 職責**: FE/BE 階段 approved 後，從 frontend-report.md / backend-report.md 提取新檔案清單並更新本表
2. **FE/BE 職責**: 開始工作前讀取本表，確認哪些檔案已存在（避免覆蓋或重複建立）
3. **修改已有檔案**: 若需修改其他 TASK 建立的檔案，在報告中標記 `[MODIFIED: 檔案路徑, 原 TASK]`
