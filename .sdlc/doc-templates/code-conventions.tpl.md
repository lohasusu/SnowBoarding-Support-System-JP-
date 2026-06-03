---
document_id: "CODECON-CONVENTIONS-v1.0"
title: "程式碼慣例規範"
version: "1.0"
date: "{YYYY-MM-DD}"
author: "PM"
status: "Living Document (Layer 2 conventions/)"
phase: "conventions"
locked_at: "{ISO time set by /sdlc:init Step 4.15 — empty / placeholder = unlocked}"
change_history:
  - version: "1.0"
    date: "{YYYY-MM-DD}"
    changes: "init"
    author: "PM"
---

# 程式碼慣例規範（Layer 2 / conventions）

> **用途**: 跨 TASK 統一程式碼風格 — 檔名、識別符、目錄結構、註解、import 順序。
>
> **生效時機**: `/sdlc:init` 鎖定後 FE / BE 必遵守。違規由 lint + Tester 雙重攔截。
>
> **角色存取**: FE / BE 唯讀。

---

## 1. 檔名規範

### 1.1 前端（TS/TSX/JS/JSX/CSS/SCSS）

| 類型 | 命名 | 範例 |
|------|------|------|
| 元件 (PascalCase) | `{Name}.tsx` | `UserCard.tsx`, `LoginForm.tsx` |
| Hook | `use{Name}.ts` | `useAuth.ts`, `useFormState.ts` |
| 工具/服務 (camelCase) | `{name}.ts` | `apiClient.ts`, `dateUtils.ts` |
| 樣式 | `{Name}.module.css` 或 `{name}.scss` | `[CUSTOMIZE: CSS Modules / Tailwind / SCSS]` |
| 型別 | `{name}.types.ts` 或 `types/index.ts` | — |
| 測試 | `{Name}.test.tsx` | `UserCard.test.tsx` |

### 1.2 後端

`[CUSTOMIZE: 依語言選擇]`
- **Node.js / TypeScript**: camelCase 檔名 (`userService.ts`, `authMiddleware.ts`)
- **Python**: snake_case 檔名 (`user_service.py`, `auth_middleware.py`)
- **Go**: snake_case (`user_service.go`)
- **.NET (C#)**: PascalCase (`UserService.cs`)
- **Java**: PascalCase (`UserService.java`)

## 2. 識別符命名

| 類型 | 前端 (TS) | 後端 |
|------|-----------|------|
| 變數 / 函式 | `camelCase` | 依語言：camelCase / snake_case / PascalCase |
| 常數 | `UPPER_SNAKE_CASE` | `UPPER_SNAKE_CASE` |
| 類別 / 元件 | `PascalCase` | `PascalCase` |
| 型別 / 介面 | `PascalCase` | — |
| 私有成員 | `_xxx` 前綴（informal）或 `private` keyword | `_xxx` (Python) / `private` |
| 列舉 | `PascalCase` 鍵 | 同 |

### 動詞前綴（函式）
- 取資料: `get`, `fetch`, `load`, `find`, `select`
- 設值: `set`, `update`, `assign`
- 動作: `submit`, `send`, `post`, `dispatch`
- 判斷: `is`, `has`, `can`, `should`
- 轉換: `to`, `parse`, `format`, `convert`

## 3. 目錄結構

### 3.1 前端（推薦）

```
frontend/
├─ src/
│  ├─ pages/         # 路由級別頁面（對應 PAGE-NNN）
│  ├─ components/    # 可複用元件（對應 COMP-NNN）
│  │  ├─ common/    # 跨頁面共用
│  │  └─ {domain}/  # 領域元件（如 auth/, user/）
│  ├─ hooks/        # 自訂 hooks
│  ├─ services/     # API client 封裝
│  ├─ stores/       # 全域狀態（Redux/Zustand/...）
│  ├─ utils/        # 純函式工具
│  ├─ types/        # 型別定義
│  └─ styles/       # 全域樣式 / Design Tokens
├─ public/
└─ tests/           # E2E 測試
```

### 3.2 後端（推薦，分層架構）

```
backend/
├─ src/
│  ├─ controllers/  # HTTP handler / API endpoint
│  ├─ services/     # 業務邏輯
│  ├─ repositories/ # 資料存取
│  ├─ models/       # ORM 模型 / domain entities
│  ├─ middleware/   # 認證、日誌、錯誤處理
│  ├─ utils/        # 純函式工具
│  ├─ types/        # 型別 / interface
│  └─ config/       # 設定載入
├─ migrations/      # DB migrations（依 db-conventions §5）
└─ tests/
```

`[CUSTOMIZE: 框架慣例如 Next.js app router / Django apps / Spring Boot package layout]`

## 4. Import / Require 順序

```typescript
// 1. 第三方標準庫
import fs from 'fs';
import path from 'path';

// 2. 第三方套件
import express from 'express';
import { z } from 'zod';

// 3. 本專案 absolute imports（依 tsconfig paths）
import { logger } from '@/utils/logger';
import type { User } from '@/types';

// 4. 相對 imports（避免深層 ../../../，超過 2 層改 absolute）
import { sessionStore } from './session';
```

ESLint plugin: `import/order` 自動 enforce。

## 5. 註解規範

| 情境 | 寫不寫 | 範例 |
|------|--------|------|
| 解釋 WHAT（程式碼能說明的）| ❌ 不寫 | `// increment counter` 顯然多餘 |
| 解釋 WHY（隱藏約束、權衡）| ✅ 寫 | `// MUST run before line 45 — DB lock window` |
| Workaround / hack | ✅ 寫 | `// HACK: lib X bug, see issue #123` |
| TODO / FIXME | ⚠️ 限期 | `// TODO(2026-Q2): replace with X after upgrade` |
| 公開 API JSDoc | ✅ 寫 | `/** @param userId — must be > 0 */` |

`[CUSTOMIZE: TSDoc / JSDoc / 純註解，看專案 IDE / 文件生成需求]`

## 6. 錯誤處理

- **不允許靜默忽略**：`catch (e) {}` 必須附理由註解或記日誌
- **不允許 catch 後 throw 包裝成資訊更少的 Error**：保留原 stack
- **預期錯誤** vs **意外錯誤**：用不同型別區分（如 `BusinessError` vs `unexpected Error`）
- 統一使用 SD/error-codes.md 的錯誤碼

## 7. 禁止項彙整

- ❌ 同檔混合 PascalCase 元件 + camelCase 元件
- ❌ 變數縮寫 `usr` `prc` `cfg`（除了極短 scope 的 `i`/`j`/`k`）
- ❌ 一個檔超過 N 行 `[CUSTOMIZE: 預設 500]`
- ❌ 一個函式超過 N 行 `[CUSTOMIZE: 預設 80]`
- ❌ Magic numbers（除 0/1/-1）
- ❌ Console.log / print 留在生產 code（只在開發模式）

## 8. RFC 流程

同 db-conventions §7。
