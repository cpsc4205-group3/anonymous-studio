"""
Usage: python screenshot.py [page] [action]
  python screenshot.py pipeline
  python screenshot.py pipeline click_row   # clicks first table row
  python screenshot.py dashboard
"""
import sys, time
from playwright.sync_api import sync_playwright

PAGE = sys.argv[1] if len(sys.argv) > 1 else "dashboard"
ACTION = sys.argv[2] if len(sys.argv) > 2 else None
URL = f"http://127.0.0.1:5000/{PAGE}"

with sync_playwright() as p:
    browser = p.chromium.launch()
    pg = browser.new_page(viewport={"width": 1400, "height": 900})
    pg.goto(URL, wait_until="domcontentloaded")
    time.sleep(5)  # let Taipy websocket connect and render

    if ACTION == "click_row":
        try:
            pg.locator("table tbody tr").first.click(timeout=10000)
            time.sleep(3)
        except Exception as e:
            print(f"Click failed: {e}")

    out = f"screenshot_{PAGE}{'_' + ACTION if ACTION else ''}.png"
    pg.screenshot(path=out, full_page=False)
    browser.close()
    print(f"Saved: {out}")
