---
document_id: "TEST-REPORT-SA-TASK-002-v1.0"
title: "SA 階段獨立測試報告 — TASK-002 SQLite → PostgreSQL 遷移"
version: "1.0"
date: "2026-06-08"
author: "Tester (independent)"
task_id: "TASK-002"
phase: "test-sa"
被測對象:
  - ".sdlc/tasks/TASK-002/sa/system-arch.md (ARCH-TASK-002-v1.0)"
  - ".sdlc/tasks/TASK-002/sa/functional-flow.md (FUNC-TASK-002-v1.0)"
  - ".sdlc/tasks/TASK-002/sa/field-spec.md (FIELD-TASK-002-v1.0)"
  - ".sdlc/tasks/TASK-002/sa/pattern-spec.md (PATTERN-TASK-002-v1.0)"
  - ".sdlc/tasks/TASK-002/sa/impact-assessment.md (IMPACT-TASK-002-v1.0)"
  - ".sdlc/tasks/TASK-002/sa/self-review.json (SA agent 自評 93/PASS)"
驗證基準:
  - ".sdlc/tasks/TASK-002/ba/requirement-spec.md (8 FR / 12 NFR / 7 BR / 14 AC)"
  - ".sdlc/tasks/TASK-002/ba/business-flow.md (3 BF)"
  - ".sdlc/tasks/TASK-002/test-ba/test-report-ba.md (2 Minor / 3 Info)"
  - ".sdlc/conventions/db-conventions.md (v1.1 locked 2026-06-03)"
  - ".sdlc/conventions/code-conventions.md (v1.1)"
  - ".sdlc/shared/id-registry.md / terminology.md"
  - "web/auth/database.py (現況真相 1-54 行)"
  - ".sdlc/baseline/baseline-audit-2026-06-03.md"
驗證方法論:
  - "~/.claude/skills/sdlc/tools/verify-architecture/SKILL.md (D1-D5)"
  - "Tester rules 1-4 (獨立 / 規格優先 / Critical 阻塞 / 100% 追溯)"
  - "Rule 6 / 8 / 11 / 13 / 18 protocols"
status: "Complete"
result: "PASS"
---

# SA 階段獨立測試報告 — TASK-002

## 1. 驗證摘要

| 指標 | 結果 |
|------|------|
| 檢查維度 | D1 追溯 / D2 架構合理 / D3 技術對齊 / D4 完整性 / D5 流程驗證 + Rule 6/8/11/13/18 protocol 合規 + 9 個 PM 重點關注項 |
| 檢查項目數 | 50 |
| 通過 | 47 |
| Critical（🔴 必須修正，阻塞下階段）| **0** |
| Major（🟠 建議修正，但不阻塞）| **0** |
| Minor（🟡 改善建議）| **3** |
| Info（🔵 參考）| **5** |
| **結論** | **✅ PASS**（無 Critical / Major；3 Minor 不阻塞 UIUX/Deploy-init/SD 階段） |

---

## 2. 獨立驗證 — L1 verify FAIL 三項 false positive 判定

> PM 觀察 SA L2 self-review 93/PASS 但 L1 sdlc-role-verify.sh 報 80/4-FAIL，判定 3 項為 false positive。Tester 獨立交叉驗證如下。

**L1 重跑結果（Tester 獨立執行）**: 80/4-FAIL，3 失敗項與 PM 觀察一致：
1. `[system-arch.md] 缺少章節: 系統架構圖`
2. `[functional-flow.md] 缺少章節: 功能模組`
3. `[field-spec.md] ENTITY ID 重複: ENTITY-001`

### L1 失敗項 #1: 「system-arch.md 缺少章節：系統架構圖」

- **抓到位置**: L1 grep `^## .*系統架構圖` 在 system-arch.md 無命中
- **實際內容**: SA 用 `## 2. 系統邊界圖（C4-Container 風格 — 增量視角）` 章節（line 63），下方為標準 mermaid `flowchart TB` 圖（line 65-123 含 13 個節點 + 完整連線 + classDef 樣式）
- **獨立判定**: ✅ **FALSE POSITIVE**
- **理由**:
  1. 「系統邊界圖（C4-Container 風格）」是業界標準的系統架構表達方式（C4 model），內容更完整（含 boundary / container / external system 三層）
  2. L1 腳本用字面 grep 「系統架構圖」過於僵化；template 規範若用 C4 命名法應被接受
  3. 實際內容已涵蓋系統架構圖該有的所有元素（節點、邊界、依賴方向、外部系統、新增/重用區分）
- **L1 修正建議**（不阻塞 SA）: regex 應接受 `(系統架構圖|系統邊界圖|系統上下文圖|Context Diagram|Container Diagram)` 任一名稱

### L1 失敗項 #2: 「functional-flow.md 缺少章節：功能模組」

- **抓到位置**: L1 grep `^## .*功能模組` 在 functional-flow.md 無命中
- **實際內容**: SA 用 `## 1. 功能清單（FUNC-101..107，共 7 個新 FUNC + 45 個 [REUSE]）` + `## 2. 功能流程` 兩個章節組合
- **獨立判定**: ✅ **FALSE POSITIVE**
- **理由**:
  1. 「功能清單 + 功能流程」是 SDLC functional-flow.md 的標準結構（functional-flow.tpl.md 模板本身就用這兩個 heading）
  2. 「功能模組」是 system-arch.md 的概念（對應 MOD-XXX），不屬於 functional-flow.md
  3. L1 腳本誤把 system-arch 的章節名套到 functional-flow 上
- **L1 修正建議**（不阻塞 SA）: 對 functional-flow.md 改 grep `(功能清單|功能流程|Functional Flow|Function List)`，不要用 system-arch 的 schema

### L1 失敗項 #3: 「field-spec.md ENTITY ID 重複: ENTITY-001」

