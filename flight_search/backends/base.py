from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class FlightResult:
    source: str            # "SerpAPI" | "Travelpayouts"
    origin: str            # IATA e.g. "TPE"
    destination: str       # IATA e.g. "NRT"
    destination_name: str  # 中文名稱
    price: float
    currency: str

    # 去程
    dep_time: str          # "2026-12-20 07:00"
    arr_time: str          # "2026-12-20 12:00"（Travelpayouts 無此欄→空字串）
    duration: str          # "3h 20m"（Travelpayouts 無此欄→空字串）
    flights_str: str       # "BR108(TPE→NRT)"（Travelpayouts 只有航空代碼）
    stops: int

    # 回程（可選）
    ret_dep_time: str | None = None
    ret_arr_time: str | None = None
    ret_duration: str | None = None
    ret_flights_str: str | None = None
    ret_stops: int | None = None

    note: str = ""         # 備注，如資料來源說明


class BackendBase(ABC):
    @abstractmethod
    def is_available(self) -> bool: ...

    @abstractmethod
    def search(
        self,
        origin: str,
        destination: str,
        dest_name: str,
        departure_date: str,
        return_date: str | None,
        currency: str,
        adults: int,
    ) -> list[FlightResult]: ...
