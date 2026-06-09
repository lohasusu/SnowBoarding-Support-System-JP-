---
document_id: "PARAMPLAN-TASK-002-v1.0"
title: "Parameter Registry 登記計畫（Rule 18）"
version: "1.0"
date: "2026-06-09"
author: "Deployer (Init)"
status: "Draft"
task_id: "TASK-002"
phase: "deploy-init"
source_documents:
  - "service-contract.yaml (本 TASK Deploy(Init) 同步產出)"
  - "impact-assessment.md §4 Parameter Registry 預期影響 (SA)"
  - "Rule 18 protocols/rule-18-parameter-registry.md"
approval:
  reviewer: "PM"
  result: "Pending"
---

# Parameter Registry 登記計畫 — TASK-002

> **Rule 18**: 本 TASK 引入 / 修改的跨 TASK 共用 parameter 必須登記到 `shared/parameter-registry.md`。
> **登記時機**: Rule 18 §18.2 規定**由 SD 階段**呼叫 `sdlc-journal-write.sh parameter_added` 寫入 journal；PM rebuild shared/ 時自動生成 registry。
> **本檔用途**: Deploy(Init) **規劃** SD 將寫入的 parameters，提供完整 spec 供 SD 直接複製貼上。

---

## 1. 將寫入的 Parameter（10 個）

> SD 階段必須依下列順序執行 `bash $HOME/.claude/skills/sdlc/scripts/sdlc-journal-write.sh TASK-002 parameter_added sd '<JSON>'`。
> 順序：先連線參數（5 個 POSTGRES_*）→ DATABASE_URL（替代方案）→ SSL → Pool（3 個）→ 共 10 個。

### 1.1 POSTGRES_HOST

```bash
bash $HOME/.claude/skills/sdlc/scripts/sdlc-journal-write.sh TASK-002 parameter_added sd '{
  "paramName": "POSTGRES_HOST",
  "paramKind": "env",
  "paramType": "string",
  "value": "(env-specific: localhost dev / Railway 內部 host prod)",
  "scope": "all",
  "required": true,
  "secret": false,
  "ownerService": "be",
  "description": "PostgreSQL host — 連線目標主機",
  "sourceFR": "FR-005",
  "envPrefix": "POSTGRES_",
  "validation": "non-empty string"
}'
```

### 1.2 POSTGRES_PORT

```bash
bash $HOME/.claude/skills/sdlc/scripts/sdlc-journal-write.sh TASK-002 parameter_added sd '{
  "paramName": "POSTGRES_PORT",
  "paramKind": "env",
  "paramType": "number",
  "value": "5432",
  "scope": "all",
  "required": true,
  "secret": false,
  "ownerService": "be",
  "description": "PostgreSQL port",
  "sourceFR": "FR-005",
  "envPrefix": "POSTGRES_",
  "validation": "1-65535"
}'
```

### 1.3 POSTGRES_USER

```bash
bash $HOME/.claude/skills/sdlc/scripts/sdlc-journal-write.sh TASK-002 parameter_added sd '{
  "paramName": "POSTGRES_USER",
  "paramKind": "env",
  "paramType": "string",
  "value": "(env-specific: snowtrip dev / Railway addon 自動 user)",
  "scope": "all",
  "required": true,
  "secret": false,
  "ownerService": "be",
  "description": "PostgreSQL 使用者",
  "sourceFR": "FR-005",
  "envPrefix": "POSTGRES_",
  "validation": "non-empty, lowercase recommended"
}'
```

### 1.4 POSTGRES_PASSWORD ⚠️ Secret

```bash
bash $HOME/.claude/skills/sdlc/scripts/sdlc-journal-write.sh TASK-002 parameter_added sd '{
  "paramName": "POSTGRES_PASSWORD",
  "paramKind": "secret",
  "paramType": "string",
  "value": "(VAULT_REF: cicd-native — Railway dashboard / .env)",
  "scope": "all",
  "required": true,
  "secret": true,
  "ownerService": "be",
  "description": "PostgreSQL 密碼 — 絕不可 commit 到 git；錯誤訊息禁止洩漏（NFR-011）",
  "sourceFR": "FR-005 + NFR-011",
  "envPrefix": "POSTGRES_",
  "validation": "non-empty, min 16 chars recommended"
}'
```

### 1.5 POSTGRES_DB

