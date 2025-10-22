# build_report.py
import json, pathlib, datetime, zoneinfo, sys

NARRATIVE_PATH = "narrative.json"
OUTPUT_PATH    = "morning_market_pulse.html"

def load_json(path):
    return json.loads(pathlib.Path(path).read_text(encoding="utf-8"))

def save_text(path, s):
    pathlib.Path(path).write_text(s, encoding="utf-8")

def main():
    try:
        n = load_json(NARRATIVE_PATH)
    except Exception as e:
        sys.exit(f"❌ Failed to read {NARRATIVE_PATH}: {e}")

    s1 = n.get("section1", "<p>(no Section 1 provided)</p>")
    s2 = n.get("section2", "<p>(no Section 2 provided)</p>")
    s3 = n.get("section3", "<p>(no Section 3 provided)</p>")

    # Timestamp in America/New_York
    ny = zoneinfo.ZoneInfo("America/New_York")
    now_ny = datetime.datetime.now(tz=ny)
    date_str = now_ny.strftime("%a, %b %d, %Y")
    ts_str   = now_ny.strftime("%I:%M %p %Z").lstrip("0")

    html = f"""<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <title>Morning Market Pulse — {date_str}</title>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <style>
    body {{ font-family: -apple-system, Segoe UI, Roboto, Helvetica, Arial, sans-serif; margin:0; padding:24px; background:#f7f8fa; color:#0f172a; }}
    .wrap {{ max-width: 720px; margin: 0 auto; }}
    .h1 {{ font-size: 20px; font-weight: 700; margin: 0 0 4px; }}
    .meta {{ color:#64748b; font-size:12px; margin:0 0 16px; }}
    .card {{ background:#fff; border:1px solid #e5e7eb; border-radius:12px; padding:16px 18px; margin: 14px 0; }}
    .title {{ font-weight:600; margin:0 0 8px; font-size:14px; color:#111827; }}
    .content {{ font-size:14px; line-height:1.5; color:#111827; }}
    .foot {{ margin-top:20px; color:#6b7280; font-size:11px; }}
    .hr {{ height:1px; background:#e5e7eb; border:0; margin:18px 0; }}
  </style>
</head>
<body>
  <div class="wrap">
    <div class="h1">Morning Market Pulse</div>
    <div class="meta">Timestamp: {ts_str} • {date_str} • Source discipline: Public data only</div>

    <div class="card">
      <div class="title">1) Macro Tone &amp; Overnight Markets</div>
      <div class="content">{s1}</div>
    </div>

    <div class="card">
      <div class="title">2) Next 7-day Earnings + Major Event Radar</div>
      <div class="content">{s2}</div>
    </div>

    <div class="card">
      <div class="title">3) Advisor-ready Interpretation — What Matters &amp; Why</div>
      <div class="content">{s3}</div>
    </div>

    <div class="foot">
      Prepared for internal use. Informational only — not investment advice.
    </div>
  </div>
</body>
</html>"""
    save_text(OUTPUT_PATH, html)
    print(f"✅ Built report → {OUTPUT_PATH}")

if __name__ == "__main__":
    main()
