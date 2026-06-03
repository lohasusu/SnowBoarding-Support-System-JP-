---
document_id: "APICON-CONVENTIONS-v1.1"
title: "API 慣例規範"
version: "1.1"
date: "2026-06-03"
author: "PM"
status: "Living Document (Layer 2 conventions/)"
phase: "conventions"
locked_at: "2026-06-03T09:30:00Z"
change_history:
  - version: "1.0"
    date: "2026-06-03"
    changes: "init: 從模板 cp + lock"
    author: "PM"
  - version: "1.1"
    date: "2026-06-03"
    changes: "init customization pass — 認證方式改為 HTTP-only cookie（對齊既有實作）；URL 命名加註 brownfield grandfather；其他 [CUSTOMIZE] 已填"
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

> **Brownfield grandfather**: 既有 28 個端點（如 `/api/ski/*`, `/api/flight/*`, `/api/auth/*`）採用單數資源名，列為已知違反但**不重寫**（會破壞 production URL + DESIGN.md 對外文件）。本規則適用於**新增**端點 — TASK-001 後所有新 REST 資源必須複數。

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

| 方式 | 載體 | 說明 |
|------|------|------|
| **JWT in HTTP-only Cookie** | `Cookie: access_token={jwt}` | 預設認證方式 — Cookie 屬性: `HttpOnly`, `Secure`（prod）, `SameSite=Lax`, `Max-Age=604800`（7 天） |

**為什麼選 cookie 而非 Bearer**:
- 既有實作（`web/auth/auth_router.py:117+`）已用 cookie，本專案是 server-rendered Jinja2 應用，沒有 SPA 跨 origin 需求
- HttpOnly cookie 對 XSS 攻擊更安全（JS 讀不到 token）
- 若未來轉 Vue SPA 跨 origin 部署，再評估是否走 `Authorization: Bearer` + CSRF token 配對

**禁止**: 同時用 cookie 與 Authorization header 認證同一端點（攻擊面變大）。

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
