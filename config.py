from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, Tuple


@dataclass
class ScraperConfig:
    """Configuration for Amazon Best Sellers scraping in Electronics."""

    best_sellers_url: str = (
        "https://www.amazon.com/Best-Sellers-Electronics/zgbs/electronics"
    )
    base_url: str = "https://www.amazon.com"
    max_pages: int = 3
    max_retries: int = 3
    delay_range_seconds: Tuple[float, float] = (1.0, 3.0)
    output_csv: str = "amazon_electronics_ranking.csv"
    locale: str = "en-US"
    timezone_id: str = "America/New_York"
    viewport: Tuple[int, int] = (1366, 768)
    proxy_pool: List[str] = field(default_factory=list)
    user_agents: List[str] = field(
        default_factory=lambda: [
            # Chrome
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            # Firefox
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0",
            # Safari (Mac)
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
        ]
    )

