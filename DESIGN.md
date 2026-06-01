# Japan Ski Trip Planner — 設計文件

> **本文件是開發的唯一參考基準。**
>
> ### 維護規則（強制）
> - 每次對話開始前必須先讀此文件
> - **任何功能新增、修改、刪除，無論大小，都必須在同次對話結束前更新此文件**
> - 更新範圍：功能說明、目前狀態、已知問題、目錄結構、下次從這裡開始
> - 違反此規則等於讓文件與程式碼脫節，後續維護成本倍增

---

## 一、專案目標

幫助使用者規劃日本滑雪行程，提供：
- **雪票查詢**：自動抓取各雪場早鳥票價，依雪季整理
- **機票查詢**：搜尋台灣出發、預算內的最便宜航班
- **整合查詢**：輸入日期 + 預算 + 地區，一次回傳機票 + 雪票的費用組合

**使用對象**：個人使用優先，架構預留擴充給社群使用。  
**輸出格式**：目前以 Excel 為主，未來擴充為網頁或其他介面。

---

## 二、目錄結構

```
D:\SideProject\
├── DESIGN.md                         ← 本文件（任何更動必須同步更新）
├── snowboarding_support\             ← 雪票模組（git repo 根目錄）
│   ├── urls.json
│   ├── ski_early_bird_scraper.py
│   ├── site_analyzer.py
│   ├── generate_review_excel.py       ← 未來合併進 site_analyzer.py
│   ├── test_analyzer.py
│   ├── analysis\
│   └── output\
└── flight_search\                    ← 機票模組
    ├── flight_search.py              ← CLI 入口
    ├── backends\
    │   ├── base.py                   ← FlightResult dataclass + BackendBase ABC
    │   ├── fast_flights_backend.py   ← Google Flights 主後端（無需 API Key）
    │   ├── mock_backend.py           ← 測試用假資料後端
    │   ├── amadeus_backend.py        ← Amadeus 備用（需 key）
    │   ├── serpapi_backend.py        ← SerpAPI 備用（需 key）
    │   └── travelpayouts_backend.py  ← Travelpayouts 備用（需 key）
    ├── output\                       ← Excel 輸出目錄（自動建立，不 commit）
    │   └── template\
    │       └── flight_search_template.xlsx  ← Excel 輸出範本格式
    ├── requirements.txt
    ├── .env                          ← 填入 API Key（不 commit）
    └── .env.example
```

未來整合時新增：
```
├── main.py                      ← 整合入口（第三階段才建）
└── shared\                      ← 共用工具（第三階段才建）
    └── config.py
```

---

## 三、雪票模組規格

### 3-1 兩支工具架構（已決策）

| 工具 | 腳本 | 執行頻率 | 說明 |
|------|------|---------|------|
| **月度分析** | `site_analyzer.py` | 每月一次 | 瀏覽各雪場網站，找正確票價頁 URL + selectors，輸出審查 Excel |
| **隨時執行爬蟲** | `ski_early_bird_scraper.py` | 隨時 | 只讀取已設定 ticket_url 的雪場做精準抓取，輸出票價 Excel |

> **通用模式（generic fallback）已決定移除**：掃描整頁找價格的方式噪音太大（實測長野地區抓出 108~313 筆不相關資料）。無 ticket_url 的雪場在爬蟲中直接跳過，標記「待設定」。

### 3-2 ski_early_bird_scraper.py 功能

| 功能 | 說明 |
|------|------|
| 全部掃描 | 爬取 urls.json 中所有已設定 ticket_url 的雪場 |
| 地區篩選 | `--region 長野`（北海道 / 長野 / 新潟 / 山形 / 青森 / 福島）|
| 名稱查詢 | `--name furano`（部分比對，大小寫不限）|
| 精準模式 | 有 ticket_url + selectors → 直接去該頁用 CSS selector 抓 |
| 無設定 | 無 ticket_url → 跳過，Excel 標「待設定」|
| 雪季判斷 | 依執行日期自動判斷（見 3-3）|

### 3-3 雪季自動判斷邏輯
```
執行月份 1–7 月  → 當前雪季 = (本年-1)/本年   例：2026-05 → 25/26
執行月份 8–12 月 → 當前雪季 = 本年/(本年+1)   例：2026-10 → 26/27
```

