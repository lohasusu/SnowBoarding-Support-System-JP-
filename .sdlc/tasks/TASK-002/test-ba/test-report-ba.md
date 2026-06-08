---
document_id: "TEST-REPORT-BA-TASK-002-v1.0"
title: "BA 階段獨立測試報告 — TASK-002 SQLite → PostgreSQL 遷移"
version: "1.0"
date: "2026-06-08"
author: "Tester (independent)"
task_id: "TASK-002"
phase: "test-ba"
被測對象:
  - ".sdlc/tasks/TASK-002/ba/requirement-spec.md (REQ-TASK-002-v1.0)"
  - ".sdlc/tasks/TASK-002/ba/business-flow.md (BF-TASK-002-v1.0)"
  - ".sdlc/tasks/TASK-002/ba/self-review.json (BA agent 自評 95/PASS)"
驗證基準:
  - ".sdlc/tasks/TASK-002/enhanced-input.md"
  - ".sdlc/config.json (techStack.database)"
  - ".sdlc/conventions/db-conventions.md v1.1 (locked 2026-06-03)"
  - ".sdlc/conventions/api-conventions.md (locked 2026-06-03)"
  - ".sdlc/conventions/i18n-conventions.md (locked 2026-06-03)"
  - ".sdlc/baseline/baseline-audit-2026-06-03.md (C-1 + M-8)"
  - ".sdlc/shared/{id-registry,terminology,parameter-registry}.md (rebuild 2026-06-08T05:36:56Z)"
驗證方法論:
  - "~/.claude/skills/sdlc/tools/verify-requirement/SKILL.md (D1-D5)"
  - "Tester rules 1-4 (獨立性 / 規格優先 / Critical 阻塞 / 100% 追溯)"
status: "Complete"
result: "PASS"
---

# BA 階段獨立測試報告 — TASK-002 SQLite → PostgreSQL 遷移

## 1. 驗證摘要

| 指標 | 結果 |
|------|------|
| 檢查維度 | D1 完整性 / D2 反腦補 / D3 一致性 / D4 可測試性 / D5 業務流程 + Tester L1 false-positive 獨立判定 + 7 個 PM 重點關注項 |
| 檢查項目數 | 38 |
| 通過 | 36 |
| Critical（🔴 必須修正）| **0** |
| Major（🟠 建議修正，但不阻塞）| **0** |
| Minor（🟡 改善建議）| **2** |
| Info（🔵 參考）| **3** |
| 結論 | **✅ PASS**（無 Critical/Major；2 Minor 不阻塞下階段；L1 三項失敗經獨立驗證確認為 false positive，不需 BA 修改） |

---

## 2. 獨立驗證 — L1 verify FAIL 三項 false positive 判定

> Tester 立場: 不為 BA agent 背書；獨立驗證 L1 報告。

L1 `sdlc-role-verify.sh ba TASK-002` 結果: 85/3-FAIL。**獨立判定皆為 false positive，與 PM 觀察一致。**

### L1 失敗項 #1: 「包含未完成標記」

- **抓到位置**: line 445 (`## 9. [待確認] 項目`), line 449 (空狀態說明), line 533 (自查表引用「`[待確認]`」)
- **獨立判定**: ✅ **FALSE POSITIVE**
- **理由**:
  1. `## 9. [待確認] 項目` 為 `requirement-spec.tpl.md` 模板的**必填章節標題**，BA 已明確聲明「本 TASK 無 [待確認] — 6 個 [BA確認] 全數已決策」
  2. L1 腳本 grep `待確認` 字串未排除 template 結構性章節
  3. 真正的 [待確認] 殘留應指「列表中個別項目」，而非「章節標題」
- **L1 修正建議**（不阻塞 BA）: regex 應改為 `^\s*-\s*\[(待確認|TBD|TODO|待補充)\]` 偵測列表項，而非整檔 grep 字串

### L1 失敗項 #2: 「FR ID 重複: FR-001」

- **抓到位置**: line 70 (§1.3 範圍摘要表), line 117 (§3 FR-001 細節章節), line 473 (§11 追溯矩陣)
- **獨立判定**: ✅ **FALSE POSITIVE**
- **理由**:
  1. `requirement-spec.tpl.md` 模板設計即要求同一 FR 在三處出現（摘要表 / 細節章節 / 追溯矩陣），是**正常 template 結構**
  2. L1 腳本若計算「`FR-NNN` 字串出現次數 > 1 = 重複」會誤殺所有合法 BA 產出
  3. 真正的 ID 重複應指「兩個不同定義的 FR 共用同一 ID」（如兩處都寫 `### FR-001: A` 和 `### FR-001: B`）
- **獨立 grep 驗證**: `grep -nE '^### FR-[0-9]{3}:' requirement-spec.md` → FR-001~008 共 8 個獨立 section heading，**無重複定義**
- **L1 修正建議**（不阻塞 BA）: regex 應改為偵測 `^### FR-NNN:` heading 重複，而非總字串次數

### L1 失敗項 #3: 「含禁止模糊用詞」

