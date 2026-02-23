"""
Builds a styled HTML email for the daily Chicago allergy alert.

The email includes:
- Overall allergy severity with color-coded indicator
- Breakdown by category (Tree, Grass, Ragweed, Weed, Mold)
- Current weather context for Chicago
- AAAAI severity scale reference
- Actionable recommendation

Inspired by the Kleenex Pollen Forecast design.
"""

try:
    from daily_alert.scraper import DailyPollenReport
except ImportError:
    from scraper import DailyPollenReport


# ── Severity color mapping ──
SEVERITY_COLORS = {
    "Absent":    {"bg": "#e8f5e9", "text": "#388e3c", "icon": "✅"},
    "Low":       {"bg": "#e8f5e9", "text": "#388e3c", "icon": "🟢"},
    "Moderate":  {"bg": "#fff8e1", "text": "#f9a825", "icon": "🟡"},
    "High":      {"bg": "#fff3e0", "text": "#e65100", "icon": "🟠"},
    "Very High": {"bg": "#ffebee", "text": "#c62828", "icon": "🔴"},
}

# ── Recommendations based on worst severity ──
RECOMMENDATIONS = {
    "Absent": "Air quality is great for allergy sufferers. Enjoy the outdoors!",
    "Low": "Pollen levels are low today. A good day to be outside, but sensitive individuals may want to keep antihistamines handy.",
    "Moderate": "Moderate pollen levels — consider taking an antihistamine (Claritin, Zyrtec, etc.) if you're sensitive. Keep windows closed.",
    "High": "High pollen today! Take your allergy medication before heading out. Avoid prolonged outdoor activity, especially in the morning. Shower after being outside.",
    "Very High": "⚠️ Very high pollen! Stay indoors if possible. Take allergy medication. Keep all windows closed. Use air purifiers. Shower and change clothes after any outdoor exposure.",
}