### 3-4 site_analyzer.py 設計規格（待實作）

**目標**：每月執行一次，真正「瀏覽」各雪場網站，產出高品質審查 Excel 供人工確認後更新 urls.json。

**瀏覽流程：**
```
1. 開首頁
   ↓
2. 擷取所有導覽連結（nav / header / footer）+ 內文連結
   ↓
3. 嚴格關鍵字評分（必須含「リフト / lift / 料金 / 早割」才算高分）
   不猜子路徑，只跟著頁面上真實存在的連結走
   ↓
4. 依序進入前 5 個候補頁面，每頁雙重確認：
   ① 頁面有日圓價格
   ② 同時含有纜車特定詞（リフト / lift ticket / 早割 / スキー場）
   → 兩個都過才算「找到票價頁」
   ↓
5. 在票價頁擷取結構化樣本，區分票種類別：
   早割 / 前売 / 当日 / 半日 / シーズン
   ↓
6. 建議 CSS selectors（table / dl / card）
   ↓
7. 輸出審查 Excel（不自動更新 urls.json，由人工確認後更新）
```

**Excel 欄位設計（可點擊連結版）：**

| 欄位 | 說明 |
|------|------|
| 地區 | 色碼區分（北海道 / 長野 / 新潟 / 山形 / 青森 / 福島）|
| 雪場名稱 | |
| 首頁 URL | 可點擊超連結 |
| 票價頁面 URL | 可點擊超連結，高亮顯示 |
| 找到票種類別 | 例：`早割 / 当日 / 半日` |
| 早割票價樣本 | 實際抓到的文字 |
| 一般票票價樣本 | |
| 建議 selector type | table / dl / card |
| 建議 container | CSS selector 字串 |
| 信心程度 | 高 / 中 / 低（綠 / 黃 / 紅）|
| 狀態 | ✅ 找到 / ⚠️ 未確認 / ❌ 錯誤（色碼）|
| 截圖路徑 | 可點擊開啟檔案 |
| 備註欄 | 人工填寫用（原有功能保留）|

**實作重點：**
- `generate_review_excel.py` 功能合併進來，不再需要兩支腳本
- 不猜子路徑（移除 CANDIDATE_PATHS 猜測機制）
- 使用更長等待時間（等 JS 渲染）
- 並行數預設 2（避免被網站封鎖）

### 3-5 urls.json 欄位規格
```json
{
  "name": "Furano",
  "url": "https://www.princehotels.co.jp/ski/furano",
  "note": "北海道 Hokkaido",
  "ticket_url": "https://...",
  "selectors": {
    "container": "table.price-table",
    "type": "table"
  }
}
```

### 3-6 目前進度（截至 2026-05-22）

**urls.json 狀態（共 40 個雪場，Tomamu 已移除）：**
- ✅ 13 個雪場：ticket_url + selectors 已設定（精準模式可用）
- 🔗 1 個雪場：ticket_url 已設定，無 selectors（Furano → webket.jp）
- ⚠️ 23 個雪場：尚無 ticket_url（待人工審查 Excel 填完後更新）
- ❌ 3 個雪場：SSL/DNS 問題（Niseko Moiwa、Sahoro、Alts Bandai）
- 人工審查 Excel 進行中：`output/RESORT_REVIEW_20260516_1750.xlsx`

**ski_early_bird_scraper.py 狀態：**
- ✅ 雪季自動判斷已實作
- ✅ --region / --name CLI 篩選已實作
- ✅ UTF-8 stdout encoding 已修正
- ✅ 移除通用模式（generic fallback）— 無 ticket_url 直接略過，輸出至「略過雪場」sheet
- ✅ 新增 `get_ticket_prices(region, name)` 公開 API
- ✅ 建立 `__init__.py` + `scraper.py`，`snowboarding_support` 成為可 import 套件
- ✅ Excel 格式全面重設計：地區色碼 / 票種分類（早鳥/現場）/ 可點擊 URL / 凍結列 / 自動篩選
- ✅ Excel 格式範例：`examples/SAMPLE_FORMAT.xlsx`（長野地區，146 筆）

**實際執行結果（2026-05-22）：**
- 全部 40 雪場：268 筆票價，27 個雪場略過
- 長野篩選：146 筆票價，9 個雪場略過

