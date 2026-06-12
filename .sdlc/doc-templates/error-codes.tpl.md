---
document_id: "ERRCODES-SHARED-v1.0"
title: "共用錯誤碼表"
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

# 共用錯誤碼表

> **用途**: 統一跨 TASK 的錯誤碼定義，避免不同 TASK 對相同錯誤使用不同碼。
> **維護者**: PM（SD 階段 approved 後更新）。
> **角色存取**: SD 唯讀（設計新 API 時引用已有碼、新增碼時確認不重複）、BE 唯讀（實作時引用）。
> **規範依據**: `MASTER-INDEX.md` §2.4、`~/.claude/sdlc/protocols/rule-08-id-naming.md` (Rule 8)。

## 1. ID 規範

| 欄位 | 格式 | 範例 |
|------|------|------|
| 正式 ID | `ERR-{DOMAIN}-NNN`（3 位零填充，MASTER-INDEX.md 規範）| `ERR-AUTH-001` |
| 程式別名（alias）| `ERR_{DOMAIN}_{SEMANTIC}`（SNAKE_CASE，用於 BE 原始碼常數名）| `ERR_AUTH_TOKEN_EXPIRED` |

- 兩者一對一對應，正式 ID 是權威
- 跨 TASK 新增必須確認 ID 不與現有碼衝突
- DOMAIN 命名空間: AUTH / USER / DATA / SYS / VAL / ORDER / PAY ... （依專案自訂）

## 2. 通用錯誤碼（SYS 域，所有 API 共用）

| ERR-ID | alias | HTTP | 說明 | 定義於 TASK | thrown_by_apis（反向追溯）|
|--------|-------|------|------|-----------|--------------------------|
| ERR-SYS-001 | ERR_UNAUTHORIZED | 401 | 未認證 / Token 過期 | — | — |
| ERR-SYS-002 | ERR_FORBIDDEN | 403 | 無權限存取 | — | — |
| ERR-SYS-003 | ERR_NOT_FOUND | 404 | 資源不存在 | — | — |
| ERR-SYS-004 | ERR_VALIDATION | 400 | 請求參數驗證失敗 | — | — |
| ERR-SYS-005 | ERR_INTERNAL | 500 | 伺服器內部錯誤 | — | — |

**發號方式**: scan-based（Rule 8.7）— 由 PM 執行 `bash scripts/sdlc-id-scan.sh <PREFIX>` 取 max + 1

## 3. 業務錯誤碼（按 DOMAIN 分類）

### 3.1 AUTH（認證授權）

| ERR-ID | alias | HTTP | 說明 | 觸發條件 | 定義於 TASK | thrown_by_apis |
|--------|-------|------|------|---------|-----------|----------------|

**發號方式**: scan-based（Rule 8.7）— 由 PM 執行 `bash scripts/sdlc-id-scan.sh <PREFIX>` 取 max + 1

### 3.2 USER（使用者）

| ERR-ID | alias | HTTP | 說明 | 觸發條件 | 定義於 TASK | thrown_by_apis |
|--------|-------|------|------|---------|-----------|----------------|

**發號方式**: scan-based（Rule 8.7）— 由 PM 執行 `bash scripts/sdlc-id-scan.sh <PREFIX>` 取 max + 1

### 3.3 DATA（資料）

| ERR-ID | alias | HTTP | 說明 | 觸發條件 | 定義於 TASK | thrown_by_apis |
|--------|-------|------|------|---------|-----------|----------------|

**發號方式**: scan-based（Rule 8.7）— 由 PM 執行 `bash scripts/sdlc-id-scan.sh <PREFIX>` 取 max + 1

### 3.4 VAL（驗證）

| ERR-ID | alias | HTTP | 說明 | 觸發條件 | 定義於 TASK | thrown_by_apis |
|--------|-------|------|------|---------|-----------|----------------|

**發號方式**: scan-based（Rule 8.7）— 由 PM 執行 `bash scripts/sdlc-id-scan.sh <PREFIX>` 取 max + 1

### 3.5 其他 DOMAIN（按需新增）

> 新增 DOMAIN 需在此登記並在 `id-registry.md` 的 ERR 段同步。

| DOMAIN | 用途 | 首次使用 TASK |
|--------|------|-------------|

## 4. 跳號與重用規則

- **不可跳號**: 同 DOMAIN 內 NNN 必須連續（`ERR-AUTH-001` 後必須是 `ERR-AUTH-002`）
- **永不重用**: 刪除的錯誤碼標記 `[DEPRECATED: TASK-NNN]`，不從表中移除
- **alias 唯一**: 同一 alias 不可對應多個 ERR-ID
- 違反 → 由 `scripts/sdlc-id-guard.sh` 攔截

## 5. 反向追溯（thrown_by_apis）

每當 SD 在 `api-spec.md` 宣告某 API 可能拋出某錯誤碼時，PM 必須更新對應 ERR 的 `thrown_by_apis` 欄位。

範例：
- API-001 (`POST /api/auth/login`) 可能拋出 ERR-AUTH-001, ERR-VAL-001
- → 更新 `ERR-AUTH-001.thrown_by_apis += [API-001]`
- → 更新 `ERR-VAL-001.thrown_by_apis += [API-001]`

查詢場景：「我想刪除 ERR-AUTH-001，哪些 API 會受影響？」→ 直接看 `thrown_by_apis` 欄位。

## 6. 更新規則

1. **SD 職責**: 設計新 API 時先查本表，已有的錯誤碼直接引用（alias），新錯誤碼確認不重複後新增
2. **PM 職責**: SD approved 後
   - 從 `api-spec.md` 萃取新錯誤碼，在本表登記 ERR-ID + alias
   - 同步更新 `id-registry.md` 的 ERR 段
   - 回填 `thrown_by_apis` 欄位
3. **BE 職責**: 實作時從本表引用錯誤碼常數（alias），禁止自行發明新碼
4. **SD-ERR 整合驗證**: 每個出現在 `api-spec.yaml` 的錯誤碼必須在本表登記；每個本表的 ERR 必須至少有一個 `thrown_by_apis`
