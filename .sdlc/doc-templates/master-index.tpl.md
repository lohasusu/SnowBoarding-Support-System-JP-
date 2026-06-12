---
document_id: "MASTER-INDEX-v1.0"
title: "全域 ID 目錄（Master Index）"
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

# 全域 ID 目錄（Master Index）

> **用途**: SDLC 全流程所有 ID 類型的權威清單 — 一份文件看懂「全世界有哪些 ID、格式、誰產生、關聯誰」。
> **維護者**: PM（ID 規範變更時同步更新）。
> **查閱時機**: 任何角色遇到 ID 相關決策（新增 / 引用 / 衝突 / 跨 TASK）時先查此表。
> **配套文件**:
> - `id-registry.md` — 實際 ID 登記（FUNC-001/ENTITY-001 等實例）
> - `page-index.md` / `component-index.md` / `deploy-index.md` — 領域總表
> - `error-codes.md` — 錯誤碼登記
> - `terminology.md` — 業務術語統一

---

## 1. 快速索引（Quick Lookup）

| 前綴 | 類別 | 產生階段 | 範圍 | 領域總表 |
|------|------|---------|------|---------|
| FR | 功能需求 | BA | TASK 內 | ba-index.md |
| NFR | 非功能需求 | BA | TASK 內 | ba-index.md |
| BR | 業務規則 | BA | TASK 內 | ba-index.md |
| AC | 驗收標準 | BA | FR 內 | ba-index.md |
| BF | 業務流程 | BA | TASK 內 | ba-index.md |
| ROLE | 角色 | BA | 全域 | ba-index.md |
| CONST | 約束 | BA | TASK 內 | ba-index.md |
| ASSUME | 假設 | BA | TASK 內 | ba-index.md |
| FUNC | 功能 | SA | 全域 | sa-index.md |
| MOD | 模組 | SA | 全域 | sa-index.md |
| ENTITY | 實體 | SA | 全域 | sa-index.md |
| PATTERN | 設計模式 | SA | 全域 | sa-index.md |
| PAGE | 頁面 | UIUX | 全域 | page-index.md |
| COMP | 元件 | UIUX | 全域 | component-index.md |
| FLOW | 使用者流程 | UIUX | TASK 內 | uiux-index.md |
| LAYOUT | 共用佈局 | UIUX | 全域 | uiux-index.md |
| TOKEN | Design Token | UIUX | 全域 | uiux-index.md |
| API | API 介面 | SD | 全域 | sd-index.md |
| TBL | 資料表 | SD | 全域 | sd-index.md |
| LOGIC | 業務邏輯 | SD | TASK 內 | sd-index.md |
| ERR | 錯誤碼 | SD | 全域 | error-codes.md |
| TEST | 測試案例 | Tester | TASK 內 | tester-index.md |
| CR | Code Review 發現 | Code Review | TASK 內 | tester-index.md |
| SEC | 資安發現 | Deployer | TASK 內 | tester-index.md |
| TASK | 任務 | PM | 全域 | state.json |

---

## 2. 詳細規格（By Stage）

### 2.1 BA 階段

#### FR（功能需求）
- **格式**: `FR-NNN`（3 位零填充，如 `FR-001`）
- **範圍**: TASK 內連續，跨 TASK 引用用 `TASK-001/FR-001`
- **產生**: BA 從使用者原文萃取
- **必要欄位**: 來源、驗收標準（AC）
- **關聯**: → AC（1:N）、→ FUNC（N:M，SA 聚合）

#### NFR（非功能需求）
- **格式**: `NFR-NNN`
- **範圍**: TASK 內連續
- **必要欄位**: 量化指標（不可用模糊語言）

#### BR（業務規則）
- **格式**: `BR-NNN`
- **範圍**: TASK 內連續
- **關聯**: → LOGIC（SD 階段實作）

#### AC（驗收標準）
- **格式**: `AC-NNN`（全域連續 — 跨 FR 不重置）
- **範圍**: 全域
- **關聯**: 每個 AC 必須有唯一的 `parent_fr` 欄位指向 FR-ID
- **舊格式**: 不再使用 `FR-001.AC-1`（巢狀編號），改為獨立 `AC-NNN`

#### BF（業務流程）
- **格式**: `BF-NNN`
- **範圍**: TASK 內
- **關聯**: → FR（N:M）、→ ROLE（N:M）

