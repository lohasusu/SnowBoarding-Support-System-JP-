# Deploy Summary — scope=local-staging

> Deploy(Execute) E-7.5 在產出檔案前呈現此摘要供使用者確認。
> `{變數}` 由 Execute 依 `deploy-env.json` 和掃描結果填入。

```
🟡 本地 + Staging 模式 — 部署設計摘要

## 基礎設施（來自 Init，不可更改）
- 部署平台: {platform}
- CI/CD 平台: {cicd}
- 環境: dev + staging

## CI/CD Pipeline
- 階段 / 觸發條件 / Path filter 摘要

## 將產出的部署檔案（共 8~10 個）
{列出所有檔案路徑}

## ⚠️ Stub 檔案（需手動補齊）
- deploy/STAGING-REQUIRED.md — 列出需手動完成的項目
  （見 doc-templates/staging-required.tpl.md）

## Env Var 一致性
- 一致 {n_ok} 個 / 不一致 {n_diff} 個

## 資安檢查結果
- Critical {n_crit} / High {n_high} / Medium {n_med} / Low {n_low}
- staging 模式：Critical + High 皆阻塞部署
```
