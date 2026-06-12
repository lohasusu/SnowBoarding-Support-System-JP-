---
document_id: "CRREVIEW-{TASK_ID}-v1.0"
title: "Code Review 報告"
version: "1.0"
date: "{YYYY-MM-DD}"
author: "{FE/BE}"
status: "Draft"
task_id: "{TASK-ID}"
phase: "{fe/be}"
source_documents:
  - "API-{TASK_ID}-v1.0"
  - "CODEARCH-{TASK_ID}-v1.0"
change_history:
  - version: "1.0"
    date: "{YYYY-MM-DD}"
    changes: "初始版本"
    author: "{FE/BE}"
approval:
  reviewer: "PM"
  date: ""
  result: "Pending"
  notes: ""
---

# Code Review 報告 — {前端/後端}

## 1. 審查摘要

| 指標 | 結果 |
|------|------|
| 審查檔案數 | {N} |
| 迭代次數 | {M} |
| 初始 Critical | {n} → 最終: 0 |
| 初始 Warning | {w} → 最終: 0 |
| 最終 Info | {i} |

## 2. 審查維度

| 維度 | 檢查內容 | 結果 |
|------|---------|------|
| 程式碼品質 | 命名、結構、可讀性、重複程式碼 | ✅/❌ |
| 規格符合度 | 是否與 SD/UIUX 規格一致 | ✅/❌ |
| 多餘程式碼 | 未使用的變數/函式/import、死碼 | ✅/❌ |
| 幽靈功能偵測 | SD 未要求但自行新增的功能 | ✅/❌ |
| 安全性（FE） | XSS 防護、敏感資訊洩漏、Content-Security-Policy | ✅/❌/N/A |
| 安全性（BE） | SQL injection、auth bypass、hardcoded secrets、加密例外處理、快取清理、SSO session 清理、JWT 驗簽 | ✅/❌/N/A |
| FE-BE 型別契約 | types.ts ↔ BE DTOs 欄位名/型別/optional 一致性 | ✅/❌ |
| 效能 | 不必要的重渲染、大型套件、過度抽象 | ✅/❌ |
| 型別安全 | 無 any、嚴格型別 | ✅/❌ |
| Design Token 合規 | 是否有裸值繞過（僅前端） | ✅/❌/N/A |
| 無障礙 | ARIA、keyboard nav（僅前端） | ✅/❌/N/A |
| API 合規 | 路徑/方法/參數與 SD 一致（僅後端） | ✅/❌/N/A |
| Migration 可逆 | up+down 可執行（僅後端） | ✅/❌/N/A |

## 3. 迭代修正紀錄

### 迭代 1

| 發現ID | 分級 | 位置 | 問題描述 | 修正方式 |
|--------|------|------|---------|---------|
| CR-001 | Critical | {file:line} | {描述} | {修正方式} |
| CR-002 | Warning | {file:line} | {描述} | {修正方式} |

### 迭代 2（如有）

| 發現ID | 分級 | 位置 | 問題描述 | 修正方式 |
|--------|------|------|---------|---------|

## 4. 最終審查結果

| 指標 | 結果 |
|------|------|
| Critical | 0 |
| Warning | 0 |
| Info | {剩餘 Info 數量} |
| 結論 | PASS |

## 5. 剩餘 Info 項目（參考）

| 發現ID | 位置 | 描述 | 建議 |
|--------|------|------|------|
| CR-INFO-001 | {file:line} | {描述} | {改善建議} |

## 6. Git 審查基準

| 項目 | 說明 |
|------|------|
| Baseline Commit | {短 SHA} (`sdlc({TASK-ID}): sd approved`) |
| HEAD Commit | {短 SHA} |
| 變更檔案數 | {N} |
| 新增行數 | {N} |
| 刪除行數 | {N} |