- **抓到位置**:
  - line 253: NFR-004 量化指標說明「P95 ≤ SQLite baseline × 1.5（PostgreSQL 透過網路連線通常較本機 SQLite 慢，**1.5x 為合理容忍**）」— **「合理」用於解釋量化選擇的理由**
  - line 254: NFR-004 來源「無使用者明示，標 **[BA合理推斷]**」— **「合理」為標籤名稱字面**
  - line 440: §8 [BA建議] SUG-006 區塊 — **[BA建議] 區為非規格陳述**
  - line 539: §12 自查表「禁止模糊語言 | ✅ | 避免『適當』『合理』『**快速**』」— **自查表引用禁字字面說明 BA 已自我把關**
- **獨立判定**: ✅ **FALSE POSITIVE**
- **理由**:
  1. 規格陳述（FR/NFR 量化指標）區段**未使用模糊詞描述需求**；NFR-004 量化值已寫「P95 ≤ SQLite × 1.5；絕對值 ≤ 500ms」精確可測
  2. line 253 的「合理容忍」是**對量化值選擇 1.5x 的人類說明**，不是規格陳述
  3. line 254/440/539 都是元語言（標籤名 / 建議區 / 自查表引文），按 verify-requirement skill 的 D2 表「無主觀語言」應僅作用於 FR/NFR 量化區
  4. BA agent 在 modal_language_check 中已主動聲明「『合理』僅出現於 §8 [BA建議] 與 §10 術語表的解釋性段落，非規格陳述」並交叉自檢
- **L1 修正建議**（不阻塞 BA）: regex 應限定在 FR/NFR 規格區段（§3、§4）內偵測，或排除 [BA建議]、[BA合理推斷]、自查表引文等 meta 上下文

### L1 false positive 總結

**3/3 L1 失敗均為 false positive；不需 BA 修改文件**。PM 對 L1 的判斷正確。

**Tester 對 PM 的腳本改進建議**（記於本報告 §6 INFO-002）:
- L1 `sdlc-role-verify.sh` 對 BA 階段的 3 個檢查（未完成標記 / FR ID 重複 / 模糊用詞）應加 context-aware 過濾，避免誤判 template 結構與 meta 上下文。
- 在腳本修正前，PM 可於 dispatch prompt 加註「L1 失敗請對照 template 結構判斷 false positive」協助下游 Tester 快速判定。

---

## 3. D1 完整性檢查

| # | 檢查項 | 結果 | 證據 / 備註 |
|---|--------|------|------------|
| D1-1 | 每個 FR 都有驗收標準 | ✅ PASS | FR-001~008 對應 AC-044~057 共 14 個 AC（每 FR ≥ 1 AC，多數 ≥ 2） |
| D1-2 | 每個 FR 都有優先順序 | ✅ PASS | FR-001/002/003/005/006/008 = P0；FR-004 = P1；FR-007 = P2 |
| D1-3 | 每個 FR 都有來源引用 | ✅ PASS | 8 個 FR 全部標 enhanced-input.md 段落 / baseline 章節 / db-conventions 條款引用 |
| D1-4 | 文件頭 metadata 完整 | ✅ PASS | document_id / version / date / source_documents (7 個) / change_history 全填 |
| D1-5 | 所有章節都已填寫（無 TODO/TBD/待補充）| ✅ PASS | 獨立 grep 確認：`[待確認]` 僅作為模板章節標題出現；無 `TODO` / `TBD` / `FIXME` |
| D1-6 | 術語表已填寫 | ✅ PASS | §10 共 9 條（含 [REUSE: TASK-001] 標記） |
| D1-7 | 追溯矩陣完整 | ✅ PASS | §11 含 4 個子表（FR 追溯 / NFR 量化 / CONST 來源 / 跨 TASK 修改預警） |
| D1-8 | 每個 BF 對應 FR | ✅ PASS | BF-001→FR-001/002/008/NFR-009；BF-002→FR-005/006/007/NFR-001/005；BF-003→CONST-009/FR-007 |
| D1-9 | 每個 BF 有異常流程表 | ✅ PASS | 3 個 BF 各有「異常流程」表（4/4/3 行） |

**D1 結果**: 9/9 PASS

---

## 4. D2 反腦補偵測（CRITICAL — Tester 主戰場）

### 4.1 FR 級 Diff 分析（enhanced-input.md → requirement-spec.md）

