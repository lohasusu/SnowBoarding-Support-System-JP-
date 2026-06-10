---
document_id: "TEST-SD-TASK-002-v1.0"
title: "測試報告 — SD 階段（SQLite → PostgreSQL 持久化遷移）"
version: "1.0"
date: "2026-06-10"
author: "Testing"
task_id: "TASK-002"
phase: "test-sd"
mode: "feature"
tested_artifacts:
  - "DB-TASK-002-v1.0 (sd/db-schema.md, ~13 章節, 690 行)"
  - "CODEARCH-TASK-002-v1.0 (sd/code-arch.md, ~15 章節, 1077 行)"
  - "API-TASK-002-v1.0 (sd/api-spec.md, ~11 章節, 415 行)"
  - "API-TASK-002-v1.0-yaml (sd/api-spec.yaml, OpenAPI 3.0.3)"
  - "ERRCODES-TASK-002-v1.0 (sd/error-codes.md, ~9 章節, 190 行)"
  - "FEMAP-TASK-002-v1.0 (sd/fe-api-mapping.md, ~7 章節, 199 行)"
  - "SD-self-review-v1.0 (sd/self-review.json, score=93)"
test_baseline_documents:
  - "ba/requirement-spec.md (8 FR + 12 NFR + 7 BR + 14 AC + 9 CONST)"
  - "sa/functional-flow.md (FUNC-101..107 + 4 [CROSS-TASK] + 1 [IRREVERSIBLE])"
  - "sa/system-arch.md (MOD-101..104 + 8 [BLOCKED_ON_SD])"
  - "deploy/deploy-env.json (4 user-confirmed decisions)"
  - "conventions/db-conventions.md v1.1 (§5.3 三段式刪欄 + §8 禁止項)"
  - "conventions/api-conventions.md (URL 命名 + 認證)"
  - "conventions/code-conventions.md §7 (檔 ≤500 / 函式 ≤80)"
  - "TASK-002 test-sa report (3 Minor / 0 Critical / 0 Major)"
  - "TASK-002 test-ba report (3 Info)"
  - "L1 verify output (sdlc-role-verify.sh sd TASK-002 = 80/100, 4 failed checks)"
  - "既有 web/auth/tests/test_auth.py (8 pytest, AC-045 100% 通過要求)"
  - "既有 web/auth/database.py (TASK-001 brownfield baseline)"
verification_method:
  - "verify-spec D1-D9 (zero-ambiguity / API coverage / DB design / schema-API coverage / FE-API mapping / logic / code-arch / conflict / OpenAPI)"
  - "Rule 8 / 11 / 18 protocol compliance"
  - "L1 4 個 failed checks 獨立評估（PM 判定 vs Tester 判定）"
  - "8 [BLOCKED_ON_SD] 選型獨立評分（reasonable / questionable / rejected）"
  - "API-101 反越界自檢"
  - "既有 8 pytest 相容性 cross-validation"
  - "Placeholder `?` → `%s` 全替換風險評估"
change_history:
  - version: "1.0"
    date: "2026-06-10"
    changes: "初始版本 — 對抗心態獨立驗證；同意 PM 對 4 L1 false positive 判定；8 [BLOCKED_ON_SD] 全部 reasonable（2 個帶 caveat）；發現 2 Major（pytest fixture 改造缺失 + placeholder 全替換無精確清單）+ 4 Minor + 3 Info；CONDITIONAL_PASS（Critical=0 但 BE 階段風險須優先處理）"
    author: "Testing"
approval:
  reviewer: "PM"
  date: ""
  result: "Pending"
  notes: ""
---

# 測試報告 — SD 階段（SQLite → PostgreSQL 持久化遷移）

> **對抗心態**: Tester 的目標是找到 bug；漏掉 bug = Tester 失敗。本報告不為 SD 93/100 的 self-review 背書，獨立評分。
> **方法**: verify-spec D1-D9 + Rule 8/11/18 protocol + L1 4 failed checks 獨立判定 + 8 [BLOCKED_ON_SD] 反推 + 既有 8 pytest 相容性 cross-validation + placeholder 全替換風險分析。
> **基線假設**: SD 階段是「給開發人員的唯一真相來源」— 兩個獨立 BE 開發讀完規格應寫出功能等價的程式碼；任一決策若無法從規格反推，即視為缺陷。

---

## 1. 測試結果摘要

| 指標 | 結果 |
|------|------|
| 被測對象 | SD 階段 6 個 artifacts（db-schema.md / code-arch.md / api-spec.md / api-spec.yaml / error-codes.md / fe-api-mapping.md）|
| 對照基準 | BA / SA / deploy-env.json / 4 conventions / 既有程式碼 / test-sa report / L1 output |
| 測試日期 | 2026-06-10 |
| 驗證維度數 | D1-D9 + Rule 8/11/18 + 4 個專項評估 = 16 維度 |
| 檢查項目數 | 約 60 項（D1-D9 + protocol + 專項）|
| 🔴 Critical | **0** |
| 🟠 Major | **2** |
| 🟡 Minor | **4** |
| 🔵 Info | **3** |
| **階段判定** | **✅ CONDITIONAL PASS** |

