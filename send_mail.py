# send_mail.py
import os, sys, smtplib, ssl, pathlib, datetime, re
from email.message import EmailMessage
from email.utils import formatdate, make_msgid
from json import loads as json_loads

# ---------- Config via env ----------
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT   = int(os.getenv("SMTP_PORT", "587"))            # 587 STARTTLS (default). Use 465 for implicit TLS.
SMTP_USER   = os.getenv("SMTP_USER")
SMTP_PASS   = os.getenv("SMTP_PASS")
FROM_EMAIL  = os.getenv("FROM_EMAIL", SMTP_USER)
TO_EMAIL    = os.getenv("TO_EMAIL")                          # comma-separated
CC_EMAIL    = os.getenv("CC_EMAIL", "")                      # optional, comma-separated
BCC_EMAIL   = os.getenv("BCC_EMAIL", "")                     # optional, comma-separated (not added to headers)
REPLY_TO    = os.getenv("REPLY_TO")                          # optional

HTML_PATH   = os.getenv("HTML_PATH", "morning_market_pulse.html")
NARRATIVE_PATH = os.getenv("NARRATIVE_PATH", "narrative.json")

# Subject/preview: allow explicit overrides, else auto from content/date
SUBJECT_OVERRIDE = os.getenv("SUBJECT", "")
PREVIEW_OVERRIDE = os.getenv("PREVIEW", "")
DRY_RUN = os.getenv("DRY_RUN", "false").lower() == "true"    # if true, compose but don't send

# ---------- Guards ----------
missing = [k for k in ("SMTP_USER","SMTP_PASS","TO_EMAIL") if not os.getenv(k)]
if missing:
    sys.exit(f"Missing required env var(s): {', '.join(missing)}")

# ---------- Helpers ----------
def parse_list(s: str) -> list[str]:
    return [t.strip() for t in (s or "").split(",") if t.strip()]

def load_text(path: str) -> str:
    return pathlib.Path(path).read_text(encoding="utf-8")

def strip_tags(html: str) -> str:
    # quick, good-enough HTML->text
    text = re.sub(r"<(br|BR)\s*/?>", "\n", html)
    text = re.sub(r"<li[^>]*>", "• ", text)
    text = re.sub(r"</li>", "\n", text)
    text = re.sub(r"<[^>]+>", "", text)
    return re.sub(r"\n{3,}", "\n\n", text).strip()

def collapse_whitespace(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()

def summarize(s: str, limit=160) -> str:
    s = collapse_whitespace(s)
    if len(s) <= limit:
        return s
    # try to cut at sentence boundary
    cut = s[:limit]
    end = cut.rfind(". ")
    if end > 40:
        return cut[: end+1]
    return cut.rstrip() + "…"

def hidden_preheader(pre: str) -> str:
    # More robust preheader block that keeps some clients from collapsing it away
    return (
        f'<div style="display:none !important; opacity:0; color:transparent; '
        f'max-height:0; max-width:0; overflow:hidden; mso-hide:all;">{pre}'
        f'&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;</div>'
    )

# ---------- Load content ----------
try:
    html = load_text(HTML_PATH)
except Exception as e:
    sys.exit(f"Failed to read HTML_PATH '{HTML_PATH}': {e}")

# Try to read narrative for subject/preview/text fallback
section1 = section2 = section3 = ""
try:
    n_raw = load_text(NARRATIVE_PATH)
    n = json_loads(n_raw)
    # accept both HTML strings or structured objects with 'bullets'
    def section_to_text(sec):
        if isinstance(sec, dict):
            bits = []
            if "bullets" in sec and isinstance(sec["bullets"], list):
                for b in sec["bullets"]:
                    lab = b.get("label", "")
                    txt = b.get("text", "")
                    if lab and txt:
                        bits.append(f"{lab}: {txt}")
                    else:
                        bits.append(txt or lab)
            if "callout" in sec and sec["callout"]:
                bits.append(sec["callout"])
            return "\n".join([b for b in bits if b])
        elif isinstance(sec, str):
            return strip_tags(sec)
        return ""

    section1 = section_to_text(n.get("section1", ""))
    section2 = section_to_text(n.get("section2", ""))
    section3 = section_to_text(n.get("section3", ""))
except Exception:
    # narrative.json is optional; we can still send
    pass

# ---------- Subject & preheader ----------
# Default subject includes NY date (only if not overridden)
try:
    from zoneinfo import ZoneInfo
    ny = ZoneInfo("America/New_York")
except Exception:
    ny = None

now = datetime.datetime.now(tz=ny) if ny else datetime.datetime.now()
date_str = now.strftime("%a, %b %d, %Y")

SUBJECT = SUBJECT_OVERRIDE or f"Morning Market Pulse — {date_str}"

# Preheader: explicit env > section3 > section1 > generic
preview_candidate = PREVIEW_OVERRIDE or (section3 or section1)
PREVIEW = summarize(preview_candidate, 160) if preview_candidate else "Daily setup + earnings/event radar."

# Inject preheader
html = hidden_preheader(PREVIEW) + html

# ---------- Plaintext fallback (real content) ----------
blocks = []
if section1: blocks.append("1) Macro Tone & overnight markets\n" + section1)
if section2: blocks.append("2) Next 7-day earnings + major event radar\n" + section2)
if section3: blocks.append("3) Advisor-ready interpretation — what matters + why\n" + section3)
text_fallback = f"Morning Market Pulse — {date_str}\n{PREVIEW}\n\n" + ("\n\n".join(blocks) if blocks else "(See HTML version)")

# ---------- Build message ----------
msg = EmailMessage()
msg["Subject"] = SUBJECT
msg["From"] = FROM_EMAIL
msg["To"] = ", ".join(parse_list(TO_EMAIL))
if CC_EMAIL:
    msg["Cc"] = ", ".join(parse_list(CC_EMAIL))
if REPLY_TO:
    msg["Reply-To"] = REPLY_TO
msg["Date"] = formatdate(localtime=True)
msg["Message-ID"] = make_msgid()

msg.set_content(text_fallback)
msg.add_alternative(html, subtype="html")

# Recipients list for SMTP (To + Cc + Bcc)
rcpts = parse_list(TO_EMAIL) + parse_list(CC_EMAIL) + parse_list(BCC_EMAIL)

# ---------- Send ----------
try:
    if SMTP_PORT == 465:
        ctx = ssl.create_default_context()
        with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT, context=ctx, timeout=30) as server:
            server.login(SMTP_USER, SMTP_PASS)
            if DRY_RUN:
                print("[DRY_RUN] Would send to:", rcpts)
            else:
                server.send_message(msg, from_addr=FROM_EMAIL, to_addrs=rcpts)
    else:
        ctx = ssl.create_default_context()
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT, timeout=30) as server:
            server.starttls(context=ctx)
            server.login(SMTP_USER, SMTP_PASS)
            if DRY_RUN:
                print("[DRY_RUN] Would send to:", rcpts)
            else:
                server.send_message(msg, from_addr=FROM_EMAIL, to_addrs=rcpts)
    print("Email sent to:", ", ".join(rcpts) if not DRY_RUN else "(dry run)")
except Exception as e:
    sys.exit(f"SMTP send failed: {e}")
