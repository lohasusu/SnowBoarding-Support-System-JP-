---
document_id: "SDIDX-SHARED-v1.0"
title: "SD 領域 ID 總表"
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

# SD 領域 ID 總表

> **用途**: 彙整 SD 階段所有產出 ID —「有哪些 API、資料表、邏輯、錯誤碼，誰呼叫/對應」。
> **維護者**: PM（SD approved 後更新）。
> **角色存取**: 所有角色唯讀；FE/BE 實作前 MANDATORY 讀取。
> **規範依據**: `MASTER-INDEX.md` §2.4、`~/.claude/sdlc/protocols/rule-08-id-naming.md` (Rule 8)。

## 1. API（介面）

| API-ID | 方法 | 路徑 | 首次定義於 TASK | 操作 ENTITY | 可能拋出 ERR | 呼叫自 COMP（反向追溯）|
|--------|------|------|---------------|-------------|-------------|------------------------|

**發號方式**: scan-based（Rule 8.7）— 由 PM 執行 `bash scripts/sdlc-id-scan.sh <PREFIX>` 取 max + 1（全域連續）

### 1.1 OpenAPI 對應

> 每個 API-ID 必須在 `api-spec.yaml` 中有對應的 path + operation。

| API-ID | OpenAPI path | operationId | 測試於（TEST-ID）|
|--------|-------------|-------------|-----------------|

## 2. TBL（資料表）

| TBL-ID | 名稱 | 首次定義於 TASK | 對應 ENTITY | Migration 檔名 |
|--------|------|---------------|-------------|---------------|

**發號方式**: scan-based（Rule 8.7）— 由 PM 執行 `bash scripts/sdlc-id-scan.sh <PREFIX>` 取 max + 1（全域連續）

## 3. LOGIC（業務邏輯）

| LOGIC-ID | 名稱 | 所屬 TASK | 實作 BR | 被哪些 API 呼叫 |
|----------|------|----------|---------|----------------|

**範圍**: TASK 內編號

## 4. ERR（錯誤碼）

格式: `ERR-{DOMAIN}-NNN`。完整清單見 `shared/error-codes.md`。

| ERR-ID | HTTP | 訊息 | 首次定義於 TASK | thrown_by_apis（反向追溯）|
|--------|------|------|---------------|--------------------------|
| ERR-AUTH-001 | 401 | {訊息} | TASK-001 | API-001, API-002 |
| ERR-USER-001 | 404 | {訊息} | TASK-001 | API-003 |

**DOMAIN 命名空間**: AUTH / USER / DATA / SYS / VAL 等，由 PM 決定

## 5. 依賴關係圖

```
FUNC (SA)
  └─ 實作為 → API (SD)
                ├─ 操作 → ENTITY (SA) → TBL (SD)
                ├─ 呼叫 → LOGIC (SD) → 實作 BR (BA)
                └─ 拋出 → ERR (SD)
                            ↑ (反向) 呼叫自 COMP (UIUX)
```

## 更新規則

1. **SD approved** → PM 從 `api-spec.md`、`api-spec.yaml`、`db-schema.md`、`logic-flow.md` 萃取 ID
2. **反向追溯 ERR.thrown_by_apis**: SD 定義 ERR 時需列出會拋出的 API
3. **反向追溯 API.呼叫自 COMP**: FE 的 fe-api-mapping 產出後 PM 回填
4. **API 變更**: 已發布的 API 變更需走 Rule 6 跨 TASK 修改協議
