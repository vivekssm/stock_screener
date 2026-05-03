# 📊 Alpha Screener — Indian Stock Screener

A deep-value stock screener for NSE-listed equities built with Streamlit.

## Screening Criteria

| # | Criterion | Default |
|---|-----------|---------|
| 1 | Current P/B ratio < Minimum P/B during Feb–Oct 2020 (COVID crash) | Auto |
| 2 | ROE (Return on Equity) > threshold | 15% |
| 3 | 3-Year Median YoY Growth in Cash from Operations > threshold | 20% |
| 4 | Market Cap > threshold | ₹10,000 Cr |

## Setup & Run Locally

```bash
# 1. Clone / copy project files
cd stock_screener

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run the app
streamlit run app.py
```

The app opens at http://localhost:8501

## Deploy on Streamlit Community Cloud

1. Push this folder to a **public GitHub repository**
2. Go to https://share.streamlit.io
3. Click **New app** → connect your GitHub repo
4. Set **Main file path** to `app.py`
5. Click **Deploy** — done!

No secrets or API keys required (data from Yahoo Finance is free).

## Notes

- Data is fetched live from Yahoo Finance via `yfinance`
- Results are cached for 1 hour to avoid rate limits
- P/B COVID low uses historical closing prices ÷ current book value per share (best available approximation via yfinance)
- Screening 50 stocks takes ~2–3 minutes; start small to test
