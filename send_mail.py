# send_mail.py
import os, sys, smtplib, ssl, pathlib
from email.message import EmailMessage
from email.utils import formatdate, make_msgid

SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT   = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER   = os.getenv("SMTP_USER")          # Gmail address (uses App Password if 2FA)
SMTP_PASS   = os.getenv("SMTP_PASS")          # Gmail App Password
FROM_EMAIL  = os.getenv("FROM_EMAIL", SMTP_USER)
TO_EMAIL    = os.getenv("TO_EMAIL")           # Comma-separated for multiple recipients
SUBJECT     = os.getenv("SUBJECT", "Morning Market Pulse — Sample")
PREVIEW     = os.getenv("PREVIEW", "Sample preview: neutral tone; earnings cluster; policy window ahead.")
HTML_PATH   = os.getenv("HTML_PATH", "morning_market_pulse_sample.html")
REPLY_TO    = os.getenv("REPLY_TO")           # optional

# Validate required env
missing = [k for k in ("SMTP_USER","SMTP_PASS","TO_EMAIL") if not os.getenv(k)]
if missing:
    sys.exit(f"Missing required env var(s): {', '.join(missing)}")

# Load HTML
try:
    html = pathlib.Path(HTML_PATH).read_text(encoding="utf-8")
except Exception as e:
    sys.exit(f"Failed to read HTML_PATH '{HTML_PATH}': {e}")

# Inject an invisible preheader so inboxes show PREVIEW nicely
def inject_preheader(html_str: str, preheader: str) -> str:
    pre = (
        f'<div style="display:none;max-height:0;overflow:hidden;opacity:0;'
        f'color:transparent;visibility:hidden;">{preheader}</div>'
    )
    return pre + html_str

html = inject_preheader(html, PREVIEW)

# Plaintext fallback
text_fallback = (
    f"Morning Market Pulse\n{PREVIEW}\n\n"
    "1) Macro Tone & overnight markets\n"
    "- Placeholder sample text.\n\n"
    "2) Next 7-day earnings + major event radar\n"
    "- Placeholder sample text.\n\n"
    "3) Advisor-ready interpretation — what matters + why\n"
    "- Placeholder sample text.\n"
)

# Build the message
msg = EmailMessage()
msg["Subject"] = SUBJECT
msg["From"] = FROM_EMAIL
msg["To"] = TO_EMAIL
msg["Date"] = formatdate(localtime=True)
msg["Message-ID"] = make_msgid()
if REPLY_TO:
    msg["Reply-To"] = REPLY_TO

msg.set_content(text_fallback)
msg.add_alternative(html, subtype="html")

# Send
ctx = ssl.create_default_context()
try:
    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        server.starttls(context=ctx)
        server.login(SMTP_USER, SMTP_PASS)
        server.send_message(msg, from_addr=FROM_EMAIL, to_addrs=[t.strip() for t in TO_EMAIL.split(",") if t.strip()])
    print("Email sent to:", TO_EMAIL)
except Exception as e:
    sys.exit(f"SMTP send failed: {e}")
