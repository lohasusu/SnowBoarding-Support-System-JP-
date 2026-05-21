# Japan Ski Resort Ticket Price Scraper

自動爬取日本各大雪場官網的票種與票價，輸出至格式化 Excel，支援作為 Python 套件獨立呼叫。

## 功能

- **精準爬取**：依 `urls.json` 設定的 CSS selector 直接抓取票價頁，不做通用掃描
- **票種分類**：自動分為「早鳥」與「現場」兩類
- **Excel 輸出**：地區色碼、可點擊超連結、自動篩選；略過的雪場記錄於第二張 Sheet
- **可 import 使用**：透過 `get_ticket_prices()` API 供外部模組整合

## 雪場清單

`urls.json` 收錄 40 個日本雪場，涵蓋：

| 地區 | 雪場數 | 已設定精準模式 |
|------|--------|---------------|
| 北海道 Hokkaido | 10 | 2 |
| 長野 Nagano | 16 | 7 |
| 新潟 Niigata | 8 | 4 |
| 山形 Yamagata | 1 | 0 |
| 青森 Aomori | 1 | 0 |
| 福島 Fukushima | 3 | 1 |

## 目錄結構

```
snowboarding_support/
├── __init__.py                  # 套件入口，export get_ticket_prices
├── scraper.py                   # 公開 API 薄包裝
├── ski_early_bird_scraper.py    # 主爬蟲（CLI + 核心邏輯）
├── site_analyzer.py             # 月度網站結構分析工具（待重構）
├── generate_review_excel.py     # 從分析報告產生人工審查 Excel
├── urls.json                    # 雪場清單（含票價頁 URL 與選擇器）
├── examples/
│   └── SAMPLE_FORMAT.xlsx       # Excel 輸出格式範例（長野地區）
├── analysis/                    # site_analyzer.py 產出
│   ├── analysis_report.json
│   └── urls_analyzed.json
└── output/                      # 爬蟲產出（gitignored）
    └── SNOWBOARD_TICKETS_YYYYMMDD_NNN.xlsx
```

## 安裝

```bash
pip install -r requirements.txt
playwright install chromium
```

## 使用方式

### CLI 爬取票價

```bash
python ski_early_bird_scraper.py              # 全部雪場
python ski_early_bird_scraper.py -r 長野      # 依地區篩選
python ski_early_bird_scraper.py -n furano    # 依名稱篩選（部分比對）
```

產出：`output/SNOWBOARD_TICKETS_YYYYMMDD_NNN.xlsx`（兩張 Sheet）

### 作為套件 import

```python
from snowboarding_support.scraper import get_ticket_prices, TicketItem

# 回傳 list[TicketItem]，不輸出 Excel
prices = get_ticket_prices(region="北海道")
prices = get_ticket_prices(name="furano")
prices = get_ticket_prices()  # 全部已設定雪場
```

### Excel 輸出格式

| 欄位 | 說明 |
|------|------|
| 地區 | 色碼區分：北海道藍 / 長野綠 / 新潟黃 / 山形紫 / 青森橘 / 福島紅 |
| 雪場名稱 | 每個雪場第一筆加粗 |
| 票種分類 | **早鳥**（淺綠）/ **現場**（淺黃） |
| 票種（日文）| 原始票種名稱 |
| 票種（中文）| 自動翻譯 |
| 票價 | |
| 雪季 | 自動判斷（1–7 月→上季，8–12 月→當季）|
| 票價頁面 | 可直接點擊開啟瀏覽器 |

格式範例：`examples/SAMPLE_FORMAT.xlsx`

## urls.json 欄位說明

| 欄位 | 必填 | 說明 |
|------|------|------|
| `name` | ✅ | 雪場名稱 |
| `url` | ✅ | 官網首頁 |
| `note` | — | 地區備註（用於地區篩選） |
| `ticket_url` | — | 票價頁面 URL（必填才會爬取） |
| `selectors` | — | CSS 選擇器（`container`、`type`、`row`）|

無 `ticket_url` 的雪場會被略過，記錄至 Excel「略過雪場」sheet。