- **抓到位置**: ENTITY-001 在 field-spec.md 出現 9 次（line 46, 56, 110, 358, 379, 388 等）
- **實際內容**: ENTITY-001 (users) 有單一定義在 §1 實體清單 + §2 ENTITY-001 細節章節 + §3 ER 圖 + §8 追溯矩陣多處引用
- **獨立驗證**: `grep -nE '^### ENTITY-001' field-spec.md` 結果 — 找到 1 個 heading `### ENTITY-001 / TBL-001: users（使用者帳號）`（line 56），**僅單一定義**
- **獨立判定**: ✅ **FALSE POSITIVE**
- **理由**:
  1. 模板要求一個 ENTITY 在多處出現（摘要表 + 細節章節 + ER 圖 + 追溯矩陣），是合法 template 結構
  2. L1 腳本若計算 ID 字串總次數 > 1 = 重複，會誤殺所有合法 SA 產出
  3. 真正的 ID 重複應該是「兩個不同實體共用同一 ID」如 `### ENTITY-001: A` 和 `### ENTITY-001: B`
- **L1 修正建議**（不阻塞 SA）: regex 改為偵測 `^### ENTITY-NNN[:\s/]` heading 重複，與 BA `### FR-NNN` 相同邏輯（test-ba 也有相同 false positive，Tester 已建議 L1 修正）

### Tester 對 PM L1 false positive 判斷的結論

✅ **3/3 false positive 判斷正確**。SA agent **不應**為了討好 L1 字面檢查而修改：
- 不應把「系統邊界圖（C4-Container 風格）」改為「系統架構圖」— C4 命名更精確
- 不應把 functional-flow 的「功能清單 + 功能流程」改為「功能模組」— 違反 template 結構
- 不應為 ENTITY-001 多次引用做手腳 — template 設計即如此

**Tester 對 PM 的 L1 腳本改進建議**（記於本報告 §11 Info-1）:
1. `sdlc-role-verify.sh sa` 對 3 個失敗項目皆應改用 `^### {PREFIX}-NNN[:\s/]` heading 偵測，並接受 C4 model 命名同義詞
2. 此問題影響所有 SA 階段 TASK；建議列為 SDLC 工具改進待辦

---

## 3. D1 追溯矩陣雙向驗證

### 3.1 正向：BA FR → SA FUNC / MOD / ENTITY

| BA FR | 對應 FUNC | 對應 MOD | 對應 ENTITY | 結果 |
|-------|----------|---------|------------|------|
| FR-001 PostgreSQL 連線層替換 | FUNC-101, FUNC-102, FUNC-105 | MOD-101, MOD-103, MOD-104, MOD-005(替換) | ENTITY-001/002/003 [REUSE] | ✅ |
| FR-002 三表 schema 重建 | FUNC-103 | MOD-102 | ENTITY-001/002/003 | ✅ |
| FR-003 正式 migration 工具 | FUNC-103, FUNC-104 | MOD-102 | — | ✅ |
| FR-004 補 updated_at / deleted_at | FUNC-103 (合併) 或 FUNC-104 (分拆) | MOD-102 | ENTITY-001/002/003 | ✅ |
| FR-005 環境變數新增 | FUNC-101 (consume) | MOD-101 | — | ✅ |
| FR-006 Railway 部署設定 | FUNC-107 | MOD-104 | — | ✅ |
| FR-007 既有資料遷移 | FUNC-106 (fallback), FUNC-107 (cutover IRREVERSIBLE) | (跨 MOD-101/102/104 + scripts/) | ENTITY-001/002/003 | ✅ |
| FR-008 全環境統一 PG | FUNC-101 + docker-compose (BF-001) | MOD-101 | ENTITY-001/002/003 | ✅ |

**正向覆蓋**: 8/8 FR 全部對應到至少 1 個新 FUNC + 至少 1 個新 MOD → ✅ PASS

### 3.2 反向：SA FUNC / MOD / ENTITY → BA FR

| SA 元素 | 對應 FR | 結果 |
|---------|---------|------|
| FUNC-101 連線池初始化 | FR-001, FR-005 | ✅ |
| FUNC-102 連線池釋放 | FR-001 | ✅ |
| FUNC-103 Schema migration | FR-002, FR-003 | ✅ |
| FUNC-104 補軟刪欄位 migration | FR-004 | ✅ |
| FUNC-105 query 適配層 | FR-001 | ✅ |
| FUNC-106 SQLite 匯入腳本 | FR-007 | ✅ |
| FUNC-107 Production 切換 [IRREVERSIBLE] | FR-006, FR-007 | ✅ |
| MOD-101 postgres_db | FR-001, FR-005, FR-008 | ✅ |
| MOD-102 migrations | FR-003, FR-004 | ✅ |
| MOD-103 auth_repositories（最小封裝） | FR-001 | ✅ |
| MOD-104 db_bootstrap | FR-001, FR-003, FR-006 | ✅ |
| PATTERN-101 Migration Versioning + Reversibility + Expand-Contract | FR-003, FR-004 | ✅ |
| **新增 ENTITY** | 無新增（全部 [REUSE]） | ✅ |

**反向覆蓋**: 12/12 SA 新增元素全部追溯到 FR → ✅ PASS。**無孤兒功能**。

### 3.3 模組依賴追溯

```
main.py [REUSE]
  → MOD-104 db_bootstrap (startup hook)
       → MOD-101 postgres_db
       → MOD-102 migrations
            → (可選) MOD-101
            → PostgreSQL
  MOD-005 auth [REUSE 邊界]
       → MOD-103 auth_repositories (最小封裝，過渡期)
            → MOD-101
       → MOD-101 (直接，過渡期)
```

**循環依賴檢測**: DFS 驗證 — 無環。
- main → MOD-104 → MOD-101/102 (單向)
- MOD-102 → MOD-101 (單向)
- MOD-005 → MOD-103 → MOD-101 (單向)
- MOD-005 → MOD-101 (單向，過渡期 inline)
- 任何節點皆無回流路徑

✅ **無循環依賴** → PASS

**D1 結果**: 4/4 通過

---

## 4. D2 架構合理性