**判定邏輯**:
- Critical = 0 → 不阻塞 SD 進入 fe+be 階段
- Major = 2 但都屬於「需在 BE 階段優先處理」（pytest fixture 改造方案缺失 + placeholder 全替換無精確清單）→ CONDITIONAL（PM 在 dispatch BE 時須明確標示優先解決）
- Minor / Info 不阻塞

---

## 2. L1 verify 4 failed checks 獨立評估

> PM 在 dispatch prompt 中判定 3/4 為 false positive。Tester 獨立執行 `bash $HOME/.claude/skills/sdlc/scripts/sdlc-role-verify.sh sd TASK-002` 得到分數 80/100，4 個 failed checks 重新評估如下：

| # | L1 finding | PM 判定 | Tester 獨立判定 | 證據 |
|---|----------|--------|----------------|------|
| 1 | 缺少 `sd/logic-flow.md` | false positive（0 新業務邏輯）| **AGREE — false positive** | 本 TASK 為純基礎設施重構，0 新業務 LOGIC；MOD-104 advisory lock 流程在 code-arch.md §1.4 + §3.4 已含完整 Python 範本 + 行為表 + Mermaid 依賴圖（§9）；既有業務 LOGIC 屬 TASK-001 [REUSE]。SD 不需另開 logic-flow.md。L1 為通用樣板檢查，本 TASK 屬合法例外。 |
| 2 | API-001 重複 | false positive（[REUSE] refs 非定義）| **AGREE — false positive** | api-spec.md §1 / §4 / §9.1 / §9.3 對 API-001..028 都標 `[REUSE: from TASK-001]`，是引用既有 API 範圍說明，非重新定義；L1 為純字串 grep，無法識別 `[REUSE]` 語義。本 TASK 唯一新 API 是 API-101；TBL/ERR 等 ID 皆連續無真實重複。 |
| 3 | fe-api-mapping 未引用 COMP | false positive（UIUX skipped）| **AGREE — false positive，但衍生 Major-1** | state.json TASK-002.phases.uiux.status = 'skipped'；fe-api-mapping.md §1 + §4 完整聲明 + §2 22 AC 影響評估表 + §3 觀察者映射補替代視角。L1 屬合法例外。**但**：UIUX skip 不代表「無 FE 端事實」— 既有 8 pytest（`web/auth/tests/test_auth.py`）= 事實上的 FE-API 邊界 = SD 改 PG 後必須改造的部分，SD 卻只在 code-arch.md §2 標一句 `fixture 改 PG`，無實作大綱。見 §4 Major-1。 |
| 4 | Rule 11: db-schema.md 含 DROP 操作但未標 expand-contract 三階段 | false positive（§5 即 Expand-Contract）| **AGREE — false positive** | Tester 獨立 grep `DROP` 5 hits：(a) §5 章節標題與導語提及「未來 DROP COLUMN」走三段式；(b) §5.1 表格「Contract: DROP 舊欄位 + RENAME」教學描述；(c) §5.2 教學 Migration C 範本；(d) §6.1 教學 `DROP INDEX CONCURRENTLY` 範本；(e) §4.3 註解提及 created_at downgrade 是 hard drop 但 production 為空。本 TASK Migration 1（FUNC-103 CREATE）/ Migration 2（FUNC-104 ADD COLUMN）皆無實際 DROP COLUMN；downgrade() 是 reversible 必備（否則違反 NFR-006）。db-conventions §5.3 「禁止單次 migration 直接 DROP COLUMN」**本 TASK 100% 遵守**。|

**Tester 結論**: 4/4 全部 false positive；SD L1 分數 80 應視為「pass with note」。Tester 不要求 SD 修改 artifacts；L1 規則本身需要強化（如能識別 `[REUSE]` / `[DEFERRED]` / 教學範本區段標記）— 屬 SDLC 框架改善建議（INFO-1）。

---

## 3. 8 個 [BLOCKED_ON_SD] 選型獨立評分

> Tester 不接受 SD 自評，逐項評分為 **reasonable**（合理）/ **reasonable_with_caveat**（合理但有保留）/ **questionable**（可商榷）/ **rejected**（拒絕）。

