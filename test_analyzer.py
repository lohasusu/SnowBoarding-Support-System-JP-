"""
test_analyzer.py
用 3 個代表性網站快速驗證 site_analyzer 的分析邏輯。
  - Furano      (英文 Prince Hotels 架構)
  - GALA Yuzawa (英日雙語，結構明確)
  - Niseko Moiwa (日文小型雪場)
"""

import asyncio
import sys
from pathlib import Path

# Windows 終端機強制 UTF-8 輸出，避免 cp950 編碼錯誤
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# 讓 import site_analyzer 能找到同目錄的模組
sys.path.insert(0, str(Path(__file__).parent))

from site_analyzer import analyze_resort, build_analyzed_urls, ANALYSIS_DIR, SCREENSHOT_DIR, HTML_DIR
import json
from playwright.async_api import async_playwright

TEST_TARGETS = [
    {"name": "Furano",    "url": "https://www.princehotels.co.jp/ski/furano",  "note": "北海道 Hokkaido"},
    {"name": "GALA Yuzawa", "url": "https://gala.co.jp/winter/",              "note": "新潟 Niigata"},
    {"name": "Rusutsu",   "url": "https://rusutsu.com/en/",                   "note": "北海道 Hokkaido"},
]

OUT_REPORT = ANALYSIS_DIR / "test_report.json"
OUT_URLS   = ANALYSIS_DIR / "test_urls_analyzed.json"


async def main() -> None:
    SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)
    HTML_DIR.mkdir(parents=True, exist_ok=True)

    semaphore = asyncio.Semaphore(2)   # 同時最多 2 個 tab
    reports = []

    print(f"分析 {len(TEST_TARGETS)} 個測試網站...\n")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        try:
            tasks = [analyze_resort(semaphore, browser, t) for t in TEST_TARGETS]
            reports = list(await asyncio.gather(*tasks))
        finally:
            await browser.close()

    # 輸出報告
    OUT_REPORT.write_text(json.dumps(reports, ensure_ascii=False, indent=2), encoding="utf-8")
    analyzed = build_analyzed_urls(TEST_TARGETS, reports)
    OUT_URLS.write_text(json.dumps(analyzed, ensure_ascii=False, indent=2), encoding="utf-8")

    print("\n===== 分析結果摘要 =====")
    for r in reports:
        status     = r["status"]
        ticket_url = r.get("ticket_url") or "(未找到子頁面，使用首頁)"
        hints      = r.get("selector_hints", [])
        hint_types = [h.get("type","?") for h in hints if not h.get("error")]
        screenshot = r.get("screenshot") or "(無)"
        print(f"\n[{r['name']}]")
        print(f"  狀態      : {status}")
        print(f"  票價頁面  : {ticket_url}")
        print(f"  選擇器建議: {hint_types if hint_types else '無'}")
        if hints:
            for h in hints[:2]:
                if not h.get("error"):
                    samples = h.get("samples", [])
                    print(f"    {h.get('type')} → container={h.get('container','')}")
                    for s in samples[:2]:
                        print(f"      範例: {s}")
        print(f"  截圖      : {screenshot}")

    print(f"\n完整報告 : {OUT_REPORT}")
    print(f"可編輯 URL: {OUT_URLS}")


if __name__ == "__main__":
    asyncio.run(main())
