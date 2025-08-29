import smtplib
from email.message import EmailMessage

SMTP_HOST = "localhost"
SMTP_PORT = 2525

msg = EmailMessage()
msg["From"] = "alice@corp.com"
msg["To"] = "finance@demo.local"
msg["Subject"] = "Q3 Salary Sheet (Confidential)"
msg.set_content("Team, attached are the confidential salary sheets for Q3. Please restrict sharing outside payroll.")

with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as s:
    s.send_message(msg)

print("Sent test email to SMTP proxy. Check MailHog at http://localhost:8025")
