#!/usr/bin/env python3
"""
Auto-capture documentation screenshots with Playwright.

Targets the Streamlit demo app (no secrets required) and saves PNGs into:
  Markaz-Products-Cloning-Doc/images/

Usage:
  # Start demo app in another terminal (or let this script start it):
  streamlit run demo_mode/app.py --server.headless true --server.port 8501

  python scripts/capture_docs_screenshots.py
  python scripts/capture_docs_screenshots.py --url http://127.0.0.1:8501 --no-start
"""

from __future__ import annotations

import argparse
import re
import signal
import subprocess
import sys
import time
from pathlib import Path

from playwright.sync_api import Page, sync_playwright

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "Markaz-Products-Cloning-Doc" / "images"
DEMO_ENTRY = ROOT / "demo_mode" / "app.py"
DEFAULT_URL = "http://127.0.0.1:8501"
DEMO_USER = "demo"
DEMO_PASS = "demo123"
DEMO_PRODUCT_URL = "https://www.markaz.app/shop/product/demo-silk-kurti-for-docs"


def slug(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-") or "shot"


class ShotCounter:
    def __init__(self, out_dir: Path):
        self.out_dir = out_dir
        self.n = 0
        self.saved: list[Path] = []

    def next_path(self, name: str) -> Path:
        self.n += 1
        path = self.out_dir / f"{self.n:02d}-{slug(name)}.png"
        return path

    def save(self, page: Page, name: str, full_page: bool = True) -> Path:
        path = self.next_path(name)
        page.screenshot(path=str(path), full_page=full_page)
        self.saved.append(path)
        print(f"  ✓ {path.name}")
        return path

    def save_locator(self, locator, name: str) -> Path | None:
        if locator.count() == 0:
            print(f"  · skip {name} (not found)")
            return None
        target = locator.first
        path = self.next_path(name)
        try:
            target.scroll_into_view_if_needed(timeout=3000)
        except Exception:
            pass
        try:
            target.screenshot(path=str(path))
        except Exception:
            # Fallback: page shot if element shot fails (hidden/offscreen).
            target.page.screenshot(path=str(path), full_page=False)
        self.saved.append(path)
        print(f"  ✓ {path.name}")
        return path


def wait_streamlit_idle(page: Page, timeout_ms: int = 20000) -> None:
    """Wait until Streamlit finished a run (spinner gone / app visible)."""
    page.wait_for_selector('[data-testid="stAppViewContainer"]', timeout=timeout_ms)
    # Give Streamlit a moment after navigation / rerun.
    page.wait_for_timeout(800)
    try:
        page.wait_for_selector('[data-testid="stStatusWidget"]', state="detached", timeout=8000)
    except Exception:
        pass
    page.wait_for_timeout(400)


def click_button(page: Page, name: str | re.Pattern, exact: bool = False) -> None:
    btn = page.get_by_role("button", name=name, exact=exact)
    btn.first.click()
    wait_streamlit_idle(page)


def click_tab(page: Page, name: str) -> None:
    tab = page.get_by_role("tab", name=name)
    if tab.count() == 0:
        # Fallback: Streamlit sometimes exposes tabs as buttons.
        page.get_by_role("button", name=name).first.click()
    else:
        tab.first.click()
    wait_streamlit_idle(page)


def fill_login(page: Page, username: str, password: str) -> None:
    # Prefer labels; fall back to placeholders / first text + password inputs.
    user = page.get_by_label("Username")
    if user.count() == 0:
        user = page.locator('input[type="text"]').first
    else:
        user = user.first
    pwd = page.get_by_label("Password")
    if pwd.count() == 0:
        pwd = page.locator('input[type="password"]').first
    else:
        pwd = pwd.first
    user.fill(username)
    pwd.fill(password)


def start_streamlit(port: int) -> subprocess.Popen:
    cmd = [
        sys.executable,
        "-m",
        "streamlit",
        "run",
        str(DEMO_ENTRY),
        "--server.headless=true",
        f"--server.port={port}",
        "--server.address=127.0.0.1",
        "--browser.gatherUsageStats=false",
    ]
    print(f"Starting Streamlit: {' '.join(cmd)}")
    proc = subprocess.Popen(
        cmd,
        cwd=str(ROOT),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        env={**dict(**{k: v for k, v in __import__("os").environ.items()}), "MARKAZ_DEMO_MODE": "1"},
    )
    return proc


def wait_for_server(url: str, timeout_s: float = 90.0) -> None:
    import urllib.error
    import urllib.request

    deadline = time.time() + timeout_s
    last_err = None
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=2) as resp:
                if resp.status < 500:
                    print(f"Server ready at {url}")
                    return
        except Exception as exc:  # noqa: BLE001
            last_err = exc
            time.sleep(0.8)
    raise RuntimeError(f"Streamlit did not become ready at {url}: {last_err}")


