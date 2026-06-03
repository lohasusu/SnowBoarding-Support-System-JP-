---
document_id: "BEIDX-SHARED-v1.0"
title: "BE 領域索引"
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

# BE 領域索引

> **用途**: 追蹤 BE 實作狀態 — 每個 SD 定義的 API/TBL/LOGIC 是否已實作、由誰實作、位於哪些檔案。
> **BE 不產生新 ID**: 只實作 SD 定義的 ID。本表是「實作映射」，不是「ID 登記」。
> **維護者**: PM（BE approved 後更新）。
> **角色存取**: FE 唯讀（確認 BE 已完成該 API）；Tester 唯讀（測試覆蓋率計算）。
> **規範依據**: `MASTER-INDEX.md` §2.5、`rules/sdlc-be.md`。

## 1. API 實作狀態

| API-ID | 方法 | 路徑 | 實作檔案 | 狀態 | 實作於 TASK | OpenAPI 合規 | Swagger UI 可測 |
|--------|------|------|---------|------|------------|--------------|----------------|
| API-001 | POST | /api/auth/login | src/handlers/auth.go | implemented | TASK-001 | ✓ | ✓ |

**狀態值**: `implemented` / `partial` / `not_started` / `blocked`

## 2. Migration 狀態

| Migration 檔名 | 對應 TBL | 所屬 TASK | up 可執行 | down 可執行 | 冪等性驗證 |
|---------------|---------|----------|----------|------------|-----------|
| 20260414_010000_create_users.sql | TBL-001 | TASK-001 | ✓ | ✓ | ✓ |

## 3. LOGIC 實作位置

| LOGIC-ID | 實作檔案 / 函式 | 所屬 TASK | 單元測試檔案 |
|----------|----------------|----------|--------------|

## 4. ENTITY → 資料表映射

| ENTITY-ID | TBL-ID | ORM Model 檔案 | 索引清單 |
|-----------|--------|---------------|---------|

## 5. 實作範圍圍欄（TASK 範圍）

> 依 `rules/sdlc-be.md` 規則 7，BE 只能修改當前 TASK 的 SD 授權範圍。本節記錄每個 TASK 的授權檔案清單。

| TASK | 授權修改的檔案 / 目錄 | 授權來源（SD 文件位置）|
|------|--------------------|---------------------|

## 更新規則

1. **BE approved** → PM 從 `backend-report.md` 萃取實作狀態更新本表
2. **OpenAPI 合規欄位**: 必須與 `api-spec.yaml` 一致，違規由 Build Gate 攔截
3. **Migration 欄位**: 必須由 Tester 實際執行 up/down/up 三步驟驗證後才可標記 ✓
