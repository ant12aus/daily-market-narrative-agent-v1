import os, json, datetime as dt
from pathlib import Path
import yfinance as yf

OUTPUT = Path(os.getenv("OUTPUT_HTML", "morning_market_pulse.html"))
NARRATIVE = Path(os.getenv("NARRATIVE_JSON", "narrative.json"))

# Approx ET (set -5 during EST if runner lacks timezone data)
NOW_UTC = dt.datetime.now(dt.timezone.utc)
ET_OFFSET = -4  # EDT now; change to -5 for EST
NOW_ET = NOW_UTC.astimezone(dt.timezone(dt.timedelta(hours=ET_OFFSET)))
TODAY_ET = NOW_ET.strftime("%a, %b %d, %Y")
TS_ET = NOW_ET.strftime("%-I:%M %p ET, %b %d, %Y")

# Read narrative JSON
try:
    nar = json.loads(NARRATIVE.read_text(encoding="utf-8"))
except Exception:
    nar = {"section1": "", "section2": "", "section3": ""}

s1 = nar.get("section1") or "<p><em>Pending — add to narrative.json → section1</em></p>"
s2 = nar.get("section2") or "<p><em>Pending — add to narrative.json → section2</em></p>"
s3 = nar.get("section3") or "<p><em>Pending — add to narrative.json → section3</em></p>"

# Public KPI snapshot (no commentary; numbers only)
QUOTES = {
    "S&P Futures": "ES=F",
    "Nasdaq Futures": "NQ=F",
    "Russell Futures": "RTY=F",
    "10Y UST (yield x10)": "^TNX",
    "DXY (USD)": "DX-Y.NYB",
    "WTI Crude": "CL=F",
    "Gold": "GC=F",
}

def fetch(t):
    try:
        info = yf.Ticker(t).fast_info
        price = info.get("last_price") or info.get("regular_market_price")
        prev = info.get("previous_close")
        pct = None
        if price is not None and prev not in (None, 0):
            pct = (price/prev - 1.0) * 100.0
        return price, pct
    except Exception:
        return None, None

# KPI tiles
kpis_html = []
for label, tick in QUOTES.items():
    p, c = fetch(tick)
    price = "—" if p is None else f"{p:,.2f}"
    pct   = "—" if c is None else f"{c:+.2f}%"
    kpis_html.append(f"""
      <div class="kpi">
        <div class="label">{label}</div>
        <div class="value">{price} <span class="pill">{pct}</span></div>
      </div>
    """)
kpis_html = "\n".join(kpis_html)

HTML = f"""
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Morning Market Pulse — {TODAY_ET}</title>
  <style>
    body {{ margin:0; padding:0; background:#f5f7fb; font-family: -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, Arial, sans-serif; }}
    .container {{ max-width: 720px; margin: 0 auto; background:#ffffff; }}
    .header {{ padding:20px 24px; border-bottom:1px solid #e6e9f2; }}
    .tag {{ font-size:12px; letter-spacing:.04em; font-weight:600; color:#4b6bfb; text-transform:uppercase; }}
    h1 {{ margin:6px 0 0; font-size:20px; line-height:1.3; color:#111; }}
    .meta {{ color:#667085; font-size:12px; margin-top:4px; }}
    .section {{ padding:20px 24px; border-top:1px solid #f0f2f7; }}
    .section h2 {{ font-size:14px; text-transform:uppercase; letter-spacing:.04em; color:#0f172a; margin:0 0 8px; }}
    .bullet {{ margin:0; padding-left:18px; color:#0f172a; }}
    .bullet li {{ margin:8px 0; }}
    .callout {{ background:#f8fafc; border:1px solid #e2e8f0; padding:12px 14px; border-radius:8px; font-size:13px; color:#0f172a; }}
    .foot {{ padding:16px 24px; color:#64748b; font-size:12px; }}
    .smallcaps {{ font-variant: all-small-caps; letter-spacing:.06em; }}
    .disclaimer {{ font-size:11px; color:#667085; line-height:1.45; }}
    .pill {{ display:inline-block; background:#eef2ff; color:#3730a3; border-radius:999px; padding:2px 8px; font-size:11px; margin-left:6px; }}
    .grid {{ display:block; }}
    @media (min-width: 640px) {{
      .grid {{ display:grid; grid-template-columns: 1fr 1fr; gap: 10px; }}
    }}
    .kpi {{ background:#fafafa; border:1px solid #eee; border-radius:10px; padding:10px 12px; }}
    .kpi .label {{ color:#64748b; font-size:12px; }}
    .kpi .value {{ font-size:16px; font-weight:700; color:#0f172a; }}
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <div class="tag">Morning Market Pulse</div>
      <h1>Daily Intelligence Brief — {TODAY_ET}</h1>
      <div class="meta">Timestamp: {TS_ET} &middot; Source discipline: Public data only</div>
    </div>

    <div class="section">
      <div class="grid">
        {kpis_html}
      </div>
    </div>

    <div class="section">
      <h2>1) Macro Tone &amp; overnight markets</h2>
      {s1}
    </div>

    <div class="section">
      <h2>2) Next 7-day earnings + major event radar (Fed, CPI, etc.)</h2>
      {s2}
    </div>

    <div class="section">
      <h2>3) Advisor-ready interpretation — what matters + why</h2>
      {s3}
      <div class="callout">Guardrails: public data only; no inference of firm/client positions; informational — not investment advice.</div>
    </div>

    <div class="foot">
      <div class="disclaimer">
        Prepared for internal use. Data sourced from public dashboards and official calendars at time of send.
      </div>
    </div>
  </div>
</body>
</html>
"""

OUTPUT.write_text(HTML, encoding="utf-8")
print("Wrote:", OUTPUT.resolve())