```bash
bash $HOME/.claude/skills/sdlc/scripts/sdlc-journal-write.sh TASK-002 parameter_added sd '{
  "paramName": "POSTGRES_DB",
  "paramKind": "env",
  "paramType": "string",
  "value": "snowtrip",
  "scope": "all",
  "required": true,
  "secret": false,
  "ownerService": "be",
  "description": "PostgreSQL 資料庫名稱",
  "sourceFR": "FR-005",
  "envPrefix": "POSTGRES_",
  "validation": "non-empty, lowercase"
}'
```

### 1.6 DATABASE_URL ⚠️ Secret（替代方案 — SD 決定是否採用）

```bash
bash $HOME/.claude/skills/sdlc/scripts/sdlc-journal-write.sh TASK-002 parameter_added sd '{
  "paramName": "DATABASE_URL",
  "paramKind": "secret",
  "paramType": "string",
  "value": "(VAULT_REF: Railway dashboard auto-injected)",
  "scope": "all",
  "required": false,
  "requiredNote": "若採用此 var 則 POSTGRES_* 5 個變為 optional；SD 決定支援哪種模式",
  "secret": true,
  "ownerService": "be",
  "description": "PostgreSQL 連線字串（替代方案 — Railway PG addon 自動注入）；格式: postgresql://user:pass@host:port/db?sslmode=require",
  "sourceFR": "FR-005 (替代方案)",
  "envPrefix": "(無 — 業界慣例特例)",
  "validation": "PostgreSQL connection URI format"
}'
```

### 1.7 POSTGRES_SSL_MODE

```bash
bash $HOME/.claude/skills/sdlc/scripts/sdlc-journal-write.sh TASK-002 parameter_added sd '{
  "paramName": "POSTGRES_SSL_MODE",
  "paramKind": "env",
  "paramType": "string",
  "value": "(env-specific: disable dev / require staging / verify-full prod)",
  "scope": "all",
  "required": true,
  "secret": false,
  "ownerService": "be",
  "description": "PostgreSQL SSL 連線模式",
  "sourceFR": "FR-005 + BA SUG-005",
  "envPrefix": "POSTGRES_",
  "validation": "enum: disable | allow | prefer | require | verify-ca | verify-full"
}'
```

### 1.8 POSTGRES_POOL_MIN

```bash
bash $HOME/.claude/skills/sdlc/scripts/sdlc-journal-write.sh TASK-002 parameter_added sd '{
  "paramName": "POSTGRES_POOL_MIN",
  "paramKind": "limit",
  "paramType": "number",
  "value": "2",
  "scope": "all",
  "required": false,
  "secret": false,
  "ownerService": "be",
  "description": "Connection pool 最小連線數",
  "sourceFR": "NFR-005",
  "envPrefix": "POSTGRES_",
  "validation": "1 <= value <= POSTGRES_POOL_MAX"
}'
```

### 1.9 POSTGRES_POOL_MAX

```bash
bash $HOME/.claude/skills/sdlc/scripts/sdlc-journal-write.sh TASK-002 parameter_added sd '{
  "paramName": "POSTGRES_POOL_MAX",
  "paramKind": "limit",
  "paramType": "number",
  "value": "10",
  "scope": "all",
  "required": false,
  "secret": false,
  "ownerService": "be",
  "description": "Connection pool 最大連線數",
  "sourceFR": "NFR-005",
  "envPrefix": "POSTGRES_",
  "validation": "POSTGRES_POOL_MIN <= value <= 100 (Railway Hobby PG max conn limit)"
}'
```

### 1.10 POSTGRES_POOL_TIMEOUT_MS

```bash
bash $HOME/.claude/skills/sdlc/scripts/sdlc-journal-write.sh TASK-002 parameter_added sd '{
  "paramName": "POSTGRES_POOL_TIMEOUT_MS",
  "paramKind": "limit",
  "paramType": "number",
  "value": "5000",
  "scope": "all",
  "required": false,
  "secret": false,
  "ownerService": "be",
  "description": "從 pool 取得連線的最大等待時間（ms）",
  "sourceFR": "NFR-005",
  "envPrefix": "POSTGRES_",
  "validation": "1000 <= value <= 30000"
}'
```

---

## 2. 既有 [REUSE] Parameters（不在本 TASK 登記，TASK-001 範圍）

下列 parameter 為既有 production 環境的 env vars，**不在本 TASK 引入**，但 service-contract.yaml 完整列出供 Execute 階段 env-consistency check 比對：

