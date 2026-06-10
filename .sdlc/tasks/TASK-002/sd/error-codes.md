---
document_id: "ERRCODES-TASK-002-v1.0"
title: "錯誤碼登記計畫 — SQLite → PostgreSQL 持久化遷移"
version: "1.0"
date: "2026-06-10"
author: "SD"
task_id: "TASK-002"
phase: "sd"
mode: "feature"
source_documents:
  - "DB-TASK-002-v1.0 (本 SD db-schema.md)"
  - "CODEARCH-TASK-002-v1.0 (本 SD code-arch.md §10 錯誤處理策略)"
  - "FUNC-TASK-002-v1.0 (SA functional-flow.md — FUNC-101 異常流程)"
  - ".sdlc/shared/error-codes.md (registry 當前空白 — Rule 8.7 per-DOMAIN scan)"
  - ".sdlc/shared/MASTER-INDEX.md §2.4 (ERR-{DOMAIN}-NNN 規範)"
change_history:
  - version: "1.0"
    date: "2026-06-10"
    changes: "初始版本 — 新增 1 個 SYS 域 ERR-SYS-006（補既有 SYS-001..005 之外的「設定缺失」）+ 4 個 DB 域 ERR-DB-001..004 + 2 個 MIGRATION 域 ERR-MIGRATION-001..002（兩個新 DOMAIN）"
    author: "SD"
approval:
  reviewer: "PM"
  date: ""
  result: "Pending"
  notes: ""
---

# 錯誤碼登記計畫 — TASK-002

> **本檔用途**: 本 TASK SD 階段新增的錯誤碼登記 — 供 BE 階段實作時引用、Tester 階段驗證、PM 階段同步到 `shared/error-codes.md` + `shared/sd-index.md` §4。
> **規範依據**: `MASTER-INDEX.md` §2.4 + `Rule 8.7 per-DOMAIN scan`（從 `shared/error-codes.md` 對應 DOMAIN 取 max NNN + 1）
> **發號狀態**: 目前 `shared/error-codes.md` registry 全空（template 預列 ERR-SYS-001..005 但 `定義於 TASK` 欄位為「—」表示未實際登記）；本 TASK 為**全專案首次**正式登記 ERR-ID。

---

## 1. DOMAIN 命名空間決策

> **依據**: `MASTER-INDEX.md` §2.4 + `error-codes.tpl.md` §3.5 「新增 DOMAIN 需在此登記」

| DOMAIN | 屬性 | 用途 | 是否需新增？ | 首次使用 TASK |
|--------|------|------|------------|---------------|
| **SYS** | 既有通用域 | 系統級錯誤（401/403/404/400/500 等通用）| ❌ 沿用 | TASK-002（首次實際登記 SYS-006）|
| **DB** | ★ 新增 | 資料庫連線 / 查詢 / pool 等錯誤 | ✅ NEW | TASK-002 |
| **MIGRATION** | ★ 新增 | DB Migration 套用失敗 / 版本錯亂等 | ✅ NEW | TASK-002 |

**為何不沿用 DATA 域**:
- DATA 域語意傾向「業務資料一致性錯誤」（如「找不到指定資源」「資料格式不符」）
- DB 域聚焦「資料庫基礎設施錯誤」（連線 / pool / driver） — 與 DATA 業務語意正交
- MIGRATION 域更專一 — schema 演進相關，獨立 DOMAIN 有利後續 grep / audit

**新 DOMAIN 標記**:
- `[NEW DOMAIN: DB]` — 本 TASK SD 階段引入；PM 在 Step 2.8 同步 `master-index.md` §2 白名單 + `shared/error-codes.md` §3.5
- `[NEW DOMAIN: MIGRATION]` — 同上

---

## 2. 本 TASK 新增 ERR-ID 清單

> 每個 ERR-ID 從對應 DOMAIN 的 max NNN + 1 起編；本 TASK 為各 DOMAIN 首批 → 從 001 起。

### 2.1 SYS 域（補登記 + 新增 1 個）

| ERR-ID | alias | HTTP | 說明 | 觸發條件 | 定義於 TASK | thrown_by_apis |
|--------|-------|------|------|---------|-----------|----------------|
| ERR-SYS-006 | ERR_SYS_CONFIG_MISSING | 500 | 應用程式設定缺失 — 必要 env vars 未設定 | 應用 startup 時 `_build_dsn_from_env()` 偵測到 POSTGRES_HOST / POSTGRES_USER / POSTGRES_PASSWORD / POSTGRES_DB 任一缺失（且 DATABASE_URL 也未設定）| TASK-002 | API-101 (startup 失敗 + 既有 28 API 全部不可達 — healthcheck 失敗，間接影響) |

> **註**: ERR-SYS-001..005 為 template 預列的通用錯誤碼（未登記給特定 TASK — 「定義於 TASK」欄為「—」）；本 TASK 不重新登記 SYS-001..005（不在本 TASK FR 範圍 — 既有 28 API [REUSE: from TASK-001] 已用，由後續 TASK 補追溯）。