#### ROLE（角色）
- **格式**: `ROLE-NNN`
- **範圍**: 全域
- **跨 TASK**: 角色定義後全域共用，後續 TASK 直接引用

#### CONST / ASSUME（約束 / 假設）
- **格式**: `CONST-NNN` / `ASSUME-NNN`
- **範圍**: TASK 內

### 2.2 SA 階段

#### FUNC（功能）
- **格式**: `FUNC-NNN`
- **範圍**: **全域連續**（跨 TASK 不重置）
- **關聯**: ← FR（BA 需求聚合）、→ MOD（部署於模組）、→ PAGE（UIUX 設計）、→ API（SD 規格）

#### MOD（模組）
- **格式**: `MOD-NNN`
- **範圍**: 全域
- **關聯**: → ENTITY（擁有）、→ API（提供）

#### ENTITY（實體）
- **格式**: `ENTITY-NNN`
- **範圍**: 全域
- **關聯**: → TBL（SD 對應實體資料表）、← API（API 操作此實體）

#### PATTERN（設計模式）
- **格式**: `PATTERN-NNN`
- **範圍**: 全域

### 2.3 UIUX 階段

#### PAGE（頁面）
- **格式**: `PAGE-NNN`（可帶子類 `PAGE-017a`，見第 4 節子類規則）
- **範圍**: 全域
- **關聯**: ← FUNC（實現功能）、→ COMP（包含元件）、→ FLOW（流程中出現）
- **必要欄位**: 路由、對應功能、所屬 App（若多 App）
- **配套**: 每個 PAGE 在 Pencil 中有對應 Frame（見 `pencil-node-mapping.md`）

#### COMP（元件）
- **格式**: `COMP-NNN`
- **範圍**: 全域
- **關聯**: ← PAGE（被頁面使用）、→ TOKEN（引用設計變數）
- **必要欄位**: Props、狀態變體、尺寸
- **跨 TASK**: 重用時標記 `[REUSE: COMP-001, from TASK-001]`

#### FLOW（使用者流程）
- **格式**: `FLOW-NNN`
- **範圍**: TASK 內
- **關聯**: ← FUNC（實現）、→ PAGE（步驟經過頁面）

#### LAYOUT（共用佈局）
- **格式**: `LAYOUT-NNN`（如 Header/Sidebar/Footer）
- **範圍**: 全域
- **定義位置**: `sitemap.md` 第 2 章

#### TOKEN（Design Token）
- **格式**: `TOKEN-{category}-{name}`（如 `TOKEN-color-primary-500`）
- **範圍**: 全域
- **定義位置**: `design-system.md`
- **使用**: FE 階段禁止裸值，必須引用 Token

### 2.4 SD 階段

#### API（介面）
- **格式**: `API-NNN`
- **範圍**: 全域
- **關聯**: ← COMP（前端呼叫）、→ ENTITY（操作實體）、→ ERR（可能拋出錯誤碼）
- **必要欄位**: 方法、路徑、Request/Response、錯誤碼表、業務邏輯步驟
- **配套**: `api-spec.yaml` OpenAPI 3.0

#### TBL（資料表）
- **格式**: `TBL-NNN`
- **範圍**: 全域
- **關聯**: ← ENTITY（資料表對應實體）

#### LOGIC（業務邏輯）
- **格式**: `LOGIC-NNN`
- **範圍**: TASK 內
- **關聯**: ← BR（實作業務規則）、← API（被 API 呼叫）

#### ERR（錯誤碼）
- **格式**: `ERR-{DOMAIN}-NNN`（如 `ERR-AUTH-001`、`ERR-USER-001`）
- **範圍**: 全域
- **定義位置**: `error-codes.md`
- **關聯**: ← API（哪些 API 可能回傳此錯誤，反向追溯欄位）

### 2.5 FE / BE 階段

- FE / BE **不產生新 ID**，只實作 SD 已定義的 ID
- 報告文件（`frontend-report.md` / `backend-report.md`）僅引用現有 ID

### 2.6 Tester / Code Review / Deployer 階段

#### TEST（測試案例）
- **格式**: `TEST-NNN`
- **範圍**: TASK 內
- **必要欄位**: `@traces_to({SPEC-ID})` — 100% 追溯需求

