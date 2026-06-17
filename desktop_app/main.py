"""SnowTrip Desktop — entry point.

Modes:
  (default)        --gui       Launch tkinter GUI
  --headless --task ski        Run ski scraper using saved config, save Excel
  --headless --task flight     Run flight search using saved config, save Excel
"""
from __future__ import annotations

import argparse
import io
import os
import sys
import traceback
from datetime import datetime
from pathlib import Path


# Make sure the `desktop_app` package resolves both in source mode and
# inside PyInstaller's _MEIPASS dir.
def _setup_path() -> None:
    if getattr(sys, "frozen", False):
        base = Path(getattr(sys, "_MEIPASS"))
    else:
        base = Path(__file__).resolve().parent.parent
    s = str(base)
    if s not in sys.path:
        sys.path.insert(0, s)


_setup_path()


def _force_utf8_stdio() -> None:
    """Windows cp950 console can't render emojis / Chinese — force UTF-8."""
    for stream_name in ("stdout", "stderr"):
        s = getattr(sys, stream_name)
        if hasattr(s, "reconfigure"):
            try:
                s.reconfigure(encoding="utf-8", errors="replace")
            except Exception:
                pass


def _headless_run(task_type: str) -> int:
    # Defer imports so GUI mode startup stays light
    from desktop_app.core import config as cfg_mod
    from desktop_app.core import output as out_mod
    from desktop_app.core import scrapers as scr_mod
    from desktop_app.core.paths import log_path

    def log(msg: str):
        line = f"[{datetime.now().strftime('%H:%M:%S')}] [headless] {msg}"
        print(line, flush=True)
        try:
            with open(log_path(), "a", encoding="utf-8") as f:
                f.write(line + "\n")
        except Exception:
            pass

    cfg = cfg_mod.load()
    out_dir = Path(cfg.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    try:
        if task_type == "ski":
            log(f"⛷ headless ski region={cfg.ski.region or '全部'} name={cfg.ski.name or '無'}")
            items = scr_mod.run_ski(region=cfg.ski.region, name=cfg.ski.name, progress_cb=log)
            fp = out_mod.write_ski(items, out_dir, {"region": cfg.ski.region, "name": cfg.ski.name})
            log(f"✅ ski 完成 {len(items)} 筆 → {fp}")
        elif task_type == "flight":
            fl = cfg.flight
            log(f"✈ headless flight {fl.origin}→{fl.destination} {fl.departure}"
                + (f"/{fl.ret_date}" if fl.ret_date else ""))
            items = scr_mod.run_flight(
                origin=fl.origin, destination=fl.destination, dest_name=fl.dest_name,
                departure=fl.departure, ret_date=fl.ret_date, adults=fl.adults,
                currency=fl.currency, serpapi_key=cfg.serpapi_key, progress_cb=log,
            )
            fp = out_mod.write_flight(items, out_dir, {
                "origin": fl.origin, "destination": fl.destination,
                "dest_name": fl.dest_name, "departure": fl.departure,
                "ret_date": fl.ret_date, "adults": fl.adults,
            })
            log(f"✅ flight 完成 {len(items)} 筆 → {fp}")
        else:
            log(f"❌ 未知 task_type: {task_type!r}")
            return 2
    except Exception as e:
        log(f"❌ 失敗: {e}\n{traceback.format_exc()}")
        return 1
    return 0


def main() -> int:
    _force_utf8_stdio()
    parser = argparse.ArgumentParser(prog="SnowTrip Desktop")
    parser.add_argument("--gui", action="store_true", help="啟動 GUI (預設)")
    parser.add_argument("--headless", action="store_true", help="無 GUI 跑排程任務")
    parser.add_argument("--task", choices=["ski", "flight"], help="--headless 時必填")
    parser.add_argument("--initial-tab", type=int, default=0,
                        help="GUI 啟動時要顯示的分頁 (0=雪票 1=機票 2=排程 3=設定)")
    args = parser.parse_args()

    if args.headless:
        if not args.task:
            print("❌ --headless 必須搭配 --task ski 或 --task flight")
            return 2
        return _headless_run(args.task)

    # GUI mode (default)
    from desktop_app.gui.app import launch
    launch(initial_tab=args.initial_tab)
    return 0


if __name__ == "__main__":
    sys.exit(main())
