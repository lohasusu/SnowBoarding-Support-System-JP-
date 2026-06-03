---
document_id: "COMP-{TASK_ID}-v1.0"
title: "元件規格"
version: "1.0"
date: "{YYYY-MM-DD}"
author: "UIUX"
status: "Draft"
task_id: "{TASK-ID}"
phase: "uiux"
source_documents:
  - "DS-{TASK_ID}-v1.0"
  - "WF-{TASK_ID}-v1.0"
change_history:
  - version: "1.0"
    date: "{YYYY-MM-DD}"
    changes: "初始版本"
    author: "UIUX"
approval:
  reviewer: "PM"
  date: ""
  result: "Pending"
  notes: ""
---

# 元件規格

## 1. 元件樹狀結構

```
App
├── Layout
│   ├── Header
│   │   ├── Logo
│   │   ├── Navigation
│   │   └── UserMenu
│   ├── Sidebar (optional)
│   ├── Content
│   └── Footer
├── Pages
│   ├── {PageName}
│   │   ├── {SectionComponent}
│   │   └── {SectionComponent}
│   └── ...
└── Shared
    ├── Button
    ├── Input
    ├── Modal
    └── ...
```

## 2. 全域佈局元件（MANDATORY — 所有頁面共用）

> **規則**: 以下佈局元件為全域單一實例，FE 必須實作為共用 Layout 元件。
> 所有頁面 import 同一個 Layout，僅替換 Content 區域。

### LAYOUT-001: AppLayout（應用佈局）
- **用途**: 全域頁面佈局容器，包含 Header + Sidebar + Content + Footer
- **所屬頁面**: **所有頁面**（全域共用）
- **實作要求**: FE 必須實作為單一 Layout 元件，所有頁面路由共用此元件

#### Props Interface
```typescript
interface AppLayoutProps {
  /** 當前頁面內容 */
  children: React.ReactNode;
  /** 當前活躍的導航項 ID（用於 Sidebar 高亮） */
  activeNavId?: string;
}
```

### LAYOUT-002: Sidebar（側邊導航）
- **用途**: 全域導航側邊欄，導航項目**固定不變**
- **所屬頁面**: **所有頁面**（全域共用）
- **實作要求**: 導航項目清單從統一配置讀取，不可逐頁硬編碼

#### Props Interface
```typescript
interface SidebarProps {
  /** 當前活躍的導航項 ID */
  activeNavId?: string;
}

/** 導航項目定義（全域唯一，對應 wireframes.md 第 2 章） */
interface NavItem {
  id: string;
  icon: React.ReactNode;
  label: string;
  path: string;
  permission?: 'public' | 'authenticated' | 'admin';
}
```

#### 導航項清單（與 wireframes.md 第 2 章完全一致）
| 順序 | NavItem.id | NavItem.label | NavItem.path | 對應 PAGE |
|------|-----------|---------------|-------------|----------|
| 1 | {id} | {標籤} | /{路由} | PAGE-001 |
| 2 | {id} | {標籤} | /{路由} | PAGE-002 |

> **一致性規則**: 此清單必須與 wireframes.md 第 2 章「Sidebar 導航項目」完全一致。
> 任何差異視為 🔴 Critical 缺陷。

### LAYOUT-003: Header（頂部導航）
- **用途**: 全域頂部欄，包含 Logo + 導航/麵包屑 + 使用者選單
- **所屬頁面**: **所有頁面**（全域共用）

### LAYOUT-004: Footer（頁腳）
- **用途**: 全域頁腳（若有）
- **所屬頁面**: **所有頁面**（全域共用）

---

## 3. 操作 Icon 對照表（MANDATORY — 遵循 sdlc-uiux.md Rule 3）

> **規則**: 所有 CRUD 列表頁的操作欄必須使用統一 icon，不可用 MoreVertical 下拉選單替代。

| 操作 | Icon | Icon 名稱（Lucide） | Icon 名稱（Material） | 用途 |
|------|------|-------|-------|------|
| 檢視 | 👁 | eye | visibility | 查看詳情 |
| 編輯 | ✏️ | pencil | edit | 編輯資料 |
| 刪除 | 🗑 | trash-2 | delete | 刪除資料 |
| 新增 | ➕ | plus | add | 新增項目 |
| 下載 | ⬇ | download | download | 下載檔案 |
| 搜尋 | 🔍 | search | search | 搜尋 |

> **一致性規則**: 同一操作在所有頁面必須使用相同 icon，不可同一功能在不同頁面用不同 icon。
> **權限選擇**: 權限等級選擇使用 Radio Button，不可用自定義元件替代。

## 4. 共用元件規格

### COMP-001: {元件名稱}
- **用途**: {描述}
- **所屬頁面**: PAGE-001, PAGE-002
- **對應功能**: FUNC-001

#### Props Interface

```typescript
interface {ComponentName}Props {
  /** {描述} */
  variant?: 'primary' | 'secondary' | 'outline' | 'ghost';
  /** {描述} */
  size?: 'sm' | 'md' | 'lg';
  /** {描述} */
  disabled?: boolean;
  /** {描述} */
  loading?: boolean;
  /** {描述} */
  onClick?: () => void;
  /** {描述} */
  children: React.ReactNode;
}
```

