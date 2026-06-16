# SnowTrip Desktop — 雪票 + 機票爬蟲桌面版

把線上版 SnowTrip Japan 的「雪票查詢」「機票查詢」核心爬蟲打包成 Windows 單檔 .exe，含：

- 🖥 **GUI**：tkinter 介面，輸入參數與網站完全一致
- 🕒 **排程**：透過 Windows 工作排程器（schtasks）— **關閉應用後仍會準時跑**
- 📊 **Excel 輸出**：自動輸出時間戳 .xlsx 到使用者選的資料夾
- 📦 **零依賴**：使用者拿 .exe 即可執行，不需安裝 Python

## 給使用者

### 安裝
1. 下載 `snowtrip_desktop.exe`
2. 雙擊執行 — 第一次會在 `%APPDATA%\SnowTripDesktop\config.json` 建立預設設定
3. 預設輸出資料夾：`%USERPROFILE%\SnowTrip_Output\`

### 使用
- **⛷ 雪票查詢**：選地區（北海道 / 長野 / 新潟 / 山形 / 青森 / 福島，或留空 = 全部）→ 立即查詢
- **✈ 機票查詢**：選出發/目的地、輸入日期、人數 → 立即查詢
  - 若有 SerpAPI Key（[免費註冊 100 次/月](https://serpapi.com/)）填到「設定」分頁可提升查詢品質
  - 沒填則自動用 fast-flights 後端（免費，但偶爾不穩）
- **🕒 排程設定**：選任務類型 + 頻率 (DAILY / WEEKLY / ONCE) + 時間 → 「建立 / 更新排程」
  - 排程觸發時會以**最新儲存的設定**跑（先在對應分頁設好參數再儲存）
  - 想取消排程：在排程清單選一筆 → 「刪除選取排程」
- **⚙ 設定**：更改輸出資料夾、SerpAPI Key

### 排程任務名稱
所有排程任務都建立在 Windows 工作排程器的 `\SnowTrip\` 群組下，可在「工作排程器」UI 看到全部。

---

## 給開發者

### 從原始碼跑（測試用）
```cmd
.venv\Scripts\python.exe -m desktop_app.main --gui
.venv\Scripts\python.exe -m desktop_app.main --headless --task ski
.venv\Scripts\python.exe -m desktop_app.main --headless --task flight
```

### Build .exe
```cmd
.\desktop_app\build_exe.bat
```
產出 `dist\snowtrip_desktop.exe`（約 30-50 MB 視 Python 版本）。

### 架構
```
desktop_app/
├── main.py              # 入口：--gui (預設) / --headless --task {ski|flight}
├── gui/app.py           # tkinter Notebook：Ski / Flight / Schedule / Settings 四分頁
├── core/
│   ├── paths.py         # PyInstaller-aware 路徑解析
│   ├── config.py        # %APPDATA%\SnowTripDesktop\config.json 持久化
│   ├── scrapers.py      # 包裝既有 http_scraper / flight_search 函式
│   ├── output.py        # openpyxl Excel writer (ski + flight)
│   └── scheduler.py     # Windows schtasks 包裝
├── data/                # （目前空；未來可放 bundled urls.json 副本）
├── build.spec           # PyInstaller spec
└── build_exe.bat        # 一鍵 build 腳本
```

### 既有 codebase 復用
- `http_scraper.get_ticket_prices_async` — ski 爬蟲（httpx + BS4，無 Playwright = 小 exe）
- `flight_search.search_all` + backends（SerpAPI / fast-flights / Amadeus / ...）
- `urls.json` — 40 個雪場設定，bundled into exe via PyInstaller datas

**未動到爬蟲與機票後端 API 的任何程式碼**（per 使用者長期約束）。

### 排程運作原理
1. GUI「建立排程」呼叫 `schtasks /Create /TR "{exe path} --headless --task {ski|flight}" /SC {freq} /ST {time}`
2. 觸發時 Windows 直接 invoke exe 的 headless 模式
3. exe 讀 `%APPDATA%\SnowTripDesktop\config.json` 取參數 → 跑爬蟲 → 寫 Excel → 寫 log
4. log 記在 `%APPDATA%\SnowTripDesktop\snowtrip.log`，可供使用者除錯

### 開發測試清單
- [ ] `python -m desktop_app.main --gui` GUI 起得來
- [ ] 雪票分頁「立即查詢」能跑通並產出 Excel
- [ ] 機票分頁「立即搜尋」能跑通並產出 Excel
- [ ] 排程分頁建立 ONCE 任務 + 5 分鐘後驗證觸發
- [ ] `python -m desktop_app.main --headless --task ski` 不開 GUI 直接跑
- [ ] PyInstaller build 成功且 dist\snowtrip_desktop.exe 可雙擊跑
