import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import requests
from datetime import datetime, date
import plotly.graph_objects as go
import plotly.express as px
from concurrent.futures import ThreadPoolExecutor, as_completed
import warnings
warnings.filterwarnings('ignore')

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Alpha Screener",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Serif+Display:ital@0;1&family=DM+Mono:wght@400;500&family=DM+Sans:wght@300;400;500;600&display=swap');

:root {
    --bg: #0a0c0f;
    --surface: #111418;
    --surface2: #181c22;
    --border: #232830;
    --accent: #c8f135;
    --accent2: #35f1c8;
    --accent3: #f1c835;
    --text: #e8edf2;
    --muted: #6b7785;
    --danger: #f13535;
    --success: #35c8a0;
}

html, body, [data-testid="stAppViewContainer"] {
    background-color: var(--bg) !important;
    color: var(--text) !important;
    font-family: 'DM Sans', sans-serif !important;
}

[data-testid="stSidebar"] {
    background-color: var(--surface) !important;
    border-right: 1px solid var(--border) !important;
}

[data-testid="stHeader"] { background: transparent !important; }

h1, h2, h3 { font-family: 'DM Serif Display', serif !important; color: var(--text) !important; }

.metric-card {
    background: var(--surface2);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 20px 24px;
    position: relative;
    overflow: hidden;
}
.metric-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 2px;
    background: linear-gradient(90deg, var(--accent), var(--accent2));
}
.metric-label { font-size: 11px; text-transform: uppercase; letter-spacing: 1.5px; color: var(--muted); margin-bottom: 6px; }
.metric-value { font-family: 'DM Mono', monospace; font-size: 28px; font-weight: 500; color: var(--accent); }
.metric-sub { font-size: 12px; color: var(--muted); margin-top: 4px; }

.pass-badge { background: rgba(53,200,160,0.15); color: var(--success); border: 1px solid rgba(53,200,160,0.3); border-radius: 6px; padding: 2px 10px; font-size: 11px; font-family: 'DM Mono', monospace; }
.fail-badge { background: rgba(241,53,53,0.15); color: var(--danger); border: 1px solid rgba(241,53,53,0.3); border-radius: 6px; padding: 2px 10px; font-size: 11px; font-family: 'DM Mono', monospace; }

[data-testid="stDataFrame"] {
    border: 1px solid var(--border) !important;
    border-radius: 12px !important;
    overflow: hidden !important;
}

.stButton > button {
    background: var(--accent) !important;
    color: #0a0c0f !important;
    border: none !important;
    border-radius: 8px !important;
    font-family: 'DM Sans', sans-serif !important;
    font-weight: 600 !important;
    font-size: 14px !important;
    padding: 10px 28px !important;
    transition: all 0.2s !important;
    width: 100%;
}
.stButton > button:hover { transform: translateY(-1px); box-shadow: 0 8px 24px rgba(200,241,53,0.25) !important; }

[data-testid="stSlider"] > div > div > div > div { background: var(--accent) !important; }

.stSelectbox > div > div, .stMultiSelect > div > div {
    background-color: var(--surface2) !important;
    border-color: var(--border) !important;
    color: var(--text) !important;
}

.criterion-row {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 12px 0;
    border-bottom: 1px solid var(--border);
}
.criterion-name { flex: 1; font-size: 13px; color: var(--muted); font-family: 'DM Mono', monospace; }
.criterion-value { font-family: 'DM Mono', monospace; font-size: 14px; color: var(--text); }

.hero-title {
    font-family: 'DM Serif Display', serif;
    font-size: 48px;
    line-height: 1.1;
    color: var(--text);
    margin-bottom: 8px;
}
.hero-sub {
    color: var(--muted);
    font-size: 15px;
    margin-bottom: 32px;
    max-width: 600px;
}
.accent-word { color: var(--accent); font-style: italic; }

.stProgress > div > div > div { background: var(--accent) !important; }

