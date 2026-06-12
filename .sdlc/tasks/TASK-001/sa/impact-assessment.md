---
document_id: "IMPACT-TASK-001-v1.0"
title: "跨 TASK 影響評估 — TASK-001 brownfield 補追溯"
version: "1.0"
date: "2026-06-04"
author: "SA"
status: "Draft"
task_id: "TASK-001"
phase: "sa"
mode: "brownfield-document"
source_documents:
  - "ARCH-TASK-001-v1.0"
  - "FUNC-TASK-001-v1.0"
  - "FIELD-TASK-001-v1.0"
  - "REQ-TASK-001-v1.0 (§9.1 + BACKLOG 規劃)"
change_history:
  - version: "1.0"
    date: "2026-06-04"
    changes: "初始 — TASK-001 為第一個 TASK 無前 TASK 影響；本檔僅列「未來 TASK 修改本 TASK 產出」的候選清單"
    author: "SA"
---

# 跨 TASK 影響評估 — TASK-001 brownfield 補追溯

> **狀態說明**: TASK-001 是專案第一個 TASK，**無前 TASK 產出可引用 / 依賴 / 重用**。標準的「BA 階段 FR → 共享層交叉比對」影響矩陣（DEPENDS / EXTENDS / CROSS-TASK / REUSE 標記）**N/A**。
>
> **本檔用途**: 反向預告 — 列出**後續 TASK 可能修改 TASK-001 產出**的候選清單，給未來 SA 階段參考 Rule 6 跨 TASK 修改協議。

---

## 1. TASK-001 與前 TASK 的影響矩陣（N/A — 第一個 TASK）

| FR | 依賴前 TASK ENTITY | 擴展前 TASK MOD | 修改前 TASK PAGE | 重用前 TASK COMP |
|----|--------------------|----------------|------------------|------------------|
| FR-001..017 | (無前 TASK) | (無前 TASK) | (無前 TASK) | (無前 TASK) |

**結論**: 本 TASK 從零建立規格（ENTITY-001..003、TBL-001..003、MOD-001..006、FUNC-001..045、PATTERN-001..008），無跨 TASK 引用需求。

---

## 2. 共享層讀取狀態（PR 13 Rule 7 / 9 / 10 對照）

| 共享層檔案 | 讀取狀態 | 內容狀態 | 影響 |
|-----------|---------|---------|------|
| `shared/id-registry.md` | ✅ 讀取 | **空白**（第一個 TASK）| 從 dispatch prompt 配額 ENTITY/MOD/FUNC/PATTERN/TBL 各 1-100 起編 |
| `shared/terminology.md` | ✅ 讀取 | 26 條（BA 階段已寫入）| 全部引用既有，未重定義 |
| `shared/MASTER-INDEX.md` | ✅ 讀取 | 通用 ID 規則 | 遵循 Rule 8 ID 規範 |
| `shared/sa-index.md` | ✅ 讀取 | 通用模板初始狀態 | 將被 PM Step 2.8 更新本 TASK 的 MOD/FUNC/PATTERN 索引 |
| `shared/api-conventions.md` | (由 conventions/api-conventions.md 替代) | locked v1.1 | brownfield grandfather 28 端點 |
| `shared/error-codes.md` | ✅ 讀取 | 空白 | TASK-001 不引入 ERR-NNN（留 SD 階段 + TASK-002+） |
| `shared/code-registry.md` | ✅ 讀取 | 模板初始 | TASK-001 不引入新 source file（brownfield-document） |
| `shared/page-index.md` (app 層) | ✅ 讀取 | 空白 | PAGE-001..007 留 UIUX 階段編號 |
| `shared/component-index.md` (app 層) | ✅ 讀取 | 空白 | COMP 留 UIUX 階段（baseline §2.4 提及 ~30 個 JS 行為片段，需 UIUX 評估升級為 COMP）|
| `shared/.abandoned-tasks.txt` | ✅ 嘗試讀取 | **不存在** | N/A — 無放棄 TASK |

---

## 3. 後續 TASK 修改 TASK-001 候選清單（給未來 SA 階段參考）