#### 變體（Variants）

| 變體 | 用途 | 視覺描述 |
|------|------|---------|
| primary | 主要操作 | 背景 color.primary.500, 文字 white |
| secondary | 次要操作 | 背景 color.secondary.500, 文字 white |
| outline | 輪廓按鈕 | 邊框 color.primary.500, 背景透明 |
| ghost | 幽靈按鈕 | 無邊框, 背景透明 |

#### 互動規範

| 狀態 | 視覺變化 | Token 引用 |
|------|---------|-----------|
| default | {描述} | - |
| hover | {描述} | color.primary.400, transition.default |
| focus | {描述} | outline: 2px solid color.primary.500 |
| active | {描述} | color.primary.600 |
| disabled | {描述} | opacity: 0.5, cursor: not-allowed |
| loading | {描述} | spinner + disabled 狀態 |

#### 無障礙規範

| 項目 | 規範 |
|------|------|
| Role | {ARIA role} |
| aria-label | {規則} |
| aria-disabled | 當 disabled=true 時設定 |
| Keyboard | Enter/Space 觸發 onClick |
| Focus | 可見的 focus ring |
| Screen reader | {描述} |

### COMP-002: {元件名稱}
{同上格式}

## 5. 共用 UI 模式

### PATTERN-001: Modal（模態對話框）

| 屬性 | 定義 |
|------|------|
| 用途 | 需要使用者回應的重要操作（新增/編輯表單、確認操作） |
| 觸發方式 | 按鈕點擊 / 系統事件 |
| 結構 | 遮罩層（overlay）+ 內容區（標題 + 內容 + 操作按鈕） |
| 關閉方式 | X 按鈕 / ESC 鍵 / 點擊遮罩（可配置） |
| 尺寸 | sm(400px) / md(560px) / lg(720px) / fullscreen |
| Token 引用 | shadow.xl, radius.lg, transition.enter, transition.exit |

#### Props Interface
```typescript
interface ModalProps {
  open: boolean;
  onClose: () => void;
  size?: 'sm' | 'md' | 'lg' | 'fullscreen';
  title?: string;
  closeOnOverlay?: boolean;
  closeOnEsc?: boolean;
  children: React.ReactNode;
}
```

### PATTERN-002: Confirm Dialog（確認對話框）

| 屬性 | 定義 |
|------|------|
| 用途 | 刪除/不可逆操作的二次確認 |
| 結構 | icon + 訊息文字 + 取消按鈕 + 確認按鈕 |
| 確認按鈕 | 刪除操作使用 color.error.500，其他使用 color.primary.500 |
| 取消按鈕 | outline variant |

#### Props Interface
```typescript
interface ConfirmDialogProps {
  open: boolean;
  onConfirm: () => void;
  onCancel: () => void;
  title: string;
  message: string;
  confirmLabel?: string;
  cancelLabel?: string;
  variant?: 'danger' | 'warning' | 'info';
  loading?: boolean;
}
```

### PATTERN-003: Toast / Notification（通知提示）

| 屬性 | 定義 |
|------|------|
| 用途 | 操作結果即時反饋（成功/失敗/警告/資訊） |
| 位置 | top-right（預設）/ top-center / bottom-center |
| 自動消失 | success: 3s / warning: 5s / error: 手動關閉 / info: 3s |
| 堆疊 | 最多 3 個同時顯示 |

#### Props Interface
```typescript
interface ToastProps {
  type: 'success' | 'warning' | 'error' | 'info';
  message: string;
  duration?: number;
  position?: 'top-right' | 'top-center' | 'bottom-center';
  closable?: boolean;
}
```

### PATTERN-004: Drawer（抽屜面板）

| 屬性 | 定義 |
|------|------|
| 用途 | 側邊詳情面板、篩選面板 |
| 方向 | right（預設）/ left / bottom |
| 寬度 | sm(320px) / md(480px) / lg(640px) |

#### Props Interface
```typescript
interface DrawerProps {
  open: boolean;
  onClose: () => void;
  placement?: 'left' | 'right' | 'bottom';
  size?: 'sm' | 'md' | 'lg';
  title?: string;
  children: React.ReactNode;
}
```

### PATTERN-005: Dropdown Menu（下拉選單）

| 屬性 | 定義 |
|------|------|
| 用途 | 操作選單、篩選選單 |
| 觸發方式 | 點擊 / hover（可配置） |
| 位置 | bottom-start（預設），自動避開邊界 |
| 鍵盤導航 | ↑↓ 切換選項，Enter 選取，Esc 關閉 |

#### Props Interface
```typescript
interface DropdownMenuProps {
  trigger: React.ReactNode;
  items: DropdownItem[];
  onSelect: (item: DropdownItem) => void;
  placement?: 'bottom-start' | 'bottom-end' | 'top-start' | 'top-end';
}
```

## 6. 頁面專用元件

### {PageName}/{ComponentName}
{同上格式，但標記為頁面專用}

## 7. 元件追溯矩陣

| 元件ID | 使用頁面 | 對應功能 |
|--------|---------|---------|
| COMP-001 | PAGE-001, PAGE-002 | FUNC-001 |
| COMP-002 | PAGE-001 | FUNC-002 |
