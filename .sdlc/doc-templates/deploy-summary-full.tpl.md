# Deploy Summary — scope=full

> Deploy(Execute) E-7.5 在產出檔案前呈現此摘要供使用者確認。
> `{變數}` 由 Execute 依 `deploy-env.json` 和掃描結果填入。

```
🔴 本地 + Staging + Prod（完整）模式 — 部署設計摘要

## 基礎設施（來自 Init，不可更改）
- 部署平台 / CI/CD 平台 / 環境（dev/staging/prod）

## CI/CD Pipeline（最終版 — Path-based）
- 階段 / 觸發條件 / Path filter 摘要
- Prod deploy 含 environment: production（required reviewers 審批）

## 將產出的部署檔案（共 15+ 個）
{列出所有檔案路徑}

## ⚠️ Stub 檔案（需手動補齊）
- deploy/FULL-REQUIRED.md — 列出 K8s manifests / Serverless / alerts / backup / DNS / TLS / prod reviewers 等需手動完成的項目
  （見 doc-templates/full-required.tpl.md）

## Env Var 一致性
- 一致 {n_ok} 個 / 不一致 {n_diff} 個

## 資安檢查結果
- Critical {n_crit} / High {n_high} / Medium {n_med} / Low {n_low}
- full 模式：Critical + High 皆阻塞部署

## Prod Approval
- GitHub Environment: production
- Required reviewers: {list 或「需手動設」}

## 後續發布流程
- test phase 通過後，執行 /sdlc:release {TASK-ID} 觸發 prod 發布
```