### 2.2 DB 域（[NEW DOMAIN: DB]）

| ERR-ID | alias | HTTP | 說明 | 觸發條件 | 定義於 TASK | thrown_by_apis |
|--------|-------|------|------|---------|-----------|----------------|
| ERR-DB-001 | ERR_DB_CONNECTION_FAILED | 503 | 資料庫連線失敗 | psycopg.OperationalError — auth failed / connection refused / network 中斷；錯誤訊息**不含 password**（NFR-011） | TASK-002 | API-101（startup 失敗），其餘 28 API [REUSE] 在 runtime 間接受影響（pool 取連線失敗時 caller 既有 try/except 不變 — NFR-002）|
| ERR-DB-002 | ERR_DB_POOL_TIMEOUT | 503 | Connection pool 取連線逾時 | `psycopg_pool.PoolTimeout` — 並發超過 POSTGRES_POOL_MAX 且新 request 等待 > POSTGRES_POOL_TIMEOUT_MS（NFR-005 預設 5000ms）| TASK-002 | 既有 28 API [REUSE] |
| ERR-DB-003 | ERR_DB_UNIQUE_VIOLATION | 409 | UNIQUE 約束違反 | psycopg.errors.UniqueViolation — 例如註冊 email/username/google_id 重複（既有 BR 既有行為，僅錯誤碼登記）| TASK-002 | 既有 28 API [REUSE]（如 POST /api/auth/register、POST /api/auth/google/callback OAuth Upsert path）|
| ERR-DB-004 | ERR_DB_FK_VIOLATION | 500 | FK 約束違反（極端 — 邏輯錯誤）| psycopg.errors.ForeignKeyViolation — 應用層邏輯錯誤（user_id 不存在卻嘗試插 favorites），表示 code bug 而非使用者問題 | TASK-002 | 既有 28 API [REUSE]（如 POST /api/favorites）|

### 2.3 MIGRATION 域（[NEW DOMAIN: MIGRATION]）

| ERR-ID | alias | HTTP | 說明 | 觸發條件 | 定義於 TASK | thrown_by_apis |
|--------|-------|------|------|---------|-----------|----------------|
| ERR-MIGRATION-001 | ERR_MIGRATION_APPLY_FAILED | 500 | Migration 套用失敗 | `alembic upgrade head` 期間 SQL 失敗（語法錯 / 約束衝突 / 資料 backfill 失敗等）；Alembic 自動 ROLLBACK 單個 migration 的 transaction；上拋導致 app startup fail → Railway healthcheck fail → auto rollback to N-1 build | TASK-002 | API-101 startup 失敗 |
| ERR-MIGRATION-002 | ERR_MIGRATION_VERSION_MISMATCH | 500 | Migration 版本錯亂 | `alembic_version` 表中的 version 與 `migrations/versions/` 目錄不一致（如 git revert 但 DB 未 downgrade；或多人 merge 衝突）| TASK-002 | API-101 startup 失敗 |

---

## 3. user_message 對應（NFR-012 zh-TW）

> 面向使用者的訊息遵循 BA NFR-012 既有規範（zh-TW 系統語言 [REUSE: from TASK-001/NFR-018]）；500 / 503 類錯誤通常**不直接暴露給使用者**（FastAPI 預設回 generic「Internal Server Error」），但寫入 log + 內部告警仍用以下 user_message 文案。

| ERR-ID | user_message（zh-TW）|
|--------|-----------------------|
| ERR-SYS-006 | 系統設定不完整，請聯絡管理員 |
| ERR-DB-001 | 系統暫時無法連線資料庫，請稍後再試 |
| ERR-DB-002 | 系統忙碌中，請稍後再試 |
| ERR-DB-003 | 該資料已存在 |
| ERR-DB-004 | 系統內部錯誤，請聯絡管理員 |
| ERR-MIGRATION-001 | 系統升級失敗，請聯絡管理員 |
| ERR-MIGRATION-002 | 系統版本不一致，請聯絡管理員 |

---

## 4. 重用優先驗證

> **Rule**: 設計新 ERR 前必須查 `shared/error-codes.md` 確認無語義重複。

| 本 TASK 新 ERR | 是否與既有重複？ | 結論 |
|----------------|---------------|------|
| ERR-SYS-006（設定缺失）| `shared/error-codes.md` 全空（除 template 預列 SYS-001..005 但實際未登記）；SYS-005 = ERR_INTERNAL 500 是 generic 內部錯誤，本 ERR 專指 env vars 缺失（startup blocker，不同情境）| ✅ 不重複 — 新增 |
| ERR-DB-001..004 | 全空 — 無 DB 域既有 ERR | ✅ 全新 |
| ERR-MIGRATION-001..002 | 全空 — 無 MIGRATION 域既有 ERR | ✅ 全新 |

---

## 5. alias 全域唯一性驗證