div[data-testid="stNotification"] { background: var(--surface2) !important; }
</style>
""", unsafe_allow_html=True)


# ── Nifty 500 tickers (NSE) ──────────────────────────────────────────────────
NIFTY500_TICKERS = [
    "RELIANCE", "TCS", "HDFCBANK", "BHARTIARTL", "ICICIBANK", "INFOSYS",
    "SBIN", "HINDUNILVR", "ITC", "LICI", "LT", "BAJFINANCE", "HCLTECH",
    "MARUTI", "SUNPHARMA", "ADANIENT", "KOTAKBANK", "TITAN", "ONGC",
    "NTPC", "POWERGRID", "ULTRACEMCO", "BAJAJFINSV", "WIPRO", "AXISBANK",
    "ADANIPORTS", "ASIANPAINT", "NESTLEIND", "COALINDIA", "TATAMOTORS",
    "DRREDDY", "JSWSTEEL", "TATASTEEL", "INDUSINDBK", "HINDALCO",
    "CIPLA", "APOLLOHOSP", "BRITANNIA", "GRASIM", "TECHM", "EICHERMOT",
    "DIVISLAB", "BPCL", "TATACONSUM", "HEROMOTOCO", "SHREECEM", "M&M",
    "SBILIFE", "HDFCLIFE", "ADANIGREEN", "ADANIPOWER", "SIEMENS",
    "PIDILITIND", "BAJAJ-AUTO", "BERGEPAINT", "HAVELLS", "MUTHOOTFIN",
    "TORNTPHARM", "COLPAL", "DABUR", "GODREJCP", "MARICO", "AMBUJACEM",
    "ACC", "BANKBARODA", "CANBK", "UNIONBANK", "PNB", "INDHOTEL",
    "IRCTC", "DMART", "NAUKRI", "MCDOWELL-N", "PAGEIND", "TATAPOWER",
    "ZYDUSLIFE", "LUPIN", "BIOCON", "ALKEM", "AUROPHARMA", "IPCALAB",
    "GLAXO", "PFIZER", "ABBOTINDIA", "SANOFI", "CHOLAFIN", "BAJAJHLDNG",
    "LICHSGFIN", "M&MFIN", "MANAPPURAM", "RECLTD", "PFC", "HUDCO",
    "IRFC", "NHPC", "SJVN", "CESC", "TORNTPOWER", "TATAELXSI",
    "PERSISTENT", "LTIM", "MPHASIS", "COFORGE", "KPITTECH", "OFSS",
    "FSL", "ZOMATO", "PAYTM", "POLICYBZR", "NYKAA",
]

NSE_SUFFIX = ".NS"


def get_ticker(symbol: str) -> str:
    return symbol + NSE_SUFFIX


# ── Data fetching helpers ─────────────────────────────────────────────────────

@st.cache_data(ttl=3600, show_spinner=False)
def fetch_stock_info(symbol: str) -> dict | None:
    try:
        ticker = yf.Ticker(get_ticker(symbol))
        info = ticker.info
        if not info or info.get("regularMarketPrice") is None:
            return None

        # Market cap in crores (1 crore = 10M INR)
        market_cap_cr = (info.get("marketCap") or 0) / 1e7

        # Current P/B
        pb = info.get("priceToBook")

        # ROE (trailing twelve months)
        roe = info.get("returnOnEquity")
        if roe is not None:
            roe = roe * 100  # convert to %

        return {
            "symbol": symbol,
            "name": info.get("longName") or info.get("shortName") or symbol,
            "sector": info.get("sector", "N/A"),
            "market_cap_cr": round(market_cap_cr, 0),
            "current_pb": pb,
            "roe": round(roe, 2) if roe else None,
            "price": info.get("regularMarketPrice"),
            "info": info,
        }
    except Exception:
        return None


@st.cache_data(ttl=3600, show_spinner=False)
def fetch_min_pb_covid(symbol: str) -> float | None:
    """
    Compute minimum P/B during Feb–Oct 2020 using HISTORICAL book value.

    Strategy:
    1. Pull quarterly balance sheet → get Total Stockholder Equity + shares
       outstanding for each quarter → book value per share per quarter.
    2. For Q1 2020 (Mar) and Q2 2020 (Jun), interpolate daily BV/share by
       forward-filling each quarter's value across its date range.
    3. Pull daily closing prices Feb–Oct 2020.
    4. Compute daily P/B = price / bv_per_share_that_day → take the minimum.
    """
    try:
        ticker = yf.Ticker(get_ticker(symbol))

        # ── Step 1: quarterly book value per share ───────────────────────────
        bs = ticker.quarterly_balance_sheet
        if bs is None or bs.empty:
            return None

        # Equity row — try multiple possible names
        equity_row = None
        for label in [
            "Stockholders Equity",
            "Total Stockholder Equity",
            "Common Stock Equity",
            "Total Equity Gross Minority Interest",
        ]:
            if label in bs.index:
                equity_row = bs.loc[label]
                break
        if equity_row is None:
            return None

        # Shares — prefer ordinary shares outstanding from balance sheet,
        # fall back to info (current value, less ideal but better than nothing)
        shares_row = None
        for label in ["Ordinary Shares Number", "Share Issued", "Common Stock"]:
            if label in bs.index:
                shares_row = bs.loc[label]
                break

        # Build a Series: date → bv_per_share
        bv_series = {}
        for col in equity_row.index:
            equity = equity_row[col]
            if pd.isna(equity):
                continue
            # Shares for this quarter
            if shares_row is not None and col in shares_row.index and not pd.isna(shares_row[col]):
                shares = shares_row[col]
            else:
                shares = ticker.info.get("sharesOutstanding")
            if not shares or shares == 0:
                continue
            bv_series[pd.Timestamp(col)] = equity / shares

        if not bv_series:
            return None

        bv_quarterly = pd.Series(bv_series).sort_index()

        # ── Step 2: forward-fill BV/share to daily frequency ────────────────
        # We need coverage from 2019-Q4 through 2020-Q3 at minimum
        covid_start = pd.Timestamp("2020-02-01")
        covid_end   = pd.Timestamp("2020-10-31")

        daily_idx = pd.date_range(
            start=min(bv_quarterly.index.min(), covid_start),
            end=max(bv_quarterly.index.max(), covid_end),
            freq="D",
        )
        bv_daily = bv_quarterly.reindex(daily_idx).ffill().bfill()

        # Slice to COVID window
        bv_covid = bv_daily.loc[covid_start:covid_end]
        if bv_covid.empty or bv_covid.isna().all():
            return None

        # ── Step 3: daily closing prices ─────────────────────────────────────
        hist = ticker.history(start="2020-02-01", end="2020-10-31")
        if hist.empty:
            return None

        hist.index = hist.index.tz_localize(None)          # strip tz
        prices = hist["Close"]

        # ── Step 4: daily P/B → minimum ──────────────────────────────────────
        aligned_bv = bv_covid.reindex(prices.index).ffill().bfill()
        daily_pb = prices / aligned_bv
        daily_pb = daily_pb[daily_pb > 0]                  # drop nonsense

        if daily_pb.empty:
            return None

        return round(float(daily_pb.min()), 2)

    except Exception:
        return None


@st.cache_data(ttl=3600, show_spinner=False)
def fetch_cfo_growth(symbol: str) -> float | None:
    """3-year median YoY growth in Cash from Operations (%)."""
    try:
        ticker = yf.Ticker(get_ticker(symbol))
        cf = ticker.cashflow
        if cf is None or cf.empty:
            return None

        # Row: Operating Cash Flow
        if "Operating Cash Flow" in cf.index:
            row = cf.loc["Operating Cash Flow"]
        elif "Total Cash From Operating Activities" in cf.index:
            row = cf.loc["Total Cash From Operating Activities"]
        else:
            return None

        values = row.dropna().sort_index(ascending=True)
        if len(values) < 2:
            return None

        growths = []
        vals = list(values)
        for i in range(1, len(vals)):
            prev = vals[i - 1]
            curr = vals[i]
            if prev and prev != 0:
                g = ((curr - prev) / abs(prev)) * 100
                growths.append(g)

        if not growths:
            return None
        return round(float(np.median(growths[-3:])), 1)
    except Exception:
        return None


def screen_stock(symbol: str, thresholds: dict) -> dict | None:
    info = fetch_stock_info(symbol)
    if not info:
        return None

    min_pb_covid = fetch_min_pb_covid(symbol)
    cfo_growth = fetch_cfo_growth(symbol)

    current_pb = info["current_pb"]
    roe = info["roe"]
    market_cap = info["market_cap_cr"]

    # Criterion 1: current P/B < 1.2 × historical COVID minimum P/B
    pb_threshold = round(1.2 * min_pb_covid, 2) if min_pb_covid is not None else None
    c1 = (current_pb is not None and pb_threshold is not None
          and current_pb < pb_threshold)
    c2 = (roe is not None and roe > thresholds["min_roe"])
    c3 = (cfo_growth is not None and cfo_growth > thresholds["min_cfo_growth"])
    c4 = (market_cap is not None and market_cap > thresholds["min_market_cap"])

    passes_all = c1 and c2 and c3 and c4
    criteria_passed = sum([c1, c2, c3, c4])

    return {
        "Symbol": symbol,
        "Name": info["name"],
        "Sector": info["sector"],
        "Price (₹)": info["price"],
        "Market Cap (Cr)": market_cap,
        "Current P/B": round(current_pb, 2) if current_pb else None,
        "Min P/B Covid (Feb-Oct'20)": min_pb_covid,
        "P/B Threshold (1.2×Covid)": pb_threshold,
        "ROE (%)": roe,
        "3Y Median CFO Growth (%)": cfo_growth,
        "✅ P/B < 1.2× COVID Low": c1,
        "✅ ROE > Threshold": c2,
        "✅ CFO Growth > Threshold": c3,
        "✅ Market Cap > Threshold": c4,
        "Criteria Passed": criteria_passed,
        "PASSES ALL": passes_all,
    }


# ── UI ────────────────────────────────────────────────────────────────────────

# Hero header
st.markdown("""
<div class="hero-title">
    Alpha <span class="accent-word">Screener</span>
