from __future__ import annotations

import asyncio
import random
from typing import Optional

from playwright.async_api import async_playwright, Browser, BrowserContext, Page
from playwright_stealth.stealth import Stealth
from config import ScraperConfig


class BrowserManager:
    """Manage Playwright browser, context, and stealth/fingerprint settings."""

    def __init__(self, config: ScraperConfig) -> None:
        self.config = config
        self._playwright = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None

    async def __aenter__(self) -> "BrowserManager":
        self._playwright = await async_playwright().start()
        self.browser = await self._playwright.chromium.launch(headless=False)
        ua = random.choice(self.config.user_agents)
        proxy = (
            {"server": random.choice(self.config.proxy_pool)}
            if self.config.proxy_pool
            else None
        )
        self.context = await self.browser.new_context(
            user_agent=ua,
            locale=self.config.locale,
            timezone_id=self.config.timezone_id,
            viewport={"width": self.config.viewport[0], "height": self.config.viewport[1]},
            proxy=proxy,
        )
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if self._playwright:
            await self._playwright.stop()

    async def new_page(self) -> Page:
        page = await self.context.new_page()
        await Stealth().apply_stealth_async(page)
        await page.add_init_script(
            """
            Object.defineProperty(Navigator.prototype, 'webdriver', {get: () => undefined});
            window.chrome = window.chrome || { runtime: {} };
            Object.defineProperty(navigator, 'languages', { get: () => ['en-US', 'en'] });
            Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3, 4, 5] });
            """
        )
        return page

    async def human_delay(self) -> None:
        low, high = self.config.delay_range_seconds
        await asyncio.sleep(random.uniform(low, high))

    async def human_scroll(self, page: Page) -> None:
        """Deprecated: simple random scroll."""
        for _ in range(random.randint(3, 6)):
            await page.mouse.wheel(0, random.uniform(500, 1400))
            await self.human_delay()

    async def scroll_to_bottom(self, page: Page) -> None:
        """Scrolls to bottom in steps of 1000px, waiting 1s between steps.
        Resilient to navigation: avoids relying on evaluate() when page reloads.
        """
        last_y = -1
        stable_steps = 0
        for _ in range(120):
            try:
                await page.mouse.wheel(0, 1000)
            except Exception:
                break
            await asyncio.sleep(1)
            try:
                y = await page.evaluate("window.scrollY")
                h = await page.evaluate("document.body.scrollHeight")
                ih = await page.evaluate("window.innerHeight")
                if y == last_y:
                    stable_steps += 1
                else:
                    stable_steps = 0
                    last_y = y
                if y + ih + 5 >= h:
                    break
                if stable_steps >= 3:
                    # No movement detected for several steps; assume bottom
                    break
            except Exception:
                # If execution context was destroyed due to navigation, stop scrolling
                break

    async def set_delivery_location(self, page: Page, zip_code: str = "10001") -> None:
        """Sets the delivery location on Amazon homepage to bypass geo-restrictions."""
        print("Navigating to Amazon homepage to set delivery location...")
        await page.goto(self.config.base_url, wait_until="domcontentloaded")
        
        # Click 'Deliver to' widget
        deliver_to = page.locator("#nav-global-location-popover-link")
        if await deliver_to.count() > 0:
            print("Clicking 'Deliver to'...")
            await deliver_to.click(force=True)
            
            # Wait for zip input
            zip_input = page.locator("#GLUXZipUpdateInput")
            try:
                await zip_input.wait_for(state="visible", timeout=15000)
            except Exception:
                alt = page.locator("#GLUXZipUpdateInput")
                await alt.wait_for(state="visible", timeout=10000)
            
            print(f"Entering zip code: {zip_code}...")
            await zip_input.fill(zip_code)
            
            # Click Apply
            apply_btn = page.locator("#GLUXZipUpdate input")  # or button
            # Sometimes it's a span or input type=submit
            if await apply_btn.count() == 0:
                apply_btn = page.locator("span[data-action='GLUXZipUpdate']")
            
            await apply_btn.click()
            await asyncio.sleep(1)
            
            # Confirm 'Done' or 'Continue' if a second popup appears
            # Usually after zip update, there is a 'Continue' or 'Done' button to refresh
            # Or the page reloads automatically.
            # We look for "glowDoneButton" or similar.
            done_btn = page.locator("button[name='glowDoneButton']")
            if await done_btn.count() > 0:
                print("Confirming location update...")
                await done_btn.click()
                # Wait for reload
                await page.wait_for_load_state("domcontentloaded")
            else:
                # Sometimes it asks for confirmation in a different way or auto reloads
                # We wait a bit to ensure it processes
                await asyncio.sleep(2)
                # Check if we need to reload manually to see effect? 
                # Usually Amazon reloads itself.
                pass
            print("Delivery location set.")
        else:
            print("Could not find 'Deliver to' widget. Skipping location set.")