def build_email_html(report: DailyPollenReport, weather: dict | None = None) -> str:
    """
    Build a styled HTML email from a pollen report.

    Args:
        report: Today's scraped pollen data.
        weather: Optional dict with keys like 'temperature', 'humidity',
                 'wind_speed', 'condition'.

    Returns:
        Complete HTML string for the email body.
    """
    worst = report.worst_level()
    worst_style = SEVERITY_COLORS.get(worst, SEVERITY_COLORS["Absent"])
    recommendation = RECOMMENDATIONS.get(worst, "")

    # Build the category rows
    category_rows = ""
    for reading in report.readings:
        style = SEVERITY_COLORS.get(reading.level, SEVERITY_COLORS["Absent"])
        category_rows += f"""
        <tr>
            <td style="padding: 12px 16px; font-size: 15px; border-bottom: 1px solid #eee;">
                {reading.category}
            </td>
            <td style="padding: 12px 16px; font-size: 15px; font-weight: bold;
                        color: {style['text']}; border-bottom: 1px solid #eee; text-align: center;">
                {style['icon']} {reading.level}
            </td>
        </tr>
        """

    # Weather section (optional)
    weather_section = ""
    if weather:
        weather_section = f"""
        <div style="background: #e3f2fd; border-radius: 8px; padding: 16px; margin: 20px 0;">
            <h3 style="margin: 0 0 8px 0; color: #1565c0; font-size: 16px;">
                🌤️ Chicago Weather
            </h3>
            <table style="width: 100%;">
                <tr>
                    <td style="padding: 4px 0;">🌡️ Temperature: <strong>{weather.get('temperature', 'N/A')}°F</strong></td>
                    <td style="padding: 4px 0;">💧 Humidity: <strong>{weather.get('humidity', 'N/A')}%</strong></td>
                </tr>
                <tr>
                    <td style="padding: 4px 0;">💨 Wind: <strong>{weather.get('wind_speed', 'N/A')} mph</strong></td>
                    <td style="padding: 4px 0;">🌧️ Precip: <strong>{weather.get('precipitation', 'N/A')} mm</strong></td>
                </tr>
            </table>
        </div>
        """

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
    </head>
    <body style="margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont,
                 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
                 background-color: #f5f5f5;">

        <!-- Container -->
        <div style="max-width: 600px; margin: 0 auto; background: white;
                    border-radius: 12px; overflow: hidden; margin-top: 20px;
                    box-shadow: 0 2px 8px rgba(0,0,0,0.1);">

            <!-- Header -->
            <div style="background: linear-gradient(135deg, #1b5e20, #43a047);
                        padding: 24px; text-align: center;">
                <h1 style="color: white; margin: 0; font-size: 22px;">
                    🌿 Chicago Daily Allergy Report
                </h1>
                <p style="color: rgba(255,255,255,0.85); margin: 8px 0 0 0; font-size: 14px;">
                    {report.date} | Chicagoland Area
                </p>
            </div>

            <!-- Overall Severity -->
            <div style="text-align: center; padding: 24px;
                        background: {worst_style['bg']};">
                <p style="margin: 0 0 8px 0; font-size: 14px; color: #666;
                          text-transform: uppercase; letter-spacing: 1px;">
                    Overall Allergy Level
                </p>
                <h2 style="margin: 0; font-size: 36px; color: {worst_style['text']};">
                    {worst_style['icon']} {worst}
                </h2>
            </div>

            <!-- Category Breakdown -->
            <div style="padding: 0 20px;">
                <h3 style="color: #333; font-size: 16px; margin: 20px 0 12px 0;
                           border-bottom: 2px solid #eee; padding-bottom: 8px;">
                    📊 Breakdown by Category
                </h3>
                <table style="width: 100%; border-collapse: collapse;">
                    <tr style="background: #fafafa;">
                        <th style="padding: 10px 16px; text-align: left; font-size: 13px;
                                   color: #888; text-transform: uppercase; letter-spacing: 0.5px;">
                            Allergen
                        </th>
                        <th style="padding: 10px 16px; text-align: center; font-size: 13px;
                                   color: #888; text-transform: uppercase; letter-spacing: 0.5px;">
                            Level
                        </th>
                    </tr>
                    {category_rows}
                </table>
            </div>

            {weather_section}

            <!-- Recommendation -->
            <div style="margin: 20px; padding: 16px; background: #f5f5f5;
                        border-left: 4px solid {worst_style['text']};
                        border-radius: 0 8px 8px 0;">
                <p style="margin: 0; font-size: 14px; color: #444; line-height: 1.5;">
                    <strong>💊 Recommendation:</strong> {recommendation}
                </p>
            </div>

            <!-- AAAAI Reference Scale -->
            <div style="padding: 0 20px 20px 20px;">
                <details style="cursor: pointer;">
                    <summary style="font-size: 13px; color: #888; padding: 8px 0;">
                        📏 AAAAI Severity Scale Reference
                    </summary>
                    <table style="width: 100%; border-collapse: collapse; margin-top: 8px;
                                  font-size: 12px;">
                        <tr style="background: #fafafa;">
                            <th style="padding: 6px 8px; text-align: left;">Level</th>
                            <th style="padding: 6px 8px; text-align: center;">Tree (gr/m³)</th>
                            <th style="padding: 6px 8px; text-align: center;">Grass (gr/m³)</th>
                            <th style="padding: 6px 8px; text-align: center;">Weed (gr/m³)</th>
                        </tr>
                        <tr><td style="padding: 6px 8px;">🟢 Low</td>
                            <td style="padding: 6px 8px; text-align: center;">1–14</td>
                            <td style="padding: 6px 8px; text-align: center;">1–4</td>
                            <td style="padding: 6px 8px; text-align: center;">1–9</td></tr>
                        <tr style="background: #fafafa;">
                            <td style="padding: 6px 8px;">🟡 Moderate</td>
                            <td style="padding: 6px 8px; text-align: center;">15–89</td>
                            <td style="padding: 6px 8px; text-align: center;">5–19</td>
                            <td style="padding: 6px 8px; text-align: center;">10–49</td></tr>
                        <tr><td style="padding: 6px 8px;">🟠 High</td>
                            <td style="padding: 6px 8px; text-align: center;">90–1,499</td>
                            <td style="padding: 6px 8px; text-align: center;">20–199</td>
                            <td style="padding: 6px 8px; text-align: center;">50–499</td></tr>
                        <tr style="background: #fafafa;">
                            <td style="padding: 6px 8px;">🔴 Very High</td>
                            <td style="padding: 6px 8px; text-align: center;">≥1,500</td>
                            <td style="padding: 6px 8px; text-align: center;">≥200</td>
                            <td style="padding: 6px 8px; text-align: center;">≥500</td></tr>
                    </table>
                    <p style="font-size: 11px; color: #aaa; margin: 6px 0 0 0;">
                        Source: American Academy of Allergy, Asthma & Immunology (AAAAI)
                    </p>
                </details>
            </div>

            <!-- Footer -->
            <div style="background: #fafafa; padding: 16px; text-align: center;
                        border-top: 1px solid #eee;">
                <p style="margin: 0; font-size: 11px; color: #aaa; line-height: 1.6;">
                    Pollen data: ASAP Illinois — asapillinois.com/pollen-count/<br>
                    Collected Mon–Fri, April–October by certified allergists<br>
                    Weather data: Open-Meteo API (open-meteo.com)
                </p>
            </div>
        </div>
    </body>
    </html>
    """
    return html


def build_email_subject(report: DailyPollenReport) -> str:
    """Build the email subject line."""
    worst = report.worst_level()
    icon = SEVERITY_COLORS.get(worst, {}).get("icon", "")
    return f"{icon} Chicago Allergy Alert ({report.date}): {worst}"
