import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import os

def send_email(to_email: str, subject: str, html_body: str):
    try:
        gmail_user = os.getenv("GMAIL_USER")
        gmail_password = os.getenv("GMAIL_APP_PASSWORD")
        sender_name = os.getenv("SENDER_NAME", "AuditSys")

        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = f"{sender_name} <{gmail_user}>"
        msg['To'] = to_email
        msg.attach(MIMEText(html_body, 'html'))

        # Try port 465 (SSL) — works on Render free tier
        try:
            with smtplib.SMTP_SSL('smtp.gmail.com', 465, timeout=10) as server:
                server.login(gmail_user, gmail_password)
                server.sendmail(gmail_user, to_email, msg.as_string())
            print(f"[EMAIL] Sent to {to_email}")
        except Exception as e1:
            print(f"[EMAIL] Port 465 failed: {e1}, trying port 587...")
            # Fallback to port 587
            with smtplib.SMTP('smtp.gmail.com', 587, timeout=10) as server:
                server.ehlo()
                server.starttls()
                server.login(gmail_user, gmail_password)
                server.sendmail(gmail_user, to_email, msg.as_string())
            print(f"[EMAIL] Sent via port 587 to {to_email}")

    except Exception as e:
        print(f"[EMAIL ERROR] Failed to send to {to_email}: {e}")




        