**site_analyzer.py 狀態：**
- ⏳ 重構計畫已設計完成 → **下次對話待實作**

---

## 四、機票模組規格

### 4-1 核心功能
| 功能 | 說明 |
|------|------|
| 出發地 | 限台灣（TPE / TSA / KHH / RMQ） |
| 目的地 | 日本各機場，或指定地區（北海道 → CTS） |
| 搜尋條件 | 出發日期、人數、幣別、預算上限 |
| 輸出 | 依價格排序，顯示航班資訊 + 總費用 |
| 獨立使用 | 不依賴雪票模組，可單獨執行 |

### 4-2 目前狀態
- ✅ **機票模組完成並實測通過**（2026-05-22）
- 主後端：**Google Flights (fast-flights)**，Protobuf 逆向爬蟲，無需 API Key
- 選用後端：SerpAPI、Travelpayouts（設定 .env 後自動啟用）
- 測試模式：`python flight_search.py --mock`（假資料，不需要任何 Key）
- 支援去回程搜尋（Enter 略過即為單程）
- 搜尋結果輸出至 `flight_search/output/flights_YYYYMMDD_HHMM.xlsx`
- **每日用量追蹤**：記錄在 `output/daily_usage.json`，超過 50 次印警告（Google IP 限速防護）
- Windows UTF-8 編碼已修正

### 4-3 機票 API 選項

| API | 免費額度 | 狀態 | 備註 |
|-----|---------|------|------|
| **SerpAPI (Google Flights)** ⭐ | 100次/月免費 | **使用中（待 key）** | 即時資料，結果準確 |
| **Travelpayouts (Aviasales)** ⭐ | 免費（affiliate 模式） | **使用中（待 key）** | 快取歷史票價，台日航線佳 |
| Amadeus for Developers | 測試環境免費（模擬資料） | ❌ 已放棄（免費方案已停）| — |
| Kiwi Tequila API | 無免費額度 | 🔲 備選 | RapidAPI 計費 |
| Duffel API | 免費（沙盒環境） | 🔲 備選 | 適合未來做訂票功能 |

> **現況**：程式碼已完成雙 API 架構，兩個 key 申請中。任一 key 填入 `.env` 即可啟動對應 backend。

---

## 五、整合查詢規格（Smart Trip Planner）

> 定位：從「查完機票再查雪票再自己心算」，升級為「輸入三個數字，系統幫你找最划算的組合並導向訂票」。

### 5-1 Web 版 Smart Trip Planner（主要實作目標）

**路由：** `/plan`（新頁面）

**輸入表單欄位：**

| 欄位 | 說明 |
|------|------|
| 出發機場 | TPE / TSA / KHH / RMQ（下拉選單） |
| 滑雪地區 | 北海道 / 長野 / 新潟 / 山形 / 青森 / 福島 |
| 出發日期 | 使用新日曆選擇器（見 9-1） |
| 回程日期 | 使用新日曆選擇器（範圍模式，min = 出發日） |
| 人數 | 1–9 人 |
| 每人總預算（TWD） | 數字 input + 快捷按鈕（3萬 / 5萬 / 8萬） |

**後端處理邏輯：**
```
POST /api/plan/search
  ↓
asyncio.gather(
  flight_search(origin, dest_airport[region], departure, return_date),
  ski_ticket_fetch(region)
)
  ↓
ski_days      = return_date - departure（天數）
min_ski_price = min(早鳥票價) per person per day
est_ski_total = ski_days × min_ski_price × adults
budget_left   = budget_per_person × adults - est_ski_total
affordable_flights = [f for f in flights if f.price ≤ budget_left]
  ↓
回傳 { flights, ski_tickets, summary }
```

**API 規格：**
```json
POST /api/plan/search
{
  "origin": "TPE",
  "region": "北海道",
  "departure": "2026-12-20",
  "return_date": "2026-12-27",
  "adults": 2,
  "budget_per_person": 50000
}

Response: {
  "ok": true,
  "flights": [...],
  "ski_tickets": [...],
  "summary": {
    "ski_days": 7,
    "min_ski_price_per_day": 4500,
    "est_ski_total": 63000,
    "budget_for_flights": 37000,
    "affordable_flights": 3
  }
}
```

**結果版面設計：**

