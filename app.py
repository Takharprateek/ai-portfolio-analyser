# ============================================================
# AI PORTFOLIO ANALYSER — STREAMLIT WEB APP
# Co-founders: Takhar & Claude AI
# Version 3.0 — Live Dashboard
# ============================================================

import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import requests
import datetime
import time
import warnings
warnings.filterwarnings('ignore')

from newsapi import NewsApiClient
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier, VotingClassifier
from sklearn.metrics import accuracy_score
from sklearn.preprocessing import StandardScaler
import xgboost as xgb
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

# ============================================================
# PAGE CONFIG
# ============================================================
st.set_page_config(
    page_title="AI Portfolio Analyser",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================
# CUSTOM CSS
# ============================================================
st.markdown("""
<style>
    .main { background-color: #0e1117; }
    .block-container { padding-top: 1rem; }

    .metric-card {
        background: linear-gradient(135deg, #1e2130, #2d3250);
        border-radius: 12px;
        padding: 16px;
        border: 1px solid #3d4266;
        text-align: center;
    }
    .metric-label {
        font-size: 11px;
        color: #8892b0;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-bottom: 4px;
    }
    .metric-value {
        font-size: 22px;
        font-weight: 700;
        color: #ccd6f6;
    }
    .metric-positive { color: #64ffda; }
    .metric-negative { color: #ff6b6b; }

    .stock-card-profit {
        background: linear-gradient(135deg, #0d2818, #1a3a2a);
        border-left: 4px solid #64ffda;
        border-radius: 8px;
        padding: 12px;
        margin: 4px 0;
    }
    .stock-card-loss {
        background: linear-gradient(135deg, #2d0d0d, #3a1a1a);
        border-left: 4px solid #ff6b6b;
        border-radius: 8px;
        padding: 12px;
        margin: 4px 0;
    }
    .stock-card-watch {
        background: linear-gradient(135deg, #2d2500, #3a3200);
        border-left: 4px solid #ffd700;
        border-radius: 8px;
        padding: 12px;
        margin: 4px 0;
    }

    .rec-strong-buy {
        background: linear-gradient(135deg, #0d2818, #1a3a2a);
        border: 1px solid #64ffda;
        border-radius: 10px;
        padding: 14px;
        margin: 6px 0;
    }
    .rec-hold-add {
        background: linear-gradient(135deg, #0d1a2d, #1a2d4a);
        border: 1px solid #4fc3f7;
        border-radius: 10px;
        padding: 14px;
        margin: 6px 0;
    }
    .rec-hold {
        background: linear-gradient(135deg, #2d2500, #3a3200);
        border: 1px solid #ffd700;
        border-radius: 10px;
        padding: 14px;
        margin: 6px 0;
    }
    .rec-exit {
        background: linear-gradient(135deg, #2d0d0d, #3a1a1a);
        border: 1px solid #ff6b6b;
        border-radius: 10px;
        padding: 14px;
        margin: 6px 0;
    }

    .section-header {
        font-size: 18px;
        font-weight: 700;
        color: #ccd6f6;
        border-bottom: 2px solid #3d4266;
        padding-bottom: 8px;
        margin: 20px 0 16px 0;
    }

    .alert-critical {
        background: #2d0d0d;
        border: 1px solid #ff4444;
        border-radius: 8px;
        padding: 12px;
        margin: 4px 0;
    }
    .alert-profit {
        background: #0d2818;
        border: 1px solid #64ffda;
        border-radius: 8px;
        padding: 12px;
        margin: 4px 0;
    }
    .alert-review {
        background: #2d2500;
        border: 1px solid #ffd700;
        border-radius: 8px;
        padding: 12px;
        margin: 4px 0;
    }

    div[data-testid="stTabs"] button {
        font-size: 14px;
        font-weight: 600;
    }

    .stProgress > div > div {
        background: linear-gradient(90deg, #64ffda, #4fc3f7);
    }
</style>
""", unsafe_allow_html=True)

# ============================================================
# CONFIGURATION
# ============================================================
NEWS_API_KEY = "b27dc133689e4dff8b0ae65aba47511d"

PORTFOLIO = {
    "LG Electronics India":    {"ticker": "LGBBROSLTD.NS", "shares": 13,  "invested": 14820.00},
    "Bajaj Housing Finance":   {"ticker": "BAJAJHFL.NS",   "shares": 174, "invested": 23429.10},
    "Adani Green Energy":      {"ticker": "ADANIGREEN.NS", "shares": 8,   "invested": 7980.00},
    "Western Carriers":        {"ticker": "WCIL.NS",       "shares": 87,  "invested": 14964.00},
    "RECL":                    {"ticker": "RECLTD.NS",     "shares": 20,  "invested": 8043.40},
    "IRFC":                    {"ticker": "IRFC.NS",       "shares": 63,  "invested": 9424.80},
    "MIC Electronics":         {"ticker": "MICEL.NS",      "shares": 100, "invested": 5700.00},
    "Blue Cloud Softech":      {"ticker": "MANUAL",        "shares": 200, "invested": 5400.00, "manual_price": 19.49},
    "Best Agrolife":           {"ticker": "BESTAGRO.NS",   "shares": 150, "invested": 4300.50},
    "NHPC":                    {"ticker": "NHPC.NS",       "shares": 29,  "invested": 2755.00},
    "Yes Bank":                {"ticker": "YESBANK.NS",    "shares": 100, "invested": 2300.00},
    "Wipro":                   {"ticker": "WIPRO.NS",      "shares": 6,   "invested": 1500.00},
    "Orient Green Power":      {"ticker": "GREENPOWER.NS", "shares": 100, "invested": 1650.00},
    "Ola Electric":            {"ticker": "OLAELEC.NS",    "shares": 16,  "invested": 892.00},
    "GTL Infrastructure":      {"ticker": "GTLINFRA.NS",   "shares": 500, "invested": 1140.00},
    "Bajaj Hindusthan Sugar":  {"ticker": "BAJAJHIND.NS",  "shares": 28,  "invested": 588.00},
    "NTPC":                    {"ticker": "NTPC.NS",       "shares": 1,   "invested": 383.00},
    "Seacoast Shipping":       {"ticker": "MANUAL",        "shares": 211, "invested": 1331.41, "manual_price": 0.92},
}

MUTUAL_FUNDS = [
    {"name": "Motilal Oswal Nifty India Defence Index Fund", "invested": 19499, "current": 22522},
    {"name": "JioBlackRock Flexi Cap Fund Direct Growth",    "invested": 11999, "current": 11936},
]

ILLIQUID = ["Blue Cloud Softech", "Seacoast Shipping"]

STOCK_SECTORS = {
    "LG Electronics India":    "Consumer Cyclical",
    "Bajaj Housing Finance":   "Financial Services",
    "Adani Green Energy":      "Utilities",
    "Western Carriers":        "Industrials",
    "RECL":                    "Financial Services",
    "IRFC":                    "Financial Services",
    "MIC Electronics":         "Technology",
    "Best Agrolife":           "Basic Materials",
    "NHPC":                    "Utilities",
    "Yes Bank":                "Financial Services",
    "Wipro":                   "Technology",
    "Orient Green Power":      "Utilities",
    "Ola Electric":            "Consumer Cyclical",
    "GTL Infrastructure":      "Technology",
    "Bajaj Hindusthan Sugar":  "Consumer Defensive",
    "NTPC":                    "Utilities",
    "Blue Cloud Softech":      "Technology",
    "Seacoast Shipping":       "Industrials",
}

NIFTY50 = {
    "Reliance Industries": "RELIANCE.NS",
    "TCS": "TCS.NS",
    "HDFC Bank": "HDFCBANK.NS",
    "Infosys": "INFY.NS",
    "ICICI Bank": "ICICIBANK.NS",
    "Bharti Airtel": "BHARTIARTL.NS",
    "State Bank of India": "SBIN.NS",
    "Bajaj Finance": "BAJFINANCE.NS",
    "HUL": "HINDUNILVR.NS",
    "ITC": "ITC.NS",
    "Larsen & Toubro": "LT.NS",
    "Kotak Mahindra Bank": "KOTAKBANK.NS",
    "Axis Bank": "AXISBANK.NS",
    "Sun Pharma": "SUNPHARMA.NS",
    "Maruti Suzuki": "MARUTI.NS",
    "HCL Technologies": "HCLTECH.NS",
    "Titan Company": "TITAN.NS",
    "Power Grid": "POWERGRID.NS",
    "NTPC": "NTPC.NS",
    "Wipro": "WIPRO.NS",
    "Tech Mahindra": "TECHM.NS",
    "Coal India": "COALINDIA.NS",
    "ONGC": "ONGC.NS",
    "Tata Motors": "TATAMOTORS.NS",
    "Cipla": "CIPLA.NS",
    "BEL": "BEL.NS",
    "Hindalco": "HINDALCO.NS",
    "Apollo Hospitals": "APOLLOHOSP.NS",
    "Dr Reddy's": "DRREDDY.NS",
    "Britannia": "BRITANNIA.NS",
}

# ============================================================
# DATA FUNCTIONS
# ============================================================

@st.cache_data(ttl=300)
def fetch_prices():
    results = {}
    for name, details in PORTFOLIO.items():
        try:
            if details["ticker"] == "MANUAL":
                price = details["manual_price"]
            else:
                hist  = yf.Ticker(details["ticker"]).history(period="2d")
                price = round(hist["Close"].iloc[-1], 2) if not hist.empty else None

            if price:
                value   = round(price * details["shares"], 2)
                pnl     = round(value - details["invested"], 2)
                pnl_pct = round((pnl / details["invested"]) * 100, 2)
                results[name] = {
                    "price": price, "value": value,
                    "pnl": pnl, "pnl_pct": pnl_pct,
                    "invested": details["invested"],
                    "shares": details["shares"]
                }
        except:
            results[name] = {
                "price": 0, "value": 0,
                "pnl": 0, "pnl_pct": 0,
                "invested": details["invested"],
                "shares": details["shares"]
            }
    return results

@st.cache_data(ttl=3600)
def fetch_sentiment():
    newsapi = NewsApiClient(api_key=NEWS_API_KEY)
    pos_words = ['growth','profit','surge','rise','gain','strong',
                 'upgrade','record','expand','win','positive',
                 'increase','boost','rally','outperform','dividend','beat']
    neg_words = ['loss','fall','drop','decline','weak','sell',
                 'downgrade','concern','risk','crash','trouble',
                 'fraud','debt','default','cut','miss','below']

    queries = {
        "LG Electronics India": "LG Electronics India",
        "Bajaj Housing Finance": "Bajaj Housing Finance",
        "Adani Green Energy": "Adani Green Energy",
        "Western Carriers": "Western Carriers India",
        "RECL": "REC Limited India power",
        "IRFC": "IRFC Indian Railway Finance",
        "MIC Electronics": "MIC Electronics India",
        "Best Agrolife": "Best Agrolife India",
        "NHPC": "NHPC India hydropower",
        "Yes Bank": "Yes Bank India",
        "Wipro": "Wipro India IT",
        "Orient Green Power": "Orient Green Power India",
        "Ola Electric": "Ola Electric India",
        "GTL Infrastructure": "GTL Infrastructure India",
        "Bajaj Hindusthan Sugar": "Bajaj Hindusthan Sugar",
        "NTPC": "NTPC India power",
        "Blue Cloud Softech": "Blue Cloud Softech",
        "Seacoast Shipping": "Seacoast Shipping India",
    }

    scores = {}
    for name, query in queries.items():
        try:
            articles = newsapi.get_everything(
                q=query, language='en', sort_by='publishedAt',
                page_size=5,
                from_param=(datetime.datetime.now() -
                           datetime.timedelta(days=7)).strftime('%Y-%m-%d')
            )
            score = 0
            headlines = []
            for article in articles.get('articles', []):
                title = article['title'].lower()
                headlines.append(article['title'])
                for w in pos_words:
                    if w in title: score += 1
                for w in neg_words:
                    if w in title: score -= 1
            scores[name] = {"score": score, "headlines": headlines[:3]}
        except:
            scores[name] = {"score": 0, "headlines": []}
    return scores

@st.cache_data(ttl=3600)
def fetch_fundamentals():
    ticker_map = {k: v["ticker"] for k, v in PORTFOLIO.items()
                  if v["ticker"] != "MANUAL"}
    ticker_map["Blue Cloud Softech"] = "BLUECLOUDS.BO"
    ticker_map["Seacoast Shipping"]  = "SEACOAST.BO"

    data = {}
    for name, ticker in ticker_map.items():
        try:
            info = yf.Ticker(ticker).info
            data[name] = {
                "pe":  round(info.get("trailingPE", 0) or 0, 2),
                "pb":  round(info.get("priceToBook", 0) or 0, 2),
                "roe": round((info.get("returnOnEquity", 0) or 0) * 100, 2),
                "de":  round(info.get("debtToEquity", 0) or 0, 2),
                "eps": round(info.get("trailingEps", 0) or 0, 2),
            }
        except:
            data[name] = {"pe": 0, "pb": 0, "roe": 0, "de": 0, "eps": 0}
    return data

def get_geo_scores():
    geo_factors = {
        "India-Pakistan Tensions":    {"sectors": ["Defence","Energy","Utilities"],          "score": 3},
        "US-China Trade War":         {"sectors": ["Technology","Consumer Cyclical"],         "score": 2},
        "Global Crude Oil Prices":    {"sectors": ["Utilities","Industrials","Consumer Defensive"], "score": -2},
        "RBI Interest Rate Policy":   {"sectors": ["Financial Services","Utilities"],         "score": 2},
        "India Green Energy Push":    {"sectors": ["Utilities","Technology"],                 "score": 2},
        "India Infrastructure Spend": {"sectors": ["Industrials","Technology","Financial Services"], "score": 2},
    }
    scores = {}
    for stock, sector in STOCK_SECTORS.items():
        scores[stock] = sum(
            d["score"] for d in geo_factors.values()
            if sector in d["sectors"]
        )
    return scores

def fund_score(pe, pb, de, eps, roe):
    s = 0
    if pe:  s += 2 if pe<15 else (1 if pe<25 else (0 if pe<40 else -1))
    if pb:  s += 2 if pb<1.5 else (1 if pb<3 else -1)
    if de:  s += 2 if de<30 else (1 if de<100 else (-1 if de<300 else -2))
    if eps: s += 2 if eps>10 else (1 if eps>0 else -2)
    if roe: s += 2 if roe>15 else (1 if roe>8 else -1)
    return s

def get_recommendations(prices, sentiment, fundamentals, geo_scores):
    recs = {}
    for stock in STOCK_SECTORS:
        pnl  = prices.get(stock, {}).get("pnl_pct", 0)
        sent = sentiment.get(stock, {}).get("score", 0)
        f    = fundamentals.get(stock, {})
        fs   = fund_score(f.get("pe"), f.get("pb"),
                          f.get("de"), f.get("eps"), f.get("roe"))
        geo  = geo_scores.get(stock, 0)

        ps = (3 if pnl>30 else 2 if pnl>10 else 1 if pnl>0
              else -1 if pnl>-15 else -2 if pnl>-30 else -3)

        total = ps + sent + fs + geo
        if stock in ILLIQUID: total -= 5

        if total >= 10:   action, color, w, m, y = "🟢 STRONG BUY",  "#64ffda", 88, 85, 90
        elif total >= 7:  action, color, w, m, y = "🟢 HOLD / ADD",  "#4fc3f7", 75, 72, 80
        elif total >= 4:  action, color, w, m, y = "🟡 HOLD",        "#ffd700", 62, 64, 70
        elif total >= 1:  action, color, w, m, y = "🟡 WATCH",       "#ffab40", 52, 55, 60
        elif total >= -2: action, color, w, m, y = "🔴 REDUCE",      "#ff6b6b", 64, 62, 58
        else:             action, color, w, m, y = "🔴 EXIT",        "#ff4444", 78, 76, 72

        if stock in ILLIQUID: action += " ⚠️"

        recs[stock] = {
            "action": action, "color": color,
            "total": total, "fund_score": fs,
            "geo": geo, "sentiment": sent,
            "week": w, "month": m, "year": y,
            "pnl_pct": pnl
        }
    return recs

@st.cache_data(ttl=300)
def scan_nifty50():
    results = {}
    owned   = list(PORTFOLIO.keys())

    for name, ticker in NIFTY50.items():
        try:
            info  = yf.Ticker(ticker).info
            pe    = info.get("trailingPE")
            pb    = info.get("priceToBook")
            roe   = info.get("returnOnEquity")
            de    = info.get("debtToEquity")
            eps   = info.get("trailingEps")
            price = info.get("currentPrice") or info.get("regularMarketPrice")
            h52   = info.get("fiftyTwoWeekHigh")
            l52   = info.get("fiftyTwoWeekLow")
            div   = info.get("dividendYield")
            sector= info.get("sector","N/A")
            mcap  = info.get("marketCap", 0)

            w52 = round(((price-l52)/(h52-l52))*100, 1) if (
                h52 and l52 and price and h52!=l52) else 50

            score = 0
            if pe:
                score += 3 if pe<15 else 2 if pe<20 else 1 if pe<30 else 0
            if pb:
                score += 2 if pb<2 else 1 if pb<3.5 else 0
            if roe:
                r = roe*100
                score += 3 if r>20 else 2 if r>15 else 1 if r>10 else 0
            if de:
                score += 2 if de<30 else 1 if de<80 else 0
            if eps:
                score += 2 if eps>50 else 1 if eps>10 else -2 if eps<0 else 0
            if w52 < 25:   score += 3
            elif w52 < 40: score += 2
            elif w52 < 55: score += 1
            if div and div > 0.015: score += 1

            already = any(name.lower() in k.lower() or
                         k.lower() in name.lower() for k in owned)

            results[name] = {
                "score": score, "pe": pe, "pb": pb,
                "roe": round(roe*100,1) if roe else None,
                "sector": sector, "w52": w52,
                "price": price, "mcap": mcap,
                "already": already
            }
            time.sleep(0.1)
        except:
            results[name] = {"score": 0, "already": False}
    return results

# ============================================================
# SIDEBAR
# ============================================================
with st.sidebar:
    st.markdown("## 🤖 AI Portfolio Analyser")
    st.markdown("**v3.0** | Built by Takhar & Claude AI")
    st.divider()

    st.markdown(f"📅 **{datetime.datetime.now().strftime('%d %B %Y')}**")
    st.markdown(f"🕐 **{datetime.datetime.now().strftime('%I:%M %p')}**")
    st.divider()

    if st.button("🔄 Refresh All Data", use_container_width=True,
                 type="primary"):
        st.cache_data.clear()
        st.rerun()

    st.divider()
    st.markdown("### ⚙️ Settings")
    show_charts = st.toggle("Show Charts", value=True)
    show_news   = st.toggle("Show News", value=True)
    conf_threshold = st.slider("ML Confidence Threshold", 50, 80, 65)

    st.divider()
    st.markdown("### 📊 Quick Stats")
    total_inv = sum(d["invested"] for d in PORTFOLIO.values())
    st.metric("Total Invested", f"₹{total_inv:,.0f}")

    mf_pnl = sum(m["current"] - m["invested"] for m in MUTUAL_FUNDS)
    st.metric("SIP Returns", f"+₹{mf_pnl:,.0f}",
              f"+{round(mf_pnl/sum(m['invested'] for m in MUTUAL_FUNDS)*100,1)}%")

    st.divider()
    st.markdown("""
    <div style='font-size:10px; color:#8892b0; text-align:center'>
    ⚠️ Not SEBI registered.<br>
    Personal research only.<br>
    Not financial advice.
    </div>
    """, unsafe_allow_html=True)

# ============================================================
# MAIN CONTENT
# ============================================================
st.markdown("# 🤖 AI Portfolio Analyser")
st.markdown("*5-Layer Intelligence: Price · Sentiment · Fundamentals · Geopolitical · ML*")
st.divider()

# Load data with progress
with st.spinner("🔄 Loading live market data..."):
    prices       = fetch_prices()
    sentiment    = fetch_sentiment()
    fundamentals = fetch_fundamentals()
    geo_scores   = get_geo_scores()
    recs         = get_recommendations(prices, sentiment, fundamentals, geo_scores)

# Portfolio totals
total_invested = sum(d["invested"] for d in prices.values())
total_current  = sum(d["value"] for d in prices.values())
total_pnl      = round(total_current - total_invested, 2)
total_pnl_pct  = round((total_pnl / total_invested) * 100, 2)

# ============================================================
# TABS
# ============================================================
tab1, tab2, tab3, tab4, tab5,
