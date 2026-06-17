"""Wrap existing async/sync scraper functions so the GUI can call them cleanly.

Reuses (does NOT modify):
- http_scraper.get_ticket_prices_async — ski tickets
- flight_search.flight_search.search_all / export_to_excel — flights
"""
from __future__ import annotations

import asyncio
import os
import sys
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Callable, Optional

import importlib.util

from desktop_app.core.paths import base_dir


def _load_flight_search_module():
    """flight_search/ is not a Python package (no __init__.py) — load
    flight_search.py directly via importlib.util so we never modify the
    upstream directory."""
    if "flight_search_inner" in sys.modules:
        return sys.modules["flight_search_inner"]
    fp = base_dir() / "flight_search" / "flight_search.py"
    spec = importlib.util.spec_from_file_location("flight_search_inner", str(fp))
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load flight_search at {fp}")
    mod = importlib.util.module_from_spec(spec)
    sys.modules["flight_search_inner"] = mod
    spec.loader.exec_module(mod)
    return mod


def _stub_deep_translator() -> None:
    """ski_early_bird_scraper imports GoogleTranslator for live JA→ZH; not used
    in the helper functions we consume. Stub to avoid bundling network-translator deps."""
    import types
    if "deep_translator" in sys.modules:
        return
    fake = types.ModuleType("deep_translator")

    class _StubTranslator:
        def __init__(self, *a, **kw): pass
        def translate(self, text: str) -> str: return text

    fake.GoogleTranslator = _StubTranslator
    sys.modules["deep_translator"] = fake


def _stub_playwright() -> None:
    """ski_early_bird_scraper.py top-level imports Playwright, but the helper
    functions we actually consume (TicketItem / extract_prices / load_targets)
    don't use it. Stub the module so the import succeeds without bundling
    Chromium (~200MB) into the exe."""
    import types
    if "playwright" in sys.modules:
        return
    fake = types.ModuleType("playwright")
    fake_async = types.ModuleType("playwright.async_api")

    class _PWTimeout(Exception):
        pass

    def _stub_launch(*args, **kw):
        raise RuntimeError(
            "Playwright was excluded from the .exe build; this scraper path "
            "is not available in the desktop distribution."
        )

    fake_async.async_playwright = _stub_launch
    fake_async.TimeoutError = _PWTimeout
    sys.modules["playwright"] = fake
    sys.modules["playwright.async_api"] = fake_async


def _ensure_path() -> None:
    """Add repo root + flight_search/ to sys.path so imports resolve in both modes."""
    root = base_dir()
    for p in (root, root / "flight_search"):
        s = str(p)
        if s not in sys.path:
            sys.path.insert(0, s)
    _stub_playwright()
    _stub_deep_translator()


# ── Ski ────────────────────────────────────────────────────────────────────────

def run_ski(region: str = "", name: str = "",
            progress_cb: Optional[Callable[[str], None]] = None) -> list[dict]:
    """Run the ski scraper synchronously (wraps async fn).

    Returns: list of TicketItem dicts (resort, region, ticket_type, ticket_type_zh,
             price, season, source_url, scraped_at).
    """
    _ensure_path()

    # urls.json is bundled at base_dir() for frozen mode; http_scraper.load_targets
    # looks for it via SCRIPT_DIR. Patch cwd so relative paths resolve.
    prev_cwd = os.getcwd()
    try:
        os.chdir(str(base_dir()))
        from http_scraper import get_ticket_prices_async  # type: ignore
        if progress_cb:
            progress_cb(f"開始查詢雪票 region={region or '全部'} name={name or '無'}")
        items = asyncio.run(
            get_ticket_prices_async(region=region or None, name=name or None)
        )
        if progress_cb:
            progress_cb(f"完成 — 共 {len(items)} 筆")
        # TicketItem may be dataclass; asdict it
        out = []
        for it in items:
            if hasattr(it, "__dataclass_fields__"):
                out.append(asdict(it))
            elif isinstance(it, dict):
                out.append(it)
            else:
                out.append(vars(it))
        return out
    finally:
        os.chdir(prev_cwd)


# ── Flight ─────────────────────────────────────────────────────────────────────

def run_flight(origin: str, destination: str, dest_name: str,
               departure: str, ret_date: str = "",
               adults: int = 1, currency: str = "TWD",
               serpapi_key: str = "",
               progress_cb: Optional[Callable[[str], None]] = None) -> list[dict]:
    """Run flight search using flight_search backends.

    Returns: list of FlightResult dicts.
    """
    _ensure_path()
    prev_cwd = os.getcwd()
    try:
        os.chdir(str(base_dir()))
        if serpapi_key:
            os.environ["SERPAPI_API_KEY"] = serpapi_key

        if progress_cb:
            progress_cb(f"開始搜尋機票 {origin} → {destination} {departure}"
                        + (f" / {ret_date}" if ret_date else ""))

        fs = _load_flight_search_module()
        backends = fs.build_backends(mock_mode=False)
        results = fs.search_all(
            backends=backends,
            origins=[origin],
            destinations=[destination],
            dest_name_map={destination: dest_name},
            departure_date=departure,
            return_date=ret_date or None,
            currency=currency,
            adults=adults,
        )
        if progress_cb:
            progress_cb(f"完成 — 共 {len(results)} 筆")
        out = []
        for r in results:
            if hasattr(r, "__dataclass_fields__"):
                out.append(asdict(r))
            elif isinstance(r, dict):
                out.append(r)
            else:
                out.append(vars(r))
        return out
    finally:
        os.chdir(prev_cwd)