def capture_flow(page: Page, shots: ShotCounter, base_url: str) -> None:
    page.set_viewport_size({"width": 1440, "height": 900})
    page.goto(base_url, wait_until="domcontentloaded")
    wait_streamlit_idle(page)

    # 01 — Login
    shots.save(page, "login")

    fill_login(page, DEMO_USER, DEMO_PASS)
    # Demo form submit
    sign_in = page.get_by_role("button", name=re.compile(r"Sign in", re.I))
    sign_in.first.click()
    wait_streamlit_idle(page)
    page.wait_for_timeout(1200)

    # 02 — Dashboard / converter home
    page.get_by_text("Markaz to Shopify CSV Converter").first.wait_for(timeout=20000)
    shots.save(page, "dashboard-overview")

    # 03 — Shopify Converter tab (explicit)
    try:
        click_tab(page, "Shopify Converter")
    except Exception:
        pass
    shots.save(page, "shopify-converter-tab")

    # 04 — Fetch product preview
    url_box = page.get_by_label("Product URL")
    if url_box.count() == 0:
        url_box = page.locator('input[placeholder*="markaz.app"]').first
    else:
        url_box = url_box.first
    url_box.fill(DEMO_PRODUCT_URL)
    click_button(page, re.compile(r"Fetch Product Data", re.I))
    page.wait_for_timeout(800)
    shots.save(page, "product-preview-and-pricing")

    # 05 — Add to list
    add_preview = page.get_by_role("button", name=re.compile(r"Add preview to list|Add to List", re.I))
    if add_preview.count():
        add_preview.first.click()
        wait_streamlit_idle(page)
    shots.save(page, "product-list-management")

    # 06 — Publish all (demo feedback)
    publish_all = page.get_by_role("button", name=re.compile(r"Publish All to Shopify", re.I))
    if publish_all.count():
        publish_all.first.click()
        wait_streamlit_idle(page)
        page.wait_for_timeout(600)
        shots.save(page, "export-csv-and-publish")
        shots.save(page, "shopify-publish-feedback")

    # 07 — Tracked Products tab
    click_tab(page, "Tracked Products")
    shots.save(page, "tracked-products-tab")

    # 08 — Bulk actions row
    shots.save(page, "tracked-products-bulk-actions")

    # 09 — Expand first *visible* tracked product card
    # st.tabs keeps inactive-panel expanders in DOM; only click visible ones.
    opened = page.evaluate(
        """() => {
            const cards = [...document.querySelectorAll('[data-testid="stExpander"]')];
            const visible = cards.find((el) => {
                const r = el.getBoundingClientRect();
                return r.width > 0 && r.height > 0 && r.bottom > 0 && r.top < window.innerHeight + 400;
            });
            if (!visible) return false;
            visible.scrollIntoView({ block: 'center' });
            const summary = visible.querySelector('summary');
            if (summary) summary.click();
            else visible.click();
            return true;
        }"""
    )
    page.wait_for_timeout(700)
    if opened:
        shots.save(page, "tracked-product-card")
    else:
        print("  · skip tracked-product-card (no visible expander)")

    # Row action buttons (visible after expand)
    for label, name in (
        ("Publish", "tracked-card-publish-button"),
        ("Sync Stock", "tracked-card-sync-button"),
        ("Delete", "tracked-card-delete-button"),
    ):
        shots.save_locator(page.get_by_role("button", name=label, exact=True), name)

    # 10 — Bulk action button close-ups
    for label, name in (
        ("Sync Stock (Demo)", "button-sync-stock-demo"),
        ("Publish to Shopify (Demo)", "button-publish-to-shopify-demo"),
        ("Refresh Status (Demo)", "button-refresh-status-demo"),
    ):
        shots.save_locator(page.get_by_role("button", name=label), name)

    # Click Refresh once to capture post-action state
    refresh = page.get_by_role("button", name="Refresh Status (Demo)")
    if refresh.count():
        refresh.first.click()
        wait_streamlit_idle(page)
        shots.save(page, "tracked-refresh-status-result")

    # 11 — Demo banner / logout chrome
    page.evaluate("window.scrollTo(0, 0)")
    page.wait_for_timeout(200)
    shots.save(page, "demo-mode", full_page=False)
    shots.save_locator(page.get_by_role("button", name="Logout"), "logout-control")

    # 12 — Back to converter + capture Fetch / Add buttons
    click_tab(page, "Shopify Converter")
    page.evaluate("window.scrollTo(0, 0)")
    page.wait_for_timeout(300)
    shots.save(page, "add-products-single-mode")
    shots.save_locator(
        page.get_by_role("button", name=re.compile(r"Fetch Product Data", re.I)),
        "button-fetch-product-data",
    )
    shots.save_locator(
        page.get_by_role("button", name=re.compile(r"Add to List", re.I)),
        "button-add-to-list",
    )
    shots.save_locator(page.get_by_role("button", name="Logout"), "button-logout")


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Capture Markaz docs screenshots via Playwright")
    p.add_argument("--url", default=DEFAULT_URL, help="Streamlit base URL")
    p.add_argument("--port", type=int, default=8501, help="Port when auto-starting Streamlit")
    p.add_argument(
        "--no-start",
        action="store_true",
        help="Do not start Streamlit; assume --url is already running",
    )
    p.add_argument(
        "--out",
        type=Path,
        default=OUT_DIR,
        help="Output directory for PNG screenshots",
    )
    p.add_argument("--headed", action="store_true", help="Show browser window")
    return p.parse_args()


