---
document_id: "API-TASK-002-v1.0"
title: "API 規格書 — SQLite → PostgreSQL 持久化遷移"
version: "1.0"
date: "2026-06-10"
author: "SD"
task_id: "TASK-002"
phase: "sd"
mode: "feature"
source_documents:
  - "ARCH-TASK-002-v1.0 (SA system-arch.md)"
  - "FUNC-TASK-002-v1.0 (SA functional-flow.md — FUNC-101..107)"
  - "DB-TASK-002-v1.0 (本 SD db-schema.md)"
  - "CODEARCH-TASK-002-v1.0 (本 SD code-arch.md — MOD-104 db_bootstrap)"
  - "ERRCODES-TASK-002-v1.0 (本 SD error-codes.md — ERR-DB-* / ERR-MIGRATION-*)"
  - "deploy/service-contract.yaml (services.backend.health_check)"
  - ".sdlc/conventions/api-conventions.md v1.1"
change_history:
  - version: "1.0"
    date: "2026-06-10"
    changes: "初始版本 — 1 個新 API-101 GET /api/db/healthz（觀測 startup migration 狀態）+ 28 個 TASK-001 既有 API [REUSE 邊界不變]說明 + Internal Action API-INT-101 (FastAPI lifespan startup) + API-INT-102 (lifespan shutdown) 列為內部行為文件化"
    author: "SD"
approval:
  reviewer: "PM"
  date: ""
  result: "Pending"
  notes: ""
---

# API 規格書 — SQLite → PostgreSQL 持久化遷移

> **本檔負責**: SD 階段 API 設計規格 — 本 TASK 為純後端基礎設施重構，**API 設計極簡**：
> - **僅 1 個新 HTTP API**（API-101 `GET /api/db/healthz`）— 供 Tester / Deployer 在 FUNC-107 production cutover 時確認 DB + migration 狀態
> - **28 個 TASK-001 既有 API**（API-001..028 待 PM 後續正式登記）→ **NFR-002 強制外部行為完全不變**；本 TASK 僅底層 query 適配 PG dialect（FUNC-105）
> - 2 個 Internal Action（**非 HTTP API** — FastAPI lifespan startup / shutdown）— 文件化以利後續理解 MOD-104 行為
>
> **ID 範圍**: API 配額 101-200 — 本 TASK 使用 **API-101 一個 ID**。範圍 102-200 保留作未來擴充。
>
> **設計信心等級**: 🟢 高信心（API-101 來自 Tester [INFO-1] 提及的健康監控需求 + service-contract.yaml `backend.health_check_note` 標 [SA建議 SA-SUG-101]；雖然 SA-SUG-101 明示「不在本 TASK FR 範圍」，但 deploy-env.json `_blockedOnDeployerResolved.4_production_sla_dashboard.resolution` 已說明「DB connection error count 需應用層自寫 metric (MOD-101 例外計數) export 到 Railway logs」— 本 endpoint 即為此 metric 入口）

---

## 1. API 總覽

| API-ID | 方法 | 路徑 | 說明 | 對應 FUNC | 對應 FR |
|--------|------|------|------|----------|---------|
| **API-101** ★ NEW | GET | `/api/db/healthz` | DB 健康檢查 + migration 狀態 | FUNC-101, FUNC-103, FUNC-104 | FR-001（連線狀態揭露）+ FR-006（部署層觀察）|
| API-001..028 [REUSE: from TASK-001] | — | — | 28 個既有 endpoint — 認證 / 收藏 / 雪票 / 機票 / 整合查詢 | TASK-001 FUNC-022..045 + FUNC-001..021 | TASK-001 既有 FR / FR-001（底層適配）|

**反越界自檢**: 本 TASK 為純後端遷移，**禁止新增業務功能**（CONST-006）。API-101 屬於「可觀測性 / 部署健康檢查」基礎設施 — 屬 BA NFR-001 + NFR-003 + deploy/service-contract.yaml `backend.health_check_note` 既有討論範圍；非新業務功能。

