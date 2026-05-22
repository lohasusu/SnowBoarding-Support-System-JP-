"""
Amadeus for Developers backend
免費 Test 帳號申請：https://developers.amadeus.com
- Test 環境使用模擬資料（免費，立即申請）
- 設定 AMADEUS_TEST=false 切換至 Production（需申請正式授權）
"""

import re
from .base import BackendBase, FlightResult

try:
    from amadeus import Client, ResponseError
    _AMADEUS_OK = True
except ImportError:
    _AMADEUS_OK = False


def _parse_duration(iso: str) -> str:
    if not iso:
        return ""
    m = re.match(r'PT(?:(\d+)H)?(?:(\d+)M)?', iso)
    if not m:
        return iso
    h = m.group(1) or "0"
    mins = m.group(2) or "0"
    return f"{h}h {mins}m"


def _format_segments(segs: list, origin: str, dest: str) -> str:
    if not segs:
        return f"{origin}→{dest}"
    return " → ".join(
        "{code}{num}({dep}→{arr})".format(
            code=s.get("carrierCode", ""),
            num=s.get("number", ""),
            dep=s["departure"]["iataCode"],
            arr=s["arrival"]["iataCode"],
        )
        for s in segs
    )


class AmadeusBackend(BackendBase):
    def __init__(self, client_id: str, client_secret: str, test_mode: bool = True):
        self._is_test = test_mode
        self.client = None
        if _AMADEUS_OK:
            self.client = Client(
                client_id=client_id,
                client_secret=client_secret,
                hostname="test" if test_mode else "production",
            )

    def is_available(self) -> bool:
        return _AMADEUS_OK and self.client is not None

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
        params = {
            "originLocationCode": origin,
            "destinationLocationCode": destination,
            "departureDate": departure_date,
            "adults": adults,
            "currencyCode": currency,
            "max": 20,
        }
        if return_date:
            params["returnDate"] = return_date

        try:
            response = self.client.shopping.flight_offers_search.get(**params)
        except Exception as e:
            print(f"  [Amadeus 錯誤] {origin}→{destination}: {e}")
            return []

        results = []
        for offer in response.data:
            r = self._parse(offer, origin, destination, dest_name, currency)
            if r:
                results.append(r)
        return results

    def _parse(
        self,
        offer: dict,
        origin: str,
        destination: str,
        dest_name: str,
        currency: str,
    ) -> FlightResult | None:
        try:
            price = float(offer["price"]["total"])
        except (KeyError, ValueError, TypeError):
            return None

        itineraries = offer.get("itineraries", [])
        if not itineraries:
            return None

        out_segs = itineraries[0].get("segments", [])
        if not out_segs:
            return None

        dep_time = out_segs[0]["departure"]["at"][:16].replace("T", " ")
        arr_time = out_segs[-1]["arrival"]["at"][:16].replace("T", " ")
        duration = _parse_duration(itineraries[0].get("duration", ""))
        stops = len(out_segs) - 1
        flights_str = _format_segments(out_segs, origin, destination)

        ret_dep_time = ret_arr_time = ret_duration = ret_flights_str = None
        ret_stops = None
        if len(itineraries) > 1:
            ret_segs = itineraries[1].get("segments", [])
            if ret_segs:
                ret_dep_time = ret_segs[0]["departure"]["at"][:16].replace("T", " ")
                ret_arr_time = ret_segs[-1]["arrival"]["at"][:16].replace("T", " ")
                ret_duration = _parse_duration(itineraries[1].get("duration", ""))
                ret_stops = len(ret_segs) - 1
                ret_flights_str = _format_segments(ret_segs, destination, origin)

        return FlightResult(
            source="Amadeus",
            origin=origin,
            destination=destination,
            destination_name=dest_name,
            price=price,
            currency=currency,
            dep_time=dep_time,
            arr_time=arr_time,
            duration=duration,
            flights_str=flights_str,
            stops=stops,
            ret_dep_time=ret_dep_time,
            ret_arr_time=ret_arr_time,
            ret_duration=ret_duration,
            ret_flights_str=ret_flights_str,
            ret_stops=ret_stops,
            note="Amadeus Test 模擬資料" if self._is_test else "",
        )