```
┌─ 預算分配（橫向 progress bar）──────────────────────────────────┐
│ [██████████████░░░░░░░░░░░░░░░░░░░]                           │
│  機票 NT$18,000  ＋  雪票 NT$31,500  ＋  剩餘 NT$500  / 人    │
└──────────────────────────────────────────────────────────────┘

左欄：機票選項（卡片式）          右欄：雪票選項
┌──────────────────────┐          ┌──────────────────────┐
│ ✈ 長榮航空 BR116     │          │ 🎿 富良野滑雪場      │
│ 08:30 → 12:45 (3h15) │          │  早鳥全日 ¥4,500     │
│ 直飛  NT$8,900        │          │  [前往購票 ↗]       │
│ [前往訂票 ↗]         │          ├──────────────────────┤
└──────────────────────┘          │ 🎿 留壽都滑雪場      │
┌──────────────────────┐          │  早鳥全日 ¥5,200     │
│ ✈ 中華航空 CI...     │          │  [前往購票 ↗]       │
│ ...                  │          └──────────────────────┘
└──────────────────────┘
```

### 5-2 訂票深連結規格

> 設計原則：Phase 1 只做深連結（引導官方/合作購票頁），不做 in-app 訂購。

| 類型 | 連結目標 | 說明 |
|------|---------|------|
| 雪票 | `ticket_url`（urls.json 欄位） | 連至官方購票頁，`target="_blank"` |
| 機票 | Google Flights 深連結 | 帶入 origin/dest/date 參數，新分頁 |
| 未來住宿 | Booking.com 搜尋深連結 | 帶入地區/日期/人數，新分頁 |

**Google Flights 深連結格式：**
```
https://www.google.com/travel/flights?q=Flights+from+{origin}+to+{dest}+on+{date}
```

**Booking.com 深連結格式（未來）：**
```
https://www.booking.com/searchresults.html?ss={地區}&checkin={departure}&checkout={return_date}&group_adults={adults}
```

**為何不做真實 in-app 訂購：**
- 各雪場使用不同票務系統（Webket、e+、自建），無統一 API
- 機票 GDS 整合成本極高且需要商業認證
- 深連結已能滿足 80% 使用需求，使用者習慣在官網確認後再購
- 先做深連結驗證流量，後續再評估是否接 Travelpayouts affiliate 或 Duffel API

### 5-3 導覽更新（實作時同步修改）
- Navbar 的「整合查詢」：disabled span → `<a href="/plan">` 可點擊連結
- 首頁功能卡片第三格：解鎖，按鈕改為「開始規劃」連至 `/plan`
- 首頁「如何使用」步驟：可調整為以 /plan 為主流程介紹

### 5-4 CLI 整合（保留，低優先度）
```
python main.py plan \
  --origin TPE --region 北海道 \
  --departure 2026-12-20 --return 2026-12-27 \
  --adults 2 --budget 50000

→ 輸出 Excel：
  Sheet 1: 機票選項（依價格排序）
  Sheet 2: 雪場票價（指定地區）
  Sheet 3: 費用摘要（機票 + 雪票 組合試算）
```

### 5-5 Python 模組介面
```python
from snowboarding_support.scraper import get_ticket_prices
from flight_search.search import find_flights
from main import plan_trip

plan_trip(origin="TPE", region="北海道",
          departure="2026-12-20", return_date="2026-12-27",
          adults=2, budget_per_person=50000)
```

---

## 六、開發優先順序