| # | [BLOCKED_ON_SD] | SD 決策 | Tester 評分 | 關鍵理由 |
|---|---------------|---------|-----------|---------|
| 1 | DB Driver 選型 | psycopg3 + psycopg_pool | **REASONABLE** | PEP 249 介面與 sqlite3 高相似 → 替換成本最低（對齊 NFR-002 行為不變）；同步介面與既有 FastAPI sync def 對齊；psycopg2 已 maintenance mode；`psycopg[binary]` Railway nixpacks 友善。**Verified**: code-arch.md §3.1 用 `dict_row` factory 解決既有 `row['col_name']` access 相容性問題。 |
| 2 | Migration 工具 | Alembic 1.13.1 | **REASONABLE** | Python 業界標準 + 內建 reversible（NFR-006）+ advisory lock + CONCURRENTLY（NFR-008）+ alembic_version 自管 + 雖 import SQLAlchemy 但不強迫 ORM（對齊 BR-001）。**Verified**: code-arch.md §3.2 配置完整（alembic.ini + env.py + versions/）。|
| 3 | Pool Library | psycopg_pool.ConnectionPool（內建）| **REASONABLE** | 同 driver 生態 → 零額外抽象；三個參數對齊 NFR-005；同步 context manager 對齊既有 `with get_conn() as conn`；不引入 pgbouncer 符合 Railway Hobby plan。|
| 4 | Migration 觸發策略 | startup-auto + PG advisory lock (key=0xCAFE0102) | **REASONABLE** | 對齊 deploy-env.json USER CONFIRMED；try + blocking 兩段式避免多 instance 競態；NFR-003 啟動延遲量化合理（<500ms）；失敗 → Railway healthcheck fail → auto rollback 對齊 ERR-MIGRATION-001。 |
| 5 | FUNC-103/104 拆分 | 拆兩個 migration（選項 B）| **REASONABLE** | 跨 TASK 修改 TBL 補欄事件獨立追蹤（Rule 6）；後續 TASK 引用 deleted_at 時可精準指 20260610_120100；FUNC-106 SQLite 匯入腳本不受拆分影響。 |
| 6 | updated_at 策略 | App-level（應用層 SET）— 不用 trigger | **REASONABLE_WITH_CAVEAT** | ✅ BR-001 schema 邏輯結構不變 / trigger 對 unit test 不友善 / Railway 自建 container trigger 安裝多風險。**Caveat**: 完全靠 grep + 人類自律；一個漏掉的 UPDATE 就破壞 INV-101。SD-SUG-102「lint rule」是必要的，不該降為 [SD建議]。MOD-103 helper 僅標「選擇性」（code-arch.md §9 依賴圖），無強制機制。→ Minor-1 |
| 7 | placeholder dialect | 全替換 `?` → `%s` | **REASONABLE_WITH_CAVEAT** | ✅ 不另寫 dialect 適配層；`%s` 是 PEP 249 DB-API 2.0 標準；少一層抽象對齊 code-conventions §7 精神。**Caveat**: SD「預估約 30 個 query」未實際 grep 統計；測試檔 test_auth.py 內 14+ 處 `?` 未列入 §8.2 BE 階段執行清單；IDE 全域 find-replace 風險（誤改 docstring/註解/URL query `?`）。→ Major-2 |
| 8 | lastrowid 替換 | INSERT ... RETURNING id + cur.fetchone()[0] | **REASONABLE** | PG 原生 SQL 支援，零 driver 依賴；比 psycopg2 cursor.lastrowid 仿真顯式可測；MOD-103 `insert_returning_id` helper 統一封裝。**Verified**: code-arch.md §3.3 + db-schema.md §8.1 完整範例。 |

**統計**: 6 reasonable / 2 reasonable_with_caveat / 0 questionable / 0 rejected。
**Tester 結論**: 8 個決策全部可接受；2 個 caveat 衍生 Major-2 與 Minor-1。**SD 是否需要修訂這 2 項？** Tester 立場 = 不要求 SD 修訂，但 BE 階段必須處理（PM dispatch BE 時應明確標示）。

---

## 4. API-101 反越界自檢（CONST-006）

> CONST-006「禁止新增業務功能」。Tester 必須獨立判定 API-101 GET `/api/db/healthz` 是否屬於越界。

### 4.1 In-scope 證據鏈

| 證據 | 來源 |
|------|------|
| service-contract.yaml `backend.health_check_note` 明示需求 | SA-SUG-101 |
| deploy-env.json `_blockedOnDeployerResolved.4_production_sla_dashboard.resolution` 「DB connection error count 需應用層自寫 metric（MOD-101 例外計數）export 到 Railway logs」 | deploy(init) USER CONFIRMED |
| test-ba INFO-2「監控 5xx / DB connection error / migration log」| BA Tester |
| FR-006 Railway 部署設定（含 healthcheck）+ FR-001 連線層替換（揭露連線狀態） | BA |
| 路徑前綴 `/api/db/`（基礎設施維運層）與業務 `/api/auth/` / `/api/favorites/` 區分 | api-spec.md §2.1 |

### 4.2 反證

| 假設 | 是否成立 |
|------|---------|
| 「無 API-101 Tester 無法驗收 FR-001 / FR-006」| ✅ 成立 — 無 API-101 則無法觀察 pool 狀態 / migration 是否套用 → 反證 API-101 為必要 |
| 「API-101 暴露給 FE 元件 = 越界」| ❌ 不成立 — fe-api-mapping.md §3 明示呼叫者為 Deployer / Railway healthcheck / Operator / Monitoring / Tester；無 FE 元件 |
| 「API-101 操作 ENTITY = 業務功能」| ❌ 不成立 — API-101 只 SELECT `alembic_version` 表（基礎設施表）+ 讀 pool 統計，無 ENTITY-001/002/003 操作 |

**Tester 判定**: API-101 **IN_SCOPE**（基礎設施可觀測性 endpoint）— 屬 SA-SUG-101 + deploy-env.json + test-ba INFO-2 已揭露的觀察需求；不是新業務功能。SD 沒有腦補。

