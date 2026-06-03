---
document_id: "SEC-{TASK_ID}-v1.0"
title: "資安檢查報告"
version: "1.0"
date: "{YYYY-MM-DD}"
author: "Deploy"
status: "Draft"
task_id: "{TASK-ID}"
phase: "deploy"
source_documents:
  - "API-{TASK_ID}-v1.0"
  - "CODEARCH-{TASK_ID}-v1.0"
change_history:
  - version: "1.0"
    date: "{YYYY-MM-DD}"
    changes: "初始版本"
    author: "Deploy"
approval:
  reviewer: "PM"
  date: ""
  result: "Pending"
  notes: ""
---

# 資安檢查報告

## 0. Scope & 掃描來源

| 項目 | 值 |
|------|-----|
| TASK ID | {TASK-ID} |
| Deploy scope | {local / local-staging / full} |
| 掃描時間 (UTC) | {YYYY-MM-DDTHH:MM:SSZ} |
| 掃描工具 | sdlc-security-scan.sh + (npm\|pip\|go\|dotnet) audit |
| 程式碼範圍 | {FE_SRC}, {BE_SRC} |
| 依賴工具實際跑過 | {npm, pip, go, dotnet 中的子集} |
| 依賴工具被略過 | {tool: reason} |

## 1. 檢查概覽（code × deps × total）

| 等級 | 程式碼掃描 | 依賴漏洞 | 合計 |
|------|-----------|---------|------|
| 🔴 Critical | {n_code_crit} | {n_deps_crit} | {n_total_crit} |
| 🟠 High | {n_code_high} | {n_deps_high} | {n_total_high} |
| 🟡 Medium | {n_code_med} | {n_deps_med} | {n_total_med} |
| 🔵 Low | {n_code_low} | {n_deps_low} | {n_total_low} |

### 部署決策（Deployer scope-aware gate）

- **Skill 內部判定**: PASS / FAIL（Critical > 0 或 High > 0 即 FAIL）
- **Deployer gate 結論**: ✅ PASS / ⚠️ WARNING / ❌ BLOCKED
  - 阻塞原因（若有）: {"Critical=N" | "High=N (scope=local-staging|full)" | "—"}
  - 依據: Critical 永遠阻塞；High 只在 scope=local-staging/full 阻塞
- **Drill-down 檔案**:
  - 程式碼發現逐筆 → `security-findings.json`
  - 依賴漏洞彙總 → `deps-audit.json`
  - 各工具原始輸出 → `deps-audit.json.{npm,pip,go,dotnet}`

## 2. OWASP Top 10 檢查

| # | OWASP 類別 | 偵測方法 | 結果 | 說明 |
|---|-----------|---------|------|------|
| A01 | Broken Access Control | SAST + auth 測試 | ✅/❌ | {說明} |
| A02 | Cryptographic Failures | SAST 弱加密規則 | ✅/❌ | {說明} |
| A03 | Injection | SAST + 參數化查詢 | ✅/❌ | {說明} |
| A04 | Insecure Design | 架構審查 | ✅/❌ | {說明} |
| A05 | Security Misconfiguration | 環境掃描 | ✅/❌ | {說明} |
| A06 | Vulnerable Components | 依賴掃描 | ✅/❌ | {說明} |
| A07 | Auth Failures | SAST session 管理 | ✅/❌ | {說明} |
| A08 | Data Integrity Failures | SAST 反序列化 | ✅/❌ | {說明} |
| A09 | Logging Failures | SAST 審計日誌 | ✅/❌ | {說明} |
| A10 | SSRF | SAST URL 驗證 | ✅/❌ | {說明} |

## 3. 發現清單

### Critical（必須修正，阻止部署）

- [SEC-CRIT-001] {問題描述}
  - **OWASP**: A{XX}
  - **位置**: {文件:行號}
  - **風險**: {描述潛在影響}
  - **修正建議**: {具體修正方式}

### High（必須修正，阻止部署）

- [SEC-HIGH-001] {問題描述}
  - **OWASP**: A{XX}
  - **位置**: {文件:行號}
  - **修正建議**: {具體修正方式}

### Medium（建議修正，不阻止）

- [SEC-MED-001] {問題描述}
  - **建議**: {修正建議}

### Low（記錄，下版本修正）

- [SEC-LOW-001] {問題描述}

## 4. 依賴掃描結果

| 依賴 | 版本 | 漏洞 | 嚴重度 | 修正版本 |
|------|------|------|--------|---------|
| {package} | {version} | {CVE-ID} | Critical/High/Medium/Low | {fixed_version} |

## 5. 密鑰偵測結果

| 類型 | 位置 | 說明 |
|------|------|------|
| 無發現 | - | 程式碼中未偵測到硬編碼密鑰 |

## 6. 結論

| 項目 | 結果 |
|------|------|
| Critical + High 數量 | {N} |
| 部署決策 | PASS（0 個 Critical/High）/ BLOCKED（有 Critical/High） |
| 必要修正事項 | {列表} |
| 建議改善事項 | {列表} |
