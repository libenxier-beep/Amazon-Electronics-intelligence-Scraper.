from __future__ import annotations

"""
Amazon Best Sellers (Electronics) Scraper

Business goal: Produce a ranked snapshot of electronics best sellers for price monitoring,
rating trend analysis, and competitive intelligence. The output is a CSV suitable for Excel.

Key features:
- Stealth/fingerprint configuration to mitigate bot detection
- Modular classes (BrowserManager, Parser, DataHandler)
- Pagination support and human-like scrolling
- Field normalization, validation, and robust selectors with fallbacks
- Retry logic for navigation/network hiccups
"""

import asyncio
from typing import List
import os
import re
import time

from playwright.async_api import Error

from browser_manager import BrowserManager
from config import ScraperConfig
from data_handler import DataHandler
from exceptions import ElementNotFound
from parser import Parser


async def dump_html(item, name: str) -> None:
    html = await item.evaluate("el => el.outerHTML")
    os.makedirs("debug_html", exist_ok=True)
    safe = re.sub(r"[^a-zA-Z0-9_-]+", "_", name)[:50]
    path = os.path.join("debug_html", f"{int(time.time())}_{safe}.html")
    with open(path, "w", encoding="utf-8") as f:
        f.write(html)


async def scrape() -> None:
    config = ScraperConfig()
    handler = DataHandler()
    parser = Parser(base_url=config.base_url)

    async with BrowserManager(config) as bm:
        page = await bm.new_page()

        # Set delivery location to NY to avoid geo-blocking
        try:
            await bm.set_delivery_location(page, "10001")
        except Exception as e:
            print(f"Warning: Failed to set delivery location: {e}")

        # Start scraping
        for pg in range(1, config.max_pages + 1):
            if pg == 1:
                 # First page is the best sellers url
                 url = config.best_sellers_url
            else:
                 # Logic for next pages - usually handled by clicking next or modifying url if known
                 # But Amazon Best Sellers usually uses pagination buttons or just page 1 and 2
                 # For simplicity, if we are on page 1, we are already there (or navigated to base above, oh wait)
                 # The previous code logic:
                 # url = f"{config.best_sellers_url}?pg={pg}" (This is often not how Amazon works exactly, but let's stick to existing logic or fix it)
                 # Actually, looking at original code, it was looping pages and doing goto.
                 # Since set_delivery_location navigates to base_url, we MUST navigate to best_sellers_url for pg=1.
                 url = f"{config.best_sellers_url}/ref=zg_bs_pg_{pg}?ie=UTF8&pg={pg}"
            
            print(f"Scraping page {pg}: {url}")
            
            ok = False
            for attempt in range(1, config.max_retries + 1):
                try:
                    await page.goto(url, wait_until="domcontentloaded", timeout=60000)
                    ok = True
                    break
                except Error as e:
                    print(f"Page load failed (attempt {attempt}): {e}")
                    if attempt < config.max_retries:
                         await bm.human_delay()
            
            if not ok:
                print(f"Skipping page {pg} after retries.")
                continue

            target_page_count = 50 if pg == 1 else min(50, 100 - len([r for r in handler.rows if r.get("name")]))
            items = []
            for scroll_attempt in range(6):
                await bm.scroll_to_bottom(page)
                try:
                    await page.wait_for_load_state("networkidle", timeout=5000)
                except Error:
                    pass
                items = await page.locator("#gridItemRoot").all()
                if len(items) >= target_page_count:
                    break
                await page.evaluate("window.scrollBy(0, -500)")
                await asyncio.sleep(2)

            if not items:
                break

            seen_urls = {r.get("url") for r in handler.rows if r.get("url")}
            for item in items[:target_page_count]:
                await bm.human_delay()
                try:
                    record = await parser.extract(item)
                except ElementNotFound:
                    continue
                except Error as e:
                    if "Target page, context or browser has been closed" in str(e):
                        print("Page closed during extraction, skipping remaining items on this page.")
                        break
                    else:
                        continue

                if handler.validate_record(record):
                    if record.get("url") not in seen_urls:
                        handler.add_record(record)
                        seen_urls.add(record.get("url"))
                if record.get("price") is None and record.get("name"):
                    await dump_html(item, record.get("name") or "item")

            total = len([r for r in handler.rows if r.get("name")])
            if total >= 100:
                break

        handler.to_csv(config.output_csv)

        sample = handler.rows[:3]
        if sample:
            print("Sample records (first 3):")
            for i, r in enumerate(sample, 1):
                print(
                    f"{i}. Name={r.get('name')} | Price={r.get('price')} | Rating={r.get('rating')} | Reviews={r.get('reviews')} | URL={r.get('url')} | Timestamp={r.get('timestamp')}"
                )


if __name__ == "__main__":
    asyncio.run(scrape())