**INFO-2**: API-101 路徑命名 `/api/db/healthz` brownfield grandfather 容忍但不完美（api-conventions.md v2 應走 kebab-case + 複數）；SD 已自評並標 [SD建議]，Tester 接受。

---

## 5. 4 個 [CROSS-TASK: TASK-001] 落地完整性

> Rule 6 跨 TASK 修改協議要求 SA 標記 → SD 落實 → BE 嚴格限定範圍。Tester 驗證 SD 階段對 4 個 marker 的落實。

| Marker | SD 落實位置 | 完整性 |
|--------|------------|-------|
| TBL-001 (users) 補 updated_at + deleted_at | db-schema.md §2.1 ALTER TABLE DDL 完整 + §3 diff 對照表標 ★ NEW + §4.3 Migration 2 Alembic op.add_column 範本 | ✅ COMPLETE |
| TBL-002 (favorites) 補 updated_at + deleted_at | db-schema.md §2.2 + §3 + §4.3 | ✅ COMPLETE |
| TBL-003 (email_verification_tokens) 補 updated_at + deleted_at + created_at baseline gap | db-schema.md §2.3 ALTER TABLE 3 欄完整 + §3 對照表 + §4.3 Migration 2 含 created_at backfill；FUNC-106 §5.2 給出 backfill 策略 | ✅ COMPLETE_WITH_INFO（見 Info-2）|
| MOD-005 storage engine 替換 (sqlite3 → Postgres driver) | code-arch.md §2 6 個 ✏️ MODIFY 既有檔 + ☆ REWRITE database.py + §3.1 MOD-101 完整實作大綱（~190 行）+ db-schema.md §8 dialect 適配規範 | ✅ COMPLETE |

**Tester 結論**: 4/4 marker 完整落實；無越界（SD 沒有改 SA 沒授權的前 TASK 產出）。

---

## 6. 既有 8 pytest 相容性 — Major-1

> AC-045「既有 8 個 pytest 對接 PostgreSQL 測試實例後全數通過」是 BA 硬性驗收。Tester 必須 cross-validate SD 是否提供 BE 階段可落地的改造方案。

### 6.1 既有 fixture 深度耦合 SQLite

Tester 讀 `web/auth/tests/test_auth.py` 確認以下 SQLite 耦合點：

| # | 耦合點 | 行 | SQLite 依賴 |
|---|--------|-----|------------|
| 1 | `from web.auth.database import init_db` | 20 | `init_db()` 在 SD code-arch.md §3.1 REWRITE 後可能不存在 |
| 2 | `monkeypatch.setattr("web.auth.database.DB_PATH", db_file)` | 19 | DB_PATH 為 SQLite 檔案路徑變數 — PG 改用 pool 物件 + DSN，DB_PATH 將消失 |
| 3 | `db_file = tmp_path / "test.db"` | 18 | tmp_path 給 SQLite 檔案 — PG 需 testcontainer / pg_ctl tmp instance 等替代 |
| 4 | 測試碼內 INSERT/SELECT 用 `?` placeholder | 38, 51, 57, 67, 71, 84, 89, 105, 117, 120, 122, 129, 130, 158, 171, 189 | 16+ 處 `?` 需改 `%s` |
| 5 | `row['col_name']` dict-like access | 多處 | 依賴 SQLite Row factory；SD 用 `dict_row` 已在 MOD-101 對齊 |
| 6 | `expired = ... .isoformat()` ISO 字串時間 | 70, 87 | PG TIMESTAMPTZ 接受 datetime 物件 — 改造後相容但需驗證 |
| 7 | `assert user["is_verified"] == 0` 用整數比較 | 39 | PG BOOLEAN 回 Python bool，原 SQLite 回 0/1 — 此 assertion 在 PG 下需改 `== False` 或 `is False` |

### 6.2 SD 提供的方案

code-arch.md §2 只標一句：
> `tests/test_auth.py ✏️ MODIFY — fixture 改 PG（AC-045 既有 8 pytest 100% 通過）`

無實作大綱，無 requirements.txt 加 PG test fixture lib（testcontainers / pytest-postgresql / pg-fixtures），無 PG 連線方式（用 docker-compose / pg_ctl / testcontainer）的選擇。

### 6.3 對 BE 階段的開放問題

| 問題 | 嚴重度 |
|------|--------|
| Q1: PG 測試 fixture 用什麼？候選 (a) testcontainers-python (b) pytest-postgresql (c) docker-compose 共用 (d) SQLite + PG 雙跑（違反 BR-001）| 高 |
| Q2: 既有 16+ 處 placeholder `?` 在測試程式碼中如何同步替換？test_auth.py **不在** SD §8.2「BE 階段執行清單」中 | 高 |
| Q3: `monkeypatch.setattr("web.auth.database.DB_PATH", ...)` 改 PG 後如何？monkeypatch POSTGRES_HOST/DB env var？或替換 pool 物件？| 高 |
| Q4: `init_db()` 在 SD §3.1 重寫 MOD-101 後是否存在？若不存在 fixture line 21 會 ImportError | 高 |
| Q5: `is_verified == 0/1` 整數比較在 PG BOOLEAN 下需改 `is False / is True` | 中 |