</div>
<div class="hero-sub">
    Deep-value filter for Indian equities · NSE · Real-time data via Yahoo Finance
</div>
""", unsafe_allow_html=True)

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### ⚙️ Filter Parameters")
    st.markdown("---")

    st.markdown("**Criterion 1 — P/B Ratio**")
    st.caption("Current P/B < Minimum P/B during Feb–Oct 2020")

    st.markdown("**Criterion 2 — ROE (%)**")
    min_roe = st.slider("Minimum ROE (%)", 5, 40, 15, 1)

    st.markdown("**Criterion 3 — CFO Growth (%)**")
    min_cfo = st.slider("Min 3Y Median CFO Growth (%)", 5, 50, 20, 1)

    st.markdown("**Criterion 4 — Market Cap**")
    min_mcap = st.slider("Min Market Cap (₹ Crores)", 1000, 100000, 10000, 1000)

    st.markdown("---")
    st.markdown("**Universe**")
    num_stocks = st.slider("Stocks to screen", 10, len(NIFTY500_TICKERS), 50, 10)

    st.markdown("---")
    run_btn = st.button("🚀 Run Screener")

thresholds = {
    "min_roe": min_roe,
    "min_cfo_growth": min_cfo,
    "min_market_cap": min_mcap,
}

# ── Criteria Summary Cards ────────────────────────────────────────────────────
c1, c2, c3, c4 = st.columns(4)
with c1:
    st.markdown(f"""<div class="metric-card">
    <div class="metric-label">Criterion 1 · P/B</div>
    <div class="metric-value">COVID Low</div>
    <div class="metric-sub">Below Feb–Oct 2020 minimum</div>
    </div>""", unsafe_allow_html=True)
with c2:
    st.markdown(f"""<div class="metric-card">
    <div class="metric-label">Criterion 2 · ROE</div>
    <div class="metric-value">&gt; {min_roe}%</div>
    <div class="metric-sub">Return on Equity (TTM)</div>
    </div>""", unsafe_allow_html=True)
with c3:
    st.markdown(f"""<div class="metric-card">
    <div class="metric-label">Criterion 3 · CFO Growth</div>
    <div class="metric-value">&gt; {min_cfo}%</div>
    <div class="metric-sub">3-year median YoY growth</div>
    </div>""", unsafe_allow_html=True)
with c4:
    st.markdown(f"""<div class="metric-card">
    <div class="metric-label">Criterion 4 · Market Cap</div>
    <div class="metric-value">₹{min_mcap:,}</div>
    <div class="metric-sub">Crores minimum</div>
    </div>""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── Main screening logic ──────────────────────────────────────────────────────