| Param | Kind | First TASK | 用途 | 備註 |
|-------|------|-----------|------|------|
| SECRET_KEY | secret | TASK-001 | JWT 簽章 [REUSE] | TASK-001 應有但 registry 仍空（需 TASK-001 retroactive 補登記？）|
| SERPAPI_API_KEY | secret | TASK-001 | 機票 API [REUSE] | 同上 |
| PORT | env | TASK-001 | Railway 動態 port [REUSE] | 同上 |

### [DEPLOYER建議 — Retroactive Parameter Registry]

> 觀察到 `shared/parameter-registry.md` 6 個區段全空 — TASK-001 brownfield-document 未追溯既有 production env vars。
>
> **建議**: PM 在 TASK-002 SD approve 後（registry 因本 TASK 開始非空），開新 retroactive TASK 補登記 TASK-001 既有 3 個 env vars，或 SD 階段在本 TASK 順帶補上（first_task 標 TASK-001，避免 Rule 18 衝突）。
>
> **本檔不主動觸發**: 留 PM 決策（避免擴大本 TASK 範圍 — CONST-004）。

---

## 3. Conflict Detection 預期狀態（Rule 18.3）

| 衝突類型 | 預期 | 理由 |
|---------|------|------|
| Value mismatch | 無 | 本 TASK 為第一個引入 POSTGRES_* — 無前 TASK 同名 |
| Semantic mismatch | 無 | 同上 |
| Owner mismatch | 無 | 全部 ownerService=be 一致 |
| Cross-TASK modification without RFC | 無 | 本 TASK 不修改前 TASK parameter |

**驗證**: SD approve 後 PM rebuild shared → 跑 `bash scripts/sdlc-parameter-check.sh` 應全綠。

---

## 4. SD 階段執行 Checklist

SD 階段在執行任一動作前驗證：

- [ ] 讀取本檔（parameter-plan.md）
- [ ] 在 api-spec.md / db-schema.md / logic-flow.md / code-arch.md 引入 env vars 時，先複製本檔 §1 的 10 個 bash 命令逐一執行
- [ ] 執行順序：先所有 POSTGRES_* env → DATABASE_URL → POOL_*
- [ ] 每執行完一個，確認 stdout 顯示 `journal entry written: parameter_added | POSTGRES_XXX`
- [ ] 全部執行完後跑 `bash $HOME/.claude/skills/sdlc/scripts/sdlc-shared-rebuild.sh --check`
- [ ] 確認 `shared/parameter-registry.md` 顯示 10 個新行
- [ ] 將執行結果記錄在 SD 階段 self-review.json 的 `parameter_registry_updates` 欄位

---

## 5. 後續 TASK 影響

| 後續 TASK | 與本 TASK 10 個 parameters 的關係 |
|----------|--------------------------------|
| `soft-delete-favorites` | 沿用 [REUSE]（不修改、不新增）|
| `add-password-reset-flow` | 可能新增 `RESET_TOKEN_TTL_SECONDS` (limit) — 不影響本 TASK |
| `oauth-upsert-race-fix` | 沿用 [REUSE] |
| Connection pool 調優 TASK | 修改 `POSTGRES_POOL_MAX` → 需走 Rule 6 + Rule 18.4 (parameter_modified 事件 + SA `[CROSS-TASK]` 標記) |
| 加 Redis 快取 TASK | 新增 `REDIS_*` — 獨立於本 TASK |
| `production-monitoring-sentry` | 新增 `SENTRY_DSN` (secret) — 獨立 |

---

## 6. 追溯矩陣

| Parameter | 來源 FR/NFR | service-contract.yaml 位置 | Rule 18 paramKind |
|-----------|-----------|---------------------------|--------------------|
| POSTGRES_HOST | FR-005 | services.backend.env_vars[0] | env |
| POSTGRES_PORT | FR-005 + config.json | services.backend.env_vars[1] | env |
| POSTGRES_USER | FR-005 | services.backend.env_vars[2] | env |
| POSTGRES_PASSWORD | FR-005 + NFR-011 | services.backend.env_vars[3] | secret |
| POSTGRES_DB | FR-005 | services.backend.env_vars[4] | env |
| DATABASE_URL | FR-005 (替代) | services.backend.env_vars[5] | secret |
| POSTGRES_SSL_MODE | FR-005 + BA SUG-005 | services.backend.env_vars[6] | env |
| POSTGRES_POOL_MIN | NFR-005 | services.backend.env_vars[7] | limit |
| POSTGRES_POOL_MAX | NFR-005 | services.backend.env_vars[8] | limit |
| POSTGRES_POOL_TIMEOUT_MS | NFR-005 | services.backend.env_vars[9] | limit |
