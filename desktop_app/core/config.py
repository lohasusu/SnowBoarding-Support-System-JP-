"""User configuration persistence (JSON in %APPDATA%/SnowTripDesktop/config.json).

Stores last-used GUI inputs + scheduled task params + SerpAPI key.
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from typing import Optional

from desktop_app.core.paths import config_path, default_output_dir


@dataclass
class SkiParams:
    region: str = ""              # "" / 北海道 / 長野 / 新潟 / 山形 / 青森 / 福島
    name: str = ""                # optional resort name filter (substring)


@dataclass
class FlightParams:
    origin: str = "TPE"
    destination: str = "CTS"
    dest_name: str = "新千歲"
    departure: str = ""           # YYYY-MM-DD
    ret_date: str = ""            # YYYY-MM-DD, empty for one-way
    adults: int = 1
    currency: str = "TWD"
    budget: int = 0               # 0 = no limit


@dataclass
class ScheduleParams:
    task_name: str = "SnowTrip-Daily"
    task_type: str = "ski"        # "ski" or "flight"
    frequency: str = "DAILY"      # DAILY / WEEKLY / ONCE
    days: str = "MON,TUE,WED,THU,FRI,SAT,SUN"  # used when WEEKLY
    time_hhmm: str = "08:00"      # 24h


@dataclass
class AppConfig:
    output_dir: str = ""          # blank → default_output_dir()
    serpapi_key: str = ""         # optional, for flight search
    ski: SkiParams = field(default_factory=SkiParams)
    flight: FlightParams = field(default_factory=FlightParams)
    schedule: ScheduleParams = field(default_factory=ScheduleParams)


def load() -> AppConfig:
    p = config_path()
    if not p.exists():
        c = AppConfig(output_dir=str(default_output_dir()))
        save(c)
        return c
    try:
        raw = json.loads(p.read_text(encoding="utf-8"))
        return AppConfig(
            output_dir=raw.get("output_dir", "") or str(default_output_dir()),
            serpapi_key=raw.get("serpapi_key", ""),
            ski=SkiParams(**raw.get("ski", {})),
            flight=FlightParams(**raw.get("flight", {})),
            schedule=ScheduleParams(**raw.get("schedule", {})),
        )
    except Exception:
        # Corrupt config — fall back to defaults
        return AppConfig(output_dir=str(default_output_dir()))


def save(cfg: AppConfig) -> None:
    p = config_path()
    p.write_text(json.dumps(asdict(cfg), ensure_ascii=False, indent=2), encoding="utf-8")