#### CR（Code Review 發現）
- **格式**: `CR-NNN`
- **範圍**: TASK 內
- **分級**: Critical / Warning / Info

#### SEC（資安發現）
- **格式**: `SEC-{LEVEL}-NNN`（如 `SEC-CRIT-001`、`SEC-HIGH-001`）
- **LEVEL**: CRIT / HIGH / MED / LOW
- **範圍**: TASK 內

### 2.7 PM 階段

#### TASK（任務）
- **格式**: `TASK-NNN`（3 位零填充，**全域統一，不可用 TASK-1 / TASK-01**）
- **範圍**: 全域
- **維護位置**: `state.json`、`audit.log`

---

## 3. 文件 ID（document_id）

文件 ID 用於 frontmatter 的 `document_id` 欄位，不參與業務引用。

| 文件 | document_id 格式 |
|------|------------------|
| 需求規格 | `REQ-{TASK-ID}-v{version}` |
| 業務流程 | `BF-{TASK-ID}-v{version}` |
| 系統架構 | `ARCH-{TASK-ID}-v{version}` |
| 功能流程 | `FUNC-{TASK-ID}-v{version}` |
| 欄位規格 | `FIELD-{TASK-ID}-v{version}` |
| 設計系統 | `DS-{TASK-ID}-v{version}` |
| Sitemap | `SM-{TASK-ID}-v{version}` |
| 風格方向 | `STYLE-{TASK-ID}-v{version}` |
| 線框圖 | `WF-{TASK-ID}-v{version}` |
| User Flow | `UF-{TASK-ID}-v{version}` |
| 頁面索引 | `PAGEIDX-SHARED-v{version}` |
| 元件索引 | `COMPIDX-SHARED-v{version}` |
| 視覺比對 | `VISCOMP-{TASK-ID}-v{version}` |
| API 規格 | `API-{TASK-ID}-v{version}` |
| DB Schema | `DB-{TASK-ID}-v{version}` |
| 程式碼架構 | `CODEARCH-{TASK-ID}-v{version}` |
| 邏輯流程 | `LOGIC-{TASK-ID}-v{version}` |
| FE 報告 | `FERPT-{TASK-ID}-v{version}` |
| BE 報告 | `BERPT-{TASK-ID}-v{version}` |
| 測試規格 | `TESTSPEC-{TASK-ID}-v{version}` |
| 測試報告 | `TEST-{TASK-ID}-v{version}` |
| Code Review | `CRREVIEW-{TASK-ID}-v{version}` |
| 部署配置 | `DEPCONF-{TASK-ID}-v{version}` |
| CI/CD | `CICD-{TASK-ID}-v{version}` |
| 部署索引 | `DEPLOY-SHARED-v{version}` |
| 部署結果 | `DEPRESULT-{TASK-ID}-v{version}` |
| 資安報告 | `SECR-{TASK-ID}-v{version}` |
| 分支策略 | `BRANCH-SHARED-v{version}` |
| 術語表 | `TERM-SHARED-v{version}` |
| ID 註冊表 | `IDREG-SHARED-v{version}` |
| Master Index | `MASTER-INDEX-v{version}` |

---

## 4. 通用命名規則

### 4.1 基本格式
- **數字**: 3 位零填充（`001`、`017`、`100`、`999`）
- **從 001 起編**：不得從 000 起
- **大寫字母**：前綴必須大寫（`FUNC-001` 而非 `func-001`）

### 4.2 子類規則（subtype）
- 格式: `{PREFIX}-{NNN}{letter}`（小寫字母 a-z）
- 用途: 原 ID 的變體或細分，如 `PAGE-017a` 是 `PAGE-017` 的子頁面
- **不可跳過母 ID**：必須先有 `PAGE-017` 才能有 `PAGE-017a`
- **連續**：子類從 `a` 起編，不可跳號（`a` → `b` → `c`，不可 `a` → `c`）

### 4.3 跳號規則
- **嚴禁跳號**：`FUNC-001` 後必須是 `FUNC-002`，不可跳到 `FUNC-005`
- **刪除不跳號**：若 `FUNC-003` 被刪除，`FUNC-002` 後仍直接是 `FUNC-004`（不重用 003）
- **例外**：App 命名空間預留範圍時，允許段落式跳號（如 admin 001-099，portal 101-199）— 需在 `id-registry.md` 登記範圍

