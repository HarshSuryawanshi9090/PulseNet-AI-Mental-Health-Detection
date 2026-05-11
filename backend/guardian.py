"""PulseNet Guardian Alert System"""
import os, smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import database

SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASS = os.getenv("SMTP_PASS", "")
CRISIS_THRESHOLD = 85

def check_and_alert(post_id, score, category, text):
    alerts = []
    if score < CRISIS_THRESHOLD:
        return alerts
    for g in database.get_guardians():
        msg = _crisis_msg(g["name"], score, category, text)
        aid = database.save_alert(g["id"], post_id, msg, "email", score)
        sent = _send_email(g["email"], "🚨 PulseNet Crisis Alert", msg)
        alerts.append({"alert_id": aid, "guardian": g["name"], "score": score, "sent": sent})
    return alerts

def send_test_alert(guardian_id, score=75):
    gs = database.get_guardians()
    g = next((x for x in gs if x["id"] == guardian_id), None)
    if not g:
        return {"success": False, "error": "Guardian not found"}
    msg = _test_msg(g["name"], score)
    aid = database.save_alert(guardian_id, None, msg, "email", score)
    sent = _send_email(g["email"], "🔔 PulseNet Test Alert", msg)
    return {"success": True, "alert_id": aid, "guardian": g["name"], "email": g["email"], "simulated": not sent}

def _crisis_msg(name, score, category, text):
    preview = text[:100] + "..." if len(text) > 100 else text
    return (f"Dear {name},\n\nPulseNet detected a potential crisis.\n\n"
            f"⚠️ Score: {score}/100 ({category})\n🕐 {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}\n\n"
            f'Post: "{preview}"\n\nPlease reach out to this person.\n\n'
            f"Resources:\n- iCall: 9152987821\n- AASRA: 9820466627\n\n— PulseNet")

def _test_msg(name, score):
    return (f"Dear {name},\n\nThis is a TEST alert from PulseNet.\n\n"
            f"⚠️ Score would be: {score}/100\n🕐 {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}\n\n"
            f"You are registered as a guardian. Real alerts fire above threshold.\n\n— PulseNet")

def _send_email(to_email, subject, body):
    if not SMTP_USER or not SMTP_PASS or not to_email:
        return False
    try:
        msg = MIMEMultipart()
        msg["From"] = SMTP_USER; msg["To"] = to_email; msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))
        s = smtplib.SMTP(SMTP_HOST, SMTP_PORT)
        s.starttls(); s.login(SMTP_USER, SMTP_PASS); s.send_message(msg); s.quit()
        return True
    except Exception as e:
        print(f"[Guardian] Email failed: {e}")
        return False