def main() -> int:
    args = parse_args()
    out_dir: Path = args.out
    out_dir.mkdir(parents=True, exist_ok=True)

    # Clear previous auto screenshots (keep folder)
    for old in out_dir.glob("*.png"):
        old.unlink()

    proc: subprocess.Popen | None = None
    base_url = args.url
    if not args.no_start:
        # Prefer URL matching chosen port
        base_url = f"http://127.0.0.1:{args.port}"
        proc = start_streamlit(args.port)
        try:
            wait_for_server(base_url)
        except Exception:
            if proc.poll() is None:
                proc.send_signal(signal.SIGTERM)
            raise

    shots = ShotCounter(out_dir)
    print(f"Capturing screenshots → {out_dir}")

    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=not args.headed)
            context = browser.new_context(
                viewport={"width": 1440, "height": 900},
                device_scale_factor=1,
            )
            page = context.new_page()
            capture_flow(page, shots, base_url)
            browser.close()
    finally:
        if proc is not None and proc.poll() is None:
            proc.send_signal(signal.SIGTERM)
            try:
                proc.wait(timeout=8)
            except subprocess.TimeoutExpired:
                proc.kill()

    print(f"\nDone. Saved {len(shots.saved)} screenshot(s):")
    for path in shots.saved:
        print(f"  - {path.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
