import os
import smtplib
from aiosmtpd.controller import Controller
from email import policy
from email.parser import BytesParser
import requests

API_URL = os.getenv("API_URL", "http://api:8000")
API_KEY = os.getenv("API_KEY", "DEMO_KEY")
RELAY_HOST = os.getenv("RELAY_HOST", "mailhog")
RELAY_PORT = int(os.getenv("RELAY_PORT", "1025"))

def classify_payload(subject, body, headers, attachments):
    r = requests.post(
        f"{API_URL}/classify",
        headers={"x-api-key": API_KEY},
        json={
            "subject": subject or "",
            "body": body or "",
            "headers": headers or {},
            "attachments": attachments or [],
        },
        timeout=15,
    )
    r.raise_for_status()
    return r.json()

class Handler:
    async def handle_DATA(self, server, session, envelope):
        try:
            msg = BytesParser(policy=policy.default).parsebytes(envelope.content)
            subject = msg["subject"] or ""

            # Extract text body (prefer text/plain)
            body_text = ""
            if msg.is_multipart():
                for part in msg.walk():
                    ctype = part.get_content_type()
                    disp = part.get_content_disposition()
                    if disp == "attachment":
                        continue
                    if ctype == "text/plain":
                        body_text = part.get_content()
                        break
                if not body_text:
                    # fallback: first text/* part
                    for part in msg.walk():
                        if part.get_content_type().startswith("text/"):
                            body_text = part.get_content()
                            break
            else:
                body_text = msg.get_content() if msg.get_content_type().startswith("text/") else ""

            # Attachment metadata
            attachments = []
            if msg.is_multipart():
                for part in msg.iter_attachments():
                    attachments.append({
                        "filename": part.get_filename() or "",
                        "size": len(part.get_payload(decode=True) or b"") if part.get_content_disposition() == "attachment" else None,
                        "mimetype": part.get_content_type(),
                    })

            headers = {
                "From": envelope.mail_from,
                "To": ",".join(envelope.rcpt_tos),
                "Subject": subject,
            }

            result = classify_payload(subject, body_text, headers, attachments)
            action = result.get("action", "Send Normally")

            # Relay decision
            with smtplib.SMTP(RELAY_HOST, RELAY_PORT) as s:
                if action == "Send Normally":
                    # forward original message as-is
                    s.send_message(msg)
                elif action == "Quarantine for Review":
                    # send to quarantine mailbox
                    qmsg = msg
                    qmsg.replace_header("To", "quarantine@demo.local") if "To" in qmsg else qmsg.add_header("To", "quarantine@demo.local")
                    s.send_message(qmsg)
                else:
                    # Trash & Alert Security: do not deliver original; send minimal alert
                    from email.message import EmailMessage
                    alert = EmailMessage()
                    alert["From"] = "dlp-alert@demo.local"
                    alert["To"] = "security@demo.local"
                    alert["Subject"] = f"[DLP ALERT] Message discarded - {headers.get('Subject','(no subject)')}"
                    alert.set_content(f"Message from {headers.get('From')} to {headers.get('To')} was discarded by DLP policy.\nClassification: {result}")
                    s.send_message(alert)

            return "250 OK"
        except Exception as e:
            # Always accept to avoid bouncing; just log server-side
            print(f"Error processing message: {e}")
            return "250 OK"

if __name__ == "__main__":
    controller = Controller(Handler(), hostname="127.0.0.1", port=2525)
    controller.start()
    try:
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_forever()
    except KeyboardInterrupt:
        controller.stop()