### 6.4 Tester 判定

**Major-1**: 不阻塞 SD approve（屬 BE 階段實作範圍），但風險不可量化。建議 PM dispatch BE 時優先要求 BE：
1. 動手前先設計 pytest fixture 改造方案並回 PM 確認（候選技術選型 + 試跑一個 test case 驗證可行）
2. 將 test_auth.py 14+ 處 `?` 加入「BE 階段執行清單」（補強 §8.2）
3. 在 BE artifacts 中補 [BLOCKED_ON_BE] 設計決策章節

或者：SD 補一個 **SD-SUG-104: pytest fixture 改造建議**（不阻塞但降風險）。

---

## 7. Placeholder `?` → `%s` 全替換風險 — Major-2

> SD 採「全替換」策略（code-arch.md §1 表 #7 + §8.1）但無精確掃描清單。

### 7.1 SD 的策略

> 「不另寫 dialect 適配層 — 7 個檔總計約 30 個 query，IDE 一次性 find-replace 風險可控」

### 7.2 風險分析

| # | 風險 | 嚴重度 |
|---|------|--------|
| R1 | `?` 是 Python regex / glob 常見字元；IDE 全域 `?` → `%s` 會誤改非 SQL 內容（如 docstring、註解、URL query `?`）。SD 未明示「限定字串字面值」| 高 |
| R2 | Multi-line SQL（三引號 string）中的 `?` 需特別處理 | 中 |
| R3 | 測試檔 `tests/test_auth.py` 內 16+ 處 `?` **不在** SD §8.2 表的 6 個檔清單內 → BE 漏改 → AC-045 fail | 高 |
| R4 | 動態 SQL 字串組裝（雖然本專案應該沒有，但 SD 未明確聲明已掃過 100%）| 低 |
| R5 | SD「預估約 30 個 query」未實際 grep 統計；BE 沒精確基線就動手會漏 | 中 |

### 7.3 Tester 建議

| 動作 | 適用對象 |
|------|---------|
| 補一個精確掃描指令範本（如 `rg "['\"][^'\"]*\?[^'\"]*['\"]" web/auth/`）| SD 補強 §8.2 |
| 統計實際 query count + 逐檔逐行清單 | BE 階段先做 |
| 將 `tests/test_auth.py` 加入 §8.2 表 | SD 補強 |
| 要求 BE 提交 dry-run grep 報告再動手 | PM dispatch 強制 |

**Tester 判定**: **Major-2** — 不阻塞 SD approve（屬可在 BE 補強），但 PM 應在 dispatch BE 時 explicitly mark 為優先項。

---

## 8. verify-spec D1-D9 結果

| 維度 | 結果 | 關鍵發現 |
|------|------|---------|
| **D1 零歧義** | ✅ PASS | API-101 Request/Response/Errors/Logic/驗證規則全齊；8 [BLOCKED_ON_SD] 全解；無 [TBD]/[TODO]；唯一不確定點是 pytest fixture 改造（Major-1）|
| **D2 API 覆蓋率** | ✅ PASS | 8 FR 全部覆蓋；FUNC-101..107 → MOD-101..104 + scripts 完整；無 PAGE → API 映射（UIUX skipped 合理例外）|
| **D3 DB 設計** | ✅ PASS | 3 TBL [REUSE] 完整 PG DDL + 6 索引 + 2 FK 約束顯式命名 + Alembic Python 範本完整；§3 diff 對照表精確；CASCADE / UTF8 / Migration reversibility 全部對齊 |
| **D4 Schema-API 覆蓋** | ✅ PASS_WITH_INFO | API-101 response 欄位 100% 對齊；9 欄 [INTERNAL_ONLY 本 TASK 階段] 註記合理。Info-1: deleted_at 揭露策略 |
| **D5 FE-API 映射** | ✅ PASS | By-design empty + UIUX skipped 證據鏈完整 + §2 替代視角 + §3 觀察者映射；test-sa Minor-2 完整落實 |
| **D6 邏輯完整性** | ✅ PASS | 0 新業務 LOGIC（合法例外）；MOD-104 advisory lock 流程含 Python 範本 + Mermaid（§9）。L1 偵測 false positive |
| **D7 程式碼架構** | ✅ PASS | code-arch.md §2 tree format 完整 + 增量視角清晰；§3 4 個 MOD 實作大綱（每 < 200 行）；§9 依賴圖無循環；§14 [SD建議] 物理隔離 |
| **D8 衝突偵測** | ✅ PASS | 無 [CONFLICT] / [FIELD_GAP]；8 [BLOCKED_ON_SD] 全解；5 [BLOCKED_ON_DEPLOYER] 已在 deploy-env.json 標 status |
| **D9 OpenAPI YAML** | ✅ PASS | api-spec.yaml 3.0.3 / paths=1 / components.schemas=7 / examples 三情境 / securitySchemes=cookieAuth REUSE 但本 API 不用 |

---

## 9. Rule 8 / 11 / 18 Protocol Compliance

