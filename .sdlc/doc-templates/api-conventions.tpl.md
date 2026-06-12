---
document_id: "APICON-CONVENTIONS-v1.0"
title: "API 慣例規範"
version: "1.0"
date: "{YYYY-MM-DD}"
author: "PM"
status: "Living Document (Layer 2 conventions/)"
phase: "conventions"
locked_at: "{ISO time set by /sdlc:init Step 4.15 — empty / placeholder = unlocked}"
change_history:
  - version: "1.0"
    date: "{YYYY-MM-DD}"
    changes: "PR 5: 從 shared/ 遷移到 conventions/，加入 locked_at + RFC 流程"
    author: "PM"
---

# API 慣例規範（Layer 2 / conventions）

> **用途**: 跨 TASK 統一 API 風格（命名、格式、認證、分頁、錯誤處理）。
>
> **生效時機**: `/sdlc:init` 鎖定後 SD / BE 必遵守。違規由 Tester 攔截。修改需要走 RFC 流程（見文末）。
>
> **角色存取**: SD 唯讀（設計新 API 時遵循）/ BE 唯讀（實作時遵循）。

## 1. URL 命名慣例

| 規則 | 範例 | 說明 |
|------|------|------|
| 資源名用複數 | `/api/users` | 不用 `/api/user` |
| 小寫 kebab-case | `/api/user-roles` | 不用 camelCase |
| 巢狀資源用路徑 | `/api/users/:id/roles` | 不用 query param |

## 2. Query Parameter 命名

| 用途 | 參數名 | 範例 | 說明 |
|------|--------|------|------|
| 分頁 | `page`, `pageSize` | `?page=1&pageSize=20` | 統一命名 |
| 排序 | `sortBy`, `sortOrder` | `?sortBy=createdAt&sortOrder=desc` | |
| 搜尋 | `keyword` | `?keyword=test` | 統一用 keyword |
| 篩選 | `{field}` | `?status=active` | 欄位名直接作為參數 |

## 3. Response 格式

### 成功回應
```json
{
  "data": { ... },
  "message": "操作成功"
}
```

### 列表回應（含分頁）
```json
{
  "data": [ ... ],
  "pagination": {
    "page": 1,
    "pageSize": 20,
    "total": 100,
    "totalPages": 5
  }
}
```

### 錯誤回應
```json
{
  "error": {
    "code": "ERR_XXXX",
    "message": "人類可讀的錯誤訊息"
  }
}
```

## 4. 認證方式

| 方式 | Header | 說明 |
|------|--------|------|
| Bearer Token | `Authorization: Bearer {token}` | 預設認證方式 |

## 5. HTTP 狀態碼慣例

| 狀態碼 | 用途 |
|--------|------|
| 200 | 成功（GET / PUT / PATCH） |
| 201 | 成功建立（POST） |
| 204 | 成功刪除（DELETE） |
| 400 | 請求格式錯誤 / 驗證失敗 |
| 401 | 未認證 |
| 403 | 無權限 |
| 404 | 資源不存在 |
| 409 | 資源衝突 |
| 500 | 伺服器內部錯誤 |

## 6. 更新規則

1. **首次建立**: `/sdlc:init` 從本模板複製到 `.sdlc/conventions/api-conventions.md`，預設留 `[CUSTOMIZE]` 標記讓 PM 在 init 時填入專案具體選擇
2. **鎖定**: PM 在 `/sdlc:init` 流程結束時把 `locked_at` 寫入當前 ISO 時間
3. **後續 TASK**: SD 設計新 API 時必須遵循本表慣例（違規由 Tester 攔截）
4. **慣例變更（RFC 流程）**:
   - 提案者開 issue / PR 描述變更原因 + 影響範圍
   - PM + 至少一個 SD 同意
   - 通過後更新 `change_history`，bump `version`
   - 通知所有 in_progress TASK 的 SD 重新檢視 api-spec.md