| 階段 | 工作項目 | 狀態 |
|------|---------|------|
| **Phase 1** | 審查 Excel，補齊雪場 ticket_url | ⏳ 進行中（Excel 繼續填寫中）|
| **Phase 1** | 精準模式驗證 | ✅ 完成（13 個雪場已設定 selectors）|
| **Phase 1** | 雪季自動判斷 | ✅ 完成（1–7月→上季，8–12月→當季）|
| **Phase 1** | 地區/名稱篩選介面 | ✅ 完成（--region / --name）|
| **Phase 1** | 移除爬蟲通用模式 | ✅ 完成（略過無設定雪場，Excel 新增略過 sheet）|
| **Phase 1** | 公開 API + 套件化 | ✅ 完成（`get_ticket_prices()`、`__init__.py`、`scraper.py`）|
| **Phase 1** | Excel 格式重設計 | ✅ 完成（地區色碼 / 票種分類 / 可點擊 URL / 範例檔）|
| **Phase 1** | 重構 site_analyzer.py | ⏳ **← 雪票下一步**（設計完成，待實作）|
| **Phase 2** | 建立雙 API 架構 | ✅ 完成（backends/ 套件）|
| **Phase 2** | 機票 Excel 輸出 | ✅ 完成（待實測驗證）|
| **Phase 2** | 機票模組實測 | ✅ 完成（fast-flights，無需 API Key）|
| **Phase 3a** | 自訂日曆選擇器（Calendar Picker） | 🔲 規格見 9-1 |
| **Phase 3a** | Smart Trip Planner（/plan 頁） | 🔲 規格見第五節 |
| **Phase 3a** | 訂票深連結（雪票 + 機票） | 🔲 規格見 5-2 |
| **Phase 3a** | Navbar 整合查詢解鎖 + 首頁卡片更新 | 🔲 |
| **Phase 3b** | 模組重構為可 import 套件 | 🔲 |
| **Phase 3b** | 建立 main.py 整合入口（CLI） | 🔲 |
| **Phase 3b** | 行動版雪票卡片佈局 | 🔲 規格見 9-3 |
| **Phase 4** | Travelpayouts affiliate 連結 | 🔲 有 key 後啟用 |
| **Phase 4** | 住宿查詢（Booking.com 深連結） | 🔲 |
| **Phase 4** | 機票價格趨勢 / 歷史資料 | 🔲 |

---

## 七、已知問題與限制

| 項目 | 說明 |
|------|------|
| GALA Yuzawa | 票價頁 JS 動態載入，等待時間不足 |
| Kiroro | 自動找到的是教練課程頁，非票價頁 |
| Niseko Moiwa / Sahoro / Alts Bandai | SSL/DNS 錯誤，需確認網站狀態 |
| 白馬五龍 / Happo One / 志賀高原 等 | 首頁無票價，尚未找到正確子頁面 |
| Karuizawa Prince | 精準模式 0 筆，selector `table.tbl-base` 可能需確認 |
| SerpAPI 去回程 | 第一次 call 只拿去程班次＋合計總價；回程班次詳情需第二次 call（Phase 2 暫不實作）|
| Travelpayouts 資料 | 快取歷史票價，無精確抵達時間與飛行時間 |

---

## 八、下次對話從這裡開始

### 雪票模組：一件事待實作

**重構 site_analyzer.py（月度分析工具）**
- 規格詳見本文件 3-4 節
- 核心改動：用真實導覽連結取代猜子路徑；嚴格雙重確認是否為纜車票頁；區分早鳥/一般票種；Excel 格式全新設計
- `generate_review_excel.py` 功能合併進來

### 雪票模組：持續進行
- 人工審查 Excel（`output/RESORT_REVIEW_20260516_1750.xlsx`）填完後，更新 urls.json 補齊剩餘 23 個雪場的 ticket_url + selectors

### 機票模組：✅ 已完成
```powershell
cd D:\SideProject\flight_search
python flight_search.py          # 真實 Google Flights 資料
python flight_search.py --mock   # 假資料測試
```

### Web UI 優化（新增，Phase 3a）
優先順序：
1. **自訂日曆選擇器**（見 9-1）— 影響現有 flight.html + 未來 plan.html，先做
2. **Smart Trip Planner /plan 頁**（見第五節）— 核心新功能
3. **Navbar + 首頁卡片解鎖** — 小改動，搭配 /plan 完成後一起做

---

## 九、UI/UX 設計規格

### 9-1 自訂日曆選擇器（Calendar Picker）

#### 問題
原生 `<input type="date">` 在各瀏覽器顯示不一致（Chrome 顯示的下拉視窗尤其混亂），與 Bootstrap 設計語言格格不入。

#### 設計目標
- 純 JS + Bootstrap CSS，不引入額外 library（保持零依賴）
- 單月視圖，整潔格線佈局，只顯示當月日期
- 在 input field 下方浮動展開，點外側 / Escape 關閉
- 同一元件支援兩種模式：單選（雪票日期）、範圍選取（機票去回程）