| Rule | 結果 | 關鍵驗證 |
|------|------|---------|
| **Rule 8 ID 命名** | ✅ PASS | API-101 在 [101, 200] 範圍 + 單一連續；ERR per-DOMAIN scan：SYS-006 / DB-001..004 / MIGRATION-001..002 均從 max+1 起；3 位零填充全合規 |
| **Rule 11 不可逆操作** | ✅ PASS | FUNC-107 [IRREVERSIBLE] mitigation 完整（14 天 SQLite emergency + scripts/migrate + Railway auto rollback）；FUNC-045 [REUSE IRREVERSIBLE] 嚴格邊界守住；無新業務 DROP COLUMN |
| **Rule 18 Parameter Registry** | ✅ PASS_WITH_INFO | 12 個 env vars 100% 對應 service-contract.yaml + parameter-plan.md 已備齊 bash 命令；SD agent 無 Bash 工具，待 PM 批次執行（Info-3）|

---

## 10. 發現清單

### 🔴 Critical

（無）

### 🟠 Major

#### Major-1: 既有 8 pytest 改造方案缺失（AC-045 風險）

- **位置**: code-arch.md §2 目錄結構（`tests/test_auth.py ✏️ MODIFY — fixture 改 PG`）+ §3.1 MOD-101 REWRITE（後 `init_db()` 等舊接口）+ §6 requirements.txt 無 PG test fixture lib
- **問題**: SD 只用一句話帶過「fixture 改 PG」，未提供具體實作策略；現況 test_auth.py 深度耦合 SQLite（DB_PATH / init_db / 16+ 處 `?` / 整數 0/1 比較 BOOLEAN 等 7 個耦合點 — 見 §6.1）
- **影響**: AC-045「pytest exit code = 0，pass 數 = 8」風險不可量化；fe-api-mapping.md §2 22 AC 驗證方式全為 pytest，連鎖影響 NFR-002 驗收
- **嚴重度**: Major（不阻塞 SD approve，但 BE 階段必須優先處理，否則 test-be 階段會卡住）
- **建議**:
  - 路徑 A: SD 補 SD-SUG-104 「pytest fixture 改造建議」+ 在 BE dispatch prompt 中要求 BE 先設計 fixture 方案再動手
  - 路徑 B: PM 在 dispatch BE 時要求 BE 開工首日提交 fixture 候選方案（testcontainers-python / pytest-postgresql / docker-compose 共用）+ 試跑 1 個 test case 驗證
- **追溯**: AC-045, AC-046, AC-047, NFR-002（既有 22 AC 透過 pytest 驗證）

#### Major-2: Placeholder `?` → `%s` 全替換無精確掃描清單

- **位置**: code-arch.md §1 表 #7 + §8.1 + §8.2「BE 階段執行清單」
- **問題**: SD 採「全替換」策略但 (a) 只「預估約 30 個 query」未實際 grep 統計；(b) `tests/test_auth.py` 不在 §8.2 6 個檔清單中（Tester grep 確認 16+ 處 `?`）；(c) 未限定字串字面值，全域 IDE find-replace 可能誤改 docstring/註解/URL query `?`
- **影響**: BE 階段漏改測試檔 → AC-045 fail；或誤改非 SQL 內容引入新 bug
- **嚴重度**: Major（不阻塞但 BE 必須在「批次替換動作前」先補精確掃描清單）
- **建議**:
  - SD 補：(a) 精確 grep 指令範本（如 `rg "['\"][^'\"]*\?[^'\"]*['\"]" web/auth/`）+ (b) 實際 query count + (c) 將 test_auth.py 加入 §8.2 表 + (d) 限定「字串字面值內的 `?`」
  - 或 PM 在 dispatch BE 時要求 BE 提交 dry-run grep 報告再動手
- **追溯**: 決策 #7（[BLOCKED_ON_SD] placeholder dialect）+ AC-045 + FUNC-105

### 🟡 Minor

#### Minor-1: updated_at App-level 策略無強制機制（INV-101 落實風險）

- **位置**: code-arch.md §3.3（MOD-103 `update_with_timestamp` helper 標「選擇性使用」）+ §9 依賴圖標「選擇性」邊 + §14 SD-SUG-102（標 [SD建議] 不強制）+ db-schema.md §7.1（範本顯示對錯）
- **問題**: 決策 #6 採 App-level + helper 封裝，但 helper 為「可選用」（依賴圖明示）+ lint rule 標 [SD建議] 非強制；INV-101「每次 UPDATE 必更新 updated_at」完全靠 grep + 人類自律
- **影響**: 一個漏掉的 UPDATE（特別是後續 TASK BE 新增的 UPDATE）會破壞 INV-101，但短期不可見（updated_at 仍會有預設值 NOW() 但不會反映實際更新時間）→ 未來 audit / sync 出錯
- **嚴重度**: Minor（不影響本 TASK 22 AC，但長期風險）
- **建議**: SD-SUG-102 應升級為「BE 階段強制」— 在 BE dispatch prompt 中要求 BE 加 lint rule（如 ruff custom rule / pre-commit hook 偵測 `UPDATE\s+\w+\s+SET[^;]*?(?!.*updated_at)`）
- **追溯**: INV-101 + 決策 #6 + SD-SUG-102