| 檢查項 | 結果 | 證據 |
|--------|------|------|
| 無循環依賴 | ✅ | §3.3 DFS 檢測 |
| 耦合度合理 | ✅ | MOD-101 被 4 個 MOD 依賴（Ca=4 < 10）；MOD-005 對外依賴 MOD-103/101（Ce=2 < 10）；MOD-102 對外依賴 MOD-101/PG（Ce=2）。全部低於門檻 |
| 單一職責 | ✅ | 每個 MOD 職責描述清晰且專注（MOD-101=連線池 / MOD-102=migration / MOD-103=repo 封裝 / MOD-104=startup hook）— 4 個 MOD 職責互不重疊 |
| 無單點故障（架構層）| ⚠️ Info | PostgreSQL 為單一資料庫實例（Railway addon 或外部託管）— 屬資料層 SPoF；但 NFR 未要求高可用，且 baseline 既有架構亦為單實例 SQLite，本 TASK 不應引入 read replica（CONST-001/006 + 範圍邊界）。標 Info-2 給後續 TASK 參考 |
| 模組邊界清晰 | ✅ | 每個 MOD 有「職責 / 輸入 / 輸出 / 依賴 / 介面契約」5 元素 |
| 介面契約明確 | ✅ | MOD-101 `get_conn()` 「介面語意 100% 相同；唯一差別 conn 物件型別」(system-arch §3 line 167-173) — 向後相容約束清楚 |

**D2 結果**: 5/5 通過（1 Info — 資料層 SPoF 屬於範圍外）

---

## 5. D3 技術對齊

| 檢查項 | 結果 | 證據 |
|--------|------|------|
| 技術選型對齊 config.json | ✅ | PostgreSQL 16 / postgres:16-alpine / port 5432 / envPrefix=`POSTGRES_` 完全一致；TASK-001 brownfield grandfather 在本 TASK 解決 — system-arch.md §4 表 |
| BLOCKED_ON_SD 委派合理 | ⚠️ Minor-1 | 8 個 [BLOCKED_ON_SD] 委派；其中 6 個合理（driver / migration tool / pool lib / 觸發策略 A vs B / FUNC-103-104 分拆 / `updated_at` trigger）；2 個邊界模糊（見 Minor-1） |
| BLOCKED_ON_DEPLOYER 委派合理 | ✅ | 5 個 [BLOCKED_ON_DEPLOYER]（Railway addon vs 外部 / SSL / Backup / SLA dashboard / volume 命名）全部屬部署層決策 |
| NFR-001 持久性架構滿足 | ✅ | PostgreSQL 為持久 storage + Railway container ephemeral 分離 — system-arch §5.1 |
| NFR-002 行為不變保證 | ⚠️ Minor-2 | SA 在 system-arch §3 MOD-005 / FUNC-105 多處聲明「外部行為不變」；但**未在 SA 文件中提供任何測試錨點**讓 Tester 驗證 22 個既有 AC（見 Minor-2） |
| NFR-003/004 效能架構量化 | ✅ | system-arch §5.2 表含 baseline 取得方法（解 test-ba MINOR-2）— 「8 個 pytest 平均 + 5 個關鍵 endpoint `ab -n 100 -c 1` P95」 |
| NFR-005 連線池量化 | ✅ | min=2/max=10 / timeout < 5s / 20 並行不丟連線（system-arch §5.2）— 與 BA NFR-005 一致 |
| NFR-006/007/008 可維護性架構 | ✅ | PATTERN-101 三大支柱完整對應 — pattern-spec §2.2 |

**D3 結果**: 6/8 PASS, 2 Minor（見 §11）

---

## 6. D4 文件完整性

| 檢查項 | 結果 | 證據 |
|--------|------|------|
| 5 個 SA 文件齊備 | ✅ | system-arch / functional-flow / field-spec / pattern-spec / impact-assessment + self-review.json |
| 所有必填章節已填寫 | ✅ | 無 TODO / TBD 殘留；8 個 [BLOCKED_ON_SD] + 5 個 [BLOCKED_ON_DEPLOYER] 為合法委派標記 |
| Mermaid 語法正確 | ✅ | 獨立檢視 8 個 mermaid 圖（system-arch §2 系統邊界 + §8.3 依賴；functional-flow FUNC-101/103/106/107 + §3 關係圖；field-spec §3 ER 圖）— 節點 / 箭頭 / classDef 語法正確 |
| ID 唯一連續 | ✅ | MOD-101..104 連續；FUNC-101..107 連續；PATTERN-101 單一 |
| 文件 metadata 完整 | ✅ | 5 個檔案 document_id / version / date / source_documents (8+) / change_history 全填 |
| 章節編號合規 | ⚠️ Minor-3 | pattern-spec.md 無 `### PATTERN-101:` heading（用 `## 2. PATTERN-101 詳細規格` 二級）— 與 system-arch.md MOD 用 `### MOD-101:`、functional-flow.md FUNC 用 `### FUNC-101:` 風格不一致；可能引發 L1 對 PATTERN 的 heading 偵測 false positive |

**D4 結果**: 5/6 PASS, 1 Minor

---

## 7. D5 功能流程驗證

| 檢查項 | 結果 | 證據 |
|--------|------|------|
| 每個 FUNC 有流程圖 | ✅ | FUNC-101 sequenceDiagram / FUNC-103 sequenceDiagram / FUNC-106 flowchart / FUNC-107 sequenceDiagram；FUNC-102/104/105 為簡單動作或屬於既有 query 適配（流程已在母流程內），未獨立繪圖屬合理 |
| 狀態轉換完整 | ✅ | FUNC-101 含「env 缺失 / auth failed / connection refused / pool timeout」4 個異常路徑；FUNC-103 含「已套用 / 未套用 / SQL 失敗 ROLLBACK」三分支；FUNC-107 含「migration 失敗 auto rollback / smoke test fail / 5xx 上升」三條 BF-003 路徑 |
| 異常處理 | ✅ | 4 個有圖 FUNC 都有「異常流程」表 |
| 欄位規格對齊 | ✅ | field-spec §2 三表欄位 vs functional-flow FUNC-103/104/105/106 使用欄位 — 對齊一致（含 `is_verified` BOOLEAN / TIMESTAMPTZ / FK CASCADE 等） |
| FUNC ↔ ENTITY 一致性 | ✅ | impact-assessment §1.1 + field-spec §8.1 雙重交叉 |

