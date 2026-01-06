# 📦 Amazon Electronics Market Intelligence Scraper

[![Python Version](https://img.shields.io/badge/python-3.14-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Framework: Playwright](https://img.shields.io/badge/framework-Playwright-green)](https://playwright.dev/)

**An industrial-grade automated system for monitoring Amazon US Best Sellers with 100% precision.**

---

##  Key Business Features

### 1. Geo-Location Standardization (Zip Code: 10001)
Unlike standard scrapers that yield localized data, this tool performs **Geo-Spoofing** to ensure the dataset reflects the competitive landscape of the core US market (New York).
* **Benefit**: Ensures 100% data consistency for professional market analysis.

### 2. Pure Organic Ranking (Anti-Ad Filtering)
The parser automatically detects and filters out **Sponsored Products (Ads)** that lack organic rank numbers.
* **Benefit**: Delivers a "Clean List" of the true Top 100 natural performers.

### 3. Full Top 100 Coverage (Multi-Page Automation)
Intelligent navigation system that handles pagination (Page 1 & 2) and dynamic "Lazy Loading" to ensure no product is missed.
* **Benefit**: Overcomes the 50-item single-page limit of basic scripts.

### 4. Advanced Stealth Engine
Uses `playwright-stealth` and custom header rotation to bypass sophisticated bot detection systems.

## Installation & Quick Start

```bash
# 1. Clone the repository
git clone [https://github.com/libenxier-beep/Amazon-Electronics-Intelligence-Scraper.git](https://github.com/libenxier-beep/Amazon-Electronics-Intelligence-Scraper.git)
cd Amazon-Electronics-Intelligence-Scraper

# 2. Setup environment and dependencies
pip install -r requirements.txt
playwright install chromium

# 3. Launch the scraper
python main.py
```

## Data Structure Output

The system generates a structured CSV file (sample_data.csv) with the following validated fields:

Name: Product Title

Price: Current listing price (handles discounts and fractional values)

Rating: Consumer feedback score (e.g., 4.7/5)

Reviews: Total review count

URL: Direct product link (cleaned of tracking parameters)

Timestamp: Exact capture time (UTC)