#### Minor-2: MOD-103 重複定義 dialect 適配層（自相矛盾）

- **位置**: code-arch.md §3.3「MOD-103 職責 #3：提供 placeholder dialect 適配層（雖然全替換 `?` → `%s`，但 helper 集中讓未來 driver 切換更容易）」
- **問題**: 決策 #7 已明示「不另寫 dialect 適配層 — 全替換 `?` → `%s`」（code-arch.md §1.7 + db-schema.md §1 #7）；但 §3.3 MOD-103 職責 #3 又標「提供 dialect 適配層」— 兩處表述矛盾
- **影響**: BE 困惑 — 到底要不要寫 adapter？讀 §1 / §8 認為「不寫」，讀 §3.3 認為「寫一個薄的」
- **嚴重度**: Minor（語意不一致影響 D1 零歧義）
- **建議**: SD 修訂 §3.3 「職責 #3」描述 — 改為「未來 driver 切換的 anchor 點（本 TASK 不實作 adapter 邏輯，僅做為 future-proof 名義位置）」或刪除整條職責 #3
- **追溯**: D1 零歧義 + 決策 #7

#### Minor-3: TBL-003 created_at backfill 「meaningful 預設」假設未驗證

- **位置**: code-arch.md §5.2「`email_verification_tokens.created_at` backfill = `expires_at - INTERVAL '24 hours'`」
- **問題**: SD 假設既有 token 有效期 = 24 小時，但未說明假設來源；若 TASK-001 設計過更短/更長有效期（如 1 小時 / 7 天）此 backfill 會有誤差
- **影響**: FUNC-106 一次性匯入腳本在非空 SQLite 檔上跑會給出「假的 created_at」
- **嚴重度**: Minor（生產為空表，影響有限；本機/staging 若有非空 SQLite 會誤差）
- **建議**: SD 在 §5.2 補一行「假設來源：既有 web/auth/email_service.py 設定 `expires_at = now + timedelta(hours=24)`」（Tester 已驗證此假設正確），或在腳本內加 CLI flag `--token-validity-hours` 預設 24
- **追溯**: FUNC-106 + AC-056

#### Minor-4: API-101 路徑 `/api/db/healthz` 命名違反 api-conventions

- **位置**: api-spec.md §5 + §2.2
- **問題**: api-conventions.md v1.1 §1 URL 命名規範要求 kebab-case + 複數；`/api/db/` 為單數技術術語；`healthz` 為 k8s 慣例但與既有 `/api/auth/me` / `/api/auth/verify` 等也屬單數的「brownfield grandfather」風格延續
- **影響**: 命名不一致但功能不影響
- **嚴重度**: Minor（SD 已自評並標 [SD建議]，brownfield grandfather 容忍）
- **建議**: 接受現狀 + SD §5 [SD建議] 留 v2 API 時修正；或在 api-conventions.md §1 補一條「`/health*` 端點允許 k8s 慣例命名」豁免條款（走 RFC）
- **追溯**: api-conventions.md §1 + SD §5

### 🔵 Info

#### Info-1: L1 規則建議強化（識別 [REUSE] / [DEFERRED] / 教學範本）

- **位置**: `scripts/sdlc-role-verify.sh` 4 failed checks
- **問題**: 本 TASK 4/4 都是 L1 false positive（無業務 LOGIC / [REUSE] 引用被當重複 / UIUX skipped / DROP 在教學範本內）；屬於 SDLC 框架可改善點
- **建議**: 框架層級在 sdlc-role-verify.sh 加入 `[REUSE]` / `[DEFERRED]` / 「未來 TASK 範本」標記識別
- **追溯**: SDLC 框架改善（不阻塞 SD）

#### Info-2: TBL-003 baseline gap 假設來源建議揭露

- **位置**: db-schema.md §2.3 + code-arch.md §5.2
- **問題**: 同 Minor-3 — 但屬 Info 等級（重複提及）
- **建議**: SD 補一行假設來源說明
- **追溯**: 同 Minor-3

#### Info-3: Rule 18 parameter_added 12 events 待 PM 批次執行

- **位置**: SD self-review.json `param_registry_status`
- **問題**: SD agent 無 Bash 工具直接執行 sdlc-journal-write.sh；deploy/parameter-plan.md §1.1-1.12 已備齊 bash 命令；待 PM approve 階段批次執行（PM 複製貼上 §1.1-1.12 即可）
- **建議**: PM 在 approve TASK-002 SD 階段時，批次執行 12 個 parameter_added events；Tester 不扣分（屬 SDLC 框架限制非 SD 過失）
- **追溯**: Rule 18 + parameter-plan.md

---

## 11. 追溯矩陣

### 11.1 發現 ↔ 規格 ID