**D5 結果**: 5/5 PASS

---

## 8. PM 9 個重點關注項獨立評估

### 8.1 L1 verify 衝突獨立判斷

詳見 §2。**3/3 false positive 判斷正確**；SA 不應修改文件；建議改 L1 腳本。

### 8.2 4 個 [CROSS-TASK: TASK-001] 標記合規性（Rule 6）

**獨立 grep 統計**: `[CROSS-TASK:` 在 SA 5 個檔案出現 38 次（除 self-review.json 6 次），證明 4 個標記在多處交叉引用。

| # | 標記內容 | 三要素檢核 | 影響評估 | rollback plan |
|---|----------|-----------|---------|--------------|
| 1 | `[CROSS-TASK: TASK-001 / TBL-001 (users) 補 updated_at + deleted_at 欄位 / 觸發 FR-004]` | ✅ 源(TASK-001) + 項(TBL-001 補欄) + 原因(FR-004) | ✅ impact-assessment §1.1 列下游影響（SD 寫 DDL / BE 寫 migration / Tester 驗 AC-050/051） | ✅ FUNC-103/104 down 操作明確 |
| 2 | TBL-002 同上 | ✅ 三要素齊 | ✅ 同上 | ✅ |
| 3 | TBL-003 同上（含補 created_at 補 baseline gap）| ✅ 三要素齊 + 補充 baseline gap | ✅ 同上 + field-spec §2 ENTITY-003 標明來源 | ✅ |
| 4 | `[CROSS-TASK: TASK-001 / MOD-005 auth.database storage engine 替換 / 觸發 FR-001]` | ✅ 三要素齊 | ✅ impact-assessment §1.1 列下游（SD 在 api-spec/logic-flow 明示 28 endpoint 簽名不變但底層適配；Tester 驗 AC-044/045） | ✅ MOD-005「邊界不變、實作替換」+ NFR-002 既有 22 AC 保證 |

**獨立判定**: ✅ **4/4 合規**。BA self-review.json `cross_task_modify_warnings` 4 項 100% 落實。

**下游 API/COMP/PAGE 影響評估涵蓋性**:
- API：28 個 endpoint 行為不變（NFR-002 + AC-045）— SA 明確列在 system-arch §3 MOD-005
- COMP / PAGE：本 TASK 無 UI 變更，影響評估 §6.1 → UIUX 階段建議「極簡或 skip」
- 與 TASK-001 in-progress uiux 衝突評估：見 §8.8

### 8.3 0 新 ENTITY / 0 新 TBL 合理性

**Tester 獨立判斷**: ✅ **合理且符合 Rule 7 重用優先原則**。

理由:
1. **本 TASK 屬「基礎設施重構」而非「新建業務功能」**：FR-001..008 全部聚焦 storage engine 替換 + schema 補欄位 + migration 工具導入 — 無任何 BA FR 要求新建業務實體
2. **「補欄位」應視為 ENTITY 的 [REUSE + 擴充]，非 NEW ENTITY**：
   - 若改為 NEW ENTITY-101 = users_v2，將造成：
     - 同一張表（users）有兩個 ENTITY ID — 違反 ID 一致性
     - TASK-001/ENTITY-001 永遠殘留作廢
     - 應用層所有引用 ENTITY-001 的 SA/SD 文件需要 cross-task 修改改為 ENTITY-101
   - SA 用 [REUSE: from TASK-001] + [CROSS-TASK: 補欄位] 是更乾淨的設計
3. **Rule 7 明示「重用優先」**：「已存在的元件/API/錯誤碼應優先重用（標記 `[REUSE: ID, from TASK-N]`），不可重新定義」
4. **field-spec.md §1 末段明確說明** ID 範圍 101-200 保留作未來擴充，邏輯清楚

**Tester 不採納「應改 NEW ENTITY」建議**。0 新 ENTITY / 0 新 TBL 為正確設計。

### 8.4 PATTERN-101 設計合理性

**Tester 獨立判斷**: ✅ **設計合理，不需拆分為 2 個 PATTERN**。

理由:
1. **跨檔通用性檢核**：PATTERN-101 跨 FUNC-103 + FUNC-104 + 跨 MOD-102 + MOD-104 — 符合 PATTERN 編號規則「跨 ≥2 FUNC 或 跨 ≥1 MOD」（pattern-spec §1）
2. **三大支柱（Versioning / Reversibility / Expand-Contract）邏輯緊密耦合**：
   - Versioning 不能無 Reversibility（無 down 的 migration 等於不能 version）
   - Expand-Contract 是 Reversibility 在「DROP COLUMN」場景的特化（不是獨立 pattern，是 reversibility 的高級用法）
   - 三者共用同一個 migration runner（MOD-102）和同一套規範性範本（pattern-spec §2.4）
3. **拆成 2 個 PATTERN 的反例**：
   - 若拆「PATTERN-101 Migration Versioning」+「PATTERN-102 Expand-Contract」，則 Reversibility 需要分到哪個？兩個 PATTERN 都需要 reversibility 機制 — 邏輯切割困難
   - 後續 TASK 引用時兩個 PATTERN 總是一起出現，沒有獨立使用情境
4. **後續 TASK 重用性**：impact-assessment §5 列出 6 個未來 TASK 候選會引用 PATTERN-101（soft-delete / password-reset / oauth-upsert-race-fix / auth-layering / 任何 schema 變更 / 任何 DROP COLUMN）— 重用性高
5. **命名建議**：當前命名「Migration Versioning + Reversibility + Expand-Contract」雖長但語意完整；可簡化為「Reversible Migration」但喪失 Expand-Contract 顯示性

**結論**: ✅ 不拆分；命名可保留現狀。SA 設計合理。

### 8.5 FUNC-107 [IRREVERSIBLE] 標記與緩解充足性（Rule 11.1）

**四要素檢核**:

