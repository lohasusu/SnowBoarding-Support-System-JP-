---
document_id: "IDREG-SHARED-v1.0"
title: "跨 TASK ID 註冊表（語意目錄）"
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

# 跨 TASK ID 註冊表（語意目錄）

> **用途**: 記錄全域 ID 的**語意**（每個 ID 是什麼、屬於哪個 TASK、是否 DEPRECATED）。
> **⚠️ 本表不維護「下一個可用 ID」— 依 Rule 8.7 採 scan-based 發號**
> **發號方式**: PM 派發 BA/SA/UIUX/SD 前呼叫 `bash scripts/sdlc-id-scan.sh {PREFIX}`，將結果透過 dispatch prompt 傳給角色 agent（agent 本身不執行 git 指令）
> **維護者**: PM（每個階段 approved 後追加**語意行**）
> **角色存取**: 所有角色唯讀；僅 PM 寫入新語意

## 1. 全域連續 ID（語意登記）

### ENTITY（實體）

| ENTITY-ID | 名稱 | 定義於 TASK | SA field-spec 位置 | 狀態 |
|-----------|------|-----------|-------------------|------|

### API（介面）

| API-ID | 方法 | 路徑 | 定義於 TASK | SD api-spec 位置 | 狀態 |
|--------|------|------|-----------|-----------------|------|

### COMP（元件）

| COMP-ID | 名稱 | 所屬 App | 定義於 TASK | UIUX component-spec 位置 | 狀態 |
|---------|------|---------|-----------|-------------------------|------|

#### App 命名空間範圍（若啟用多 App）

| App | COMP 範圍 | 說明 |
|-----|----------|------|

> 範例: admin 001-099, portal 101-199。單 App 專案不需設定。
> 注意: 預留範圍只是登記，發號時仍由 scan-based 自動遵循該範圍內的 max + 1。

### PAGE（頁面）

| PAGE-ID | 名稱 | 所屬 App | 定義於 TASK | UIUX wireframes 位置 | 狀態 |
|---------|------|---------|-----------|---------------------|------|

### MOD（模組）

| MOD-ID | 名稱 | 定義於 TASK | SA system-arch 位置 | 狀態 |
|--------|------|-----------|-------------------|------|

### FUNC（功能）

| FUNC-ID | 名稱 | 定義於 TASK | SA functional-flow 位置 | 狀態 |
|---------|------|-----------|------------------------|------|

### TBL（資料表）

| TBL-ID | 名稱 | 對應 ENTITY | 定義於 TASK | SD db-schema 位置 | 狀態 |
|--------|------|-------------|-----------|-------------------|------|

### ERR（錯誤碼）

> 詳細資料見 `shared/error-codes.md`；本表僅登記已使用的 DOMAIN 清單。

| DOMAIN | 首次使用 TASK | 說明 |
|--------|-------------|------|
| SYS | — | 系統級錯誤 |
| AUTH | — | 認證授權錯誤 |
| USER | — | 使用者輸入錯誤 |
| DATA | — | 資料完整性錯誤 |
| VAL | — | 驗證錯誤 |

### LAYOUT（共用佈局）

| LAYOUT-ID | 名稱 | 定義於 TASK | UIUX sitemap 位置 | 狀態 |
|-----------|------|-----------|-------------------|------|
| LAYOUT-001 | Header | — | sitemap.md §2 | Active |
| LAYOUT-002 | Sidebar | — | sitemap.md §2 | Active |
| LAYOUT-003 | Footer | — | sitemap.md §2 | Active |

### AC（驗收標準）

| AC-ID | 所屬 FR | 定義於 TASK | BA requirement-spec 位置 | 狀態 |
|-------|---------|-----------|-------------------------|------|

### ROLE（角色）

| ROLE-ID | 名稱 | 定義於 TASK | BA 位置 | 狀態 |
|---------|------|-----------|--------|------|

## 2. TASK 範圍 ID（每個 TASK 獨立編號）

以下 ID 類型在每個 TASK 內獨立編號，跨 TASK 引用時需加 TASK 前綴。

| ID 類型 | 格式 | 跨 TASK 引用格式 | 說明 |
|---------|------|-----------------|------|
| FR | FR-001 | TASK-001/FR-001 | 功能需求 |
| NFR | NFR-001 | TASK-001/NFR-001 | 非功能需求 |
| BR | BR-001 | TASK-001/BR-001 | 業務規則 |

## 3. 狀態欄位定義

- **Active**: 正常使用中
- **[DEPRECATED: TASK-NNN abandoned]**: 所屬 TASK 被 /sdlc:abandon，按 Rule 8.4 ID 永不重用
- **[DEPRECATED: superseded by {ID}]**: 被其他 ID 取代（罕見，需 SA/SD 決策）

## 4. 更新規則

1. **PM 職責**: 每個階段 approved 後，PM 從角色產出中提取新 ID 並**追加語意行**到本表
2. **角色職責**: 開始工作前讀取本表了解已分配 ID 的語意；發號時走 Rule 8.7 的 scan-based 方式
3. **衝突處理**: scan-based 發號天然避免衝突（單人本地），若發生則視為 agent 錯誤執行 scan
4. **DEPRECATED 維護**: `/sdlc:abandon` 會自動把該 TASK 的 ID 狀態標記為 DEPRECATED；`/sdlc:unabandon` 會恢復為 Active