| Finding ID | 規格追溯 | 對應 SD artifact |
|------------|---------|----------------|
| Major-1 (pytest fixture) | @traces_to(AC-045), @traces_to(NFR-002), @traces_to(FR-001) | code-arch.md §2 / §3.1 / §6 |
| Major-2 (placeholder 替換) | @traces_to(決策#7), @traces_to(AC-045), @traces_to(FUNC-105) | code-arch.md §1.7 / §8.1 / §8.2 |
| Minor-1 (updated_at App-level) | @traces_to(INV-101), @traces_to(決策#6) | code-arch.md §3.3 / §9 / db-schema.md §7 |
| Minor-2 (MOD-103 adapter 矛盾) | @traces_to(D1 零歧義), @traces_to(決策#7) | code-arch.md §3.3 vs §1.7 + §8 |
| Minor-3 (TBL-003 backfill 假設) | @traces_to(FUNC-106), @traces_to(AC-056) | code-arch.md §5.2 |
| Minor-4 (API-101 命名) | @traces_to(api-conventions §1), @traces_to(API-101) | api-spec.md §5 |
| Info-1 (L1 規則改善) | @traces_to(SDLC framework) | scripts/sdlc-role-verify.sh |
| Info-2 (TBL-003 假設揭露) | @traces_to(Minor-3) | code-arch.md §5.2 |
| Info-3 (Rule 18 PM 批次執行) | @traces_to(Rule 18), @traces_to(parameter-plan §1.1-1.12) | sd/self-review.json |

### 11.2 8 FR 覆蓋驗證

| FR | SD 落實位置 | 驗收方式 | 風險 |
|----|------------|---------|-----|
| FR-001 連線層替換 | code-arch.md §3.1 MOD-101 REWRITE + §8.2 6 檔 ✏️ MODIFY | AC-044 (smoke test) + AC-045 (8 pytest) | Major-1（pytest fixture）|
| FR-002 三表 schema 重建 | db-schema.md §2.1-2.3 完整 DDL | AC-046 (\\d 比對) + AC-047 (約束) | 無 |
| FR-003 正式 migration 工具 | code-arch.md §3.2 Alembic 配置 | AC-048 (grep ALTER TABLE 0 hits) + AC-049 (檔名正則) | 無 |
| FR-004 補 timestamp 欄位 | db-schema.md §2 + §4.3 Migration 2 | AC-050 + AC-051 | 無 |
| FR-005 env vars 註冊 | code-arch.md §3.1 + §12 + parameter-plan.md | AC-052 (.env.example) + AC-053 (shared/parameter-registry) | Info-3（待 PM 執行）|
| FR-006 Railway 部署切換 | API-101 + service-contract.yaml | AC-054 (deploy log) + AC-055 (5 步驟 smoke) | 無 |
| FR-007 既有資料遷移 | code-arch.md §5 scripts/migrate_sqlite_to_postgres.py | AC-056 (匯入 3/2/1 對應) | Minor-3（backfill 假設）|
| FR-008 全環境 PG | code-arch.md §7 docker-compose.yml | AC-057 (pytest 連 PG) | Major-1（同 FR-001）|

### 11.3 4 個 [CROSS-TASK: TASK-001] 落實

詳見 §5 — 4/4 marker 完整落實。

### 11.4 8 個 [BLOCKED_ON_SD] 解決

詳見 §3 — 6 reasonable + 2 reasonable_with_caveat（衍生 Major-2 + Minor-1）。

---

## 12. 結論

- **測試結果**: ✅ **CONDITIONAL PASS**（Critical = 0，但 2 個 Major 需在 BE 階段優先解決）
- **阻塞項**: 0
- **建議 PM 行動**:
  1. Approve SD 階段（Critical = 0）
  2. **強烈建議** dispatch BE 時，dispatch prompt 中明確標示「優先解決 Major-1 + Major-2」+ 引用本報告 §6 + §7 + §10
  3. 執行 12 個 Rule 18 parameter_added events（parameter-plan.md §1.1-1.12 — 複製貼上即可）
  4. （可選）回覆 SD 是否修訂 Minor-2（MOD-103 §3.3 vs §1.7 矛盾）— 屬於零歧義小修

- **如果 SD 不修訂任何項目**:
  - SD approve 仍然成立（CONDITIONAL PASS）
  - BE 階段風險: Major-1 / Major-2 須由 BE 階段補強，可能延長 BE 開工首日的設計時間（~半天）

- **如果 SD 願意補修 Major-1**（補 SD-SUG-104 pytest fixture 改造建議）+ Minor-2（修 §3.3 矛盾）:
  - 可升級為 PASS（無條件通過）
  - BE 階段風險降低

---

## 13. Tester 立場聲明

- 本報告為**獨立第三方對抗心態驗證**，不為 SD 93/100 self-review 背書
- 採用「找不到 bug = Tester 失敗」的對抗心態
- L1 4 失敗項全部判定為 false positive，與 PM 判定一致（4/4 同意），但 1 個衍生 Major-1
- 8 個 [BLOCKED_ON_SD] 全部可接受，但 2 個 caveat 衍生 Major-2 + Minor-1
- API-101 判定 IN_SCOPE（非越界）
- 4 個 [CROSS-TASK: TASK-001] 落地完整
- 既有 8 pytest 相容性 = Major-1（不阻塞 SD，必須在 BE 階段優先處理）
- Placeholder 全替換風險 = Major-2（不阻塞 SD，必須在 BE 階段優先處理）

**簽署**: Testing (TASK-002 test-sd) / 2026-06-10
