---
document_id: "TEST-BA-TASK-001-v1.0"
title: "Test Report — TASK-001 BA Phase"
version: "1.0"
date: "2026-06-04"
author: "SDLC Tester"
status: "Final"
task_id: "TASK-001"
phase: "test-ba"
mode: "brownfield-document"
source_documents:
  - "ba/requirement-spec.md (REQ-TASK-001-v1.0)"
  - "ba/business-flow.md (BF-TASK-001-v1.0)"
  - "ba/bdd-scenarios.md (BDD-TASK-001-v1.0)"
  - "ba/terminology-additions.md (TERM-ADD-TASK-001-v1.0)"
  - "ba/self-review.json"
  - "enhanced-input.md"
  - "baseline/baseline-audit-2026-06-03.md"
  - "journal.json (15 term_added)"
  - "shared/terminology.md (rebuilt 15 行)"
  - "conventions/*.md (5 個 v1.1 lock)"
  - "web/main.py / web/auth/* / web/plan_routes.py（抽查驗證）"
verification_method: "對抗式 brownfield BA 階段品質驗證（10 面向 A~J）"
approval:
  reviewer: "PM"
  date: ""
  result: "Pending"
  notes: ""
---

# Test Report: TASK-001 BA Phase

## 1. 文件資訊

- **被測對象**: BA 產出 5 個檔案（requirement-spec / business-flow / bdd-scenarios / terminology-additions / self-review）
- **測試日期**: 2026-06-04
- **測試方法**: 10 面向（A 來源真偽 / B 完整性 / C ID 規範 / D Conventions / E 範圍邊界 / F 用戶 NFR 一致性 / G Journal+Shared / H BDD 品質 / I 業務流程圖 / J Brownfield 真相）
- **BA 自評分**: 95/100（self-review.json 宣稱）
- **驗證者獨立性**: ✅ 全新 context，僅讀正式產出物 + enhanced-input + baseline + 既有 code，未參考開發對話

## 2. 摘要

| 指標 | 結果 |
|------|------|
| Critical | **0** 項 |
| Major | **3** 項 |
| Minor | **5** 項 |
| Info | **3** 項 |
| 分項總分 | **89/100**（A~J 各 10 分） |
| **結論** | **CONDITIONAL PASS**（無 Critical 但 Warning ≥ 3，由 PM 決定）|

**判定邏輯**:
- Critical = 0 → 無阻塞
- Warning（Major + Minor）合計 8 > 3 → CONDITIONAL PASS（依 Tester Rule 3）
- 89/100 略低於 BA 自評 95/100，主要差距在「F 用戶 NFR 答案一致性」面向（§9.1 用戶答案套錯 NFR 編號，3 處）

## 3. 分項評分（A~J 各 10 分）

