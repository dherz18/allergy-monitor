"""
Tests for the ASAP Illinois pollen scraper.
"""

import pytest
import requests
from unittest.mock import patch, MagicMock
from daily_alert.scraper import (
    scrape_pollen_data,
    _extract_date,
    _extract_readings,
    _find_level_near_element,
    PollenReading,
    DailyPollenReport,
    EXPECTED_CATEGORIES,
)
from bs4 import BeautifulSoup


# ── Sample HTML that mimics the ASAP Illinois page structure ──
# The real page nests: grandparent div > parent div (h4) + sibling div (level)
SAMPLE_HTML = """
<html>
<body>
<div>02/15/2026</div>
<div class="ct-div-block c-columns-5">
    <div class="ct-div-block">
        <div class="ct-div-block"><h4>Tree Pollen</h4></div>
        <div class="ct-div-block"><span>High</span></div>
    </div>
    <div class="ct-div-block">
        <div class="ct-div-block"><h4>Grass Pollen</h4></div>
        <div class="ct-div-block"><span>Low</span></div>
    </div>
    <div class="ct-div-block">
        <div class="ct-div-block"><h4>Ragweed Pollen</h4></div>
        <div class="ct-div-block"><span>Absent</span></div>
    </div>
    <div class="ct-div-block">
        <div class="ct-div-block"><h4>Total Weed Pollen</h4></div>
        <div class="ct-div-block"><span>Moderate</span></div>
    </div>
    <div class="ct-div-block">
        <div class="ct-div-block"><h4>Mold</h4></div>
        <div class="ct-div-block"><span>High</span></div>
    </div>
</div>
</body>
</html>
"""

SAMPLE_HTML_ABSENT = """
<html>
<body>
<div>02/13/2026</div>
<div class="ct-div-block c-columns-5">
    <div class="ct-div-block">
        <div class="ct-div-block"><h4>Tree Pollen</h4></div>
        <div class="ct-div-block"><span>Absent</span></div>
    </div>
    <div class="ct-div-block">
        <div class="ct-div-block"><h4>Grass Pollen</h4></div>
        <div class="ct-div-block"><span>Absent</span></div>
    </div>
    <div class="ct-div-block">
        <div class="ct-div-block"><h4>Ragweed Pollen</h4></div>
        <div class="ct-div-block"><span>Absent</span></div>
    </div>
    <div class="ct-div-block">
        <div class="ct-div-block"><h4>Total Weed Pollen</h4></div>
        <div class="ct-div-block"><span>Absent</span></div>
    </div>
    <div class="ct-div-block">
        <div class="ct-div-block"><h4>Mold</h4></div>
        <div class="ct-div-block"><span>Moderate</span></div>
    </div>
</div>
</body>
</html>
"""


class TestPollenReading:
    """Tests for the PollenReading dataclass."""

    def test_creation(self):
        reading = PollenReading(
            category="Tree Pollen",
            level="High",
            date="02/15/2026"
        )
        assert reading.category == "Tree Pollen"
        assert reading.level == "High"
        assert reading.date == "02/15/2026"
        assert reading.source == "ASAP Illinois — asapillinois.com/pollen-count/"


class TestDailyPollenReport:
    """Tests for the DailyPollenReport dataclass."""

    def test_get_reading(self):
        readings = [
            PollenReading("Tree Pollen", "High", "02/15/2026"),
            PollenReading("Grass Pollen", "Low", "02/15/2026"),
        ]
        report = DailyPollenReport(
            date="02/15/2026",
            readings=readings,
            scrape_time="2026-02-15 08:00:00"
        )
        tree = report.get_reading("Tree Pollen")
        assert tree is not None
        assert tree.level == "High"

    def test_get_reading_case_insensitive(self):
        readings = [PollenReading("Tree Pollen", "High", "02/15/2026")]
        report = DailyPollenReport("02/15/2026", readings, "2026-02-15 08:00:00")
        assert report.get_reading("tree pollen") is not None

    def test_get_reading_not_found(self):
        readings = [PollenReading("Tree Pollen", "High", "02/15/2026")]
        report = DailyPollenReport("02/15/2026", readings, "2026-02-15 08:00:00")
        assert report.get_reading("Ragweed Pollen") is None

    def test_worst_level(self):
        readings = [
            PollenReading("Tree Pollen", "High", "02/15/2026"),
            PollenReading("Grass Pollen", "Low", "02/15/2026"),
            PollenReading("Mold", "Moderate", "02/15/2026"),
        ]
        report = DailyPollenReport("02/15/2026", readings, "2026-02-15 08:00:00")
        assert report.worst_level() == "High"

    def test_worst_level_very_high(self):
        readings = [
            PollenReading("Tree Pollen", "Very High", "02/15/2026"),
            PollenReading("Grass Pollen", "High", "02/15/2026"),
        ]
        report = DailyPollenReport("02/15/2026", readings, "2026-02-15 08:00:00")
        assert report.worst_level() == "Very High"

    def test_worst_level_all_absent(self):
        readings = [
            PollenReading("Tree Pollen", "Absent", "02/15/2026"),
            PollenReading("Grass Pollen", "Absent", "02/15/2026"),
        ]
        report = DailyPollenReport("02/15/2026", readings, "2026-02-15 08:00:00")
        assert report.worst_level() == "Absent"


class TestExtractDate:
    """Tests for date extraction from HTML."""

    def test_extracts_date(self):
        soup = BeautifulSoup(SAMPLE_HTML, "html.parser")
        date = _extract_date(soup)
        assert date == "02/15/2026"

    def test_extracts_winter_date(self):
        soup = BeautifulSoup(SAMPLE_HTML_ABSENT, "html.parser")
        date = _extract_date(soup)
        assert date == "02/13/2026"


class TestExtractReadings:
    """Tests for extracting pollen readings from HTML."""

    def test_extracts_all_categories(self):
        soup = BeautifulSoup(SAMPLE_HTML, "html.parser")
        readings = _extract_readings(soup, "02/15/2026")
        categories = [r.category for r in readings]
        for expected in EXPECTED_CATEGORIES:
            assert expected in categories, f"Missing category: {expected}"

    def test_extracts_correct_levels(self):
        soup = BeautifulSoup(SAMPLE_HTML, "html.parser")
        readings = _extract_readings(soup, "02/15/2026")
        levels = {r.category: r.level for r in readings}
        assert levels["Tree Pollen"] == "High"
        assert levels["Grass Pollen"] == "Low"
        assert levels["Ragweed Pollen"] == "Absent"
        assert levels["Total Weed Pollen"] == "Moderate"
        assert levels["Mold"] == "High"

    def test_absent_readings(self):
        soup = BeautifulSoup(SAMPLE_HTML_ABSENT, "html.parser")
        readings = _extract_readings(soup, "02/13/2026")
        pollen_readings = [r for r in readings if r.category != "Mold"]
        for r in pollen_readings:
            assert r.level == "Absent"


class TestScraper:
    """Integration tests for the scraper (mocked HTTP)."""

    @patch("daily_alert.scraper.requests.get")
    def test_scrape_success(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = SAMPLE_HTML
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        report = scrape_pollen_data()
        assert report.date == "02/15/2026"
        assert len(report.readings) == 5

    @patch("daily_alert.scraper.requests.get")
    def test_scrape_connection_error(self, mock_get):
        mock_get.side_effect = requests.exceptions.ConnectionError("Network error")
        with pytest.raises(ConnectionError):
            scrape_pollen_data()
