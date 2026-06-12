---
document_id: "BERPT-{TASK_ID}-v1.0"
title: "後端開發報告"
version: "1.0"
date: "{YYYY-MM-DD}"
author: "BE"
status: "Draft"
task_id: "{TASK-ID}"
phase: "be"
source_documents:
  - "API-{TASK_ID}-v1.0"
  - "DB-{TASK_ID}-v1.0"
  - "CODEARCH-{TASK_ID}-v1.0"
  - "LOGIC-{TASK_ID}-v1.0"
change_history:
  - version: "1.0"
    date: "{YYYY-MM-DD}"
    changes: "初始版本"
    author: "BE"
approval:
  reviewer: "PM"
  date: ""
  result: "Pending"
  notes: ""
---

# 後端開發報告

## 1. 實作摘要

| 項目 | 數量 |
|------|------|
| API endpoint 數 | {N} |
| 資料表數 | {N} |
| Migration 數 | {N} |
| 業務邏輯模組數 | {N} |

## 2. API 實作清單

| API ID | 方法 | 路徑 | 狀態 | 說明 |
|--------|------|------|------|------|
| API-001 | POST | /api/{resource} | 已完成 | - |

## 3. API 合規性 9 維度報告

| 維度 | 結果 | 說明 |
|------|------|------|
| Endpoint 路徑 | ✅/❌ | 差異數: {N} |
| HTTP 方法 | ✅/❌ | |
| Request 參數名 | ✅/❌ | |
| 參數類型 | ✅/❌ | |
| 驗證規則 | ✅/❌ | |
| Response 結構 | ✅/❌ | |
| 錯誤碼 | ✅/❌ | |
| HTTP 狀態碼 | ✅/❌ | |
| 分頁格式 | ✅/❌ | |

## 4. 資料庫實作清單

| 資料表ID | 資料表名 | DDL 一致性 | 索引 | Migration |
|---------|---------|-----------|------|-----------|
| TBL-001 | {table} | ✅ 完全一致 | ✅ | {migration_file} |

## 5. Migration 可逆性報告

| Migration 檔案 | Up | Down | 冪等 | 狀態 |
|---------------|-----|------|------|------|
| {filename} | ✅ | ✅ | ✅ | 已驗證 |

## 6. 業務邏輯實作清單

| 邏輯ID | 名稱 | 對應 API | 狀態 | 說明 |
|--------|------|---------|------|------|
| LOGIC-001 | {名稱} | API-001 | 已完成 | - |

## 7. 未實作邏輯（Stub）

| 標記 | 位置 | 原因 |
|------|------|------|
| [BLOCKED_ON_SD] | {file:line} | SD 未指定此場景的邏輯 |

## 8. 測試覆蓋率

| 指標 | 結果 | 目標 |
|------|------|------|
| 行覆蓋率 | {N}% | > 80% |
| 分支覆蓋率 | {N}% | > 70% |
| 正向測試數 | {N} | 每 API ≥ 1 |
| 負向測試數 | {N} | 比率 ≥ 30% |

## 9. 依賴清單

| 套件 | 版本 | 用途 | SD 授權 |
|------|------|------|---------|
| {package} | ^{version} | {用途} | ✅ / [PENDING_APPROVAL] |

## 10. OpenAPI 合規性報告

| 檢查項 | 結果 | 說明 |
|--------|------|------|
| api-spec.yaml 存在 | ✅/❌ | SD 產出的 OpenAPI 3.0 規格檔案 |
| paths 數量一致 | ✅/❌ | api-spec.yaml paths: {N}, 已註冊路由: {N} |
| Endpoint 路徑完全一致 | ✅/❌ | 差異數: {N} |
| HTTP 方法完全一致 | ✅/❌ | 差異數: {N} |
| Request Schema 對齊 | ✅/❌ | 不一致欄位: {清單} |
| Response Schema 對齊 | ✅/❌ | 不一致欄位: {清單} |
| 錯誤碼對齊 | ✅/❌ | 缺少/多餘: {清單} |
| operationId 對應 API-ID | ✅/❌ | |

### OpenAPI 差異清單（若有）

| API ID | 維度 | api-spec.yaml 定義 | 實際實作 | 狀態 |
|--------|------|-------------------|---------|------|
| {API-NNN} | {維度} | {定義} | {實作} | 已修正/待修正 |

## 11. 追溯矩陣

| 原始碼檔案 | 對應 API | 對應邏輯 | 對應資料表 |
|-----------|---------|---------|-----------|
| src/{path} | API-001 | LOGIC-001 | TBL-001 |
