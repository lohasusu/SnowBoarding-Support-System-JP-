# Deploy Summary — scope=local

> Deploy(Execute) E-7.5 在產出檔案前呈現此摘要供使用者確認。
> `{變數}` 由 Execute 依 `deploy-env.json` 和掃描結果填入。

```
🟢 本地 only 模式 — 部署設計摘要

## 範圍
- 本次只產出本地開發所需檔案
- 不含 staging / prod 配置
- 不含 CI/CD deploy workflow（只含 lint + test + build）

## 將產出的部署檔案（共 5 個）
- docker-compose.yml
- deploy/Dockerfile.fe
- deploy/Dockerfile.be
- .env.example
- .github/workflows/ci.yml（最簡版）

## 資安檢查結果
- Critical {n_crit} / High {n_high} / Medium {n_med} / Low {n_low}
- 本地模式：Critical 仍阻塞（合規一致性），High 僅警告不阻塞

## 本地驗證計畫（E-9）
- docker compose build + up → curl health 檢查 → 清理

若需升級到 staging/prod，稍後可執行 /sdlc:revise deploy-init 改 scope。
```