| 要素 | 內容 | 結果 |
|------|------|------|
| description | 「Production 部署切換 ★ [IRREVERSIBLE]」+ functional-flow.md FUNC-107 6 步驟詳細流程 | ✅ |
| business impact | line 397-398 「資料層：SQLite ephemeral 殘留資料丟棄屬於 hard-delete 變體 / 業務層：切換到 PG 後若回到 SQLite 期間 PG 寫入資料 rollback 後消失」 | ✅ |
| when triggered | line 334-342 「通過所有 SDLC 階段（test-be PASS）後，ROLE-004 發起 production 切換」+ 前置條件 5 項 | ✅ |
| mitigation | line 399 「14 天 SQLite emergency path 保留 + rollback plan 必填 + BF-003 緊急回滾流程」三層緩解 | ✅ |

**14 天 SQLite emergency path 雙處覆蓋**:
- functional-flow.md: line 341, 379, 381, 394, 399, 405（6 處）
- impact-assessment.md: line 175（明示 deploy/service-contract.yaml rollback plan 內容）
- ✅ 雙處明確

**rollback 觸發條件清晰度**:
- functional-flow FUNC-107 「異常 / 回滾流程」表（line 388-394）明確列 4 個觸發點：
  1. migration 失敗 → Railway healthcheck fail → auto rollback
  2. smoke test 失敗 → 立即手動 rollback（ROLE-004 決定）
  3. 60 分鐘監控 5xx 異常 → 觸發 BF-003（ROLE-004 + ROLE-003 共同決定）
  4. 14 天 window 後發現 → 走完整 SDLC 新開 TASK
- ✅ **誰決定 / 什麼條件清楚**（部分自動 / 部分人為決策已明示）

**Tester 判定**: ✅ **緩解充足，標記合規**。Rule 11.1 四要素齊。

**SD/UIUX/FE/BE 下游責任（Rule 11.2）**:
- functional-flow line 400-405 明確列出 5 個角色責任：
  - SD: service-contract.yaml rollback plan / 無需 confirm 參數（部署層而非 API 層）
  - UIUX: N/A
  - FE: N/A
  - BE: Migration 三段式能力 + 連線錯誤訊息不洩漏 password
  - Tester: §5.9 D9 維度
- ✅ Rule 11.2 落實完整

### 8.6 13 個 [BLOCKED] 委派合理性

**8 個 [BLOCKED_ON_SD] 獨立評估**:

| BLOCKED 項 | 應由誰決定？ | 評估 |
|-----------|------------|------|
| Postgres driver 選型 | SD ✅ | 實作 lib 選型，SD 階段標準範圍 |
| Migration 工具選型 | SD ✅ | 同上 |
| Connection pool library | SD ✅ | 實作 lib + SA 已給 NFR-005 量化指標 |
| Migration 觸發策略 A vs B（startup auto vs CI/CD）| SD ✅ | NFR-003 啟動時間約束已給；SD 依此微調 |
| FUNC-103/104 分拆 vs 合併 | SD ✅ | 屬實作粒度選擇，SD 階段決策 |
| `updated_at` 刷新策略（應用層 SET vs trigger）| SD ✅ | 屬於實作機制選擇 |
| SQL placeholder 適配策略（`?` → `%s` 全替換 vs adapter layer）| SD ✅ | 屬於程式重構策略 |
| `lastrowid` 替換策略（`RETURNING id` vs driver）| SD ✅ | 同上 |

✅ **8/8 委派合理**。SA 規範行為（NFR / FR / 介面契約），SD 規範實作（具體 lib / 程式策略）— 邊界清晰。

**5 個 [BLOCKED_ON_DEPLOYER] 獨立評估**:

| BLOCKED 項 | 應由誰決定？ | 評估 |
|-----------|------------|------|
| Railway PG addon vs 外部託管（Supabase / Neon）| Deployer ✅ | 部署平台層決策 |
| SSL 模式（sslmode=require）| Deployer ✅ | 部署層安全配置 |
| Backup 策略 | Deployer ✅ | 部署平台特性 |
| Production SLA dashboard 監控（5xx / connection error / migration log）| Deployer ✅ | 部署層監控 |
| docker-compose volume 命名 / 路徑 | Deployer ✅ | 部署層 |

✅ **5/5 委派合理**。

**Tester 判定**: 13/13 [BLOCKED] 委派全部合理。**無真實阻塞**（皆為合法委派標記，不算 TODO/遺漏）。

### 8.7 NFR-002 「100% 既有 22 AC 通過」可測性

**追溯到 BA NFR-002**：「TASK-001 既有 AC-015~AC-036 共 22 個驗收標準在本 TASK 部署後仍全數通過」

**SA functional-flow 是否設計測試錨點？** ⚠️ **Minor-2 — 設計不足**

獨立檢視:
- FUNC-105 適配層 (line 247-285) 提到「對應 AC：AC-045 (既有 8 pytest 通過)」— 但 AC-045 只涵蓋 pytest，**不涵蓋 22 個 AC 中的手動驗證項**（如 OAuth callback 完整流程、Email 驗證連結點擊、cookie SameSite 設定等）
- functional-flow §1.2 [REUSE 表] (line 60-67) 列出 TASK-001 既有 FUNC-022..045 「底層 query 改 PG，外部行為不變」— 但**未明示哪些 cookie / JWT / email 流程被影響**
- system-arch §3 MOD-005 (line 252-274) 明示「28 個 API endpoint 的 status code / response body / cookie 設定 / redirect URL 完全不變」— 但**未列出哪 22 個 AC 被涵蓋、要怎麼測**

**MOD-005 driver 替換後 cookie/JWT/email 流程影響評估**:
| TASK-001 機制 | 受 FUNC-105 影響？ | SA 是否說明？ |
|--------------|------------------|------------|
| Cookie 設定（PATTERN-007 HTTP-only）| ❌ 不受 DB 影響 | ✅ pattern-spec §1.2 line 56「不變」 |
| JWT 簽發 / 驗證 | ❌ 不受 DB 影響（純 in-memory） | ⚠️ 未明示 |
| OAuth state 驗證 | ❌ 不受 DB 影響（純 cookie） | ⚠️ 未明示 |
| OAuth Upsert（PATTERN-006 SELECT then INSERT/UPDATE）| ✅ 受 FUNC-105 query 適配影響 | ✅ pattern-spec §1.2 line 56 標明 |
| Email 驗證 token CRUD（FUNC-026/028/034）| ✅ 受 FUNC-105 影響 | ✅ functional-flow §1.2 提及 |
| 登入時 SELECT user by email | ✅ 受 FUNC-105 影響 | ⚠️ 未明示 |
| 收藏 CRUD（FUNC-044/045）| ✅ 受 FUNC-105 影響 | ⚠️ 未明示 |
| is_verified 0/1 → BOOLEAN | ✅ 移除 adapter（FUNC-105） | ✅ 明確列出 |