> 以下清單為**預告**，TASK-002+ 的 SA 在執行對應 BACKLOG / HOTFIX 時，必須依 Rule 6 跨 TASK 修改協議：
> 1. SA 在 functional-flow.md 標 `[CROSS-TASK: TASK-001 / 修改項目 / 原因]`
> 2. UIUX 修改既有 Pencil 頁面（若涉及 PAGE）
> 3. SD 明確列出跨 TASK 修改項
> 4. FE/BE 嚴格限定範圍照做

### 3.1 HOTFIX 候選（high priority — 用戶選「立即修」）

| Hotfix Branch | TASK-001 受影響項目 | 修改類型 | 觸發 BA Q |
|--------------|-------------------|---------|----------|
| `hotfix/auth-security-hardening` | FUNC-030（登入 JWT + cookie） | Cookie Secure 從寫死 False → env-aware（`Secure=True` 當 prod HTTPS）| Q-009 / HOTFIX-A |
| `hotfix/auth-security-hardening` | MOD-005 啟動邏輯（SECRET_KEY 讀取）| 移除 fallback 字串 → fail-fast on startup | Q-010 / HOTFIX-B |
| `hotfix/auth-security-hardening` | FUNC-042（`/api/auth/verify` 維運 API） | 加 admin token gate（防 user enumeration）| Q-006 / HOTFIX-C |
| `hotfix/remove-env-check` | API-009（`/api/env-check` debug endpoint）— **未進本 TASK SA 編號**（因屬未來 SD 階段 API 範圍） | 直接刪除 endpoint | Q-015（commit 132e0bb 已存在）|

### 3.2 TASK-002 主軸候選（SQLite → Postgres + 用戶資料持久化）

| 修改 ID | TASK-001 受影響項目 | 修改類型 | 觸發 BACKLOG |
|---------|-------------------|---------|--------------|
| TBL-001/002/003 schema | ENTITY-001/002/003 + TBL-001/002/003 | 加 `updated_at`、`deleted_at`（軟刪）；email_verification_tokens 加 `created_at` | BACKLOG-007/008/014 |
| 連線層 | MOD-005 `database.py` | SQLite → Postgres（用 asyncpg 或 SQLAlchemy）；引入 Repository Pattern | BACKLOG-008 + SA-SUG-004 |
| 軟刪行為 | FUNC-045 收藏刪除 | 從 `DELETE` 改為 `UPDATE SET deleted_at=now`；所有 SELECT 加 `WHERE deleted_at IS NULL` filter | BACKLOG-007 |
| Rate limit | FUNC-034 重寄驗證信 | 加 in-memory / Redis rate limit（每 email 每 60 秒最多 1 次）| BACKLOG-006 |
| Migration | TBL-001/002/003 | 走 db-conventions v1.1 §5 expand-contract（建議 Alembic 或純 SQL + Flyway）| BACKLOG-008 |

### 3.3 TASK-002+ 規格目標值更新候選

| 修改 ID | TASK-001 受影響項目 | 修改類型 | 觸發 BACKLOG / Q |
|---------|-------------------|---------|------------------|
| NFR-001 timeout | FUNC-002 / FUNC-012 雪票批次/Excel | 45 秒 → 30 秒 | BACKLOG-001 / Q-001 |
| NFR-003 JWT 有效期 | FUNC-030 / FUNC-040 登入/OAuth | 7 天 → 1 天 | BACKLOG-002 / Q-002 |
| NFR-006 密碼複雜度 | FUNC-022 註冊密碼驗證 | ≥ 8 字元 → ≥ 12 + 數字 + 字母 | BACKLOG-003 / Q-003 |
| NFR-010 寄信失敗行為 | FUNC-027 / FUNC-034 寄信子流程 | silent + log → 用戶可見錯誤 + 重寄鈕 | BACKLOG-004 / Q-004 |
| BR-009 OAuth redirect | FUNC-040 OAuth callback | `/plan` → `/`（首頁） | BACKLOG-005 / Q-005 |
| 新增 NFR-019 | FUNC-042 verify endpoint | 加 admin token / API key 保護 | Q-006（與 HOTFIX-C 合併處理）|

### 3.4 TASK-003+ 技術重構候選

