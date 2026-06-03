---
document_id: "I18NCON-CONVENTIONS-v1.1"
title: "i18n 慣例規範"
version: "1.1"
date: "2026-06-03"
author: "PM"
status: "Living Document (Layer 2 conventions/)"
phase: "conventions"
locked_at: "2026-06-03T09:30:00Z"
change_history:
  - version: "1.0"
    date: "2026-06-03"
    changes: "init: 從模板 cp + lock"
    author: "PM"
  - version: "1.1"
    date: "2026-06-03"
    changes: "init customization pass — 預設語系=zh-TW / i18n key 規範暫不啟用（brownfield Jinja2 階段）/ Vue 重構時啟用"
    author: "PM"
---

# i18n 慣例規範（Layer 2 / conventions）

> **用途**: 跨 TASK 統一 i18n 字串管理 — Key 格式、namespace、變數插值、預設語系。
>
> **生效時機**: `/sdlc:init` 鎖定後 UIUX/SD/FE 必遵守。違規由 Tester 攔截 + Rule 14 i18n_key_added 來源驗證。
>
> **角色存取**: UIUX 寫入（Pencil 文字框 → i18n key）/ SD 引用 / FE 唯讀（直接從 i18n 字典取值，不可硬編碼字串）。

---

## 1. 預設語系

| 語系 | 代碼 | 用途 |
|------|------|------|
| **繁體中文** | `zh-TW` | 預設 fallback 語系（唯一支援語系，目標客群為日本雪場資訊的繁中讀者） |

**鎖定原則**：預設語系一旦在 `/sdlc:init` 寫入後，所有 PAGE-NNN 與 COMP-NNN 必須提供至少這一語系的字串。其他語系可漸進補上。

> **本專案目前狀態（brownfield）**: i18n key 機制**暫不啟用**。Jinja2 模板與 FastAPI `HTTPException(detail="...")` 都使用硬編碼中文字串。**啟用時機**: TASK-N 把前端轉 Vue 時，§2-§7 規則生效；屆時前端字串集中到 i18n 字典 + key 註冊到 `shared/i18n-registry.md`。

## 2. Key 格式

統一格式：`{namespace}.{domain}.{name}`

| 段 | 值 | 範例 |
|----|------|------|
| `namespace` | 字串範圍：`common` / `page-{slug}` / `comp-{slug}` / `error` / `validation` | `common`, `page-login`, `comp-modal`, `error`, `validation` |
| `domain` | 字串分類：`button` / `label` / `placeholder` / `tooltip` / `title` / `message` / `error` | `button`, `label`, `tooltip` |
| `name` | 具體名稱 kebab-case 或 camelCase | `submit`, `cancel`, `email-required` |

### 範例

```
common.button.submit              "送出"
common.button.cancel              "取消"
common.label.email                "電子郵件"
page-login.title                  "登入"
page-login.placeholder.email      "請輸入電子郵件"
comp-modal.button.confirm         "確認"
error.network                     "網路連線失敗"
validation.email-required         "電子郵件必填"
validation.password-min-length    "密碼至少 {minLength} 個字元"
```

## 3. 變數插值

統一使用 **named** 插值，不用 positional：

```js
// ✅ 正確
t('validation.password-min-length', { minLength: 8 });

// ❌ 禁止
t('validation.password-min-length', [8]);
t('validation.password-min-length').replace('{0}', '8');
```

### 變數命名
- camelCase
- 語意明確（`userName` 不是 `name1`）
- 數字相關用 `count`, `amount`, `quantity`

```
"common.greeting"          "您好，{userName}！"
"common.cart.summary"      "購物車中有 {itemCount} 件商品"
```

## 4. 複數規則（Pluralization）

**本專案：N/A（單一 zh-TW 語系，無複數變化）**

未來若新增英文版：採 **Vue I18n** 內建複數機制（Vue 重構後同步引入）。中文用 `{count} 件商品` 即可，無分支。

```
"cart.item"         "{{count}} 件商品"  (zh-TW)
"cart.item_one"     "{{count}} item"   (en-US 未來)
"cart.item_other"   "{{count}} items"  (en-US 未來)
```

## 5. 不同語系的特殊規則

### 5.1 中文（zh-TW / zh-CN）
- 標點：全形「，。：；！？」（不混用半形）
- 數字：阿拉伯數字 + 全形單位 `30 分鐘`
- 引號：「」與『』

### 5.2 英文（en-US）

**本專案 N/A** — 目前無英文版，下列規則為未來啟用時的預設值：
- 按鈕：**sentence case**（如 `Submit`, `Cancel`，非 `SUBMIT`）
- 縮寫保持簡寫：`OK`（非 `Okay`）
- 拼寫採 **US 英文**：`color` / `behavior` / `analyze`（非 UK `colour` / `behaviour` / `analyse`）

## 6. Key 註冊與來源（與 Rule 14 整合）

新 i18n key 引入時走 journal：

```bash
bash $HOME/.claude/skills/sdlc/scripts/sdlc-journal-write.sh \
  TASK-002 i18n_key_added uiux \
  '{"key":"page-login.title","defaultText":"登入","compId":"COMP-005"}'
```

`compId`：綁定的 COMP-NNN，FE 實作時可從 component-spec.md 反查使用點。

PM 在 next.md Step 2.45.1 萃取，Step 2.45.2 rebuild 後出現於 `shared/i18n-registry.md`。

## 7. 禁止項彙整

- ❌ FE 原始碼硬編碼字串：`<button>送出</button>`（必須 `t('common.button.submit')`）
- ❌ Key 用 PascalCase / snake_case（混亂）
- ❌ Positional 插值（`{0}`, `{1}`）
- ❌ 跨 namespace 重複定義同一文字（如 `page-login.button.submit` 與 `page-register.button.submit` 都是「送出」→ 應提到 `common.button.submit`）
- ❌ 在 i18n 字典中放 HTML（除非框架明確支援 `dangerouslyUseHTMLString` + sanitization）
- ❌ Key 名稱含空白 / 中文 / 特殊字元

## 8. RFC 流程

同 db-conventions §7。