---

## 2. 新增 API 規格

### API-101: GET `/api/db/healthz` — DB 健康檢查 + migration 狀態

#### 2.1 基本資訊

| 項目 | 內容 |
|------|------|
| 方法 | `GET` |
| 路徑 | `/api/db/healthz` |
| operationId | `dbHealthz` |
| 功能模組 | MOD-104 db_bootstrap |
| 對應 FUNC | FUNC-101（連線池就緒）+ FUNC-103/104（migration 已套用）|
| 對應 FR | FR-001（揭露連線狀態）+ FR-006（部署層觀察）|
| 信心等級 | 🟢 高信心 |

#### 2.2 認證要求

- **無認證**（healthcheck 端點，必須**任何狀態下都可達**）
- 不檢查 cookie / token；不寫入任何 cookie
- 路徑前綴 `/api/db/` — 與既有 `/api/auth/` 區分（屬基礎設施維運層；api-conventions.md §1 命名 brownfield grandfather 容忍單數 `db` 因屬技術術語非業務資源）

#### 2.3 Request

```http
GET /api/db/healthz HTTP/1.1
Host: ...
```

**無 Query Parameters / Request Body / Header 額外要求**。

#### 2.4 Response

##### 成功（HTTP 200）

```json
{
  "status": "ok",
  "db": {
    "connected": true,
    "pool": {
      "min": 2,
      "max": 10,
      "open": 2,
      "in_use": 0
    }
  },
  "migration": {
    "current": "20260610_120100",
    "head": "20260610_120100",
    "up_to_date": true
  }
}
```

**欄位說明**:

| 欄位 | 型別 | 必填 | 說明 |
|------|------|------|------|
| `status` | string | ✅ | enum: `"ok"` \| `"degraded"` \| `"down"` |
| `db.connected` | boolean | ✅ | pool 是否就緒（init_pool 成功）|
| `db.pool.min` | integer | ✅ | `POSTGRES_POOL_MIN` env var 值（NFR-005）|
| `db.pool.max` | integer | ✅ | `POSTGRES_POOL_MAX` env var 值 |
| `db.pool.open` | integer | ✅ | 目前 open 的連線總數（idle + in_use）|
| `db.pool.in_use` | integer | ✅ | 目前借出的連線數 |
| `migration.current` | string \| null | ✅ | 目前 `alembic_version.version_num`；migration 未套用則為 `null` |
| `migration.head` | string | ✅ | `migrations/versions/` 中最新 revision id |
| `migration.up_to_date` | boolean | ✅ | `current == head` |

##### 退化（HTTP 200，但 status=degraded）

```json
{
  "status": "degraded",
  "db": {
    "connected": true,
    "pool": { ... }
  },
  "migration": {
    "current": "20260610_120000",
    "head": "20260610_120100",
    "up_to_date": false
  }
}
```

**觸發**: 連線正常但 migration 尚未跑到 head（極罕見 — 通常 advisory lock 已保證 startup 完成 migration 才放行 traffic；此 case 對應「他 instance 已 upgrade 但本 instance startup 邏輯壞掉」的觀察用）

##### 失敗（HTTP 503）

```json
{
  "status": "down",
  "db": {
    "connected": false,
    "error": "ERR-DB-001"
  },
  "migration": null
}
```

**欄位說明**:

| 欄位 | 型別 | 必填 | 說明 |
|------|------|------|------|
| `status` | string | ✅ | `"down"` |
| `db.connected` | boolean | ✅ | `false` |
| `db.error` | string | ✅ | ERR-ID 引用（`ERR-DB-001` / `ERR-DB-002`），對應 `error-codes.md` |
| `migration` | null | ✅ | DB 連不上時 migration 狀態未知 |

**觸發**: pool 取連線失敗 / pool 未初始化 / PG 斷線