| 修改 ID | TASK-001 受影響項目 | 修改類型 | 觸發 BACKLOG |
|---------|-------------------|---------|--------------|
| BACKLOG-009 v2 API | 全部 28 端點（API-001..028 由 SD 階段建立後）| 引入 v2 命名（複數）+ 統一 `{data, message, error: {code, message}}` 格式 + 引入 ERR-* 錯誤碼 | BACKLOG-009 / Q-013 |
| BACKLOG-010 dead code | MOD-004 backends/ | 移除 Travelpayouts/Amadeus 殘留 backend 檔；標 [DEAD-CODE] | BACKLOG-010 / Q-012 |
| MOD-005 分層重構 | MOD-005 內部結構 | flat → `controllers/services/repositories/models/middleware/`（baseline M-10）| SA-SUG-001 |
| Vue 重構 | FR-016 PAGE-001..007 | Jinja2 SSR → Vue SPA（config.json 宣告目標）| 未列入 BACKLOG，留長期規劃 |
| Redis 分散式鎖 | PATTERN-008（per-process asyncio.Lock）| 改 Redis SETNX / Redlock；配合多 worker 部署 | SA-SUG-005 |

---

## 4. Rule 6 跨 TASK 修改協議檢查清單（給未來 SA 階段）

當 TASK-002+ SA 接到 BACKLOG / HOTFIX 任務時，**必須**：

1. **在 functional-flow.md 標 `[CROSS-TASK: TASK-001 / 修改項目 / 原因]`**
   - 範例：`[CROSS-TASK: TASK-001 / FUNC-030 改 Cookie Secure 為 env-aware / 安全強化 HOTFIX-A]`

2. **列出受影響的 ENTITY/API/COMP/PAGE**
   - TASK-001 已建立的：MOD-001..006, PATTERN-001..008, FUNC-001..045, ENTITY-001..003, TBL-001..003
   - 後續 SD/UIUX 將建立：API-001..028（28 端點）, PAGE-001..007（8 頁含 LAYOUT-001）, COMP-XXX（依 UIUX 設計）

3. **UIUX 階段配合**（若涉及 PAGE 變更）:
   - **修改原有 Pencil 頁面**，不新建
   - 確保視覺稿同步

4. **SD 階段明確列出跨 TASK 修改項**:
   - api-spec.md 或 fe-api-mapping.md 標明哪些 TASK-001 端點需要修改
   - 提供新版實作方式

5. **FE/BE 嚴格限定範圍**:
   - 只改 SD 明確指定的項目
   - 違反 → Tester 階段 Critical

---

## 5. TASK-001 階段內檔案受其他 sub agent 修改的預期

| 階段 | 預期修改 TASK-001 SA 產出? | 說明 |
|------|--------------------------|------|
| test-sa | **唯讀**（測試驗證） | Tester 跑 sdlc-role-verify.sh sa；只讀不改 SA 產出 |
| uiux | **唯讀**（讀 SA 規劃 PAGE）| UIUX 階段定義 PAGE-001..007（不修改 SA） |
| deploy-init | **唯讀**（讀架構決定 deploy 模式）| Deploy-init 階段（如需要）|
| sd | **唯讀**（讀 SA 決定 API/DB schema）| SD 階段建立 API-001..028 + db-schema.md（不修改 SA） |
| fe / be | **唯讀** | FE/BE 階段依 SD 產出實作 |
| code-review / build-gate / deploy / test | **唯讀** | — |

→ **TASK-001 內**，SA 產出在 sa 階段完成後**理應不再被修改**；後續若需修訂走 `/sdlc:revise` 重新進入 sa 階段。

---

## 6. 自我驗證

| 檢查項 | 通過 | 說明 |
|--------|------|------|
| 共享層讀取完整（10 個檔）| ✅ | §2 表格逐項標狀態 |
| 第一個 TASK 影響矩陣為 N/A 已說明 | ✅ | §1 + §2 |
| 未來修改 TASK-001 候選清單完整 | ✅ | §3.1/3.2/3.3/3.4 共 4 類分組 |
| 對應 Rule 6 / BA 階段 BACKLOG 一致 | ✅ | 全部對應 BACKLOG-001..010 + HOTFIX-A/B/C + SA-SUG-001..006 |
| Rule 6 協議步驟說明完整 | ✅ | §4 給後續 SA 參考 |