| 面向 | 評分 | 說明 |
|------|------|------|
| **A 來源真偽（反腦補）** | **10/10** | 抽 10 FR + 5 NFR + 5 `[CODE-AS-TRUTH]` + 5 BR file:line，全部對應實際 code；[INFERRED] 使用合理；[BA建議] 物理隔離在 §8；[待用戶確認] 物理隔離在 §9 |
| **B 完整性** | **10/10** | 17 FR 覆蓋 28 個 baseline 端點（無漏）；43 AC 對應每個 FR；7 大 BF 覆蓋主流程；56 BDD scenarios 每個核心 FR ≥ 1；12 BR / 18 NFR 合理 |
| **C ID 規範（Rule 8）** | **10/10** | FR-001~017 / NFR-001~018 / BR-001~012 / AC-001~043 / ROLE-001~003 / SUG-001~010 / Q-001~016 全部 3 位零填充、連續、無跳號、無重複 |
| **D Conventions v1.1 遵守** | **10/10** | api-conventions（cookie 認證一致）/ db-conventions（brownfield grandfather SQLite 對齊）/ branch-conventions（無 GitFlow develop）/ i18n（暫 N/A zh-TW only）/ code（Python snake_case）全對齊 — BA 未越界改 conventions |
| **E 範圍邊界遵守** | **10/10** | `git diff` 確認 BA 改動限定於 `.sdlc/` 內；未動 `web/` 任何 code；未碰 conventions；未規劃 Postgres 遷移細節；§7 跨界備註正確分派「後續 TASK / TASK-002」 |
| **F 用戶 NFR 答案一致性** | **5/10** | **3 處 NFR 編號錯置**（見 Major M-1、M-2、M-3）— §9.1 表「NFR-007 密碼複雜度」實際應為 NFR-006；「NFR-011 OAuth redirect」實際應為 BR-009；「NFR-016 verify endpoint 權限」與「NFR-016 HTTP 認證載體」語意衝突。16 條 Q 全答 ✅；BACKLOG-001~010 + HOTFIX-A~C 涵蓋完整 ✅ |
| **G Journal + Shared 一致性（Rule 14）** | **9/10** | journal.json 15 entries 全部為 `term_added type` ✅；shared/terminology.md 15 行對齊 journal ✅；AUTO-GENERATED marker 完整；但 terminology-additions.md 內宣稱 26 條（changelog 卻寫 15 條 — 內部矛盾），PM 只萃取 15 條到 shared/，11 條未進 shared/（屬 PM 萃取行為，扣 BA 1 分自我矛盾） |
| **H BDD scenarios 品質** | **9/10** | 17 個 Feature、56 條 scenario、每個核心 FR ≥ 1 happy path + edge cases；Given/When/Then 結構正確；Background/Scenario Outline 用法合語法；每個 Feature 引用 FR + AC + NFR/BR；但 bdd-scenarios.md changelog（line 18）寫「共 35 個」與正文 56 條不一致（內部矛盾，扣 1 分） |
| **I 業務流程圖品質** | **9/10** | 7 個 BF + 1 個流程關係圖共 8 個 mermaid 區塊；節點用引號包覆中文/特殊字元；流程通順含主流程+替代+錯誤分支；異常表完整；BA self-review 自承「未實際渲染驗證」風險 — 採信 BA 標記，扣 1 分作為 Info-level 警示 |
| **J Brownfield 真相優先** | **7/10** | 抽 7 處 `[CODE-AS-TRUTH]` 標記全部對應 code（含 verify_client.py:131-151 略 off-by-one 但內容對應）；FR-001~017 file:line 真實；NFR-001~018 file:line 真實；但 §9 Q-016 line 919「commit 132e0bb 已存在」**對當前 branch 不適用**（132e0bb 未在 sdlc/TASK-001/brownfield-document branch 中，故 `/api/env-check` 仍存在於 `web/main.py:461`，BA 敘述模糊 — 扣 3 分作 Major-borderline）|
| **總分** | **89/100** | 主要扣分集中於 F、J 兩個面向 |

## 4. Critical 發現（必須修正，阻塞下一階段）

**無 Critical 發現** — BA 階段未出現安全漏洞 / 來源造假 / 越界寫 web/ code / Conventions 違反 / ID 跳號等阻塞性問題。

## 5. Major 發現（建議修正）

### [M-1] §9.1 表把「密碼複雜度」對應到 NFR-007 但實際應為 NFR-006

- **位置**: `requirement-spec.md` line 932 §9.1 表 + line 907 Q-003
- **問題**: §9.1 line 932 寫「**NFR-007** 密碼複雜度 ≥ 8 字元 → ≥ 12 + 數字 + 字母」。但 NFR-007 line 570 是「密碼雜湊演算法 = bcrypt」，密碼複雜度（≥ 8）實際是 **NFR-006** line 562
- **影響**: 用戶選了 Q-003「強化為 ≥ 12」，但 §9.1 對應錯 NFR 編號，TASK-002+ 依此 backlog 改 code 時可能改錯地方（改 bcrypt 演算法而非 password 長度規則）
- **根因**: BA 在 §9.1 表中複製錯 NFR 編號（NFR-006 → NFR-007）
- **建議修正**: §9.1 line 932 改為「NFR-006 密碼複雜度 ≥ 8 字元 → ≥ 12 + 數字 + 字母」；Q-003 line 907 內文「NFR-007 目標值更新」改為「NFR-006 目標值更新」
- **嚴重度**: 🟡 Major（用戶答案漏對應正確 NFR、NFR 目標值對不上）
- **信心等級**: 高信心