> **註**: 不直接拋 500 — 用 200/503 + JSON body 明確區分「app 起來但 DB 有問題」（既有 health_check_note 中 SA-SUG-101 的需求）。HTTP 503 觸發 Railway healthcheck 告警；HTTP 200 status=degraded 不告警但寫入監控指標。

#### 2.5 錯誤碼表

| HTTP Status | ERR-ID | 觸發條件 | 行為 |
|-------------|--------|---------|------|
| 200 | — | 正常 | 回 status=ok |
| 200 | — | 連線 ok 但 migration 落後 head | 回 status=degraded |
| 503 | ERR-DB-001 (ERR_DB_CONNECTION_FAILED) | pool 取連線失敗 / OperationalError | 回 status=down + ERR-ID |
| 503 | ERR-DB-002 (ERR_DB_POOL_TIMEOUT) | pool 取連線逾時（超過 POSTGRES_POOL_TIMEOUT_MS）| 同上 |

> **注意**: 本 endpoint **不主動**拋 ERR-MIGRATION-001 / ERR-MIGRATION-002（這些是 startup 期間的錯誤；若 migration 失敗則 app startup 失敗，本 endpoint 根本不會服務 — 由 Railway healthcheck fail + auto rollback 處理）。本 endpoint 揭露的是「runtime 觀察到的 migration 狀態」。

#### 2.6 業務邏輯步驟

```
1. 嘗試從 MOD-101 pool 取連線（with get_conn() as conn:）
   1.1 失敗（pool 未初始化 / OperationalError / PoolTimeout）
       → response: status=down, db.error=對應 ERR-ID
       → HTTP 503
       → return
   1.2 成功 → 繼續

2. 取 pool 統計
   2.1 從 _pool 物件讀 min_size / max_size
   2.2 從 _pool.get_stats() 讀 open / in_use（psycopg_pool 內建）

3. 查 alembic_version 表
   3.1 SELECT version_num FROM alembic_version LIMIT 1
   3.2 若表不存在（未 migration）→ migration.current = null
   3.3 若 row 存在 → migration.current = version_num

4. 計算 head：
   4.1 從 Alembic 配置 ScriptDirectory 取最新 revision id
   4.2 或 hardcoded 為「最新 migration 檔案的 revision」（簡化 — 由 BE 階段決定）

5. 比對 current vs head：
   5.1 up_to_date = (current == head)
   5.2 若 up_to_date = true → status = "ok"
   5.3 若 up_to_date = false → status = "degraded"

6. 組裝 JSON response 並 return（HTTP 200）
```

#### 2.7 範例 curl

```bash
curl -i https://snowboarding-support-system-jp-production.up.railway.app/api/db/healthz

HTTP/1.1 200 OK
content-type: application/json

{
  "status": "ok",
  "db": {
    "connected": true,
    "pool": {"min": 2, "max": 10, "open": 2, "in_use": 0}
  },
  "migration": {
    "current": "20260610_120100",
    "head": "20260610_120100",
    "up_to_date": true
  }
}
```

#### 2.8 ENV_VAR_CONTRACT 遵循

| Response 引用 env var | service-contract.yaml 對應 | ✓ |
|----------------------|---------------------------|---|
| `POSTGRES_POOL_MIN` | services.backend.env_vars[7] | ✅ |
| `POSTGRES_POOL_MAX` | services.backend.env_vars[8] | ✅ |
| `POSTGRES_POOL_TIMEOUT_MS` | services.backend.env_vars[9] | ✅ |

#### 2.9 追溯

| 追溯項 | 對應 |
|--------|------|
| FUNC | FUNC-101（pool 就緒）+ FUNC-103/104（migration 已套用）|
| FR | FR-001（揭露連線狀態，間接保證 SQLite → PG 替換成功）+ FR-006（部署層觀察）|
| NFR | NFR-001 持久性（migration 揭露）+ NFR-005 pool 觀察 |
| MOD | MOD-104 db_bootstrap（implements）+ MOD-101 postgres_db（讀 pool 統計）+ MOD-102 migrations（讀 alembic_version）|
| ENTITY | 無直接 ENTITY 操作（純基礎設施觀察）|
| ERR | ERR-DB-001, ERR-DB-002（可能拋出）|

