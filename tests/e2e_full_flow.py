"""
E2E full flow test with screenshots — 2026-06-15.

Runs: home → register → login → ski/flight/plan/favorites → logout → relogin → persistence.
Each step captures a viewport screenshot to .sdlc/test-evidence/{run_id}/.
Final report at .sdlc/test-evidence/{run_id}/report.json.

Usage:
    .venv\\Scripts\\python.exe tests\\e2e_full_flow.py [--base URL]

Idempotent: each run gets a fresh user account (ts in email) so re-runs don't collide.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import sys
import time
from pathlib import Path

from playwright.async_api import async_playwright, Page, TimeoutError as PWTimeout


BASE_DEFAULT = "https://snowboarding-support-system-jp-production.up.railway.app"


class Report:
    def __init__(self, run_dir: Path):
        self.run_dir = run_dir
        self.steps: list[dict] = []
        self.run_dir.mkdir(parents=True, exist_ok=True)

    def step(self, key: str, ok: bool, screenshot: str = "", **extra):
        self.steps.append({
            "step": key,
            "ok": ok,
            "screenshot": screenshot,
            "ts": int(time.time()),
            **extra,
        })
        flag = "PASS" if ok else "FAIL"
        print(f"  [{flag}] {key}  screenshot={screenshot}  {extra}")

    def write(self) -> Path:
        out = self.run_dir / "report.json"
        out.write_text(
            json.dumps({"run_dir": str(self.run_dir), "steps": self.steps}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return out


async def shot(page: Page, run_dir: Path, name: str) -> str:
    fp = run_dir / f"{name}.png"
    await page.screenshot(path=str(fp), full_page=True)
    return fp.name


async def run_flow(base: str, run_dir: Path) -> Report:
    rpt = Report(run_dir)
    ts = int(time.time())
    email = f"e2e-{ts}@flow-test.local"
    username = f"e2euser{ts}"
    password = f"E2eFlow_{ts}"
    meta = {"email": email, "username": username, "base": base}
    (run_dir / "creds.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")

    async with async_playwright() as p:
        # Headless Chromium — works on Windows + Linux + CI
        browser = await p.chromium.launch(headless=True)
        ctx = await browser.new_context(viewport={"width": 1280, "height": 900}, locale="zh-TW")
        page = await ctx.new_page()
        # 60s nav timeout — flight search can be slow
        page.set_default_navigation_timeout(60_000)
        page.set_default_timeout(30_000)

        try:
            # ───────── STEP 01: Home page ─────────
            await page.goto(f"{base}/")
            await page.wait_for_load_state("networkidle")
            sn = await shot(page, run_dir, "01-home")
            # Verify integration card is enabled (no '即將推出', has '開始試算')
            html = await page.content()
            ok = "即將推出" not in html and "敬請期待" not in html and "開始試算" in html
            rpt.step("01-home", ok, sn, has_kaishishisuan="開始試算" in html, has_old="即將推出" in html)

            # ───────── STEP 02: Register page ─────────
            await page.goto(f"{base}/register")
            await page.wait_for_load_state("networkidle")
            sn = await shot(page, run_dir, "02-register-blank")
            rpt.step("02-register-blank", True, sn)

            # ───────── STEP 03: Fill register form ─────────
            await page.fill("#reg-email", email)
            await page.fill("#reg-username", username)
            await page.fill("#reg-password", password)
            sn = await shot(page, run_dir, "03-register-filled")
            rpt.step("03-register-filled", True, sn)

            # ───────── STEP 04: Submit register → should land on /login?registered=1 ─────────
            t0 = time.monotonic()
            async with page.expect_navigation():
                await page.click("#register-form button[type=submit]")
            reg_dur = time.monotonic() - t0
            await page.wait_for_load_state("networkidle")
            url_after = page.url
            sn = await shot(page, run_dir, "04-login-with-success-alert")
            ok = "/login" in url_after and "registered=1" in url_after
            # Verify success alert rendered
            alert = await page.locator("#login-alert .alert-success").count()
            rpt.step(
                "04-register-submit",
                ok and alert > 0,
                sn,
                url=url_after,
                duration_s=round(reg_dur, 3),
                no_email_send_indicator=reg_dur < 2.0,
                success_alert_count=alert,
            )

            # ───────── STEP 05: Fill login form + submit ─────────
            await page.fill("#login-identifier", email)
            await page.fill("#login-password", password)
            sn = await shot(page, run_dir, "05-login-filled")
            rpt.step("05-login-filled", True, sn)

            async with page.expect_navigation():
                await page.click("#login-form button[type=submit]")
            await page.wait_for_load_state("networkidle")
            url_after = page.url
            sn = await shot(page, run_dir, "06-profile-after-login")
            ok = "/profile" in url_after
            rpt.step("06-login-submit", ok, sn, url=url_after)

            # ───────── STEP 07: Empty profile state ─────────
            sn = await shot(page, run_dir, "07-profile-empty")
            empty_alert = await page.locator(".alert-info:has-text('尚無收藏')").count()
            rpt.step("07-profile-empty", empty_alert > 0, sn, empty_alert=empty_alert)

            # ───────── STEP 08: Ski search ─────────
            await page.goto(f"{base}/ski")
            await page.wait_for_load_state("networkidle")
            sn = await shot(page, run_dir, "08-ski-search-page")
            rpt.step("08-ski-search-page", True, sn)

            # Select 北海道 region (option value)
            await page.select_option("#region", "北海道")
            await page.click("#ski-form button[type=submit]")
            # Wait for at least one row to appear (SSE streams)
            try:
                await page.locator("#results-tbody tr").first.wait_for(timeout=45_000)
                # Wait a bit more for more rows
                await asyncio.sleep(8)
            except PWTimeout:
                pass
            try:
                await page.wait_for_load_state("networkidle", timeout=10_000)
            except PWTimeout:
                pass
            row_count = await page.locator("#results-tbody tr").count()
            sn = await shot(page, run_dir, "09-ski-results")
            rpt.step("09-ski-results", row_count > 0, sn, row_count=row_count)

            # ───────── STEP 10: Click ♡ on first ski row ─────────
            fav_btns_before = await page.locator(".fav-btn").count()
            if fav_btns_before > 0:
                first_fav = page.locator(".fav-btn").first
                await first_fav.click()
                # Wait for visual feedback (btn-danger class)
                try:
                    await page.locator(".fav-btn.btn-danger").first.wait_for(timeout=10_000)
                    fav_ok = True
                except PWTimeout:
                    fav_ok = False
                sn = await shot(page, run_dir, "10-ski-favorited")
                rpt.step("10-ski-favorite", fav_ok, sn, fav_btn_count=fav_btns_before)
            else:
                rpt.step("10-ski-favorite", False, "", error="no fav-btn rendered")

            # ───────── STEP 11: Flight search ─────────
            await page.goto(f"{base}/flight")
            await page.wait_for_load_state("networkidle")
            sn = await shot(page, run_dir, "11-flight-search-page")
            rpt.step("11-flight-search-page", True, sn)

            await page.select_option("#origin", "TPE")
            await page.select_option("#destination", "CTS")
            # departure 2027-02-15
            await page.fill("#departure", "2027-02-15")
            await page.fill("#ret-date", "2027-02-22")
            await page.click("#flight-form button[type=submit]")
            # Flight search via SerpAPI takes a few seconds
            try:
                await page.locator(".fav-btn").first.wait_for(timeout=60_000)
            except PWTimeout:
                pass
            row_count_fl = await page.locator("tbody tr").count()
            sn = await shot(page, run_dir, "12-flight-results")
            rpt.step("12-flight-results", row_count_fl > 0, sn, row_count=row_count_fl)

            # ───────── STEP 13: Click ♡ on first flight row ─────────
            fav_btns_fl = await page.locator(".fav-btn").count()
            if fav_btns_fl > 0:
                await page.locator(".fav-btn").first.click()
                try:
                    await page.locator(".fav-btn.btn-danger").first.wait_for(timeout=10_000)
                    fav_ok = True
                except PWTimeout:
                    fav_ok = False
                sn = await shot(page, run_dir, "13-flight-favorited")
                rpt.step("13-flight-favorite", fav_ok, sn, fav_btn_count=fav_btns_fl)
            else:
                rpt.step("13-flight-favorite", False, "", error="no fav-btn rendered")

            # ───────── STEP 14: Plan (integration query) page ─────────
            await page.goto(f"{base}/plan")
            await page.wait_for_load_state("networkidle")
            sn = await shot(page, run_dir, "14-plan-page")
            rpt.step("14-plan-page", True, sn)

            await page.select_option("#plan-origin", "TPE")
            await page.select_option("#plan-dest", "CTS")
            await page.select_option("#plan-region", "北海道")
            await page.fill("#plan-departure", "2027-02-15")
            await page.fill("#plan-return", "2027-02-22")
            await page.click("#plan-form button[type=submit]")
            # Plan page does Promise.all on flight + ski — wait for results
            try:
                await page.wait_for_selector("#plan-results table", timeout=90_000)
            except PWTimeout:
                pass
            sn = await shot(page, run_dir, "15-plan-results")
            tables = await page.locator("#plan-results table").count()
            rpt.step("15-plan-results", tables > 0, sn, tables_rendered=tables)

            # ───────── STEP 16: Profile (favorites populated) ─────────
            await page.goto(f"{base}/profile")
            await page.wait_for_load_state("networkidle")
            sn = await shot(page, run_dir, "16-profile-with-favs")
            fav_cards = await page.locator(".card .del-fav-btn").count()
            loc_label = await page.locator("text=地點：").count()
            time_label = await page.locator("text=時間：").count()
            rpt.step(
                "16-profile-with-favs",
                fav_cards >= 2 and loc_label >= 2 and time_label >= 2,
                sn,
                fav_cards=fav_cards,
                location_labels=loc_label,
                time_labels=time_label,
            )

            # ───────── STEP 17: Delete one favorite ─────────
            if fav_cards >= 1:
                # Auto-accept the confirm() dialog
                page.once("dialog", lambda d: asyncio.create_task(d.accept()))
                await page.locator(".del-fav-btn").first.click()
                await asyncio.sleep(2)
                sn = await shot(page, run_dir, "17-profile-after-delete")
                after = await page.locator(".del-fav-btn").count()
                rpt.step("17-delete-favorite", after == fav_cards - 1, sn, before=fav_cards, after=after)
            else:
                rpt.step("17-delete-favorite", False, "", error="no favorites to delete")

            # ───────── STEP 18: Logout ─────────
            # logout-btn handler: await fetch + location.href = '/' — must explicitly wait for navigation
            try:
                async with page.expect_navigation(timeout=15_000):
                    await page.click("#logout-btn")
            except PWTimeout:
                # Fallback: manually wait then check
                await asyncio.sleep(3)
            await page.wait_for_load_state("networkidle", timeout=10_000)
            sn = await shot(page, run_dir, "18-after-logout")
            url_lo = page.url
            # Check session: fetch /api/auth/me — should be 401 if logout worked
            me_status = await page.evaluate(
                "async () => (await fetch('/api/auth/me')).status"
            )
            rpt.step(
                "18-logout",
                me_status == 401,
                sn,
                url=url_lo,
                me_status=me_status,
            )

            # ───────── STEP 19: Re-login by username ─────────
            await page.goto(f"{base}/login", wait_until="domcontentloaded")
            await page.wait_for_load_state("networkidle")
            await page.fill("#login-identifier", username)
            await page.fill("#login-password", password)
            async with page.expect_navigation():
                await page.click("#login-form button[type=submit]")
            await page.wait_for_load_state("networkidle")
            sn = await shot(page, run_dir, "19-relogin-profile")
            after_relogin_favs = await page.locator(".del-fav-btn").count()
            rpt.step(
                "19-relogin-by-username",
                "/profile" in page.url and after_relogin_favs >= 1,
                sn,
                url=page.url,
                persistent_favs=after_relogin_favs,
            )

            # ───────── STEP 20: Removed routes still 404 (via fetch in browser context) ─────────
            results = await page.evaluate(
                """async (base) => {
                    const ve = await fetch(base + '/api/auth/verify-email?token=x').then(r => r.status);
                    const rv = await fetch(base + '/api/auth/resend-verification', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: '{}'
                    }).then(r => r.status);
                    return {verify_email: ve, resend_verification: rv};
                }""",
                base,
            )
            rpt.step(
                "20-removed-routes-404",
                results["verify_email"] == 404 and results["resend_verification"] == 404,
                "",
                **results,
            )

        finally:
            await ctx.close()
            await browser.close()

    rpt.write()
    return rpt


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", default=BASE_DEFAULT)
    parser.add_argument("--out", default=".sdlc/test-evidence")
    args = parser.parse_args()

    run_id = time.strftime("%Y%m%d_%H%M%S")
    run_dir = Path(args.out) / run_id

    print(f"==> base    : {args.base}")
    print(f"==> run_dir : {run_dir}")
    print(f"==> starting Playwright Chromium (headless)...")

    rpt = asyncio.run(run_flow(args.base, run_dir))

    print()
    print("=" * 60)
    total = len(rpt.steps)
    passed = sum(1 for s in rpt.steps if s["ok"])
    failed = total - passed
    print(f"FINAL: {passed}/{total} steps PASS, {failed} FAIL")
    print(f"Report: {run_dir / 'report.json'}")
    print(f"Screenshots: {run_dir / '*.png'}")

    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
