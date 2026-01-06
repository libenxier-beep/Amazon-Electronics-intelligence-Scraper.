from __future__ import annotations

import re
from typing import Dict, Optional

from playwright.async_api import Locator

from exceptions import ElementNotFound


class Parser:
    """Extract product fields from a Best Sellers grid item."""

    def __init__(self, base_url: str) -> None:
        self.base_url = base_url.rstrip("/")

    @staticmethod
    def _normalize_text(raw: Optional[str]) -> str:
        if not raw:
            return ""
        return re.sub(r"\s+", " ", raw).strip()

    @staticmethod
    def _parse_price(raw: Optional[str]) -> Optional[float]:
        if not raw:
            return None
        cleaned = raw.replace("\u00a0", " ")
        m = re.search(r"([\d,.]+)", cleaned)
        if not m:
            return None
        num = m.group(1).replace(",", "")
        try:
            return float(num)
        except ValueError:
            return None

    @staticmethod
    def _parse_rating(raw: Optional[str]) -> Optional[float]:
        if not raw:
            return None
        m = re.search(r"([0-9]+(?:\.[0-9])?)\s*out of\s*5", raw, flags=re.I)
        if not m:
            # Fallback: extract first float
            m2 = re.search(r"([0-9]+(?:\.[0-9])?)", raw)
            if not m2:
                return None
            try:
                return round(float(m2.group(1)), 1)
            except ValueError:
                return None
        try:
            return round(float(m.group(1)), 1)
        except ValueError:
            return None

    @staticmethod
    def _parse_reviews(raw: Optional[str]) -> Optional[int]:
        if not raw:
            return None
        m = re.search(r"([0-9,]+)", raw)
        if not m:
            return None
        try:
            return int(m.group(1).replace(",", ""))
        except ValueError:
            return None

    async def extract(self, item: Locator) -> Dict[str, Optional[str]]:
        # Product URL
        url = None
        for selector in [
            'a.a-link-normal.aok-block[href]',
            'a.a-link-normal[href*="/dp/"]',
            'a.a-link-normal[href*="/gp/"]',
            'a[href^="/dp/"]',
            'a[href^="/gp/"]',
        ]:
            locator = item.locator(selector).first
            if await locator.count() > 0:
                href = await locator.get_attribute("href")
                if href:
                    if href.startswith("http"):
                        url = href
                    else:
                        url = f"{self.base_url}{href}"
                    break
        if not url:
            raise ElementNotFound("Product URL not found")

        # Product Name
        name = ""
        for selector in [
            'div._cDEzb_p13n-sc-css-line-clamp-3_g3dy1',
            'a.a-link-normal[href] .p13n-sc-truncated',
            'a.a-link-normal[href] span[aria-hidden="true"]',
            '.a-size-medium.a-color-base.a-text-normal',
            '.a-link-normal .a-size-base-plus',
        ]:
            locator = item.locator(selector).first
            if await locator.count() > 0:
                name = self._normalize_text(await locator.text_content())
                if name:
                    break

        price = await self.get_price(item)

        # Original price (if present)
        orig_raw = None
        for selector in [
            'span.a-price.a-text-price span.a-offscreen',
            'span.a-text-price span.a-offscreen',
        ]:
            locator = item.locator(selector).first
            if await locator.count() > 0:
                orig_raw = await locator.text_content()
                if orig_raw:
                    break
        original_price = self._parse_price(self._normalize_text(orig_raw))

        # Rating
        rating_raw = None
        for selector in [
            'a.a-link-normal[aria-label*="out of 5 stars"]',
            'span[aria-label*="out of 5 stars"]',
            'i.a-icon-star-small span.a-icon-alt',
            'i.a-icon-star span.a-icon-alt',
        ]:
            locator = item.locator(selector).first
            if await locator.count() > 0:
                rating_raw = await locator.get_attribute("aria-label")
                if not rating_raw:
                    rating_raw = await locator.text_content()
                if rating_raw:
                    break
        rating = self._parse_rating(self._normalize_text(rating_raw))

        # Review count
        reviews_raw = None
        for selector in [
            'a[href*="#customerReviews"]',
            'a.a-link-normal .a-size-small',
            'span[aria-label$="ratings"]',
            'span.a-size-base.s-underline-text',
        ]:
            locator = item.locator(selector).first
            if await locator.count() > 0:
                reviews_raw = await locator.text_content()
                if reviews_raw:
                    break
        reviews = self._parse_reviews(self._normalize_text(reviews_raw))

        item_type = "Sponsored" if await self.is_sponsored(item) else "Organic"
        return {
            "name": name or None,
            "price": price,
            "original_price": original_price,
            "rating": rating,
            "reviews": reviews,
            "url": url,
            "item_type": item_type,
        }

    async def get_price(self, item: Locator) -> Optional[float]:
        a = item.locator('span.aok-offscreen').first
        if await a.count() > 0:
            raw = await a.text_content()
            v = self._parse_price(self._normalize_text(raw))
            if v is not None:
                return v
        c = item.locator('span.a-price').first
        if await c.count() > 0:
            whole_loc = c.locator('span.a-price-whole').first
            frac_loc = c.locator('span.a-price-fraction').first
            whole = await whole_loc.text_content() if await whole_loc.count() > 0 else None
            frac = await frac_loc.text_content() if await frac_loc.count() > 0 else None
            if whole or frac:
                w = None
                f = None
                if whole:
                    m1 = re.search(r"[\d,]+", whole)
                    if m1:
                        w = m1.group(0).replace(',', '')
                if frac:
                    m2 = re.search(r"\d{1,2}", frac)
                    if m2:
                        f = m2.group(0)
                if w and f:
                    try:
                        return float(f"{w}.{f}")
                    except ValueError:
                        pass
                if w and not f:
                    try:
                        return float(w)
                    except ValueError:
                        pass
        text = await item.inner_text()
        text = self._normalize_text(text)
        # Fallback: look for $ pattern to avoid picking up rank numbers (e.g. "1", "2")
        m = re.search(r"\$([0-9,.]+)", text)
        if m:
            return self._parse_price(m.group(1))
        return None

    async def is_sponsored(self, item: Locator) -> bool:
        l1 = item.get_by_text("Sponsored", exact=False)
        if await l1.count() > 0:
            return True
        l2 = item.locator('[aria-label="Sponsored"]')
        return await l2.count() > 0