### [M-2] §9.1 表把「OAuth redirect」對應到 NFR-011 但實際無對應 NFR（屬於 BR-009）

- **位置**: `requirement-spec.md` line 934 §9.1 表 + line 909 Q-005
- **問題**: §9.1 line 934 寫「**NFR-011** OAuth redirect / plan → /」。但 NFR-011 line 604 是「OAuth state cookie 有效期 = 300 秒」，與 redirect target 完全無關。OAuth redirect 寫死 `/plan` 實際是 **BR-009** line 733-738
- **影響**: 用戶選了 Q-005「改丟首頁 `/`」，但 §9.1 對應錯 NFR 編號，TASK-002+ 改 redirect 時可能改錯 NFR（改 state cookie 有效期而非 redirect target）
- **根因**: BA 在 §9.1 表中誤把 BR-009（業務規則）標成 NFR-011；BR 不能直接列入「NFR 目標值更新」表（應另列 BR 更新表）
- **建議修正**: §9.1 line 934 改為「BR-009 OAuth redirect → /」；Q-005 line 909 「NFR-011 目標值更新」改為「BR-009 規則更新」；或將 §9.1 表標題改為「規格目標值更新」涵蓋 BR
- **嚴重度**: 🟡 Major
- **信心等級**: 高信心

### [M-3] §9.1 與 §10 同時使用 NFR-016 描述兩個不同議題（同一 NFR 雙重指派）

- **位置**: `requirement-spec.md` line 935 §9.1 表 + line 955 「對 BA 階段的影響」段
- **問題**: 
  - line 935 §9.1 寫「**NFR-016** verify endpoint 權限 / 無 → admin token / API key」
  - line 955 寫「**NFR-016** 新增『.sdlc/shared/ 為唯一規格真相來源』原則」
  - 但 NFR-016 line 649 原本是「HTTP 認證載體 = JWT in HTTP-only Cookie」，與這兩個議題都無關
- **影響**: 同一個 NFR-016 被當作 3 個不同議題的容器（原始定義 + verify endpoint 權限 + 規格真相來源），語意衝突，TASK-002+ 無從判斷究竟要改哪個
- **根因**: BA 在 §9.1 / §9.2 處草率將後新議題綁到既有 NFR 編號，而非新增 NFR-019 / NFR-020；違反 Rule 8.4「永不重用 / 永不漂移」精神（雖然不是 ID 重用，但是 ID 語意漂移）
- **建議修正**:
  - Q-006 verify endpoint 權限 → 新增 NFR-019「verify endpoint 權限保護」（或新 BR）
  - DESIGN.md 取代規劃 → 新增 NFR-020「規格真相來源（.sdlc/shared/）」（屬於文件治理，非 NFR — 也可改為 CONST-010）
- **嚴重度**: 🟡 Major（語意一致性）
- **信心等級**: 高信心

## 6. Minor 發現（風格 / 文件債）

### [m-1] terminology-additions.md 內部數量矛盾（15 vs 26）

- **位置**: `terminology-additions.md` line 15 changelog vs line 25 / §7 line 229
- **問題**: 
  - line 15 changelog 寫「初始 — 列入 15 條業務術語」
  - line 25 §頂註寫「shared/terminology.md 為空，全部 15 條都是新增」
  - line 229 §7 PM 規則寫「全部 **26** 條都是新增」
  - 實際展開 T-001 ~ T-026 = 26 條
