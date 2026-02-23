# 🌿 Allergy Monitor

**A data-driven seasonal allergy analysis and daily alert system.**

Combines 5 years of historical pollen data analysis (2021–2025) with a daily web-scraping pipeline that emails you Chicago's allergen levels every morning during allergy season — so you know whether to take a Claritin before heading out.

![Python](https://img.shields.io/badge/Python-3.11-blue?logo=python)
![License](https://img.shields.io/badge/License-MIT-green)
![Data](https://img.shields.io/badge/Data-2021--2025-orange)

---

## 📋 What This Project Does

### Phase 1: Historical Pollen Analysis

A Jupyter notebook that pulls **5 years of hourly pollen data** (2021–2025) from the CAMS European pollen model and performs deep analysis:

- 📊 Monthly pollen trends per species (Birch, Grass, Ragweed, Alder, Mugwort)
- 📈 Year-over-year trend analysis with statistical significance testing
- 🌡️ Weather ↔ pollen correlation (temperature, humidity, wind, rain vs. pollen counts)
- 🗓️ Seasonal allergy calendar heatmap
- 🌧️ Rainfall "day-after" effect analysis
- ⏰ Hourly patterns — when is pollen worst during the day?

### Phase 2: Daily Chicago Allergy Email

An automated pipeline that runs every weekday morning during allergy season:

1. **Scrapes** today's pollen data from [ASAP Illinois](https://asapillinois.com/pollen-count/) — the official Chicago-area pollen count
2. **Fetches** current Chicago weather from Open-Meteo
3. **Builds** a styled HTML email with severity levels, weather context, and recommendations
4. **Sends** it to your inbox before you start your day

---

## 🔬 Why Berlin for the Analysis?

You might wonder why the historical analysis uses Berlin instead of Chicago. Here's the honest reason:

**Free, reliable historical pollen data with actual grain counts (grains/m³) is extremely hard to find for US cities.**

| Data Source   | US Pollen?     | Grain Counts?       | Free?               | Historical Depth         |
| ------------- | -------------- | ------------------- | ------------------- | ------------------------ |
| Open-Meteo    | ❌ Europe only | ✅ grains/m³        | ✅ Free, no API key | ✅ 2021–present (pollen) |
| Tomorrow.io   | ✅ US          | ❌ Index only (0–5) | ⚠️ Limited free     | ❌ 7 days back           |
| Ambee         | ✅ US          | ✅ Counts           | ❌ Paid             | ⚠️ Paid tier             |
| Google Pollen | ✅ US          | ✅ Index + species  | ❌ $1,200/mo        | ❌ No historical         |
| NAB (AAAAI)   | ✅ US          | ✅ Actual counts    | ✅ Free website     | ❌ No API                |

The **Open-Meteo Air Quality API** is the only source that provides **hourly pollen data in actual grains/m³** — completely free, no API key required. It's powered by the CAMS European pollen forecast model (data available from 2021 onwards), but only covers European cities.

For the **daily email alerts**, we scrape [ASAP Illinois](https://asapillinois.com/pollen-count/) directly — they provide the official certified Chicago-area pollen count, collected by allergists from physical samples counted under a microscope.

> This data limitation is a real-world constraint that any data project faces. Rather than using lower-quality data, we chose the best available source for each purpose.

---

## 🚀 Quick Start

### 1. Clone & install

```bash
git clone https://github.com/daveherzau/allergy-monitor.git
cd allergy-monitor
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Run the analysis notebook

```bash
cd analysis
jupyter notebook pollen_analysis.ipynb
```

Run all cells — the first run fetches data from Open-Meteo (takes ~1 min), then caches it as CSV.

### 3. Set up daily alerts (optional)

```bash
# Copy the example env file and add your Gmail credentials
cp .env.example .env
# Edit .env with your SMTP_EMAIL, SMTP_PASSWORD, and ALERT_RECIPIENT

# Preview the email locally (no email sent)
cd daily_alert
python main.py --preview

# Test with actual email
python main.py --test

# Normal mode (respects April–October season window)
python main.py
```

**Gmail App Password setup:**

1. Enable 2-Factor Authentication on your Google account
2. Go to [App Passwords](https://myaccount.google.com/apppasswords)
3. Generate a password for "Mail"
4. Paste the 16-character password into `.env` as `SMTP_PASSWORD`

---

## 📁 Project Structure

```
allergy-monitor/
├── analysis/                       # Phase 1 — Historical pollen analysis
│   ├── pollen_analysis.ipynb       #   Jupyter notebook with all analysis & charts
│   └── data/                       #   Cached CSVs & generated chart images
│
├── daily_alert/                    # Phase 2 — Daily email alert pipeline
│   ├── main.py                     #   Entry point (season check → scrape → email)
│   ├── scraper.py                  #   ASAP Illinois web scraper
│   ├── email_builder.py            #   HTML email template builder
│   └── email_sender.py             #   Gmail SMTP sender
│
├── tests/                          # Unit tests
│   ├── test_scraper.py
│   └── test_email_builder.py
│
├── .github/workflows/
│   └── daily_alert.yml             # GitHub Actions — runs Mon–Fri 8AM CT, Apr–Oct
│
├── .env.example                    # Template for email credentials
├── requirements.txt
├── .gitignore
└── README.md
```

---

## 📊 Severity Scale (AAAAI)

Pollen levels are classified using thresholds from the **American Academy of Allergy, Asthma & Immunology**:

| Level        | Tree Pollen (gr/m³) | Grass Pollen (gr/m³) | Weed Pollen (gr/m³) |
| ------------ | ------------------- | -------------------- | ------------------- |
| 🟢 Low       | 1–14                | 1–4                  | 1–9                 |
| 🟡 Moderate  | 15–89               | 5–19                 | 10–49               |
| 🟠 High      | 90–1,499            | 20–199               | 50–499              |
| 🔴 Very High | ≥1,500              | ≥200                 | ≥500                |

> Note: The scale differs by pollen type because tree pollen is far more prolific than grass or weed pollen.

---

## ⏰ Seasonal Awareness

The daily alert system is season-aware:

- **ASAP Illinois collects pollen data Monday–Friday, April through October only**
- Outside this window, the script logs that it's off-season and exits cleanly
- Use `--test` to force a run anytime (for testing the scraper/email)
- GitHub Actions workflow also only runs during allergy season months

---

## 🛠️ Tech Stack

| Component         | Technology                          |
| ----------------- | ----------------------------------- |
| Data analysis     | pandas, scipy                       |
| Visualization     | matplotlib, seaborn, plotly         |
| Web scraping      | requests, BeautifulSoup             |
| Email             | smtplib (Python stdlib)             |
| Weather API       | Open-Meteo (free, no key)           |
| Pollen API        | Open-Meteo Air Quality (historical) |
| Daily pollen data | ASAP Illinois (web scrape)          |
| Scheduling        | GitHub Actions                      |
| Testing           | pytest                              |

---

## 📜 Data Sources & Attribution

- **Historical pollen data**: [Open-Meteo Air Quality API](https://open-meteo.com/en/docs/air-quality-api) — powered by [CAMS European Air Quality Forecast](https://atmosphere.copernicus.eu/)
- **Daily Chicago pollen counts**: [ASAP Illinois](https://asapillinois.com/pollen-count/) — certified readings from the Allergy, Sinus & Asthma Professionals
- **Weather data**: [Open-Meteo Weather API](https://open-meteo.com/)
- **Severity thresholds**: [AAAAI / National Allergy Bureau](https://www.aaaai.org/)

---

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.
