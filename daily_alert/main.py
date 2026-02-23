"""
Daily Allergy Alert — Main Entry Point

This script:
1. Checks if we're in allergy season (April–October)
2. Scrapes today's pollen data from ASAP Illinois
3. Fetches current Chicago weather from Open-Meteo
4. Builds a styled HTML email
5. Sends it via Gmail SMTP

Usage:
    python main.py              # Normal run (respects season window)
    python main.py --test       # Force run regardless of season (for testing)
    python main.py --preview    # Generate email HTML and save locally (no send)

Schedule:
    Runs daily via GitHub Actions at 8:00 AM CT (after ASAP updates at 7:30 AM).
    ASAP Illinois collects data Monday–Friday, April through October only.
"""

import argparse
import sys
import os
import requests
from datetime import datetime

# Add parent directory to path for imports when running directly
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from daily_alert.scraper import scrape_pollen_data
    from daily_alert.email_builder import build_email_html, build_email_subject
    from daily_alert.email_sender import send_alert_email
except ImportError:
    from scraper import scrape_pollen_data
    from email_builder import build_email_html, build_email_subject
    from email_sender import send_alert_email


# ── Allergy season: April (4) through October (10) ──
SEASON_START_MONTH = 4
SEASON_END_MONTH = 10

# ── Chicago coordinates for weather ──
CHICAGO_LAT = 41.88
CHICAGO_LON = -87.63


def is_allergy_season() -> bool:
    """Check if the current date falls within allergy season (Apr–Oct)."""
    month = datetime.now().month
    return SEASON_START_MONTH <= month <= SEASON_END_MONTH


def is_weekday() -> bool:
    """Check if today is a weekday (ASAP doesn't update on weekends)."""
    return datetime.now().weekday() < 5  # Mon=0 ... Fri=4


def fetch_chicago_weather() -> dict | None:
    """
    Fetch current Chicago weather from Open-Meteo (free, no API key).

    Returns:
        Dict with temperature, humidity, wind_speed, precipitation
        or None if the request fails.
    """
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": CHICAGO_LAT,
        "longitude": CHICAGO_LON,
        "current": "temperature_2m,relative_humidity_2m,wind_speed_10m,precipitation",
        "temperature_unit": "fahrenheit",
        "wind_speed_unit": "mph",
        "timezone": "America/Chicago",
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()["current"]

        return {
            "temperature": round(data.get("temperature_2m", 0)),
            "humidity": round(data.get("relative_humidity_2m", 0)),
            "wind_speed": round(data.get("wind_speed_10m", 0)),
            "precipitation": round(data.get("precipitation", 0), 1),
        }
    except Exception as e:
        print(f"  ⚠️  Could not fetch weather: {e}")
        return None


def run(test_mode: bool = False, preview_mode: bool = False) -> None:
    """
    Main execution flow.

    Args:
        test_mode: If True, skip season/weekday checks.
        preview_mode: If True, save HTML to file instead of sending email.
    """
    print("=" * 50)
    print("🌿 Chicago Daily Allergy Alert")
    print(f"📅 {datetime.now().strftime('%A, %B %d, %Y %I:%M %p')}")
    print("=" * 50)

    # ── Season check ──
    if not test_mode:
        if not is_allergy_season():
            print(f"\n❄️  Off-season (current month: {datetime.now().strftime('%B')})")
            print(f"   ASAP Illinois collects data April–October only.")
            print(f"   Use --test flag to force a run for testing.")
            return

        if not is_weekday():
            print(f"\n📅 Weekend — ASAP Illinois doesn't update on weekends.")
            print(f"   Use --test flag to force a run for testing.")
            return
    else:
        print("\n🧪 TEST MODE — skipping season/weekday checks")

    # ── Step 1: Scrape pollen data ──
    print("\n📡 Step 1: Scraping ASAP Illinois pollen data...")
    try:
        report = scrape_pollen_data()
        print(f"  ✅ Got {len(report.readings)} readings for {report.date}")
        for reading in report.readings:
            print(f"     {reading.category:20s} → {reading.level}")
    except ConnectionError as e:
        print(f"  ❌ Connection error: {e}")
        sys.exit(1)
    except ValueError as e:
        print(f"  ❌ Parse error: {e}")
        sys.exit(1)

    # ── Step 2: Fetch weather ──
    print("\n🌤️  Step 2: Fetching Chicago weather...")
    weather = fetch_chicago_weather()
    if weather:
        print(f"  ✅ {weather['temperature']}°F, {weather['humidity']}% humidity, "
              f"{weather['wind_speed']} mph wind")

    # ── Step 3: Build email ──
    print("\n✉️  Step 3: Building email...")
    html = build_email_html(report, weather)
    subject = build_email_subject(report)
    print(f"  ✅ Subject: {subject}")

    # ── Step 4: Send or preview ──
    if preview_mode:
        preview_path = os.path.join(os.path.dirname(__file__), "preview.html")
        with open(preview_path, "w") as f:
            f.write(html)
        print(f"\n👁️  Preview saved to: {preview_path}")
        print("   Open in a browser to see the email.")
    else:
        print("\n📨 Step 4: Sending email...")
        success = send_alert_email(subject, html)
        if success:
            print(f"\n🎉 Daily allergy alert sent successfully!")
        else:
            print(f"\n⚠️  Email failed to send. Check your .env configuration.")
            sys.exit(1)

    print("\n" + "=" * 50)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Chicago Daily Allergy Alert — Scrape & Email",
        epilog="ASAP Illinois provides data Mon–Fri, April–October."
    )
    parser.add_argument(
        "--test",
        action="store_true",
        help="Force run regardless of season/weekday (for testing the scraper)"
    )
    parser.add_argument(
        "--preview",
        action="store_true",
        help="Save email as HTML file instead of sending (no SMTP needed)"
    )

    args = parser.parse_args()
    run(test_mode=args.test, preview_mode=args.preview)
