---
document_id: "FUNC-{TASK_ID}-v1.0"
title: "功能流程圖"
version: "1.0"
date: "{YYYY-MM-DD}"
author: "SA"
status: "Draft"
task_id: "{TASK-ID}"
phase: "sa"
source_documents:
  - "REQ-{TASK_ID}-v1.0"
  - "ARCH-{TASK_ID}-v1.0"
change_history:
  - version: "1.0"
    date: "{YYYY-MM-DD}"
    changes: "初始版本"
    author: "SA"
approval:
  reviewer: "PM"
  date: ""
  result: "Pending"
  notes: ""
---

# 功能流程圖

## 1. 功能清單

| 功能ID | 功能名稱 | 描述 | 所屬模組 | 來源需求 | 優先順序 |
|--------|---------|------|---------|---------|---------|
| FUNC-001 | {功能名稱} | {描述} | MOD-001 | FR-001 | P0 |
| FUNC-002 | {功能名稱} | {描述} | MOD-001 | FR-002 | P1 |

## 2. 功能流程

### FUNC-001: {功能名稱}
- **觸發**: {觸發條件}
- **輸入**: {輸入資料}
- **輸出**: {輸出資料}
- **前置條件**: {必須滿足的條件}

#### 系統流程圖

```mermaid
sequenceDiagram
    actor User as 使用者
    participant FE as 前端
    participant BE as 後端
    participant DB as 資料庫

    User->>FE: {動作}
    FE->>BE: {API 呼叫}
    BE->>DB: {資料操作}
    DB-->>BE: {回傳}
    BE-->>FE: {回應}
    FE-->>User: {顯示}
```

#### 狀態轉換圖（如適用）

```mermaid
stateDiagram-v2
    [*] --> 初始狀態
    初始狀態 --> 處理中: {事件}
    處理中 --> 完成: {條件}
    處理中 --> 失敗: {錯誤}
    完成 --> [*]
    失敗 --> 初始狀態: {重試}
```

### FUNC-002: {功能名稱}
{同上格式}

## 3. 功能關係圖

```mermaid
graph TD
    FUNC001["FUNC-001<br/>{功能名稱}"] --> FUNC002["FUNC-002<br/>{功能名稱}"]
    FUNC001 --> FUNC003["FUNC-003<br/>{功能名稱}"]
```

## 4. 追溯矩陣

| 功能ID | 來源需求 | 所屬模組 | 相關業務流程 |
|--------|---------|---------|------------|
| FUNC-001 | FR-001 | MOD-001 | BF-001 |
| FUNC-002 | FR-002 | MOD-001 | BF-001, BF-002 |
