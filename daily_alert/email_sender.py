"""
Sends the daily allergy alert email via Gmail SMTP.

Uses Python's built-in smtplib — no external email service needed.
Credentials are loaded from a .env file (never committed to Git).

Setup:
    1. Enable 2FA on your Google account
    2. Generate an App Password: https://myaccount.google.com/apppasswords
    3. Add to .env:
        SMTP_EMAIL=your_email@gmail.com
        SMTP_PASSWORD=your_16_char_app_password
        ALERT_RECIPIENT=recipient@example.com
"""

import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv


# Load .env from the project root (one level up from daily_alert/)
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587


def send_alert_email(subject: str, html_body: str) -> bool:
    """
    Send an HTML email via Gmail SMTP.

    Args:
        subject: Email subject line.
        html_body: Complete HTML content for the email body.

    Returns:
        True if sent successfully, False otherwise.

    Raises:
        ValueError: If SMTP credentials are not configured.
    """
    sender_email = os.getenv("SMTP_EMAIL")
    sender_password = os.getenv("SMTP_PASSWORD")
    recipient_email = os.getenv("ALERT_RECIPIENT")

    if not all([sender_email, sender_password, recipient_email]):
        raise ValueError(
            "Missing email configuration. Please set SMTP_EMAIL, SMTP_PASSWORD, "
            "and ALERT_RECIPIENT in your .env file. See .env.example for details."
        )

    # Build the email
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = f"Allergy Monitor 🌿 <{sender_email}>"
    msg["To"] = recipient_email

    # Plain text fallback
    plain_text = (
        f"Chicago Daily Allergy Report\n"
        f"Subject: {subject}\n\n"
        f"View this email in an HTML-capable email client for the full report."
    )
    msg.attach(MIMEText(plain_text, "plain"))
    msg.attach(MIMEText(html_body, "html"))

    # Send via Gmail SMTP
    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, recipient_email, msg.as_string())

        print(f"  ✅ Email sent to {recipient_email}")
        return True

    except smtplib.SMTPAuthenticationError:
        print("  ❌ SMTP authentication failed. Check your App Password.")
        print("     Generate one at: https://myaccount.google.com/apppasswords")
        return False
    except smtplib.SMTPException as e:
        print(f"  ❌ SMTP error: {e}")
        return False
    except Exception as e:
        print(f"  ❌ Unexpected error sending email: {e}")
        return False
