---
document_id: "I18NCON-CONVENTIONS-v1.0"
title: "i18n 慣例規範"
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
| `[CUSTOMIZE: 主要語系]` | `[CUSTOMIZE: zh-TW \| en-US \| ja-JP \| ...]` | 預設 fallback 語系（BA 階段定義） |

**鎖定原則**：預設語系一旦在 `/sdlc:init` 寫入後，所有 PAGE-NNN 與 COMP-NNN 必須提供至少這一語系的字串。其他語系可漸進補上。

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

`[CUSTOMIZE: 框架支援？]`
- React i18next: `{ count: 1 }` 自動切 `_one`/`_other` 後綴
- Vue I18n: `@.linked` 語法

中文沒有複數變化，但若有英文版可能需要：
```
"cart.item_one"     "{{count}} item"
"cart.item_other"   "{{count}} items"
"cart.item"         "{{count}} 件商品"  (zh-TW)
```

## 5. 不同語系的特殊規則

### 5.1 中文（zh-TW / zh-CN）
- 標點：全形「，。：；！？」（不混用半形）
- 數字：阿拉伯數字 + 全形單位 `30 分鐘`
- 引號：「」與『』

### 5.2 英文（en-US）
- 句首大寫；按鈕用 sentence case 或 Title Case（全專案統一）`[CUSTOMIZE]`
- 縮寫展開或保持？`OK` vs `Okay` `[CUSTOMIZE]`
- 拼寫變體：US `color` vs UK `colour`，全專案統一 US `[CUSTOMIZE: US/UK]`

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
