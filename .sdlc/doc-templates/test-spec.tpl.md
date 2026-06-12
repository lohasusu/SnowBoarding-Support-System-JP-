---
document_id: "TESTSPEC-{TASK_ID}-v1.0"
title: "測試規格（TDD 模式）"
version: "1.0"
date: "{YYYY-MM-DD}"
author: "SD"
status: "Draft"
task_id: "{TASK-ID}"
phase: "sd"
source_documents:
  - "API-{TASK_ID}-v1.0"
  - "LOGIC-{TASK_ID}-v1.0"
change_history:
  - version: "1.0"
    date: "{YYYY-MM-DD}"
    changes: "初始版本"
    author: "SD"
approval:
  reviewer: "PM"
  date: ""
  result: "Pending"
  notes: ""
---

# 測試規格（TDD 模式 — 開發前撰寫）

> 此文件僅在 TDD 模式下產出。測試必須在實作之前完成。

## 1. 測試總覽

| 測試類型 | 數量 | 對應 API |
|---------|------|---------|
| 單元測試 | {N} | - |
| 整合測試 | {N} | API-001 ~ API-xxx |
| E2E 測試 | {N} | 全流程 |

## 2. 測試規格

### TEST-001: {測試名稱}
- **對應 API**: API-001
- **測試類型**: 整合測試
- **對應規格**: @traces_to(API-001)

#### 前置條件
```
- 測試資料庫已建立
- 測試資料: {描述 seed data}
- 環境變數: {必要環境變數}
```

#### 正向測試

| # | 測試案例 | 輸入 | 預期結果 |
|---|---------|------|---------|
| 1 | 成功場景 | POST /api/{resource} `{request_body}` | 201 + `{response_body}` |
| 2 | {其他場景} | {輸入} | {預期} |

#### 負向測試

| # | 測試案例 | 輸入 | 預期結果 | 對應錯誤碼 |
|---|---------|------|---------|-----------|
| 1 | 空必填欄位 | `{"field": ""}` | 400 INVALID_INPUT | {error_code} |
| 2 | 無效格式 | `{"email": "not-email"}` | 400 INVALID_INPUT | {error_code} |
| 3 | 未認證 | 無 Authorization header | 401 UNAUTHORIZED | {error_code} |
| 4 | 資源不存在 | GET /api/{resource}/999 | 404 NOT_FOUND | {error_code} |

#### 邊界測試

| # | 測試案例 | 輸入 | 預期結果 |
|---|---------|------|---------|
| 1 | 最大長度 | `{"name": "a".repeat(255)}` | 201 成功 |
| 2 | 超過最大長度 | `{"name": "a".repeat(256)}` | 400 錯誤 |
| 3 | 特殊字元 | `{"name": "<script>alert(1)</script>"}` | 400 或正確轉義 |
| 4 | 空集合 | GET /api/{resource}?page=1 （無資料） | 200 + `{"data":[],"meta":{...}}` |

### TEST-002: {測試名稱}
{同上格式}

## 3. 測試程式碼骨架

```typescript
// TEST-001: {測試名稱}
describe('API-001: {API 名稱}', () => {
  // @traces_to(API-001)

  beforeAll(async () => {
    // 前置條件設定
  });

  afterAll(async () => {
    // 清理
  });

  // 正向測試
  describe('成功場景', () => {
    it('should {預期行為}', async () => {
      // Arrange
      const input = { /* from TEST-001 正向測試 #1 */ };

      // Act
      const response = await request(app)
        .post('/api/{resource}')
        .send(input);

      // Assert
      expect(response.status).toBe(201);
      expect(response.body).toMatchObject({ /* 預期結構 */ });
    });
  });

  // 負向測試
  describe('錯誤場景', () => {
    it('should return 400 for empty required field', async () => {
      // from TEST-001 負向測試 #1
    });

    it('should return 401 for unauthenticated request', async () => {
      // from TEST-001 負向測試 #3
    });
  });

  // 邊界測試
  describe('邊界案例', () => {
    it('should handle maximum length input', async () => {
      // from TEST-001 邊界測試 #1
    });
  });
});
```

## 4. 追溯矩陣

| 測試ID | 對應 API | 對應邏輯 | 來源需求 |
|--------|---------|---------|---------|
| TEST-001 | API-001 | LOGIC-001 | FR-001 |

## 5. 品質指標

| 指標 | 目標 |
|------|------|
| 正向測試覆蓋 | 每個 API 至少 1 個 |
| 負向測試比率 | ≥ 30% |
| 邊界測試 | 每個驗證規則至少 1 個 |
| 行覆蓋率 | > 80% |
| 分支覆蓋率 | > 70% |
