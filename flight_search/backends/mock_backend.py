"""
Mock backend - 完整流程測試，不需要任何 API Key
用法：python flight_search.py --mock
"""

import random
from datetime import datetime, timedelta
from .base import BackendBase, FlightResult

_AIRLINES = [
    ("CI", 9500),
    ("BR", 10200),
    ("JL", 14000),
    ("NH", 13500),
    ("MM", 6800),
    ("IT", 6200),
    ("AK", 5900),
]

_BASE_DURATION_H = {
    "NRT": 3.5, "HND": 3.5, "KIX": 2.8, "ITM": 2.8, "NGO": 2.5,
    "CTS": 3.8, "FUK": 2.2, "OKA": 2.0, "HIJ": 2.5, "SDJ": 3.0,
    "TAK": 2.6, "NGS": 2.5,
}

_TWD_TO_USD = 32.0
_TWD_TO_JPY = 4.5


def _convert(price_twd: float, currency: str) -> float:
    if currency == "USD":
        return round(price_twd / _TWD_TO_USD, 2)
    if currency == "JPY":
        return round(price_twd * _TWD_TO_JPY)
    return round(price_twd)


def _duration_str(hours: float) -> str:
    h = int(hours)
    m = int((hours - h) * 60)
    return f"{h}h {m}m"


class MockBackend(BackendBase):
    def is_available(self) -> bool:
        return True

    def search(
        self,
        origin: str,
        destination: str,
        dest_name: str,
        departure_date: str,
        return_date: str | None,
        currency: str,
        adults: int,
    ) -> list[FlightResult]:
        # 同一組參數每次出一樣的結果（方便測試）
        rng = random.Random(f"{origin}{destination}{departure_date}")
        dep_dt = datetime.strptime(departure_date, "%Y-%m-%d")
        base_h = _BASE_DURATION_H.get(destination, 3.0)

        results = []
        for airline_code, base_price_pp in rng.sample(_AIRLINES, k=min(5, len(_AIRLINES))):
            dep_hour = rng.randint(6, 22)
            dep_time = dep_dt.replace(hour=dep_hour, minute=0)
            dur_h = base_h + rng.uniform(-0.25, 0.5)
            arr_time = dep_time + timedelta(hours=dur_h)
            flight_num = f"{airline_code}{rng.randint(100, 999)}"

            price_twd = base_price_pp * adults * rng.uniform(0.85, 1.25)

            ret_dep_time = ret_arr_time = ret_flights_str = ret_duration = None
            ret_stops = None
            if return_date:
                ret_dt = datetime.strptime(return_date, "%Y-%m-%d")
                ret_dep_h = rng.randint(6, 22)
                ret_dep = ret_dt.replace(hour=ret_dep_h, minute=0)
                ret_arr = ret_dep + timedelta(hours=base_h + rng.uniform(-0.25, 0.5))
                ret_dep_time = ret_dep.strftime("%Y-%m-%d %H:%M")
                ret_arr_time = ret_arr.strftime("%Y-%m-%d %H:%M")
                ret_fn = f"{airline_code}{rng.randint(100, 999)}"
                ret_flights_str = f"{ret_fn}({destination}→{origin})"
                ret_duration = _duration_str(base_h)
                ret_stops = 0
                price_twd *= 1.85  # 去回程約 1.85 倍單程

            results.append(FlightResult(
                source="Mock",
                origin=origin,
                destination=destination,
                destination_name=dest_name,
                price=_convert(price_twd, currency),
                currency=currency,
                dep_time=dep_time.strftime("%Y-%m-%d %H:%M"),
                arr_time=arr_time.strftime("%Y-%m-%d %H:%M"),
                duration=_duration_str(dur_h),
                flights_str=f"{flight_num}({origin}→{destination})",
                stops=0,
                ret_dep_time=ret_dep_time,
                ret_arr_time=ret_arr_time,
                ret_duration=ret_duration,
                ret_flights_str=ret_flights_str,
                ret_stops=ret_stops,
                note="[MOCK 測試資料，非真實票價]",
            ))

        return results