| FR | 使用者原文來源（enhanced-input.md）| 判定 |
|----|----------------------------------|------|
| FR-001 PostgreSQL 連線層替換 | 「web/auth/database.py 的 sqlite3 driver 改為 Postgres driver」（line 32） | ✅ 直接對應 |
| FR-002 三表 schema 在 PG 重建 | 「3 張既有資料表必須遷移：TBL-001 users / TBL-002 favorites / TBL-003 email_verification_tokens」（line 28-31） | ✅ 直接對應 |
| FR-003 正式 migration 工具導入 | 「既有 ALTER TABLE try/except 安全遷移 hack（database.py:44-52）改為正式 migration 工具」（line 33） | ✅ 直接對應 |
| FR-004 補 updated_at / deleted_at | [BA確認] 第 5 項「是否補齊」+ BA 決策「補」+ db-conventions §2/§8 強制 | ✅ [BA確認] 流程合規（BC-5 已決策） |
| FR-005 環境變數新增 | 「環境變數：新增 POSTGRES_*」（line 34） + config.json envPrefix | ✅ 直接對應 |
| FR-006 Railway 部署設定切換 | 「Railway 部署設定：addon Postgres 或 DATABASE_URL env var」（line 35） | ✅ 直接對應 |
| FR-007 既有資料遷移處理 | [BA確認] 第 1 項「現有 SQLite 資料是否需要遷移」+ BA 決策「不遷移 + fallback 腳本」 | ✅ [BA確認] 流程合規（BC-1 已決策） |
| FR-008 全環境 DB engine 策略 | [BA確認] 第 2 項「dev/staging/prod 是否都 Postgres」+ BA 決策「全環境統一」 | ✅ [BA確認] 流程合規（BC-2 已決策） |

**結論**: 8 個 FR **無腦補**。4 個直接對應 enhanced-input.md 明示項；4 個經 [BA確認] 6 項決策流程落地。

### 4.2 NFR 來源檢核（12 個）

| NFR | 來源 | 判定 |
|-----|------|------|
| NFR-001 持久性 | baseline C-1 + DESIGN.md §八 + 使用者「解 Critical」 | ✅ 高信心 |
| NFR-002 認證流程外部行為零變化 | enhanced-input.md「不破壞既有認證流程」+ TASK-001 22 AC | ✅ 高信心 |
| NFR-003 啟動延遲 | [BA建議] SUG-003 + 業界經驗 | ⚠️ 標 [BA建議] 推斷 — 已合規隔離 |
| NFR-004 查詢延遲 | [BA建議] SUG-003 + 業界經驗 + 標 [BA合理推斷] | ⚠️ 標 [BA合理推斷] — 已合規隔離 |
| NFR-005 連線池與並行容忍 | [BA確認] 第 4 項 → 委派 SD + Railway 連線數常識 | ✅ [BA確認] 落地 |
| NFR-006 Migration 可逆性 | db-conventions §5.2 | ✅ conventions 強制 |
| NFR-007 三段式刪欄保留 | db-conventions §5.3 + §8 | ✅ conventions 強制 |
| NFR-008 大表索引 CONCURRENTLY | db-conventions §5.4 | ✅ conventions 強制 |
| NFR-009 字串編碼 | db-conventions §6 | ✅ conventions 強制 |
| NFR-010 環境變數 owner 一致性 | api-conventions + envPrefix + Rule 18 | ✅ Rule 18 強制 |
| NFR-011 Secret 管理 | 業界 secret 慣例 + baseline §1.1 | ⚠️ 業界常識 — 可接受 |
| NFR-012 系統語言 zh-TW | i18n-conventions + TASK-001/NFR-018 | ✅ conventions + TASK-001 延續 |

**結論**: 12 個 NFR **無腦補**。9 個直接源於 conventions / TASK-001 / 使用者；3 個（NFR-003/004/011）為合理業界推斷且已標 [BA建議] 隔離。

### 4.3 紅旗模式檢核

| 紅旗 | 結果 |
|------|------|
| 出現使用者從未提及的功能（未標 [BA建議]）| ✅ 無 |
| 業務需求文件出現技術實作細節（API path / DB 內部表名）| ⚠️ **見 Minor-1**：FR-002 提到「INTEGER PRIMARY KEY AUTOINCREMENT」「BIGINT GENERATED ALWAYS AS IDENTITY」「TIMESTAMPTZ DEFAULT NOW()」等 PG/SQLite 型別字面，**但**這些是 conventions §2 強制規範引用（非 BA 自行設計），可視為合規 |
| NFR 無使用者來源且未標假設 | ✅ NFR-003/004 已標 [BA建議]；NFR-011 為業界常識可接受 |

### 4.4 不納入清單 (§1.4) 反腦補完整性檢核

獨立檢視「使用者可能腦補但 BA 應該排除」的項目：