### 4.4 ID 刪除與重用
- **永不重用**：一旦指派給某實體的 ID，即使該實體被刪除，ID 也不可分配給其他實體
- **標記作廢**：刪除的 ID 在 `id-registry.md` 標記 `[DEPRECATED: TASK-NNN]`，不從表中移除
- **理由**：保持歷史 commit / audit.log / 測試報告的追溯性

### 4.5 跨 TASK 引用
- 格式: `TASK-NNN/{ID}`（如 `TASK-001/FR-003`）
- 全域連續 ID（FUNC/ENTITY/API/PAGE/COMP 等）可省略 TASK 前綴
- TASK 內 ID（FR/NFR/BR/LOGIC 等）跨 TASK 引用時**必須**加前綴

---

## 5. 反向追溯欄位（MANDATORY）

以下 ID 類型必須維護反向追溯欄位，方便「被誰用」查詢：

| ID 類型 | 反向欄位 | 查詢問題 |
|---------|---------|---------|
| ENTITY | `used_by_apis: [API-NNN, ...]` | 「這個 Entity 被哪些 API 操作？」 |
| ERR | `thrown_by_apis: [API-NNN, ...]` | 「這個錯誤碼會被哪些 API 拋出？」 |
| TBL | `used_by_entities: [ENTITY-NNN, ...]` | 「這張表對應哪個 Entity？」 |
| TOKEN | `used_by_comps: [COMP-NNN, ...]` | 「這個 Token 被哪些元件引用？」 |
| COMP | `used_by_pages: [PAGE-NNN, ...]` | 「這個元件出現在哪些頁面？」 |
| PAGE | `implements_funcs: [FUNC-NNN, ...]` | 「這個頁面實作哪些功能？」 |
| FR | `implemented_by_apis: [API-NNN, ...]`、`implemented_by_pages: [PAGE-NNN, ...]` | 「這個需求由誰實現？」 |

> PM 於每階段 approved 時負責更新反向欄位。

---

## 6. 外部工具 ID 綁定

以下為外部工具產生的 ID，需與 SDLC 內部 ID 建立對應關係（詳見 `rules/sdlc-external-id-binding.md`）：

| 外部工具 | 外部 ID 格式 | 綁定 SDLC ID | 對應文件 |
|---------|--------------|--------------|---------|
| Pencil 節點 | `node-xxxxxx` | PAGE-NNN / COMP-NNN | `pencil-node-mapping.md` |
| Pencil Frame | `frame-xxxxxx` | PAGE-NNN | `pencil-node-mapping.md` |
| Pencil Variant | `variant-xxxxxx` | COMP-NNN 的狀態 | `pencil-node-mapping.md` |
| Pencil Variable | `var-xxxxxx` | TOKEN-* | `design-system.md` |
| i18n Key | `{ns}.{key}` | COMP-NNN 的文字屬性 | `i18n-registry.md` |
| Git Commit | SHA | TASK-NNN / Phase | `audit.log` |
| Git Branch | `{prefix}/{TASK-ID}/...` | TASK-NNN | `branch-strategy.md` |
| Docker Image | `{service}:{tag}` | MOD-NNN | `deploy-config.md` |
| CI/CD Job | `job-{name}` | Phase | `cicd-spec.md` |

---

## 7. ID 驗證腳本

執行完整 ID 健康檢查：

```bash
# 見 scripts/sdlc-id-guard.sh
bash scripts/sdlc-id-guard.sh {TASK-ID}
```

檢查項目：
- [ ] 所有全域連續 ID 無跳號
- [ ] 所有全域連續 ID 無重複
- [ ] 跨 TASK 引用格式正確（`TASK-NNN/{ID}`）
- [ ] 子類 ID 有對應母 ID
- [ ] 反向追溯欄位一致（ENTITY.used_by_apis 與實際 API 定義一致）
- [ ] DEPRECATED ID 未被重用

---

## 8. 變更流程

修改本文件必須走以下流程：

1. PM 提出變更提案（說明理由與影響範圍）
2. 評估對既有 TASK 產出的影響
3. 更新本文件 + 相關 template + 相關 rules
4. 在 `audit.log` 記錄 `master_index_updated | {變更項目}`
5. 通知所有進行中 TASK 的角色
