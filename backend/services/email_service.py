# Core email sender using Gmail SMTP.
# All other notification functions call send_email() from here.
# Uses TLS on port 587 — works with Gmail App Passwords.

import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

load_dotenv()

GMAIL_USER = os.getenv("GMAIL_USER")
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD")
SENDER_NAME = os.getenv("SENDER_NAME", "AuditSys")

def send_email(to_email: str, subject: str, html_body: str) -> bool:
    """
    Sends an HTML email via Gmail SMTP.

    Args:
        to_email  : recipient email address
        subject   : email subject line
        html_body : full HTML content of the email

    Returns:
        True if sent successfully, False otherwise
    """
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"]    = f"{SENDER_NAME} <{GMAIL_USER}>"
        msg["To"]      = to_email

        part = MIMEText(html_body, "html")
        msg.attach(part)

        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.ehlo()
            server.starttls()
            server.login(GMAIL_USER, GMAIL_APP_PASSWORD)
            server.sendmail(GMAIL_USER, to_email, msg.as_string())

        print(f"[EMAIL] Sent '{subject}' to {to_email}")
        return True

    except Exception as e:
        print(f"[EMAIL ERROR] Failed to send to {to_email}: {e}")
        return False