"""
SnowTrip Japan — FastAPI Web Application
執行: python main.py  或  uvicorn main:app --reload
"""
import io
import sys
from dataclasses import asdict
from pathlib import Path

# 本地開發：web/ 在 D:\SideProject\web\，ROOT = D:\SideProject\
# 部署環境：web/ 在 snowboarding_support\web\，ROOT = snowboarding_support\
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "flight_search"))

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, Response, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import uvicorn

BASE_URL = "https://snowtrip.tw"  # 部署後改這裡

app = FastAPI(title="SnowTrip Japan", docs_url=None, redoc_url=None)

TEMPLATE_DIR = Path(__file__).parent / "templates"
STATIC_DIR   = Path(__file__).parent / "static"

app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
templates = Jinja2Templates(directory=str(TEMPLATE_DIR))


def _ctx(request: Request, **kw) -> dict:
    return {
        "base_url": BASE_URL,
        "canonical_url": BASE_URL + str(request.url.path),
        **kw,
    }


# ── 頁面路由 ──────────────────────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse(request, "index.html", _ctx(request))


@app.get("/ski", response_class=HTMLResponse)
async def ski_page(request: Request):
    return templates.TemplateResponse(request, "ski.html", _ctx(request))


@app.get("/flight", response_class=HTMLResponse)
async def flight_page(request: Request):
    return templates.TemplateResponse(request, "flight.html", _ctx(request))


@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse(request, "auth/login.html", _ctx(request))


@app.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    return templates.TemplateResponse(request, "auth/register.html", _ctx(request))


# ── API：雪票 ─────────────────────────────────────────────────────────────────

def _import_ski():
    try:
        from snowboarding_support.scraper import get_ticket_prices
    except ImportError:
        from scraper import get_ticket_prices  # 部署環境：ROOT 即 snowboarding_support/
    return get_ticket_prices


@app.get("/api/ski/search")
async def api_ski_search(region: str = None, name: str = None):
    try:
        get_ticket_prices = _import_ski()
        results = get_ticket_prices(region=region or None, name=name or None)
        return {"ok": True, "data": [asdict(r) for r in results]}
    except Exception as e:
        return {"ok": False, "error": str(e)}


@app.get("/api/ski/download")
async def api_ski_download(region: str = None, name: str = None):
    try:
        import openpyxl
        from openpyxl.styles import Font, PatternFill, Alignment
        get_ticket_prices = _import_ski()

        results = get_ticket_prices(region=region or None, name=name or None)
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "雪票價格"

        headers = ["雪場", "地區", "票種（日文）", "票種（中文）", "票價", "雪季", "查詢時間", "票價頁連結"]
        header_fill = PatternFill("solid", fgColor="1565C0")
        header_font = Font(color="FFFFFF", bold=True)
        for col, h in enumerate(headers, 1):
            cell = ws.cell(row=1, column=col, value=h)
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = Alignment(horizontal="center")

        for row_i, r in enumerate(results, 2):
            d = asdict(r)
            ws.cell(row=row_i, column=1, value=d.get("resort", ""))
            ws.cell(row=row_i, column=2, value=d.get("region", ""))
            ws.cell(row=row_i, column=3, value=d.get("ticket_type", ""))
            ws.cell(row=row_i, column=4, value=d.get("ticket_type_zh", ""))
            ws.cell(row=row_i, column=5, value=d.get("price", ""))
            ws.cell(row=row_i, column=6, value=d.get("season", ""))
            ws.cell(row=row_i, column=7, value=d.get("scraped_at", ""))
            ws.cell(row=row_i, column=8, value=d.get("source_url", ""))

        for col in ws.columns:
            ws.column_dimensions[col[0].column_letter].width = 18

        buf = io.BytesIO()
        wb.save(buf)
        buf.seek(0)
        filename = f"ski_prices_{region or 'all'}.xlsx"
        return StreamingResponse(
            buf,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )
    except Exception as e:
        return Response(content=str(e), status_code=500)


# ── API：機票 ─────────────────────────────────────────────────────────────────

@app.get("/api/flight/search")
async def api_flight_search(
    origin: str = "TPE",
    destination: str = "CTS",
    dest_name: str = "新千歲",
    departure: str = None,
    ret_date: str = None,
    currency: str = "TWD",
    adults: int = 1,
):
    if not departure:
        return {"ok": False, "error": "請輸入出發日期"}
    try:
        from backends.fast_flights_backend import FastFlightsBackend
        backend = FastFlightsBackend()
        results = backend.search(
            origin=origin,
            destination=destination,
            dest_name=dest_name,
            departure_date=departure,
            return_date=ret_date or None,
            currency=currency,
            adults=adults,
        )
        return {"ok": True, "data": [asdict(r) for r in results]}
    except Exception as e:
        return {"ok": False, "error": str(e)}


# ── SEO ───────────────────────────────────────────────────────────────────────

@app.get("/robots.txt", response_class=Response)
async def robots():
    return Response(
        content=f"User-agent: *\nAllow: /\nDisallow: /api/\n\nSitemap: {BASE_URL}/sitemap.xml\n",
        media_type="text/plain",
    )


@app.get("/sitemap.xml", response_class=Response)
async def sitemap():
    pages = [("/", "1.0", "weekly"), ("/ski", "0.9", "daily"), ("/flight", "0.8", "weekly")]
    items = "\n".join(
        f"  <url><loc>{BASE_URL}{p}</loc><changefreq>{cf}</changefreq><priority>{pr}</priority></url>"
        for p, pr, cf in pages
    )
    xml = f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{items}\n</urlset>'
    return Response(content=xml, media_type="application/xml")


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