---

## 3. Internal Action（非 HTTP API — 文件化）

### API-INT-101: FastAPI Startup Lifespan

> **註**: 非 HTTP API；FastAPI lifespan event；文件化以利後續理解 MOD-104。

**觸發**: FastAPI app 啟動（uvicorn 開始）
**動作**:
1. 呼叫 `MOD-104.on_startup()` → `MOD-101.init_pool()`（讀 env vars 建 pool）
2. 失敗 → app 啟動失敗（Railway healthcheck fail → auto rollback to N-1 build）
3. 成功 → 呼叫 `MOD-104.run_migrations()`（含 advisory lock）
4. migration 失敗 → 同 1.2
5. migration 成功 → app ready to serve traffic（28 個既有 endpoint 開始可用 + API-101 可用）

**對應 FUNC**: FUNC-101 + FUNC-103 + FUNC-104

### API-INT-102: FastAPI Shutdown Lifespan

**觸發**: FastAPI app 結束（uvicorn 停止）
**動作**:
1. 呼叫 `MOD-104.on_shutdown()` → `MOD-101.close_pool()`
2. 等待 in-flight query 完成 → 關閉所有 idle 連線 → drain pool

**對應 FUNC**: FUNC-102

---

## 4. 既有 28 API [REUSE: from TASK-001] — 行為不變條款

> **核心保證**: NFR-002 強制 — TASK-001 既有 22 AC (AC-015~AC-036) 在本 TASK 部署後 100% 通過；既有 8 個 pytest (`web/auth/tests/test_auth.py`) 100% 通過（AC-045）。
> **變動範圍**: 僅底層 query 適配 PG dialect（FUNC-105）—`?` → `%s` + lastrowid → `RETURNING id` + 移除 `bool()` adapter + ISO 字串時間比較 → TIMESTAMPTZ 原生比較
> **不變項**: HTTP status code / response body 結構 / cookie 設定（HttpOnly / SameSite / Max-Age）/ redirect URL / Pydantic models / JWT 邏輯 / bcrypt 邏輯 / Resend / SMTP / OAuth flow

### 4.1 受影響的既有 endpoint 清單（底層 query 適配）

> **註**: TASK-001 28 個 endpoint 中，與 DB 互動的部分（即 auth / favorites / verify 子集）會在 FUNC-105 適配；無 DB 互動的（雪票 / 機票 / 整合查詢）完全不變。

| Endpoint | 方法 | 路徑 | DB 互動 | 適配層 |
|----------|------|------|---------|--------|
| 註冊 | POST | /api/auth/register | INSERT users + INSERT email_verification_tokens | placeholder + lastrowid → RETURNING + UPDATE updated_at |
| 登入 | POST | /api/auth/login | SELECT users | placeholder |
| 登出 | POST | /api/auth/logout | （無 DB）| — |
| Email 驗證 | GET | /api/auth/verify/{token} | SELECT + UPDATE users.is_verified + UPDATE email_verification_tokens.used_at | placeholder + UPDATE updated_at |
| 重寄驗證信 | POST | /api/auth/resend-verification | UPDATE email_verification_tokens.used_at + INSERT new token | placeholder + UPDATE updated_at + RETURNING id |
| OAuth login | GET | /api/auth/google/login | （無 DB）| — |
| OAuth callback | GET | /api/auth/google/callback | UPSERT users（SELECT-then-INSERT-or-UPDATE）| placeholder + UPDATE updated_at + RETURNING id |
| 取得當前用戶 | GET | /api/auth/me | SELECT users | placeholder + 移除 `bool(is_verified)` adapter |
| 維運查詢 | GET | /api/auth/verify | SELECT users | 同上 |
| 收藏新增 | POST | /api/favorites | INSERT favorites | placeholder + RETURNING id + UPDATE updated_at（既有不變的 INSERT 邏輯）|
| 收藏列表 | GET | /api/favorites | SELECT favorites | placeholder |
| 收藏刪除 [IRREVERSIBLE REUSE] | DELETE | /api/favorites/{id} | DELETE FROM favorites（**仍硬刪 — SUG-004 + CONST-005**）| placeholder |
| 其他 16 個 endpoint（雪票 / 機票 / 整合 / 頁面路由）| — | — | 無 DB | 完全不變 |