| 候選腦補項 | enhanced-input.md「不納入」列出？ | BA spec §1.4 列出？ | 結果 |
|----------|-----------------------------|----------|------|
| 新增資料表 | ✅ | ✅ | OK |
| UUID PK / partitioning | ✅ | ✅ (「DB schema 整體 refactor") | OK |
| Read replica | ✅ | ✅ | OK |
| Caching layer | ✅ | ✅ | OK |
| DB 監控 / Grafana | ✅ | ✅ | OK |
| 其他模組 storage 變更 | ✅ | ✅ | OK |
| DESIGN.md 同步 | 未提（PM 文件債）| ✅ 主動標記 | BA 主動補 |
| `/api/env-check` 下架 | 未提 | ✅ 主動標記 | BA 主動補 |
| 雪票/機票/行程功能變更 | 未提（隱含）| ✅ 主動標記 | BA 主動補 |
| 新增業務功能 (忘記密碼) | 未提 | ✅ 主動標記 | BA 主動補 |
| 認證流程外部行為變更 | ✅（隱含於「不破壞既有認證流程」）| ✅ 主動標記 | OK |
| Connection pool 大小自行決定 | （非腦補議題，已委派 SD）| 委派 §7 | ✅ 委派 |
| Migration 工具自選 | [BA確認] 第 3 項 → 委派 SD | 委派 §7 + FR-003 | ✅ 委派 |
| 加密強化（SSL）| 未提 | §8 SUG-005 隔離 | ✅ 列為建議 |
| 用戶通知 / 公告 production 切換 | 未提 | **未列入** | ⚠️ **見 Info-1**（可考慮補 SUG）|
| Migration 自動 vs 手動觸發策略 | 未提（隱含啟動時自動）| **未明示** | ⚠️ **見 Info-3** |

**結論**: 不納入清單**覆蓋完整**，使用者明示與隱含腦補候選皆已標記；2 個邊緣項（Info-1/Info-3）為改善建議，**不構成腦補**。

### 4.5 建議隔離合規檢核

| 檢查 | 結果 |
|------|------|
| `[BA建議]` 只出現在 §8 區塊 | ✅ 7 個 SUG-001~007 全在 §8；FR/NFR 區無混入 |
| `[待確認]` 只出現在 §9 區塊 | ✅ §9 為空（已決策完畢）；其他地方無「待 BA / 使用者確認」殘留 |

**D2 結果**: 12/12 PASS（無腦補，無紅旗，建議與正式規格物理分離）

---

## 5. D3 一致性檢查

| # | 檢查項 | 結果 | 證據 |
|---|--------|------|------|
| D3-1 | 無矛盾需求 | ✅ PASS | FR-004 補 deleted_at 欄位 + SUG-004 明示不改 hard-delete 為 soft-delete = 邊界清楚；FR-007 不遷移 + FR-008 全環境 Postgres = 邏輯一致；FR-002 「保持既有 INSERT/SELECT 行為」+ FR-004 補欄位但「不改 application-level delete」= 一致 |
| D3-2 | ID 唯一連續 | ✅ PASS | FR-001~008 TASK 內連續；NFR-001~012 連續；BR-001~007 連續；AC-044~057 全域接續 TASK-001/AC-043 連續；ROLE-004 全域接續 TASK-001/ROLE-003；獨立 grep 驗證無重複定義 |
| D3-3 | 術語一致 | ✅ PASS | 既有術語標 [REUSE: from TASK-001 terminology]（ephemeral storage / 軟刪除 / Expand-Contract）；新術語在 §10 集中定義 9 條；shared/terminology.md rebuild 2026-06-08T05:36:56Z 已含 8 條 TASK-002 新術語 |
| D3-4 | conventions 引用正確 | ✅ PASS | db-conventions §2/§3/§4/§5.1/§5.2/§5.3/§5.4/§6/§8 對應位置全部存在且引用語意正確（獨立交叉檢核） |
| D3-5 | shared/ 已有元素正確 [REUSE] 標記 | ✅ PASS | ENTITY-001/002/003 / TBL-001/002/003 / MOD-005 / ROLE-001/002/003 全部標 [REUSE: from TASK-001]；id-registry.md 確認 ID 存在 |
| D3-6 | 跨 TASK 引用格式 | ✅ PASS | 引用 TASK-001 ID 使用 `TASK-001/FR-007~FR-014`、`TASK-001/AC-015~AC-036`、`TASK-001/NFR-018`、`TASK-001/ROLE-001~003`、`TASK-001/BF-001 ~ TASK-001/BF-N` 格式（Rule 8.5 合規） |

**D3 結果**: 6/6 PASS

---

## 6. D4 可測試性檢查

| # | 檢查項 | 結果 | 證據 |
|---|--------|------|------|
| D4-1 | 每個 AC 可寫成 Given/When/Then | ✅ PASS | 14 個 AC 全部含「**可測**: ...」具體驗證指令（pytest exit code / grep / `\d`）；FR-001 附完整 Gherkin Scenario |
| D4-2 | NFR 已量化 | ✅ PASS | 12 個 NFR 全部含量化指標 — NFR-001 100%、NFR-002 100% / 22 AC、NFR-003 ≤ +2s / P95 ≤ 5s、NFR-004 P95 ≤ 1.5x / ≤ 500ms、NFR-005 pool 2-10 / 20 並行、NFR-006 round-trip 等價、NFR-009 UTF8、NFR-010 paramKind=env + ownerService=be、NFR-011 git grep 無密碼、NFR-012 無新英文字串 |
| D4-3 | NFR-004 baseline 可量測？ | ⚠️ **Minor-2**: 「P95 ≤ SQLite baseline × 1.5」**未指定 baseline 取得方法**（在哪測？多少請求？哪個 endpoint？）— 留 SD 階段補充但 BA 可標明「baseline 來源 = test-be 階段以 8 個 pytest 量測平均」會更明確 |
| D4-4 | NFR-005 「20 並行」可測？ | ✅ PASS | NFR-005 已明示「ab/wrk 模擬 20 並行」驗證方式 |
| D4-5 | AC-055 「人工 / 腳本驗證」可重現？ | ✅ PASS | 5 步驟 smoke test 步驟清楚（註冊 → 登入 → 收藏 → 重啟 → 再登入） |
| D4-6 | AC-056 mock SQLite 數值可驗證？ | ✅ PASS | 明示「3 用戶 / 2 收藏 / 1 token」期望值 |
| D4-7 | 拒絕主觀語言 | ✅ PASS | 規格陳述區無「快速」「用戶友好」「容易使用」；line 253「合理容忍」是量化選擇的人類解釋（在 NFR 量化值之後），不是規格陳述 |

**D4 結果**: 6/7 PASS, 1 Minor

---

## 7. D5 業務流程驗證

| # | 檢查項 | 結果 | 證據 |
|---|--------|------|------|
| D5-1 | 流程覆蓋 — 每個 FR 至少對應 1 BF | ✅ PASS | FR-001 → BF-001；FR-002 → BF-001；FR-003 → BF-001（步驟 3 migration upgrade）；FR-004 → BF-001（步驟 3）；FR-005 → BF-002 步驟 2；FR-006 → BF-002；FR-007 → BF-002 + BF-003；FR-008 → BF-001 步驟 4 |
| D5-2 | 異常流程完整 | ✅ PASS | 3 BF 各 3-4 行異常流程；BF-003 緊急回滾完整覆蓋 FR-007 [IRREVERSIBLE] 後果 |
| D5-3 | Mermaid 語法正確 | ✅ PASS | 4 個 Mermaid 區塊（3 BF + 1 流程關係）均為 `flowchart TD/LR`，節點與箭頭語法正確 |
| D5-4 | BF → FR 映射完整 | ✅ PASS | §5 追溯矩陣三行對應清楚 |
| D5-5 | 終端用戶流程不變聲明 | ✅ PASS | §6 明確聲明 NFR-002 已涵蓋；不重述 TASK-001/BF |

**D5 結果**: 5/5 PASS

---

## 8. PM 重點關注項獨立評估（7 項）

### 8.1 6 個 [BA確認] 決策合理性

| 編號 | 決策 | 獨立評估 |
|------|------|---------|
| **BC-1** 不遷移歷史 SQLite | ✅ **合理**。CLAUDE.md 與 baseline-audit C-1 已認定 production 為 ephemeral；強制歷史遷移為空跑風險；fallback 腳本（FR-007 + AC-056）覆蓋本機/staging 殘留場景；ASSUME-002 假設清楚（若使用者另有備份須調整）。範圍邊界正確。 |
| **BC-2** 全環境統一 PostgreSQL | ✅ **合理但應補強對開發者本機便利性的說明**。BA 已寫「docker-compose 已備 postgres:16-alpine」+「BF-001 開發環境準備」步驟 1-5 清楚，覆蓋 dev onboarding。**Info-1 建議**: 可補一句「對既有開發者：首次 setup 需執行 `docker-compose up -d postgres` 約 30s；後續開發 zero overhead」減少開發者疑慮，但不阻塞。 |
| **BC-3** 委派 SD 階段選 migration 工具 | ✅ **合理且範圍清楚**。BA 規範行為（reversible + 檔名 + 三段式刪欄）而非工具；FR-003 + BR-002 + BR-007 + AC-048/049 提供 SD 充分約束；委派理由明示「Alembic / yoyo / 手寫 SQL 各有適用」。SD 階段有充分判斷空間且不會偏離 BA 意圖。 |
| **BC-4** 委派 SD connection pool | ✅ **合理**。NFR-005 已給量化指標（min=2 / max=10 / timeout < 5s / 20 並行）+ 委派理由（Railway 連線數限制屬 SD/Deployer 知識領域）。SD 階段能據此 NFR 量化值選擇具體 lib（SQLAlchemy QueuePool / psycopg pool / asyncpg pool）。**範圍清楚**。 |
| **BC-5** 補 updated_at / deleted_at（觸發 [CROSS-TASK]）| ✅ **合理；跨 TASK 修改授權標記充足**。BA 已預警 §11 「跨 TASK 修改預警」共 3 條（TBL-001/002/003 + MOD-005），明確列觸發 FR + 原因。**SA 階段須在 functional-flow.md 落實 [CROSS-TASK:] 標記**（Rule 6 強制），BA 已盡 BA 階段該做的 — 不能更早，因 SA 才有 functional-flow.md 工件。BA 預警與 Rule 6 對齊。 |
| **BC-6** 移除 ALTER TABLE try/except hack | ✅ **範圍邊界清楚**。FR-003 + BR-002 + AC-048 明示「grep ALTER TABLE in web/auth/ excluding migrations/ 應 exit 1」可測；理由（db-conventions §8 第 1 條 + PostgreSQL 環境 silent fail 風險）充分。範圍嚴格限於 database.py:44-52 三行，不擴張到其他模組。 |

**6/6 BA確認決策均合理**，無 Critical/Major 異議。

### 8.2 Cross-TASK 修改預警影響評估（Rule 6）

**核心問題**: 「跨 TASK 修改是否在 BA 階段就需要更精確的影響評估？是否會破壞 TASK-001 仍 in-progress 的 uiux 階段產出？」

**獨立調查**:
1. **TASK-001 當前 currentPhase = uiux**（state.json line 17）
2. **TASK-001/uiux/ 實際產出**: 只有 `pencil-component-sync.json` 初始化檔（無 wireframes.md / component-spec.md / 視覺稿）
3. **TASK-001 為 brownfield-document 模式**: 「補追溯既有 28 API + 3 ENTITY + 8 PAGE 到 shared/，**不寫新代碼**，純規格產出」（state.json line 7）
4. **TASK-001 uiux 預期產出範圍**: 既有 8 個 PAGE 的「補追溯」型 wireframes（紀錄既有 UI），**不會引入新的 form 欄位設計或 schema-bound UI 元件**

**評估結論**:
- **不會破壞 TASK-001 uiux**：因 TASK-001 uiux 是補追溯既有 UI；補 updated_at / deleted_at 為**後端 schema 層**變更，**不涉及 UI**（用戶不會直接看到 timestamp 欄位 — 既有 `web/static/js/auth.js`、`web/templates/*.html` 無對應渲染）。
- **BA 階段已預警充分**：§11 跨 TASK 修改預警表 + §1.4 不納入「認證流程外部行為變更」+ NFR-002 100% 既有 22 AC 通過 = 對 TASK-001 既有 FR/AC/UI 三層保護網。SA 階段只需落實 [CROSS-TASK:] 標記，不需 BA 補強。
- **更早影響評估之必要性？**: BA 階段尚無 SA 的 functional-flow.md / UIUX 的 wireframes 工件，無法做「具體頁面影響評估」；BA 已盡 BA 階段該做的（標出影響的 TBL/MOD）。SA 階段會接手做頁面層級影響分析。

**Tester 判定**: ✅ **跨 TASK 修改預警充足**。無 Critical/Major。

### 8.3 Rule 11 不可逆操作 — FR-007 [IRREVERSIBLE] 緩解充足性

**檢查項**:
- FR-007 [IRREVERSIBLE] 標記: ✅ 存在（line 210，business 影響說明完整）
- CONST-009 緩解: ✅ 要求 deploy 階段提供 rollback plan + 保留 SQLite 應用層代碼直到 production 穩定 N 天
- SUG-006 緩解: ✅ 建議保留 `database_sqlite.py` 14 天 rollback window
- BF-003 緊急回滾流程: ✅ 完整 6 步驟 + 3 行異常 + Mermaid 圖

**獨立評估**:
- **緩解措施充足**：CONST-009（強制）+ SUG-006（建議，PM 確認後即可入 SD/Deploy）+ BF-003（流程化）三層保護
- **N 天 / 14 天**：BA 已明示「建議 14 天」具體可測；deploy 階段可微調
- **BF-003 涵蓋 5 個失敗根因**：migration 邏輯錯 / pool 不足 / Railway addon 異常 / 其他；分別有 BE/SD/SA 修正路徑

**唯一改善**: BF-003 異常流程提到「14 天 rollback window 後發現問題」處置為「走完整 SDLC 開新 TASK 修正」是接受 trade-off，**不阻塞**。可考慮加 SUG「production 切換後設 SLA dashboard 監控 5xx / connection error / migration log 異常」進一步降低延遲發現風險 — 為 Info-2 改善建議。

**Tester 判定**: ✅ **FR-007 緩解充足**。Rule 11 [IRREVERSIBLE] 標記 + 緩解 + 確認流程（BF-003）完整。

### 8.4 Rule 18 Parameter Registry 預警充足性

**檢查項**:
- BA 預告 SD 階段將寫入「5 個 POSTGRES_* 或 1 個 DATABASE_URL」: ✅ 存在於 self-review.json `parameter_registry_impacts`
- ownerService / scope / required: ✅ 都已預告（be / all / true）

**潛在缺漏檢核**:

| 候選參數 | BA 預告？ | 評估 |
|---------|----------|------|
| `POSTGRES_HOST` / `_PORT` / `_USER` / `_PASSWORD` / `_DB` | ✅ | 對應 config.json envPrefix |
| `DATABASE_URL`（alternative）| ✅ | 對應 enhanced-input.md + 業界 |
| `POSTGRES_SSL_MODE` / `?sslmode=require` | ⚠️ 只在 SUG-005 提及 | 若 PM 採納 SUG-005，SD 須補入 parameter-registry；BA 已隔離為建議，**不算缺漏** |
| Migration 工具連線參數（如 Alembic `SQLALCHEMY_DATABASE_URL`）| ❌ 未預告 | **Info-3**：Alembic 通常與應用共用 DATABASE_URL，**不算新參數**；但若 SD 選 yoyo-migrations 等獨立配置可能引入新 env，留 SD 階段判斷 |
| Connection pool 參數（如 `DB_POOL_MIN` / `DB_POOL_MAX` / `DB_POOL_TIMEOUT`）| ⚠️ 隱含於 NFR-005 | NFR-005 量化值（min=2 / max=10 / timeout < 5s）若 SD 決定 externalize 為 env vars 而非 hardcoded，需追加；BA 階段委派 SD 合理 |
| SSL cert 路徑 / Vault path | ❌ 未預告 | Railway addon 通常用 DATABASE_URL 內嵌憑證，不需獨立 cert 檔案 env；自建 PG 才需要。屬 deploy 階段決策。**不算缺漏** |

**Tester 判定**: ✅ **Rule 18 預警充足**（5 個 POSTGRES_* + 1 個 DATABASE_URL 涵蓋主要需求）；SSL / pool externalization / cert path 屬 SD/Deploy 階段條件性追加，BA 階段委派合理。**無 Critical/Major**。

### 8.5 NFR 量化完整性抽樣

詳見 D4 表（§6）。12/12 NFR 量化值合理。**唯一可改善**：NFR-004 「P95 ≤ SQLite baseline × 1.5」未明示 baseline 取得方法 → Minor-2（建議補「baseline 來源 = test-be 階段以 8 個 pytest 量測平均」）。

### 8.6 不納入清單反腦補完整性

詳見 D2.4 表（§4.4）。15/15 候選腦補項涵蓋完整。2 個邊緣項（用戶通知 / migration 觸發策略）為 Info 改善建議，**不構成腦補**。

### 8.7 跨 TASK 增量產出（Rule 7）合規性

| 檢查 | 結果 |
|------|------|
| 共享層 [REUSE] 標記 | ✅ ENTITY-001/002/003、TBL-001/002/003、MOD-005、ROLE-001/002/003、術語表既有條目均標 [REUSE: from TASK-001] |
| ID 連續（TASK-002 範圍 101-200）| ✅ BA 階段未使用全域 ID（ENTITY/MOD/FUNC/PATTERN/API/TBL/COMP/PAGE/LAYOUT 都留給 SA/SD/UIUX）；TASK-local ID（FR/NFR/BR）從 001 起連續；AC-044 接續 TASK-001/AC-043 全域連續 |
| ROLE-004 全域連續 | ✅ 接續 TASK-001/ROLE-003 |
| 前 TASK 產出唯讀 | ✅ 透過 [REUSE] 標記，無修改既有定義；跨 TASK 修改預警（§11）已委派 SA 階段標 [CROSS-TASK:]（Rule 6 流程） |

**8.7 PASS**

---

## 9. 發現清單

### 🔴 Critical
- **無**

### 🟠 Major
- **無**

### 🟡 Minor

#### Minor-1: FR-002 技術型別字面出現在需求規格
- **位置**: requirement-spec.md line 146
- **描述**: FR-002 提到 `INTEGER PRIMARY KEY AUTOINCREMENT` / `BIGINT GENERATED ALWAYS AS IDENTITY` / `TIMESTAMPTZ DEFAULT NOW()` 等 PG/SQLite 特定型別字面，按 verify-requirement skill D2 表「無技術實作細節」屬 Warning
- **但**: 這些是 conventions §2 強制規範引用（BA 標明「依 db-conventions §2」），非 BA 自行設計
- **建議**: 可改為「依 db-conventions §2 對應 PostgreSQL 等價型別」並把具體型別移至 SD 階段的 db-schema.md
- **嚴重度**: Minor（不影響規格正確性；conventions 引用合規）
- **不阻塞**

#### Minor-2: NFR-004 baseline 取得方法未明示
- **位置**: requirement-spec.md line 253 + §11 NFR 追溯矩陣
- **描述**: 「P95 ≤ SQLite baseline × 1.5」未指定 baseline 怎麼測（測幾次？哪個 endpoint？什麼負載？）
- **建議**: 補一句「baseline 來源: test-be 階段以 8 個 pytest 量測平均 + 5 個關鍵 auth endpoints 用 ab -n 100 -c 1 取 P95」明確化
- **嚴重度**: Minor（SD/Tester 階段可推導 baseline 規範，但 BA 補上會更明確）
- **不阻塞**

### 🔵 Info

#### Info-1: BF-001 對既有開發者 onboarding 體驗的補充說明
- **建議**: BF-001 開發環境準備流程可加一句「對既有開發者：首次 setup 需執行 `docker-compose up -d postgres` 約 30s；後續開發 zero overhead」減少開發者疑慮
- **不阻塞**

#### Info-2: production 切換後 SLA dashboard 建議
- **建議**: 可考慮加 SUG「production 切換後設 SLA dashboard 監控 5xx / connection error / migration log 異常 ≥ 24h」進一步降低 BF-003 觸發前的延遲發現風險
- **不阻塞**

#### Info-3: Migration 觸發策略未明示（啟動自動 vs 手動）
- **建議**: BA 隱含「啟動時自動執行 migration」（BF-001 步驟 3 + BF-002 步驟 4），可考慮明示為一條 NFR 或 [BA確認]（自動觸發 vs CI/CD 階段預先執行）
- **不阻塞**（屬 SD 階段技術決策，BA 委派可接受）

---

## 10. 追溯矩陣驗證

| 需求 ID | 有驗收標準 | 有來源引用 | 有流程對應 | 結果 |
|---------|----------|----------|----------|------|
| FR-001 | AC-044/045 | enhanced-input + baseline | BF-001 (步驟 1-5) | ✅ |
| FR-002 | AC-046/047 | enhanced-input + conventions §2 + TBL-001/002/003 | BF-001 (步驟 3) | ✅ |
| FR-003 | AC-048/049 | enhanced-input + conventions §5 + §8 | BF-001 (步驟 3) | ✅ |
| FR-004 | AC-050/051 | [BA確認] BC-5 + conventions §2/§8 | BF-001 (步驟 3) | ✅ |
| FR-005 | AC-052/053 | enhanced-input + Rule 18 + envPrefix | BF-002 (步驟 2) | ✅ |
| FR-006 | AC-054/055 | enhanced-input + config healthcheck | BF-002 (步驟 1-7) | ✅ |
| FR-007 | AC-056 | [BA確認] BC-1 | BF-002 + BF-003 + CONST-009 | ✅ |
| FR-008 | AC-057 | [BA確認] BC-2 | BF-001 (步驟 4) | ✅ |

**全部 8 FR 三向追溯完整（AC + 來源 + BF）**。

---

## 11. 反腦補偵測結果（彙整）

| FR ID | 使用者原文來源 / [BA確認] 流程 | 判定 |
|-------|------------------------------|------|
| FR-001 | enhanced-input.md「sqlite3 driver 改為 Postgres driver」line 32 | ✅ 有來源 |
| FR-002 | enhanced-input.md「3 張既有資料表必須遷移」line 28-31 + TBL-001/002/003 [REUSE] | ✅ 有來源 |
| FR-003 | enhanced-input.md「正式 migration 工具」line 33 + conventions §5/§8 | ✅ 有來源 |
| FR-004 | [BA確認] BC-5 流程合規 → 採納（理由 SUG-001 充分）| ✅ [BA確認] 落地 |
| FR-005 | enhanced-input.md「環境變數：新增 POSTGRES_*」line 34 + Rule 18 | ✅ 有來源 |
| FR-006 | enhanced-input.md「Railway 部署設定」line 35 + config healthcheck | ✅ 有來源 |
| FR-007 | [BA確認] BC-1 流程合規 → 採納（理由：CLAUDE.md / baseline 已認定 ephemeral）| ✅ [BA確認] 落地 |
| FR-008 | [BA確認] BC-2 流程合規 → 採納（理由 SUG-001 隱含 + docker-compose 已備）| ✅ [BA確認] 落地 |

**結論**: 0 個腦補 FR。

---

## 12. 結論

| 項目 | 結果 |
|------|------|
| **Tester 獨立分數** | **94/100** |
| **BA 階段獨立判定** | **✅ PASS** |
| Critical 數 | **0** |
| Major 數 | **0** |
| Minor 數 | **2**（FR-002 型別字面 / NFR-004 baseline 取法）— **不阻塞** |
| Info 數 | **3**（onboarding 說明 / SLA dashboard / migration 觸發策略） |
| L1 false positive 三項判定 | **3/3 確認為 false positive**（PM 判斷正確；建議改進 L1 腳本但不阻塞 BA）|
| 6 個 [BA確認] 決策 | **6/6 合理且範圍清楚** |
| Cross-TASK 修改預警 | **充足**（TASK-001 uiux 為 brownfield-document 模式無 schema-bound UI，不會破壞；SA 階段落實 [CROSS-TASK:] 即可）|
| Rule 11 IRREVERSIBLE 緩解 | **充足**（CONST-009 + SUG-006 + BF-003 三層保護） |
| Rule 18 Parameter Registry 預警 | **充足**（5 POSTGRES_* + 1 DATABASE_URL；SSL/pool/cert 屬 SD/Deploy 條件性追加，BA 階段委派合理）|
| NFR 量化 | **12/12 量化**（1 個 Minor：NFR-004 baseline 取得方法可更明確） |
| 不納入清單反腦補 | **15/15 候選涵蓋**（覆蓋完整）|

**建議行動**:
1. **PM**: 採納本報告，標記 test-ba PASS，可進入 SA 階段
2. **PM**（可選）: 把 2 Minor + 3 Info 在 SD/SA 階段 dispatch prompt 中提示 SD/SA agent 留意（如 SD 補 baseline 取法、SA 處理 [CROSS-TASK:] 標記細節）
3. **PM**（可選）: 在後續 PR 中改進 L1 `sdlc-role-verify.sh` 腳本對 BA 階段的三項檢查（未完成標記 / FR ID 重複 / 模糊用詞），加 context-aware 過濾減少 false positive
4. **BA**: 不需修改文件（無 Critical/Major）

---

## 13. [BLOCKED] 項目

無。Tester 完成獨立驗證，無阻塞項。

---

> **附註**:
> - 本報告由 Tester 在獨立上下文中執行（未存取 BA agent 開發對話歷史）
> - 對照基準: enhanced-input.md / config.json / conventions/*.md / baseline-audit / shared/*.md
> - 驗證工具: Read / Grep / Bash（sdlc-role-verify.sh L1 + 獨立 Grep 交叉驗證）
> - Tester 立場: 對抗心態 — 找 bug 即成功；BA score 95 自評不採信，獨立評分 94 與 BA 接近，差 1 分主因 NFR-004 baseline 取法 Minor
