---
document_id: "API-{TASK_ID}-v1.0"
title: "API 規格書"
version: "1.0"
date: "{YYYY-MM-DD}"
author: "SD"
status: "Draft"
task_id: "{TASK-ID}"
phase: "sd"
source_documents:
  - "FUNC-{TASK_ID}-v1.0"
  - "FIELD-{TASK_ID}-v1.0"
  - "COMP-{TASK_ID}-v1.0"
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

# API 規格書

## 1. API 總覽

| API ID | 方法 | 路徑 | 說明 | 對應功能 | 認證 |
|--------|------|------|------|---------|------|
| API-001 | POST | /api/{resource} | {說明} | FUNC-001 | 是/否 |
| API-002 | GET | /api/{resource} | {說明} | FUNC-002 | 是 |

## 2. 共用定義

### 2.1 認證方式
- 方式: {JWT / Session / API Key}
- Header: `Authorization: Bearer {token}`
- Token 有效期: {時間}

### 2.2 共用錯誤格式
```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "人類可讀的錯誤訊息",
    "details": {}
  }
}
```

### 2.3 分頁格式
```json
{
  "data": [],
  "meta": {
    "page": 1,
    "pageSize": 20,
    "total": 100,
    "totalPages": 5
  }
}
```

## 3. API 詳細規格

### API-001: {API 名稱}
- **方法**: POST
- **路徑**: `/api/{resource}`
- **說明**: {詳細說明}
- **對應功能**: FUNC-001
- **認證**: 是/否

#### Request

**Headers**:
| Header | 值 | 必填 |
|--------|-----|------|
| Content-Type | application/json | 是 |
| Authorization | Bearer {token} | 是 |

**Body**:
| 欄位 | 類型 | 必填 | 驗證規則 | 說明 |
|------|------|------|---------|------|
| {欄位名} | string | 是 | {規則} | {說明} |
| {欄位名} | number | 否 | {規則} | {說明} |

**Request 範例**:
```json
{
  "field1": "value1",
  "field2": 123
}
```

#### Response

**成功回應 (200/201)**:
| 欄位 | 類型 | 說明 | DB 來源 |
|------|------|------|---------|
| id | string | 唯一識別碼 | {table}.id |
| {欄位名} | string | {說明} | {table}.{column} |

**Response 範例**:
```json
{
  "id": "uuid-xxx",
  "field1": "value1",
  "createdAt": "2026-01-01T00:00:00Z"
}
```

#### 錯誤碼

| HTTP Status | Error Code | 觸發條件 | 回應範例 |
|-------------|-----------|---------|---------|
| 400 | INVALID_INPUT | {觸發條件} | `{"error":{"code":"INVALID_INPUT","message":"..."}}` |
| 401 | UNAUTHORIZED | 未提供 token 或 token 過期 | |
| 404 | NOT_FOUND | {觸發條件} | |
| 409 | CONFLICT | {觸發條件} | |
| 500 | INTERNAL_ERROR | 伺服器內部錯誤 | |

#### 業務邏輯步驟

```
1. 驗證 Request Body
   → 欄位驗證失敗 → 400 INVALID_INPUT
2. 驗證認證 Token
   → Token 無效 → 401 UNAUTHORIZED
3. {業務邏輯步驟}
   → {條件} → {結果}
4. 寫入資料庫
   → {衝突條件} → 409 CONFLICT
5. 回傳成功回應
```

### API-002: {API 名稱}
{同上格式}

## 4. FE-API 映射表

| UIUX 元件 | 元件 Props | UI Copy（按鈕/標籤/Tooltip/驗證訊息） | 對應 API | Response 欄位 | 轉換邏輯 |
|-----------|-----------|--------------------------------------|---------|---------------|---------|
| {元件名} | {props} | {按鈕文字/標籤/Tooltip/錯誤訊息} | API-001 | {欄位} | {轉換邏輯} |

## 5. 追溯矩陣

| API ID | 對應功能 | 來源需求 |
|--------|---------|---------|
| API-001 | FUNC-001 | FR-001 |
| API-002 | FUNC-002 | FR-002 |

## 6. OpenAPI 3.0 規格

> 本章節的 YAML 內容必須同步產出為獨立檔案 `api-spec.yaml`。
> 此為機器可讀的 API 合約，BE 和 FE 開發時必須遵循。

```yaml
openapi: "3.0.3"
info:
  title: "{專案名稱} API"
  version: "1.0.0"
  description: "Generated from SD api-spec.md"
servers:
  - url: "http://localhost:{port}"
    description: "Development"

paths:
  /api/{resource}:
    post:
      operationId: "API-001"
      summary: "{說明}"
      tags: ["{功能模組}"]
      security:
        - bearerAuth: []
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: "#/components/schemas/{Resource}CreateRequest"
            example:
              field1: "value1"
              field2: 123
      responses:
        "201":
          description: "建立成功"
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/{Resource}Response"
              example:
                id: "uuid-xxx"
                field1: "value1"
                createdAt: "2026-01-01T00:00:00Z"
        "400":
          $ref: "#/components/responses/BadRequest"
        "401":
          $ref: "#/components/responses/Unauthorized"

    get:
      operationId: "API-002"
      summary: "{說明}"
      tags: ["{功能模組}"]
      parameters:
        - name: page
          in: query
          schema:
            type: integer
            default: 1
        - name: pageSize
          in: query
          schema:
            type: integer
            default: 20
      responses:
        "200":
          description: "查詢成功"
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/{Resource}ListResponse"

components:
  schemas:
    {Resource}CreateRequest:
      type: object
      required: [field1]
      properties:
        field1:
          type: string
          description: "{說明}"
          example: "value1"
        field2:
          type: number
          description: "{說明}"
          example: 123

    {Resource}Response:
      type: object
      properties:
        id:
          type: string
          format: uuid
        field1:
          type: string
        createdAt:
          type: string
          format: date-time

    {Resource}ListResponse:
      type: object
      properties:
        data:
          type: array
          items:
            $ref: "#/components/schemas/{Resource}Response"
        meta:
          $ref: "#/components/schemas/PaginationMeta"

    PaginationMeta:
      type: object
      properties:
        page:
          type: integer
        pageSize:
          type: integer
        total:
          type: integer
        totalPages:
          type: integer

    ErrorResponse:
      type: object
      properties:
        error:
          type: object
          properties:
            code:
              type: string
            message:
              type: string
            details:
              type: object

  securitySchemes:
    bearerAuth:
      type: http
      scheme: bearer
      bearerFormat: JWT

  responses:
    BadRequest:
      description: "請求參數錯誤"
      content:
        application/json:
          schema:
            $ref: "#/components/schemas/ErrorResponse"
          example:
            error:
              code: "INVALID_INPUT"
              message: "欄位驗證失敗"
    Unauthorized:
      description: "未認證"
      content:
        application/json:
          schema:
            $ref: "#/components/schemas/ErrorResponse"
          example:
            error:
              code: "UNAUTHORIZED"
              message: "Token 無效或已過期"
```

### 合規檢查清單

- [ ] `openapi: "3.0.3"` 版本宣告正確
- [ ] 每個 API-NNN 在 `paths` 中都有對應的 operation
- [ ] 每個 operation 有 `operationId` 對應 API ID
- [ ] 所有 `$ref` 引用的 schema 在 `components/schemas` 中存在
- [ ] 所有 example 符合對應的 schema 定義
- [ ] 認證方式與第 2.1 節一致
- [ ] 錯誤格式與第 2.2 節一致
- [ ] 分頁格式與第 2.3 節一致