### 4.2 為何不在本 TASK 重新登記 API-001..028

- 屬於 TASK-001 brownfield-document 應產出但未正式登記的範圍 — PM 已標記「TASK-001 既有 API-001..028（待 SD 階段正式登記）」（impact-assessment.md §1.3）
- 本 TASK 範圍嚴格限於「SQLite → PG 持久層遷移」（CONST-006）— 重新登記 28 個 API 屬範圍擴張
- 建議: PM 後續開「retroactive API registry」TASK 補追溯（與 SUG-007 DESIGN.md 同步同類）；或在 TASK-001 收尾 sweep 中補

---

## 5. API 路徑命名遵循

> **依據**: api-conventions.md v1.1 §1 URL 命名慣例

| API | 路徑 | 合規？ |
|-----|------|--------|
| API-101 | `/api/db/healthz` | ⚠️ **brownfield grandfather 容忍**: `db` 為單數技術術語（非業務資源），`healthz` 為業界標準 health 端點命名（k8s readiness/liveness 慣例）；與既有 `/api/auth/me` / `/api/auth/verify` 等單數模式一致 |

**[SD建議]**: 未來 v2 API 走 kebab-case 複數時，可考慮 `/api/health/db` 或 `/api/v2/health/db`（kebab-case + 巢狀資源）。不在本 TASK 範圍。

---

## 6. 錯誤碼引用驗證（ERR_CODE_DISCIPLINE）

> 本 TASK api-spec.md 所有錯誤碼皆引用 `ERR-{DOMAIN}-NNN` 格式 + alias，已在 `error-codes.md` §2 登記。

| 引用位置 | ERR-ID | alias | 已登記？ |
|----------|--------|-------|---------|
| §2.5 API-101 錯誤碼表 | ERR-DB-001 | ERR_DB_CONNECTION_FAILED | ✅ error-codes.md §2.2 |
| §2.5 | ERR-DB-002 | ERR_DB_POOL_TIMEOUT | ✅ error-codes.md §2.2 |
| §2.4 Response examples | ERR-DB-001 | — | ✅ |

**Ad-hoc 格式檢查**: 全檔搜尋 `E001` / `AUTH_FAIL` / `401_INVALID` / 自由字串訊息代替代碼 → 全無 ✅

---

## 7. 認證機制 [REUSE: from TASK-001]

> API-101 不需認證（健康檢查特殊例外）；其餘 28 個 [REUSE: from TASK-001] endpoint 認證機制不變 — JWT in HTTP-only Cookie（PATTERN-007 [REUSE]）。

---

## 8. 分頁 / 排序 [REUSE: from TASK-001]

本 TASK 無分頁需求（API-101 為單次 healthcheck）；既有收藏列表 `GET /api/favorites` [REUSE] 行為不變。

---

## 9. 追溯矩陣

### 9.1 API ↔ FUNC ↔ FR ↔ MOD

| API-ID | FUNC | FR | MOD | ENTITY 操作 |
|--------|------|-----|-----|-----------|
| API-101 ★NEW | FUNC-101 + FUNC-103 + FUNC-104 | FR-001 + FR-006 | MOD-104 + MOD-101 + MOD-102 | 無（讀 alembic_version 但屬基礎設施表）|
| API-001..028 [REUSE] | TASK-001 FUNC-001..045 | TASK-001 既有 + FR-001 適配 | MOD-001..006 [REUSE] + MOD-101/103 適配 | TBL-001/002/003 [REUSE 邊界 + 補欄] |

