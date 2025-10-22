# Morning Market Pulse (No-LLM, Public Data)

This repo builds a daily HTML email using only public data (yfinance + a static macro calendar) — no paid APIs and no LLM usage.
It then sends the email through Gmail SMTP via `send_mail.py`.

## Files
- `build_report.py` — builds `morning_market_pulse.html` from public sources
- `sp_large_sample.csv` — list of large-cap tickers to scan for upcoming earnings (extend as desired)
- `macro_calendar.json` — official macro events you can edit/extend
- `send_mail.py` — emails the HTML via Gmail SMTP (App Password recommended)
- `send-market-pulse.yml` — GitHub Actions workflow (cron at 8:15 AM ET on weekdays)

## Local run
```bash
python build_report.py
SMTP_USER="you@gmail.com" SMTP_PASS="app_password" TO_EMAIL="you@domain.com" python send_mail.py
```

## GitHub Actions
Place the files in your repo root and add secrets:
- `SMTP_USER`, `SMTP_PASS`, `FROM_EMAIL` (optional), `TO_EMAIL`

The workflow will:
1. `pip install yfinance pandas`
2. `python build_report.py`
3. `python send_mail.py`

## Notes
- yfinance is free, but subject to rate limits and occasional data delays.
- Earnings coverage is limited by the sample ticker list and yfinance availability. For broader coverage without LLMs, expand the list or add a free calendar scraper later.