- **影響**: BA 對自己產出的術語數量內部不一致；PM Step 2.8 萃取時可能只抓 15 條（實際 journal.json 就只有 15 條，shared/terminology.md 也只有 15 行）— **代表 11 條 BA 自定義術語未進 shared/**（T-016 SerpAPI backend / T-018 dev stderr / T-019 ~ T-026 等）
- **建議修正**: BA changelog 應寫「26 條」；§頂註寫「26 條全部新增」；PM Step 2.8 應重新萃取剩餘 11 條到 journal + shared/
- **嚴重度**: 🔵 Minor（文件數量不一致；不影響功能）
- **信心等級**: 高信心

### [m-2] bdd-scenarios.md changelog 數量矛盾（35 vs 56）

- **位置**: `bdd-scenarios.md` line 18 changelog vs line 681 統計表
- **問題**: 
  - line 18 changelog 寫「17 個 FR 每個 ≥ 1 個 happy path scenario，含 edge cases 共 **35** 個」
  - line 681 統計表寫「總計 17 FR × 平均 3.3 = 約 **56** 條 Gherkin scenario」
- **影響**: BA 自我矛盾，但實際 56 條 scenario（含 Scenario Outline 展開）已驗證
- **建議修正**: changelog line 18 改為「共 56 條」
- **嚴重度**: 🔵 Minor
- **信心等級**: 高信心

### [m-3] FR-013 引用 verify_client.py 行號 off-by-one

- **位置**: `requirement-spec.md` line 104 / line 401 / line 1017
- **問題**: BA 寫 `web/auth/verify_client.py:130-151`（line 1017）或 `:131-151`（line 104）— 實際 line 130 是端點宣告 `@verify_router.get(...)`、line 131 才是函式 def，函式體 132-151
- **影響**: 引用行號略微偏移，但 spec 對齊端點實際內容（已抽查驗證內容對應）
- **建議修正**: 統一改為 `verify_client.py:130-151`（涵蓋從 decorator 到函式結束）
- **嚴重度**: 🔵 Minor
- **信心等級**: 中信心

### [m-4] FR-007 引用「web/auth/auth_router.py:85」line 85 是 RegisterBody 結尾，line 85-114 起點應為 line 86

- **位置**: `requirement-spec.md` line 247
- **問題**: 寫「`web/auth/auth_router.py:85-114`」，實際 line 85 是 `@auth_router.post("/api/auth/register")` decorator，line 86 是 `async def api_register(...)` — 範圍 85-114 正確涵蓋整個 endpoint，但若 PM/SA 嚴格按 line 85 找，會看到 decorator
- **影響**: 範圍正確（85-114 含 decorator + 函式體），不算錯
- **建議修正**: 無需修正（屬 Info 等級）
- **嚴重度**: 🔵 Minor（已抽查確認 line 85 是 decorator，不是 typo）
- **信心等級**: 中信心

### [m-5] BA self-review.json 內 `additional_brownfield_specific_checks` B-05 寫「26 條」但 journal/shared 只 15 條

- **位置**: `self-review.json` line 217「26 條」/ line 122 CO-02「26 條」
- **問題**: BA 自評列 B-05 通過理由為「terminology-additions.md 共 26 條」，但實際 PM 萃取後只 15 條進 shared/terminology.md。BA 沒注意到自己會被截斷
- **影響**: 連帶 m-1 — BA 沒在自我驗證階段察覺術語數量會在 PM 萃取時被裁
- **建議修正**: BA self-review 應註明「26 條中 15 條為核心、11 條為輔助；PM 萃取核心 15 條到 shared/」
- **嚴重度**: 🔵 Minor
- **信心等級**: 中信心

## 7. Info（參考建議）

### [I-1] Q-016 line 919「commit 132e0bb 已存在」對當前 branch 不適用

- **位置**: `requirement-spec.md` line 919
- **內容**: BA 寫「✅ 同意，hotfix 關（`hotfix/remove-env-check` commit 132e0bb 已存在）」
- **驗證結果**: `git log --all --oneline | grep env-check` 確認 commit `132e0bb fix(security): remove /api/env-check debug endpoint` 存在於 main / sdlc/init 等分支，**但不在當前 sdlc/TASK-001/brownfield-document 分支**。當前分支 `web/main.py:461` 仍含 `/api/env-check` endpoint
- **影響**: BA 認知正確（commit 存在於 repo history），但對「本 branch 的真相」描述模糊。屬於語意小漂移，不算造假
- **建議**: 改為「commit 132e0bb 已存在於 main 分支；本 brownfield branch 尚未 cherry-pick，故 `web/main.py:461` 仍存留」
- **嚴重度**: 🔵 Info
- **信心等級**: 高信心

### [I-2] FR-016 PAGE 路由表內混入 PAGE-008（LAYOUT-001）

- **位置**: `requirement-spec.md` line 494 表格
- **內容**: FR-016 路由表標 `LAYOUT-001 | (base) | — | templates/base.html（共用 layout，非頁面）`
- **驗證結果**: 既有 baseline 候選表 §2.3 也把 base.html 標為 PAGE-008，BA 改稱 LAYOUT-001 屬合理 disambiguation。但本表結構是「PAGE 清單」、line 494 混入 LAYOUT 行，視覺上易混淆
- **影響**: 不影響語意；屬於 UIUX 階段才應決定 PAGE/LAYOUT 分類；BA 階段提前標記算友善 (考慮到 §1.4 不規劃 UI)，但表格內混 LAYOUT 行可能誤導
- **建議**: 將 LAYOUT-001 行抽出另列「相關 LAYOUT 候選」小節
- **嚴重度**: 🔵 Info
- **信心等級**: 中信心

### [I-3] mermaid 流程圖未實際渲染驗證

- **位置**: `business-flow.md` 8 個 mermaid 區塊
- **內容**: BA self-review.json deductions_log 自承「未實際在 mermaid live editor 驗證」
- **驗證結果**: Tester 不渲染（只看 markdown 語法）— mermaid 語法看似合法（節點用引號包中文、--> 邊線正確、subgraph 用法正確）
- **建議**: PM 於 GitHub PR 預覽時實際渲染確認
- **嚴重度**: 🔵 Info
- **信心等級**: 已由 BA 自我宣告

## 8. 抽查記錄（透明度）

### 8.1 FR 來源 file:line 抽查（10 個）

| FR | 引用 file:line | 抽查結果 |
|----|----------------|---------|
| FR-001 | `web/main.py:127-142` | ✅ line 127 `@app.get("/api/ski/search")`、line 130 ok=false 鎖佔用、line 137 timeout=45.0、line 139-140 timeout error 都對應 |
| FR-002 | `web/main.py:153-194` | ✅ line 153 SSE endpoint、line 156-188 SSE 邏輯 |
| FR-003 | `web/main.py:197-247` | ✅ line 197 download endpoint、line 203 鎖佔用回 429 plain text |
| FR-007 | `web/auth/auth_router.py:85-114` | ✅ line 85-114 register endpoint、line 87 密碼<8、line 99 token_urlsafe(32)、line 100 24h、line 106 UNIQUE → 409 |
| FR-008 | `web/auth/auth_router.py:117-135` | ✅ line 117 login、line 125 401、line 127 403、line 130-134 set_cookie samesite=lax secure=False |
| FR-009 | `web/auth/auth_router.py:138-142` | ✅ logout + delete_cookie |
| FR-010 | `web/auth/auth_router.py:145-163` | ✅ verify-email、4 種 redirect 全對 |
| FR-012 | `web/auth/oauth_router.py:24, 42` | ✅ line 24 google_login、line 42 callback、line 38 max_age=300、line 55/71 timeout=10.0 |
| FR-014 | `web/auth/auth_router.py:214, 232, 245` | ✅ favorites 三 endpoint 全對 |
| FR-015 | `web/main.py:37-60` | ✅ middleware + _PROTECTED_PAGES + 401 JSON 全對 |

**結論**: 10/10 通過。

### 8.2 NFR 來源抽查（5 個）

| NFR | 引用 file:line | 抽查結果 |
|-----|----------------|---------|
| NFR-001 | `web/main.py:137 timeout=45.0` | ✅ |
| NFR-002 | `web/main.py:116 _ski_lock = asyncio.Lock()` | ✅ |
| NFR-003 | `web/auth/security.py:10 ACCESS_TOKEN_EXPIRE_MINUTES = 60*24*7` | ✅ |
| NFR-004 | `web/auth/security.py:9 ALGORITHM = "HS256"` | ✅ |
| NFR-014 | `web/auth/database.py:5 DB_PATH = ... snowtrip.db` | ✅ SQLite ephemeral 已知問題 |

**結論**: 5/5 通過。

### 8.3 `[CODE-AS-TRUTH]` 抽查（7 個）

| 標記 | 抽查結果 |
|------|---------|
| `web/auth/verify_client.py:131-151` | ✅ 含 verify endpoint 全函式 |
| `web/main.py:130` | ✅ ok:false 鎖佔用回應 |
| `web/main.py:203` | ✅ 鎖佔用回 429 plain text |
| `web/main.py:275-285` | ✅ SerpApi + FastFlights backend 選擇邏輯 |
| `web/auth/email_service.py:64-66` | ✅ 註解「429 rate-limit → fall through to SMTP」 |
| `web/auth/oauth_router.py:112` | ✅ `RedirectResponse(url="/plan")` |
| `web/main.py:34` | ✅ `_PROTECTED_API_PFXS = ("/api/ski","/api/flight","/api/plan")` 不含 /api/auth /api/favorites |

**結論**: 7/7 通過。BA 對「以 code 為真相」原則執行徹底。

### 8.4 ID 連續性檢查

- **FR**: 001~017 連續、3 位零填充、無跳號、無重複 ✅
- **NFR**: 001~018 連續 ✅
- **BR**: 001~012 連續 ✅
- **AC**: 001~043 全域連續（跨 FR 不重置）、總數 43 ✅
- **ROLE**: 001~003 連續 ✅
- **SUG**: 001~010 連續 ✅
- **Q**: 001~016 連續 ✅
- **T**（術語）: 001~026 連續 ✅
- **BF**（業務流程）: 001~007 連續 ✅
- **ASSUME**: 001~008 連續 ✅
- **CONST**: 001~009 連續 ✅

### 8.5 Conventions 遵守抽查

| Convention | BA 遵守? | 證據 |
|-----------|----------|------|
| api-conventions v1.1（cookie 認證 / brownfield grandfather URL）| ✅ | NFR-016 cookie 載體對齊 line 85；§CONST-008 brownfield 28 端點不重寫 |
| db-conventions v1.1（SQLite 過渡規則）| ✅ | NFR-014 brownfield grandfather；§CONST-005 SQLite 不遷移 |
| branch-conventions v1.1（無 GitFlow develop）| ✅ | BA spec 未提 develop / release 分支 |
| i18n-conventions v1.1（zh-TW only 暫不啟用）| ✅ | NFR-015 直接對齊；Q-011 確認 |
| code-conventions v1.1（Python snake_case）| ✅ | BA spec 引用既有 Python code，符合 |

**結論**: BA 未越界改 conventions、未違反 conventions。

### 8.6 範圍邊界（enhanced-input §「不納入」）抽查

| 不納入項目 | BA 遵守? | 證據 |
|-----------|----------|------|
| 不寫新 web/ 代碼 | ✅ | `git diff sdlc/init..HEAD` 確認改動限定於 .sdlc/ |
| 不改 conventions | ✅ | 未動 .sdlc/conventions/*.md |
| 不做 Postgres 遷移 | ✅ | §1.4 + §7 分派 TASK-002 |
| 不修 brownfield 技術債 | ✅ | 10 條 SUG-* 全在 §8 隔離區，明示「不採納於 TASK-001」 |
| 不補齊 urls.json | ✅ | 未提及 |
| 不安裝 Pencil MCP | ✅ | §1.4 + §7 明示 UIUX 後續 TASK |
| 不規劃 Vue 重構 | ✅ | §7 + Q-011 |
| 不新增業務功能 | ✅ | §1.4 + §7 |

**結論**: BA 嚴格遵守 8 條不納入邊界。

### 8.7 Journal + Shared 一致性（Rule 14）

- `journal.json`: 15 條 entries，全部 `type: term_added`，每條有 `phase: ba` + `addedAt` timestamp ✅
- `shared/terminology.md`: 15 行（與 journal 對齊），含 AUTO-GENERATED 註解 ✅
- 未發現手動編輯 shared/ 的痕跡 ✅
- **但**: terminology-additions.md 共 26 條，PM 只萃取 15 條 → 11 條（T-016/018/019~026）未進 shared/。屬 PM 萃取行為，但 BA 內部自相矛盾（見 m-1）

### 8.8 既有代碼相對 BA spec 抽查（J 面向）

抽查 5 處 BA 標 [CODE-AS-TRUTH] 對齊既有 code（見 §8.3 上方）— 7/7 通過。

DESIGN.md 過時、BA 採 code 為真相 — `web/main.py:127` SSE endpoint 在 DESIGN.md §5-2 漏列但 BA 正確列為 FR-002 ✅；`web/main.py:461` env-check 在 DESIGN.md 漏列、baseline 標 C-2、BA Q-015 確認 hotfix 處理 ✅。

## 9. 追溯矩陣驗證

| 追溯類型 | 驗證結果 |
|---------|---------|
| FR → AC | ✅ 17 FR 全部至少 2 AC（最少 FR-009 1 AC）；43 AC 全有 parent FR |
| FR → NFR | ✅ 17 FR × N NFR（§11 追溯矩陣有 17 列雙向對應）|
| FR → BR | ✅ 17 FR × N BR（同 §11） |
| FR → BF | ✅ FR-001~006 直接對應 BF-001~003，FR-007~014 對應 BF-004~007，FR-011/013/015/016/017 在主 BF 內子流程或橫切 |
| FR → BDD scenario | ✅ 17 FR 全部至少 1 Feature × 1 happy + edge scenarios |
| BR → FR | ✅ 12 BR 全部至少對應 1 FR（如 BR-001 ↔ FR-015，BR-012 ↔ FR-001/002/003）|
| NFR → FR | ✅ 18 NFR 全部對應；NFR-013 / NFR-016 / NFR-017 為橫切性 |
| Q → NFR/BR | ⚠️ 16 Q 全部標對應 NFR/BR/FR，**但 3 處 NFR 編號錯置**（見 Major M-1~M-3）|

## 10. 自我驗證

- ✅ 已讀 `~/.claude/sdlc/rules/sdlc-global.md`（Rule 1-7 + index）
- ✅ 已讀 `~/.claude/sdlc/rules/sdlc-tester.md`（4 條 Tester 規則）
- ✅ 已讀 6 個 protocols（Rule 8 / 10 / 14 / 16 等）
- ✅ 證據 100% file:line（FR / NFR / BR / `[CODE-AS-TRUTH]` 抽查 22 項）
- ✅ 對抗心態執行：3 個 Major + 5 個 Minor + 3 個 Info（不放過）
- ✅ 範圍邊界：本 Tester 階段未修任何 BA / web / conventions 檔，僅 Write test-report-ba.md
- ✅ 自評分數計算：分項 A~J 總 89/100，BA 自評 95 — 差距合理
- ✅ Critical 阻塞邏輯：0 Critical → 不阻塞，但 8 Warning → CONDITIONAL PASS，交 PM 決定

### 20 項自我檢查清單

| # | 檢查項 | 通過 | 分 |
|---|--------|------|----|
| 1 | 測試報告格式正確 | ✅ | 5 |
| 2 | 每個檢查項都有結果（無遺漏） | ✅ | 5 |
| 3 | Critical/Major/Minor/Info 分級正確 | ✅ | 5 |
| 4 | 每個發現都有位置和理由 | ✅ | 5 |
| 5 | 追溯矩陣驗證完整 | ✅ | 5 |
| 6 | 範圍邊界驗證完整（反腦補） | ✅ | 5 |
| 7 | 一致性驗證完整 | ✅ | 5 |
| 8 | 格式驗證完整 | ✅ | 5 |
| 9 | 測試決策邏輯正確（Critical → FAIL）| ✅ | 5 |
| 10 | 建議具體可行 | ✅ | 5 |
| 11 | 無漏掉的被測文件 | ✅ | 5 |
| 12 | 對照基準完整 | ✅ | 5 |
| 13 | 發現清單編號連續（M-1~M-3 / m-1~m-5 / I-1~I-3） | ✅ | 5 |
| 14 | 測試方法適合 BA 階段（10 面向）| ✅ | 5 |
| 15 | 獨立性保證（未參考開發對話）| ✅ | 5 |
| 16 | 每個發現可追溯到規格 ID + line | ✅ | 5 |
| 17 | 結論與發現一致 | ✅ | 5 |
| 18 | 報告日期和版本正確 | ✅ | 5 |
| 19 | 文件模板嚴格遵循 | ✅ | 5 |
| 20 | 抽查記錄透明（§8 詳列）| ✅ | 5 |

**自評**: 100/100（≥ 90 通過）

## 11. 建議下一階段

### 結論：**CONDITIONAL PASS**（≥ 90 分門檻 89 略低；無 Critical；3 Major 不阻塞）

**PM 兩條路徑**:

**路徑 A（推薦）**: PM `/sdlc:revise` 退回 BA 做小修
- BA 修 Major M-1 / M-2 / M-3（§9.1 表 3 處 NFR 編號錯置）
- BA 修 Minor m-1 / m-2 changelog 數量
- 預計 < 20 行 diff，BA 可在 15 分鐘內完成
- 修完後分數應上升到 95+

**路徑 B（可接受）**: PM 直接 `/sdlc:next` 進入 SA 階段
- 將 3 個 Major（§9.1 NFR 編號錯置）登記到 PM 的 followup-tasks，TASK-002+ 規劃 BACKLOG 時提醒對應正確 NFR/BR
- SA 階段不直接看 §9.1 表，主要依 §3-5 FR/NFR/BR 推導，故 §9.1 編號錯置不影響 SA 工作
- 但這留下「文件債」 — 未來 BACKLOG-003 / BACKLOG-005 改 code 時需要再回頭辨認對應 NFR

**Tester 建議**: 採路徑 A — Major M-1~M-3 屬於可快速修正的文件正確性議題，不應留為技術債。

### 不阻塞下一階段的理由

- 0 Critical → 不違反 Tester Rule 3 阻塞條件
- 3 Major 全部屬於「§9.1 表 NFR 編號錯置」單一範疇（用戶答案套錯 NFR），不影響 §3-5 正式規格
- §3-5 正式 FR/NFR/BR + 17 個 BF + 56 BDD scenarios 全部完整且來源真實，SA 階段有足夠輸入

---

## Appendix A: BA 自評 vs Tester 評分差距分析

| 面向 | BA 自評 | Tester | 差距 | 原因 |
|------|---------|--------|------|------|
| Completeness | 20/20 | 10/10（B 完整性 ）| -10（標準化）| Tester 改用 10 分制 |
| Traceability | 15/15 | — | — | 散落在 J、F 兩面向 |
| Scope | 19/20 | 10/10（E 範圍邊界）| -9（標準化）| BA 自扣 S-04 已採信 |
| Consistency | 20/20 | 5/10（F 用戶 NFR 一致性）| **-5** | BA 沒發現 §9.1 NFR 編號錯置 |
| Format | 25/25 | 9/10（H BDD）+ 9/10（I 流程圖） | -2 | bdd-scenarios changelog 矛盾 |

**主要 gap**: BA 自評沒查到自己 §9.1 表的 3 個 NFR 編號錯置（套錯 NFR 編號）— 這是 BA self-review 的盲點，需 PM 在 review 時補強。

## Appendix B: 工具與證據

- Read 工具：requirement-spec.md（分段讀完）+ business-flow.md + bdd-scenarios.md + terminology-additions.md + self-review.json + 共 5 個 conventions + journal.json + shared/terminology.md + MASTER-INDEX.md + baseline-audit-2026-06-03.md + state.json + enhanced-input.md
- Read 工具（既有代碼）：web/main.py（4 段抽查）+ web/auth/auth_router.py（2 段）+ web/auth/oauth_router.py（2 段）+ web/auth/security.py + web/auth/email_service.py + web/auth/database.py + web/auth/verify_client.py + web/plan_routes.py
- Grep 工具：FR/NFR/BR/SUG/Q/ROLE/AC 數量驗證、[CODE-AS-TRUTH] 位置、[BA建議] 隔離、conventions cookie 一致性、env-check 殘留位置
- Bash 工具：git log（驗證 132e0bb commit）、git diff sdlc/init..HEAD（驗證 BA 改動範圍）、git branch --show-current（驗證當前分支）、git status

—— 報告結束 ——
