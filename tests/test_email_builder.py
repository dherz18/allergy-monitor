"""
Tests for the email builder.
"""

import pytest
from daily_alert.scraper import PollenReading, DailyPollenReport
from daily_alert.email_builder import (
    build_email_html,
    build_email_subject,
    SEVERITY_COLORS,
    RECOMMENDATIONS,
)


def _make_report(levels: dict[str, str], date: str = "06/15/2026") -> DailyPollenReport:
    """Helper to create a DailyPollenReport from a dict of category → level."""
    readings = [
        PollenReading(category=cat, level=lvl, date=date)
        for cat, lvl in levels.items()
    ]
    return DailyPollenReport(date=date, readings=readings, scrape_time="2026-06-15 08:00:00")


class TestBuildEmailHtml:
    """Tests for HTML email generation."""

    def test_returns_html_string(self):
        report = _make_report({"Tree Pollen": "High", "Grass Pollen": "Low"})
        html = build_email_html(report)
        assert "<html>" in html
        assert "</html>" in html

    def test_includes_date(self):
        report = _make_report({"Tree Pollen": "Moderate"}, date="07/04/2026")
        html = build_email_html(report)
        assert "07/04/2026" in html

    def test_includes_all_categories(self):
        report = _make_report({
            "Tree Pollen": "High",
            "Grass Pollen": "Moderate",
            "Ragweed Pollen": "Low",
            "Total Weed Pollen": "Absent",
            "Mold": "Moderate",
        })
        html = build_email_html(report)
        assert "Tree Pollen" in html
        assert "Grass Pollen" in html
        assert "Ragweed Pollen" in html
        assert "Total Weed Pollen" in html
        assert "Mold" in html

    def test_includes_severity_levels(self):
        report = _make_report({"Tree Pollen": "Very High"})
        html = build_email_html(report)
        assert "Very High" in html

    def test_includes_recommendation(self):
        report = _make_report({"Tree Pollen": "High"})
        html = build_email_html(report)
        assert "Recommendation" in html
        assert "allergy medication" in html.lower() or "antihistamine" in html.lower()

    def test_includes_weather_when_provided(self):
        report = _make_report({"Tree Pollen": "Moderate"})
        weather = {
            "temperature": 72,
            "humidity": 65,
            "wind_speed": 8,
            "precipitation": 0.0,
        }
        html = build_email_html(report, weather=weather)
        assert "72" in html
        assert "65" in html
        assert "Chicago Weather" in html

    def test_no_weather_section_when_none(self):
        report = _make_report({"Tree Pollen": "Moderate"})
        html = build_email_html(report, weather=None)
        assert "Chicago Weather" not in html

    def test_includes_aaaai_scale(self):
        report = _make_report({"Tree Pollen": "Low"})
        html = build_email_html(report)
        assert "AAAAI" in html

    def test_includes_data_source_attribution(self):
        report = _make_report({"Tree Pollen": "Low"})
        html = build_email_html(report)
        assert "ASAP Illinois" in html
        assert "Open-Meteo" in html


class TestBuildEmailSubject:
    """Tests for email subject line generation."""

    def test_subject_includes_date(self):
        report = _make_report({"Tree Pollen": "High"}, date="06/15/2026")
        subject = build_email_subject(report)
        assert "06/15/2026" in subject

    def test_subject_includes_severity(self):
        report = _make_report({"Tree Pollen": "High", "Grass Pollen": "Low"})
        subject = build_email_subject(report)
        assert "High" in subject

    def test_subject_includes_chicago(self):
        report = _make_report({"Tree Pollen": "Low"})
        subject = build_email_subject(report)
        assert "Chicago" in subject

    def test_subject_very_high(self):
        report = _make_report({"Tree Pollen": "Very High"})
        subject = build_email_subject(report)
        assert "Very High" in subject
        assert "🔴" in subject


class TestSeverityColors:
    """Tests for severity color configuration."""

    def test_all_levels_have_colors(self):
        expected_levels = ["Absent", "Low", "Moderate", "High", "Very High"]
        for level in expected_levels:
            assert level in SEVERITY_COLORS
            assert "bg" in SEVERITY_COLORS[level]
            assert "text" in SEVERITY_COLORS[level]
            assert "icon" in SEVERITY_COLORS[level]


class TestRecommendations:
    """Tests for recommendation text."""

    def test_all_levels_have_recommendations(self):
        expected_levels = ["Absent", "Low", "Moderate", "High", "Very High"]
        for level in expected_levels:
            assert level in RECOMMENDATIONS
            assert len(RECOMMENDATIONS[level]) > 10  # Not empty strings
