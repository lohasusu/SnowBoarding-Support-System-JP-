---
document_id: "DEPRESULT-{TASK_ID}-v1.0"
title: "部署執行結果報告"
version: "1.0"
date: "{YYYY-MM-DD}"
author: "Deploy"
status: "Draft"
task_id: "{TASK-ID}"
phase: "deploy"
source_documents:
  - "CICD-{TASK_ID}-v1.0"
  - "DEPCONF-{TASK_ID}-v1.0"
  - "SECR-{TASK_ID}-v1.0"
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

# 部署執行結果報告

## 1. 部署摘要

| 項目 | 結果 |
|------|------|
| 部署平台 | {platform} |
| CI/CD 平台 | {cicd} |
| 部署策略 | {deployStrategy} |
| 建構狀態 | ✅ 成功 / ❌ 失敗 |
| 本地部署驗證 | ✅ 成功 / ❌ 失敗 |
| 健康檢查 | ✅ 通過 / ❌ 失敗 |
| 遠端部署 | ✅ 成功 / ⏳ 待執行 / ❌ 失敗 |

## 2. 產出的部署檔案

| 檔案 | 路徑 | 狀態 | 說明 |
|------|------|------|------|
| CI/CD 配置 | {path} | ✅ 已建立 | {Pipeline 描述} |
| Dockerfile.fe | deploy/Dockerfile.fe | ✅ 已建立 | {基礎映像} |
| Dockerfile.be | deploy/Dockerfile.be | ✅ 已建立 | {基礎映像} |
| Docker Compose | {path} | ✅ 已建立 | {服務數量} |
| 環境變數範本 | {path} | ✅ 已建立 | {變數數量} |
| Nginx 配置 | {path} | ✅ 已建立 / N/A | {說明} |

## 3. 建構日誌摘要

### 前端建構
```
{建構過程的關鍵輸出}
```

### 後端建構
```
{建構過程的關鍵輸出}
```

## 4. 本地部署驗證

| 服務 | 端口 | 狀態 | 回應時間 |
|------|------|------|---------|
| 前端 | {port} | ✅ 運行中 / ❌ 失敗 | {ms} |
| 後端 | {port} | ✅ 運行中 / ❌ 失敗 | {ms} |
| 資料庫 | {port} | ✅ 運行中 / ❌ 失敗 | {ms} |

## 5. 健康檢查結果

| 端點 | 方法 | 預期狀態碼 | 實際狀態碼 | 結果 |
|------|------|---------|---------|------|
| /health | GET | 200 | {code} | ✅/❌ |
| /api/health | GET | 200 | {code} | ✅/❌ |

## 6. 未完成項目（若有）

| 標記 | 描述 | 所需資訊 |
|------|------|---------|
| [DEPLOY_LOCAL_ONLY] | 遠端部署需要額外資訊 | {缺少的資訊} |
| [PENDING_CONFIG] | 需要使用者提供環境變數 | {具體變數名} |
| [PENDING_DNS] | 需要 DNS 設定 | {域名} |

## 7. 追溯矩陣

| 部署項目 | 對應 CICD 規格 | 對應 Deploy 配置 |
|---------|--------------|----------------|
| CI/CD Pipeline | CICD-{TASK_ID} Stage 1-6 | deploy-config.md Section 1 |
| Container 建構 | CICD-{TASK_ID} Build Stage | deploy-config.md Section 2 |
| 環境配置 | CICD-{TASK_ID} Stage Stage | deploy-config.md Section 3 |