#### 視覺規格
```
┌──────────────────────────────────┐
│  ◀       2026 年 12 月      ▶    │
│  一   二   三   四   五   六   日 │
│                  1    2    3    4 │
│  5    6    7    8    9   10   11  │
│  12  13   14   15   16   17   18  │
│  19  20   21   22   23   24   25  │
│  26  27   28   29   30   31       │
└──────────────────────────────────┘
```

#### 日期狀態樣式（CSS class 設計）

| 狀態 | Class | 外觀 |
|------|-------|------|
| 普通日期 | `.cal-day` | 透明背景，hover 時 `bg-primary bg-opacity-10` |
| 今天 | `.cal-day.today` | `border border-primary` 圓形框 |
| 已選（單一） | `.cal-day.selected` | `bg-primary text-white` 實心圓 |
| 範圍起點 | `.cal-day.range-start` | 實心圓 + 右半側 `bg-primary bg-opacity-15` |
| 範圍終點 | `.cal-day.range-end` | 實心圓 + 左半側 `bg-primary bg-opacity-15` |
| 範圍內 | `.cal-day.in-range` | `bg-primary bg-opacity-15` 矩形背景 |
| 已過日期 | `.cal-day.disabled` | `text-muted opacity-50`，pointer-events: none |
| 其他月空格 | — | 空白，不顯示數字 |

#### 互動行為
- 點 input field → 展開日曆 panel
- **單選模式**：點日期 → 更新 input value → 關閉 panel
- **範圍模式**：第一次點 = 起點，滑鼠移動時顯示 hover 範圍預覽；第二次點 = 終點 → 更新兩個 input value → 關閉 panel
- 點 ◀ / ▶ → 切換月份（panel 不關閉）
- 點 panel 外側 / 按 Escape → 關閉 panel
- input 顯示格式：`YYYY-MM-DD`（與後端 API 一致）

#### 適用頁面
| 頁面 | 欄位 | 模式 |
|------|------|------|
| `flight.html` | 出發日期、回程日期 | 各自獨立單選（回程 min = 出發日） |
| `plan.html`（新） | 出發 + 回程 | 範圍選取模式（一個日曆控制兩個欄位） |

#### 實作位置
- **JS**：`web/static/js/calendar-picker.js`（共用元件，export `CalendarPicker` class）
- **CSS**：`web/static/css/custom.css` 的 `.calendar-picker { }` 區塊
- **引入**：`base.html` `<head>` 內全局載入，或各頁 `extra_scripts` block 引入

#### CalendarPicker API 草稿
```javascript
// 單選模式
new CalendarPicker('#departure', { mode: 'single', min: today });

// 範圍模式（兩個 input 共用一個日曆）
new CalendarPicker('#departure', {
  mode: 'range',
  rangeEndInput: '#ret-date',
  min: today
});
```

---

### 9-2 雪票查詢頁優化

#### 行動版卡片佈局（sm 以下）
目前 ski.html 結果用 `<table>`，在手機上需橫向捲動。改為：
- `≥ md`：保留現有 table layout
- `< md`：改為 Bootstrap card 堆疊，每張卡片顯示：雪場名稱（大）+ 地區 badge + 票種 + 票價（大紅字）+ 官網連結

#### 「前往購票」按鈕
在結果表格的「官網」欄，現有外連按鈕（`bi-box-arrow-up-right`）改為：
- 若 `source_url` 存在且為 ticket_url（非首頁）：按鈕文字改為「前往購票」，樣式 `btn-outline-success`
- 若為首頁 URL：維持「官網」標示，`btn-outline-secondary`

---

### 9-3 其他 UI 優化（低優先度，排 Phase 3b 後）

| 項目 | 說明 | 影響範圍 |
|------|------|---------|
| Skeleton loading | 查詢中用骨架屏取代純 spinner，減少白屏感 | ski.html、flight.html、plan.html |
| 預算滑桿 | 機票查詢加入最高票價滑桿，即時過濾結果 | flight.html |
| Toast 通知 | 錯誤訊息改用 Bootstrap Toast，不蓋住結果 | 所有查詢頁 |
| 深色模式 | Bootstrap `data-bs-theme="dark"` toggle，存 localStorage | base.html |
| 雪場計數更新 | 首頁「40+」改為從 urls.json 動態讀取實際數量 | index.html + main.py |

---

*最後更新：2026-05-27*