**Tester 判定**: ⚠️ **Minor-2** — SA 對「22 個 AC 哪些被影響、如何驗證」說明不夠系統化；應補一個明確的「TASK-001 既有 22 AC 影響評估表」讓 Tester / BE 可逐條驗收。

不過此屬於「補強說明」而非「設計錯誤」— SA 的設計（NFR-002 強制 + MOD-005 邊界不變）邏輯正確，只是缺少**逐 AC 對照表**讓下游驗收簡化。

### 8.8 跨 TASK 修改對 TASK-001 in-progress uiux 階段衝突評估

**獨立調查**:
- TASK-001 currentPhase: 從 git log 與 brownfield-document 模式可知 — 補追溯既有 8 PAGE，**不寫新 UI 代碼**
- 補 timestamp 欄位（updated_at / deleted_at / created_at）為**後端 schema 層變更**，**不對應任何 UI 元件**：
  - 既有 web/static/js/ 4 個 js 檔（ski / flight / plan / auth）無 timestamp 渲染
  - 既有 web/templates/*.html 無 timestamp 顯示
  - 既有 API response 28 endpoint 不暴露 timestamp 欄位（NFR-002 強制不變）
- MOD-005 storage engine 替換為**內部實作替換**，外部行為（API response / cookie / status code）不變 → UIUX 看不到變化

**Tester 判定**: ✅ **不會破壞 TASK-001 in-progress uiux**。

**SA impact-assessment §6.1** (line 152-160) 已明確記錄此結論：「因本 TASK 為純後端重構，UIUX 階段可能極簡（或 PM 評估後 skip）」+ 建議聲明 `[NO_UI_CHANGE]`。✅ 影響評估涵蓋。

### 8.9 5/5 BA Minor/Info 處理完整性檢查

**Tester 獨立驗證每項落實**:

| BA 項目 | 落實位置 | 獨立驗證結果 |
|---------|---------|------------|
| **MINOR-1** FR-002 技術型別字面 | system-arch.md §4 + field-spec.md §5 SQLite↔PG 對映表 | ✅ **已處理** — field-spec.md §5 完整對映表（INTEGER AUTOINCREMENT → BIGINT IDENTITY / BOOLEAN 行為 / TIMESTAMP→TIMESTAMPTZ 等），SA 接過 BA 的 type 字面把它放到 SA 層的 type-mapping 表 — 合理分層 |
| **MINOR-2** NFR-004 baseline 取得方法 | system-arch.md §5.2 效能架構表「Baseline 取得方法」行 | ✅ **已處理** — Tester 獨立 grep `Baseline 取得方法` 在 system-arch.md line 313 找到：「1) 8 個 pytest 平均時間（SQLite vs PG fixture 對比）2) 5 個關鍵 auth endpoint 以 `ab -n 100 -c 1` 取 P95」+ 列出 5 個 endpoint |
| **INFO-1** docker-compose 30s onboarding | system-arch.md §7.2 Docker Compose 策略表 | ✅ **已處理** — Tester 獨立檢視 system-arch.md line 404「Onboarding 啟動時間 (test-ba INFO-1 補充)」`docker-compose up -d postgres` 約 30s |
| **INFO-2** Production SLA dashboard | system-arch.md §5.5 可觀測性表 | ✅ **已處理** — line 342「Production 監控 (test-ba INFO-2 補充)」標 [SA建議] [BLOCKED_ON_DEPLOYER]，列 3 項建議指標（5xx 率 / DB connection error count / Migration log 完整性）|
| **INFO-3** Migration 觸發策略（startup 自動 vs CI/CD）| system-arch.md §3 MOD-104 第 2 點 + pattern-spec.md §2.3 | ✅ **已處理** — system-arch.md line 238-241 MOD-104 列選項 A（startup auto-upgrade）vs 選項 B（CI/CD 手動），標 [BLOCKED_ON_SD]；pattern-spec.md §2.3 「觸發方式」行進一步列出兩選項利弊 |

**Tester 獨立判定**: ✅ **5/5 全部真的落實**（非表面提及）— SA 對 test-ba 反饋處理完整。

---

## 9. Rule Protocol 合規性檢查

### 9.1 Rule 6 跨 TASK 修改 — 4 個標記合規

詳見 §8.2。✅ 4/4 合規。

### 9.2 Rule 8 ID 編號規範

| 檢查項 | 結果 | 證據 |
|--------|------|------|
| 3 位零填充 | ✅ | MOD-101..104 / FUNC-101..107 / PATTERN-101 |
| TASK 內連續 | ✅ | MOD 101→102→103→104；FUNC 101→102→103→104→105→106→107（從 grep 結果證實 line 75,127,137,213,241,289,332 順序對） |
| 起始正確 | ✅ | 從範圍 101 起編，非 100 或 000 |
| 子類無誤用 | ✅ | 無 PATTERN-101a / FUNC-101a |
| 永不重用 | ✅ | 本 TASK 全為新編號，無重用 |
| ID 範圍 (Rule 13) | ✅ | 全在 101-200 內 |

✅ **Rule 8 合規 6/6**

### 9.3 Rule 11 不可逆操作

詳見 §8.5。✅ FUNC-107 + FUNC-045 (REUSE) 標記合規，緩解完整。

### 9.4 Rule 13 ID Allocator 合規

✅ MOD-101..104 / FUNC-101..107 / PATTERN-101 全部在 101-200 範圍內；未跨範圍取號；未從別的 TASK 範圍取號。

### 9.5 Rule 18 Parameter Registry 預規劃

**獨立檢視 impact-assessment.md §4**：
- 列出 5 個 POSTGRES_*（HOST / PORT / USER / PASSWORD / DB）+ 1 個 DATABASE_URL 候選
- 每個有 paramName / paramKind / scope / ownerService / required / 來源 FR 6 個欄位
- 提供 SD 階段 mandatory 動作的 `sdlc-journal-write.sh parameter_added` 完整範本（含 JSON payload）
- ⚠️ Tester 注意 — Rule 18 規定「SD/BE/Deployer 引入 / 修改 / 棄用 env 時觸發」，SA 階段不直接 emit `parameter_added` event 是正確的；SA 的責任是預規劃 + 提示 SD（已做到）

✅ **Rule 18 預規劃充足**，SD 階段可直接執行。

---

## 10. 追溯矩陣驗證

| 規格 ID | 來源（BA）| 對應 SA 元素 | 對應 AC | 結果 |
|---------|----------|-------------|---------|------|
| FR-001 | enhanced-input.md「sqlite3 → Postgres」| FUNC-101/105 + MOD-101/103 + MOD-005 替換 | AC-044/045 | ✅ |
| FR-002 | enhanced-input.md「3 表必遷移」| FUNC-103 + MOD-102 + ENTITY-001/002/003 | AC-046/047 | ✅ |
| FR-003 | enhanced-input.md「正式 migration」| FUNC-103/104 + MOD-102 + PATTERN-101 | AC-048/049 | ✅ |
| FR-004 | BA BC-5 決策 | FUNC-103/104 + ENTITY-001/002/003 補欄位 | AC-050/051 | ✅ |
| FR-005 | enhanced-input.md「POSTGRES_*」+ Rule 18 | FUNC-101 + impact §4 預規劃 | AC-052/053 | ✅ |
| FR-006 | enhanced-input.md「Railway 部署」| FUNC-107 + MOD-104 | AC-054/055 | ✅ |
| FR-007 [IRREVERSIBLE] | BA BC-1 決策 | FUNC-106 + FUNC-107 + 14 天 emergency path | AC-056 | ✅ |
| FR-008 | BA BC-2 決策 | FUNC-101 + system-arch §7.2 docker-compose | AC-057 | ✅ |

**全部 8 FR 三向追溯完整**。

---

## 11. 發現清單

### 🔴 Critical
- **無**

### 🟠 Major
- **無**

### 🟡 Minor

#### Minor-1: MOD-103 (auth_repositories) 邊界模糊 — 「最小封裝 vs 完整 Repository Pattern」歧義

- **位置**: system-arch.md §3 MOD-103 (line 215-231)
- **描述**: MOD-103 預期路徑為「`web/auth/repositories/`（新目錄）或 inline 在現有 `web/auth/*.py` 中以 helper function 形式」— 兩個路徑語意差別大；SA 又標「若 SD 判斷不必要可標 [DEFERRED]」。對 SD 階段而言，「MOD-103 究竟是新目錄 / 新檔案 / 還是僅 inline helper function」缺乏明確判斷標準
- **影響**: SD 階段選 inline 與選新目錄產生的 code-registry 影響、SD/BE 工作量差異大
- **建議**: SA 應給 SD 明確判斷標準（如「若 SD 選 SQLAlchemy ORM → 用 repository class；若選 raw psycopg → 用 inline helper」），而非開放「兩種皆可」+ 允許整個 MOD-103 [DEFERRED]
- **嚴重度**: Minor（SD 階段可依 BLOCKED_ON_SD 自行決定，但決策依據不充分）
- **不阻塞**

#### Minor-2: NFR-002「100% 既有 22 AC 通過」缺逐 AC 影響評估表

- **位置**: system-arch.md §3 MOD-005 + functional-flow.md §1.2 [REUSE 表] + impact-assessment.md
- **描述**: SA 聲明「28 個 API endpoint 行為不變」+ 「既有 8 個 pytest 在 PG fixture 下全數通過」是涵蓋自動化測試；但 NFR-002 強制的 22 個 AC（TASK-001 AC-015~AC-036）包含手動驗證項（如 OAuth callback / Email 連結 / SameSite cookie），SA 未提供逐 AC 對照表
- **影響**: test-be / Tester 階段無法快速判斷哪些 AC 受 FUNC-105 query 適配影響、需要重點重測；可能漏測某些 cookie / OAuth race condition
- **建議**: SA 應補一個「22 AC × MOD-005 query 適配影響」表，列出每個 AC「受影響 / 不受影響 / 受影響但 fix 機制相同」三類，協助 test-be 階段聚焦
- **嚴重度**: Minor（不影響 SA 設計正確性，但補強會降低 test-be 階段工作量）
- **不阻塞**

#### Minor-3: PATTERN-101 章節 heading 風格不一致

- **位置**: pattern-spec.md line 62 (`## 2. PATTERN-101 詳細規格 ★ NEW`)
- **描述**: PATTERN-101 用 `## 2.` 二級 heading 命名，與 system-arch.md MOD-101..104 用 `### MOD-NNN:`、functional-flow.md FUNC-101..107 用 `### FUNC-NNN:` 三級 heading 風格不一致
- **影響**: L1 verify 腳本（若加 `^### PATTERN-NNN[:\s]` heading 檢查）會誤判 PATTERN-101 缺定義；對人工閱讀也不直觀（其他 SDLC 文件 PATTERN-XXX 通常用 `### PATTERN-XXX:` heading）
- **建議**: 加一個 `### PATTERN-101: Migration Versioning + Reversibility + Expand-Contract ★ NEW` 三級 heading（可與現有 `## 2.` 共存或合併）
- **嚴重度**: Minor（純格式問題，不影響內容正確性）
- **不阻塞**

### 🔵 Info

#### Info-1: L1 sdlc-role-verify.sh sa 腳本改進建議

- **建議**:
  1. 對「系統架構圖」檢查接受 `(系統架構圖|系統邊界圖|系統上下文圖|Context Diagram|Container Diagram)` 同義詞
  2. 對「功能模組」改為對 functional-flow.md 用 `(功能清單|功能流程|Functional Flow)` 偵測
  3. 對 ENTITY ID 重複改用 `^### ENTITY-NNN[:\s/]` heading 偵測，避免 template 多次引用被誤判
- **不阻塞**（影響所有 SA 階段 TASK，建議列為 SDLC 工具改進待辦）

#### Info-2: PostgreSQL 單實例為資料層 SPoF

- **建議**: SA 設計合理（NFR 未要求 HA + baseline 既有架構為單實例）；但長期建議考慮 read replica / connection retry 機制；屬範圍外，留後續 TASK
- **不阻塞**

#### Info-3: FUNC-104 在「選項 A」下變 [DEFERRED] 設計

- **建議**: FUNC-104 在 SD 選擇「FUNC-103 + FUNC-104 合併為單一 migration」時變 [DEFERRED]，類似 MOD-103 開放性問題；可考慮在 SA 階段就決定一個預設選項，讓 [DEFERRED] 變更明確
- **不阻塞**（SA self-review.json 已扣 3 分自評）

#### Info-4: ROLE-004 部署者未在 SA 文件中正式登記為 ROLE-XXX

- **觀察**: BA requirement-spec.md §2 line 106-108 已定義 ROLE-004（部署者）；但 SA system-arch.md mermaid 圖直接寫 `Deployer(["🚀 部署者 ROLE-004"])` 沒有獨立 ROLE 章節登記
- **建議**: SA 可在 system-arch.md 補一個簡短 ROLE 引用區塊明確 [REUSE: from BA]，與 ROLE-001/002/003 列在一起；或標明「ROLE 引用以 BA 為主，SA 不複述」減少歧義
- **不阻塞**（已透過 BA 標清楚）

#### Info-5: PATTERN-006 OAuth Upsert race condition 在 PG 環境的處理建議

- **觀察**: SA-SUG-103 (system-arch §11) 列 PG `INSERT ... ON CONFLICT` 改寫建議，留後續 TASK
- **建議**: 可考慮在本 TASK SD 階段選 SQLAlchemy 2.0 或 psycopg3 時順帶評估 ON CONFLICT 改寫成本；若成本 < 半天可在 SD 階段順帶處理（不擴大本 TASK 範圍但消除 race condition）
- **不阻塞**（屬建議性質）

---

## 12. 結論

| 項目 | 結果 |
|------|------|
| **Tester 獨立分數** | **91/100** |
| **SA 階段獨立判定** | **✅ PASS** |
| Critical 數 | **0** |
| Major 數 | **0** |
| Minor 數 | **3**（MOD-103 邊界模糊 / NFR-002 缺逐 AC 表 / PATTERN-101 heading 風格）— 不阻塞 |
| Info 數 | **5** |
| L1 false positive 3 項判斷 | **3/3 確認為 false positive**（PM 判斷正確；改 L1 腳本但 SA 不需改文件）|
| 4 個 [CROSS-TASK] 標記合規 | **4/4 合規**（三要素齊全 + 影響評估清晰 + rollback 明確）|
| FUNC-107 [IRREVERSIBLE] 緩解充足性 | **充足**（4 要素 + 14 天 emergency path 雙處覆蓋 + Rule 11.2 下游責任清晰）|
| PATTERN-101 是否拆分 | **不需拆分**（三大支柱邏輯緊密耦合 + 命名可保留）|
| 0 新 ENTITY / 0 新 TBL 合理性 | **合理**（符合 Rule 7 重用優先；補欄位視為 [REUSE + 擴充] 不應改 NEW ENTITY）|
| 13 個 [BLOCKED] 委派合理性 | **13/13 合理**（8 BLOCKED_ON_SD 屬實作層 + 5 BLOCKED_ON_DEPLOYER 屬部署層；無真實阻塞）|
| 對 TASK-001 in-progress uiux 影響 | **無影響**（純後端重構 + 不對應任何 UI 元件 + impact-assessment §6.1 已記錄）|
| 5/5 BA Minor/Info 處理完整性 | **5/5 真的落實**（非表面提及；Tester 逐項獨立 grep 證實）|
| Rule 6/8/11/13/18 合規 | **全部合規** |

**建議行動**:
1. **PM**: 採納本報告，標記 test-sa PASS，可進入 UIUX 階段（建議 PM 評估是否 skip UIUX，因本 TASK 為純後端重構 — impact-assessment §6.1 已建議）
2. **PM**（可選）: 把 3 Minor 在 SD/Deploy-init dispatch prompt 中提示下游 agent 留意：
   - SD 處理 MOD-103 時請給明確判斷標準（不要傳遞「兩種皆可」的歧義到 BE）
   - SD/Tester 在 db-schema.md / test-be 階段補一個「22 AC × MOD-005 query 適配影響」表
   - SA 可選擇性修補 pattern-spec.md PATTERN-101 heading 風格（屬格式微調）
3. **PM**（可選）: 規劃改進 L1 `sdlc-role-verify.sh sa` 對三個檢查項加 context-aware 過濾（與 ba 的相同 false positive 一併處理）
4. **SA**: 不需修改文件（無 Critical/Major）；3 Minor 全部不阻塞下階段

---

## 13. [BLOCKED] 項目

無。Tester 完成獨立驗證，無阻塞項。

---

> **附註**:
> - 本報告由 Tester 在獨立上下文中執行（未存取 SA agent 開發對話歷史）
> - 對照基準: BA requirement-spec.md / BA business-flow.md / test-ba/test-report-ba.md / conventions/*.md / shared/*.md / web/auth/database.py 現況
> - 驗證工具: Read / Grep / Bash（sdlc-role-verify.sh L1 + 獨立 grep 交叉驗證）
> - Tester 立場: 對抗心態 — 找 bug 即成功；SA score 93 自評不採信，獨立評分 91 與 SA 接近，差 2 分主因 MOD-103 邊界模糊 + NFR-002 缺逐 AC 表
> - L1 verify 三項 false positive 與 PM 觀察一致；建議改進 L1 腳本對所有 SA 階段 TASK 通用
