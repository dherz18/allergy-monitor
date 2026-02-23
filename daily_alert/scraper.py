"""
Scraper for ASAP Illinois (asapillinois.com/pollen-count/)

The Allergy, Sinus & Asthma Professionals (ASAP) of Illinois provide
the official Chicago-area pollen and mold readings. Samples are collected
from the roof of the Gottlieb Professional Building and counted under a
microscope each weekday morning.

Data is updated Monday–Friday by 7:30 AM, April through October.
"""

import requests
from bs4 import BeautifulSoup
from dataclasses import dataclass
from datetime import datetime


@dataclass
class PollenReading:
    """A single pollen/mold reading from ASAP Illinois."""
    category: str       # e.g. "Tree Pollen", "Grass Pollen", etc.
    level: str          # e.g. "Absent", "Low", "Moderate", "High", "Very High"
    date: str           # e.g. "02/12/2026"
    source: str = "ASAP Illinois — asapillinois.com/pollen-count/"


@dataclass
class DailyPollenReport:
    """All pollen readings for a single day."""
    date: str
    readings: list[PollenReading]
    scrape_time: str

    def get_reading(self, category: str) -> PollenReading | None:
        """Get a specific reading by category name."""
        for reading in self.readings:
            if reading.category.lower() == category.lower():
                return reading
        return None

    def worst_level(self) -> str:
        """Return the worst severity level across all readings."""
        severity_rank = {"Absent": 0, "Low": 1, "Moderate": 2, "High": 3, "Very High": 4}
        worst = max(self.readings, key=lambda r: severity_rank.get(r.level, -1))
        return worst.level


URL = "https://asapillinois.com/pollen-count/"

# The categories we expect to find on the page
EXPECTED_CATEGORIES = [
    "Tree Pollen",
    "Grass Pollen",
    "Ragweed Pollen",
    "Total Weed Pollen",
    "Mold",
]


def scrape_pollen_data() -> DailyPollenReport:
    """
    Scrape today's pollen readings from ASAP Illinois.

    Returns:
        DailyPollenReport with all available readings.

    Raises:
        ConnectionError: If the website is unreachable.
        ValueError: If the page structure has changed and can't be parsed.
    """
    headers = {
        "User-Agent": (
            "AllergyMonitor/1.0 (personal portfolio project; "
            "not for commercial use; contact: github.com/daveherzau)"
        )
    }

    try:
        response = requests.get(URL, headers=headers, timeout=15)
        response.raise_for_status()
    except requests.RequestException as e:
        raise ConnectionError(f"Failed to reach {URL}: {e}")

    soup = BeautifulSoup(response.text, "html.parser")

    # Extract the date from the page
    report_date = _extract_date(soup)

    # Extract each pollen/mold reading
    readings = _extract_readings(soup, report_date)

    if not readings:
        raise ValueError(
            "No pollen readings found on the page. "
            "The site structure may have changed."
        )

    return DailyPollenReport(
        date=report_date,
        readings=readings,
        scrape_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    )


def _extract_date(soup: BeautifulSoup) -> str:
    """Extract the report date from the page."""
    # The date appears as text on the page (e.g., "02/12/2026")
    # Look for a date pattern in the page content
    import re

    text = soup.get_text()
    # Match MM/DD/YYYY pattern
    date_match = re.search(r"(\d{2}/\d{2}/\d{4})", text)
    if date_match:
        return date_match.group(1)

    return datetime.now().strftime("%m/%d/%Y")


def _extract_readings(soup: BeautifulSoup, report_date: str) -> list[PollenReading]:
    """Extract all pollen/mold readings from the page.

    The ASAP Illinois page structure (as of 2025–2026):
    - Each category is an <h4> inside a <div class="ct-div-block">
    - The h4's parent div is wrapped in a grandparent div that also
      contains a sibling div with the severity level (e.g. "Absent", "High")
    - All 5 categories sit inside a great-grandparent grid div
    """
    readings = []

    h4_tags = soup.find_all("h4")
    seen_categories = set()

    for h4 in h4_tags:
        category_text = h4.get_text(strip=True)

        # Check if this h4 matches one of our expected categories
        matched_category = None
        for expected in EXPECTED_CATEGORIES:
            if expected.lower() == category_text.lower():
                # Exact match first (prefer "Tree Pollen" over "Tree")
                matched_category = expected
                break

        if not matched_category:
            for expected in EXPECTED_CATEGORIES:
                if expected.lower() in category_text.lower():
                    matched_category = expected
                    break

        if not matched_category:
            continue

        # Skip duplicates — the page has both short ("Tree") and
        # long ("Tree Pollen") forms for some categories
        if matched_category in seen_categories:
            continue
        seen_categories.add(matched_category)

        # The level is in a sibling div of the h4's parent div,
        # both wrapped in a grandparent div
        level = _find_level_near_element(h4)

        if level:
            readings.append(PollenReading(
                category=matched_category,
                level=level,
                date=report_date,
            ))

    return readings


def _find_level_near_element(element) -> str | None:
    """
    Find the severity level text near an h4 element.

    Page structure:
        <div class="ct-div-block">        ← grandparent
            <div class="ct-div-block">    ← parent (contains the h4)
                <h4>Tree Pollen</h4>
            </div>
            <div class="ct-div-block">    ← sibling div with the level
                <span>Absent</span>
            </div>
        </div>
    """
    valid_levels = ["Very High", "High", "Moderate", "Low", "Absent"]

    # Go up to grandparent: h4 → parent div → grandparent div
    parent = element.parent
    grandparent = parent.parent if parent else None

    if grandparent:
        # Look at the grandparent's text — it contains "Category | Level"
        text = grandparent.get_text(separator=" ", strip=True)
        for level in valid_levels:
            if level in text:
                return level

    return None


if __name__ == "__main__":
    # Quick test
    print("🔍 Scraping ASAP Illinois pollen data...\n")
    try:
        report = scrape_pollen_data()
        print(f"📅 Report date: {report.date}")
        print(f"⏰ Scraped at:  {report.scrape_time}\n")
        for reading in report.readings:
            print(f"  {reading.category:20s} → {reading.level}")
        print(f"\n⚠️  Worst level today: {report.worst_level()}")
    except Exception as e:
        print(f"❌ Error: {e}")