if run_btn:
    tickers_to_screen = NIFTY500_TICKERS[:num_stocks]
    total = len(tickers_to_screen)

    progress_bar = st.progress(0)
    status_text = st.empty()
    results = []

    for i, symbol in enumerate(tickers_to_screen):
        status_text.markdown(f"*Screening `{symbol}` ... ({i+1}/{total})*")
        result = screen_stock(symbol, thresholds)
        if result:
            results.append(result)
        progress_bar.progress((i + 1) / total)

    progress_bar.empty()
    status_text.empty()

    if not results:
        st.warning("No data returned. Check your internet connection.")
        st.stop()

    df = pd.DataFrame(results)

    # Summary metrics
    total_screened = len(df)
    passed = df["PASSES ALL"].sum()
    partial = ((df["Criteria Passed"] >= 3) & (~df["PASSES ALL"])).sum()

    st.markdown("### 📊 Screening Results")
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.markdown(f"""<div class="metric-card">
        <div class="metric-label">Stocks Screened</div>
        <div class="metric-value">{total_screened}</div></div>""", unsafe_allow_html=True)
    with m2:
        st.markdown(f"""<div class="metric-card">
        <div class="metric-label">Passed All 4</div>
        <div class="metric-value" style="color:var(--success)">{passed}</div></div>""", unsafe_allow_html=True)
    with m3:
        st.markdown(f"""<div class="metric-card">
        <div class="metric-label">Passed 3/4</div>
        <div class="metric-value" style="color:var(--accent3)">{partial}</div></div>""", unsafe_allow_html=True)
    with m4:
        hit_rate = round((passed / total_screened) * 100, 1) if total_screened else 0
        st.markdown(f"""<div class="metric-card">
        <div class="metric-label">Hit Rate</div>
        <div class="metric-value">{hit_rate}%</div></div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Tabs
    tab1, tab2, tab3 = st.tabs(["✅ Passed All Criteria", "📋 Full Results", "📈 Analysis"])

    display_cols = [
        "Symbol", "Name", "Sector", "Price (₹)", "Market Cap (Cr)",
        "Current P/B", "Min P/B Covid (Feb-Oct'20)", "P/B Threshold (1.2×Covid)",
        "ROE (%)", "3Y Median CFO Growth (%)", "Criteria Passed", "PASSES ALL"
    ]

    with tab1:
        passed_df = df[df["PASSES ALL"]].sort_values("Market Cap (Cr)", ascending=False)
        if passed_df.empty:
            st.info("No stocks passed all 4 criteria in this batch. Try expanding the universe size or adjusting thresholds.")
        else:
            st.success(f"🎯 {len(passed_df)} stock(s) passed all criteria")
            st.dataframe(
                passed_df[display_cols].reset_index(drop=True),
                use_container_width=True,
                hide_index=True,
            )
            csv = passed_df[display_cols].to_csv(index=False)
            st.download_button("⬇️ Download Passed Stocks CSV", csv, "passed_stocks.csv", "text/csv")

    with tab2:
        sort_by = st.selectbox("Sort by", ["Criteria Passed", "Market Cap (Cr)", "ROE (%)", "3Y Median CFO Growth (%)"], key="sort_full")
        full_df = df.sort_values(sort_by, ascending=False)
        st.dataframe(
            full_df[display_cols].reset_index(drop=True),
            use_container_width=True,
            hide_index=True,
        )
        csv_full = full_df[display_cols].to_csv(index=False)
        st.download_button("⬇️ Download Full Results CSV", csv_full, "full_results.csv", "text/csv")

    with tab3:
        col_a, col_b = st.columns(2)

        with col_a:
            # Criteria pass rate bar chart
            criteria_names = ["P/B < 1.2× COVID Low", "ROE > Threshold", "CFO Growth > Threshold", "Market Cap > Threshold"]
            criteria_cols = ["✅ P/B < 1.2× COVID Low", "✅ ROE > Threshold", "✅ CFO Growth > Threshold", "✅ Market Cap > Threshold"]
            pass_counts = [df[c].sum() for c in criteria_cols]

            fig = go.Figure(go.Bar(
                x=criteria_names,
                y=pass_counts,
                marker_color=["#c8f135", "#35f1c8", "#f1c835", "#f13535"],
                text=pass_counts,
                textposition="outside",
            ))
            fig.update_layout(
                title="Stocks Passing Each Criterion",
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#e8edf2", family="DM Sans"),
                yaxis=dict(gridcolor="#232830"),
                margin=dict(t=50, b=20),
            )
            st.plotly_chart(fig, use_container_width=True)

        with col_b:
            # Sector breakdown of passed stocks
            sector_counts = df.groupby("Sector")["PASSES ALL"].sum().sort_values(ascending=False).head(10)
            if sector_counts.sum() > 0:
                fig2 = px.pie(
                    values=sector_counts.values,
                    names=sector_counts.index,
                    title="Passed Stocks by Sector",
                    color_discrete_sequence=px.colors.sequential.Plasma_r,
                )
                fig2.update_layout(
                    paper_bgcolor="rgba(0,0,0,0)",
                    font=dict(color="#e8edf2", family="DM Sans"),
                    margin=dict(t=50),
                )
                st.plotly_chart(fig2, use_container_width=True)
            else:
                # Sector breakdown of all screened
                sector_all = df["Sector"].value_counts().head(8)
                fig2 = px.bar(
                    x=sector_all.values, y=sector_all.index,
                    orientation="h",
                    title="Screened Universe by Sector",
                    color=sector_all.values,
                    color_continuous_scale="Plasma",
                )
                fig2.update_layout(
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    font=dict(color="#e8edf2", family="DM Sans"),
                    margin=dict(t=50),
                )
                st.plotly_chart(fig2, use_container_width=True)

        # Scatter: ROE vs CFO Growth
        df_plot = df.copy()
        df_plot["Status"] = df_plot["PASSES ALL"].map({True: "Passed All", False: "Filtered"})
        df_plot["ROE (%)"] = pd.to_numeric(df_plot["ROE (%)"], errors="coerce")
        df_plot["3Y Median CFO Growth (%)"] = pd.to_numeric(df_plot["3Y Median CFO Growth (%)"], errors="coerce")
        df_clean = df_plot.dropna(subset=["ROE (%)", "3Y Median CFO Growth (%)"])

        fig3 = px.scatter(
            df_clean,
            x="ROE (%)", y="3Y Median CFO Growth (%)",
            color="Status",
            size="Market Cap (Cr)",
            hover_data=["Symbol", "Name", "Sector"],
            title="ROE vs CFO Growth (bubble = Market Cap)",
            color_discrete_map={"Passed All": "#c8f135", "Filtered": "#6b7785"},
        )
        fig3.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#e8edf2", family="DM Sans"),
            xaxis=dict(gridcolor="#232830"),
            yaxis=dict(gridcolor="#232830"),
        )
        st.plotly_chart(fig3, use_container_width=True)

else:
    # Landing state
    st.markdown("""
    <div style="text-align:center; padding: 60px 20px; color: #6b7785;">
        <div style="font-size:64px; margin-bottom:16px;">📡</div>
        <div style="font-family:'DM Serif Display',serif; font-size:24px; color:#e8edf2; margin-bottom:12px;">
            Ready to screen
        </div>
        <div style="font-size:14px; max-width:480px; margin:0 auto; line-height:1.7;">
            Adjust the filter parameters in the sidebar, then click <strong style="color:#c8f135">Run Screener</strong>.
            Data is fetched live from Yahoo Finance and cached for 1 hour.
        </div>
    </div>
    """, unsafe_allow_html=True)

# Footer
st.markdown("""
<hr style="border-color:#232830; margin-top:48px;">
<div style="text-align:center; color:#6b7785; font-size:12px; padding:16px 0; font-family:'DM Mono',monospace;">
    Data: Yahoo Finance · Universe: NSE · For educational purposes only · Not financial advice
</div>
""", unsafe_allow_html=True)