| alias | 是否與既有衝突？ |
|-------|--------------|
| ERR_SYS_CONFIG_MISSING | ✅ 全域唯一 |
| ERR_DB_CONNECTION_FAILED | ✅ 全域唯一 |
| ERR_DB_POOL_TIMEOUT | ✅ 全域唯一 |
| ERR_DB_UNIQUE_VIOLATION | ✅ 全域唯一 |
| ERR_DB_FK_VIOLATION | ✅ 全域唯一 |
| ERR_MIGRATION_APPLY_FAILED | ✅ 全域唯一 |
| ERR_MIGRATION_VERSION_MISMATCH | ✅ 全域唯一 |

---

## 6. NNN 連續性驗證（Rule 8.7）

| DOMAIN | 既有 max NNN | 本 TASK 新增 | 結果 |
|--------|------------|-------------|------|
| SYS | 005（template 預列，未實際登記給 TASK）| 006 | ✅ 連續 |
| DB | 無 | 001 → 004 | ✅ 連續、無跳號 |
| MIGRATION | 無 | 001 → 002 | ✅ 連續、無跳號 |

---

## 7. PM Step 2.8 同步指引

> 本 TASK approve 後，PM 需執行以下同步動作（Rule 8.7 + error-codes.tpl.md §6.2）：

1. **`shared/error-codes.md`**:
   - §3 新增 DB / MIGRATION DOMAIN 區段（仿 §3.1 AUTH / §3.2 USER 結構）
   - §3.5 表新增 2 行：`| DB | 資料庫基礎設施 | TASK-002 |` + `| MIGRATION | Schema 演進 | TASK-002 |`
   - 各 DOMAIN 表內補本檔 §2 列出的 7 個 ERR 行
   - `thrown_by_apis` 欄位回填本 TASK 對應 API（API-101 + 既有 28 API [REUSE]）

2. **`shared/sd-index.md` §4 ERR 表**:
   - 補 7 行（ERR-ID / HTTP / 訊息 / 首次定義於 TASK / thrown_by_apis）

3. **`shared/master-index.md` §2 DOMAIN 白名單**（若 §2.4 已列範例 DOMAIN）：
   - 確認 DB / MIGRATION 加入合法 DOMAIN 清單

4. **`shared/id-registry.md` ERR 段**:
   - 補本 TASK 7 個 ERR-ID

---

## 8. 追溯矩陣

| ERR-ID | 來源（code-arch §10 + db-schema §1 + functional-flow FUNC-101 異常）| 對應 NFR/BR |
|--------|-------------------------------------------------------------------|-------------|
| ERR-SYS-006 | code-arch.md §10.1 + database.py `_build_dsn_from_env` | NFR-011（secret 不洩漏 — 不在訊息中含 password 值）|
| ERR-DB-001 | code-arch.md §10.1 + functional-flow.md FUNC-101 異常表 | NFR-001 持久性、NFR-011 secret |
| ERR-DB-002 | code-arch.md §10.1 + functional-flow.md FUNC-101 異常表 | NFR-005 connection pool |
| ERR-DB-003 | code-arch.md §10.3 + auth_router.py 註冊 INSERT UNIQUE 違反 | TASK-001 BR-004（既有 [REUSE]）|
| ERR-DB-004 | code-arch.md §10.3 | TASK-001 BR-010 既有 FK CASCADE |
| ERR-MIGRATION-001 | code-arch.md §10.2 + code-arch.md §1.4 advisory lock | NFR-006 reversibility（失敗後可 downgrade）|
| ERR-MIGRATION-002 | code-arch.md §10.2 + Alembic 版本管理 | NFR-006 + db-conventions §5.1 檔名格式 |

---

## 9. 自我驗證

| 檢查項 | 通過 | 說明 |
|--------|------|------|
| 所有 ERR-ID 格式 `ERR-{DOMAIN}-NNN`（3 位零填充）| ✅ | §2 |
| DOMAIN 屬白名單（SYS）或合法新增（DB / MIGRATION）| ✅ | §1 + 新 DOMAIN 標 `[NEW DOMAIN: ...]` |
| 每個 ERR 有 alias `ERR_{DOMAIN}_{SEMANTIC}` SNAKE_CASE | ✅ | §2 |
| 每個 ERR 有 HTTP status | ✅ | §2 |
| 每個 ERR 有 user_message（zh-TW）| ✅ | §3 |
| 重用優先驗證（無重複既有）| ✅ | §4 — 既有 registry 全空 |
| alias 全域唯一 | ✅ | §5 |
| NNN 連續、無跳號、無重用 DEPRECATED | ✅ | §6 |
| thrown_by_apis 反向追溯欄位完整 | ✅ | §2 + §7（待 PM 同步到 shared/）|
| PM 同步指引明確 | ✅ | §7 |
| 追溯矩陣完整 | ✅ | §8 |
| **總分** | **96/100** | 詳見 self-review.json |