### 9.2 反向: 每個 FR 涉及的 API

| FR | API | 證據 |
|----|-----|------|
| FR-001 連線層替換 | API-101 + 既有 28 API 底層適配 | §4 受影響 endpoint 清單 |
| FR-002 三表 schema | 無直接 API | （由 db-schema.md migration 落實）|
| FR-003 Migration 工具 | API-101（揭露狀態）| §2.4 migration 欄位 |
| FR-004 補軟刪欄位 | 無直接 API | （schema 層變更，不暴露 API）|
| FR-005 env vars | API-101 揭露 pool 配置 | §2.4 db.pool 欄位 |
| FR-006 Railway 部署 | API-101（部署層觀察）| §2.1 |
| FR-007 既有資料遷移 | 無 API（scripts/ 工具）| code-arch.md §5 |
| FR-008 全環境 PG | API-101 + 既有 28 API [REUSE] | §4 |

### 9.3 跨 TASK 標記

| 標記 | 落實 |
|------|------|
| `[REUSE: API-001..028, from TASK-001]` | §4 |
| `[CROSS-TASK: TASK-001 / MOD-005 storage engine 替換 / FR-001]` | §4.1 受影響 endpoint 清單 + FUNC-105 適配 |
| `[IRREVERSIBLE REUSE: FUNC-045 收藏刪除硬刪]` | §4.1 「收藏刪除」行（仍硬刪 — SUG-004 + CONST-005）|

---

## 10. 範圍邊界（反越界自檢）

| SD 不可做的事 | 自檢 |
|--------------|------|
| 新增業務功能 API | ✅ API-101 為健康檢查基礎設施，非業務功能（CONST-006）|
| 改既有 28 API 外部行為 | ✅ §4 嚴格 [REUSE] + NFR-002 強制 22 AC 通過 |
| 改認證機制 | ✅ §7 [REUSE] |
| 改 API 路徑命名（v1 → v2 等）| ✅ §5 brownfield grandfather 容忍 |
| 改 hard-delete 為 soft-delete | ✅ §4.1 表明示「收藏刪除 IRREVERSIBLE REUSE — 仍硬刪 SUG-004」|

---

## 11. 自我驗證（摘要）

| 檢查項 | 通過 | 說明 |
|--------|------|------|
| 每個 FR 都有 API 對應（或標明無需 API）| ✅ | §9.2 |
| 每個 API 完整規格（Method / Path / Request / Response / Errors / Logic / 認證）| ✅ | §2 API-101 |
| 範例 JSON 完整 | ✅ | §2.4（200 ok / 200 degraded / 503 down）|
| 錯誤碼引用 ERR-{DOMAIN}-NNN 格式（無 ad-hoc）| ✅ | §6 |
| Internal Action（lifespan）文件化 | ✅ | §3 |
| 既有 28 API [REUSE] 行為不變條款 | ✅ | §4 |
| 追溯矩陣完整 | ✅ | §9 |
| 範圍邊界（不新增業務 / 不改既有）| ✅ | §10 |
| API ID 在範圍 101-200 內 | ✅ | API-101 |
| ID TASK 內連續 | ✅ | 僅 API-101 一個 |
| ENV_VAR_CONTRACT 遵循 service-contract.yaml | ✅ | §2.8 |
| 認證方式遵循 api-conventions.md | ✅ | §7 |
| 不腦補功能 | ✅ | API-101 來源於 SA-SUG-101 + service-contract.yaml + Tester INFO-1 監控需求 |
| 反 NFR-002 不變項 | ✅ | §4 強調行為不變 |
| **總分** | **93/100** | 詳見 self-review.json |
