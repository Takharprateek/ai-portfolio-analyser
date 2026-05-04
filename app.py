import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import datetime
import time
import warnings
warnings.filterwarnings('ignore')

from newsapi import NewsApiClient
import plotly.graph_objects as go

# Sentiment Upgrade
from nltk.sentiment.vader import SentimentIntensityAnalyzer
import nltk
nltk.download('vader_lexicon')

st.set_page_config(
    page_title="AI Portfolio Analyser",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

NEWS_API_KEY = "b27dc133689e4dff8b0ae65aba47511d"

# ---------------- FULL ORIGINAL DATA ----------------
DEFAULT_PORTFOLIO = {
    "LG Electronics India": {"ticker": "LGBBROSLTD.NS", "shares": 13, "invested": 14820.00},
    "Bajaj Housing Finance": {"ticker": "BAJAJHFL.NS", "shares": 174, "invested": 23429.10},
    "Adani Green Energy": {"ticker": "ADANIGREEN.NS", "shares": 8, "invested": 7980.00},
    "Western Carriers": {"ticker": "WCIL.NS", "shares": 87, "invested": 14964.00},
    "RECL": {"ticker": "RECLTD.NS", "shares": 20, "invested": 8043.40},
    "IRFC": {"ticker": "IRFC.NS", "shares": 63, "invested": 9424.80},
    "MIC Electronics": {"ticker": "MICEL.NS", "shares": 100, "invested": 5700.00},
    "Blue Cloud Softech": {"ticker": "MANUAL", "shares": 200, "invested": 5400.00, "manual_price": 19.49},
    "Best Agrolife": {"ticker": "BESTAGRO.NS", "shares": 150, "invested": 4300.50},
    "NHPC": {"ticker": "NHPC.NS", "shares": 29, "invested": 2755.00},
    "Yes Bank": {"ticker": "YESBANK.NS", "shares": 100, "invested": 2300.00},
    "Wipro": {"ticker": "WIPRO.NS", "shares": 6, "invested": 1500.00},
    "Orient Green Power": {"ticker": "GREENPOWER.NS", "shares": 100, "invested": 1650.00},
    "Ola Electric": {"ticker": "OLAELEC.NS", "shares": 16, "invested": 892.00},
    "GTL Infrastructure": {"ticker": "GTLINFRA.NS", "shares": 500, "invested": 1140.00},
    "Bajaj Hindusthan Sugar": {"ticker": "BAJAJHIND.NS", "shares": 28, "invested": 588.00},
    "NTPC": {"ticker": "NTPC.NS", "shares": 1, "invested": 383.00},
    "Seacoast Shipping": {"ticker": "MANUAL", "shares": 211, "invested": 1331.41, "manual_price": 0.92},
}

STOCK_SECTORS = {
    "LG Electronics India": "Consumer Cyclical",
    "Bajaj Housing Finance": "Financial Services",
    "Adani Green Energy": "Utilities",
    "Western Carriers": "Industrials",
    "RECL": "Financial Services",
    "IRFC": "Financial Services",
    "MIC Electronics": "Technology",
    "Best Agrolife": "Basic Materials",
    "NHPC": "Utilities",
    "Yes Bank": "Financial Services",
    "Wipro": "Technology",
    "Orient Green Power": "Utilities",
    "Ola Electric": "Consumer Cyclical",
    "GTL Infrastructure": "Technology",
    "Bajaj Hindusthan Sugar": "Consumer Defensive",
    "NTPC": "Utilities",
    "Blue Cloud Softech": "Technology",
    "Seacoast Shipping": "Industrials",
}

GEO_FACTORS = {
    "India-Pakistan Tensions": {"sectors": ["Utilities"], "score": 2},
    "US-China Trade War": {"sectors": ["Technology"], "score": 2},
    "Interest Rates": {"sectors": ["Financial Services"], "score": 2},
}

# ---------------- INIT ----------------
def init_portfolio():
    if "portfolio" not in st.session_state:
        st.session_state.portfolio = DEFAULT_PORTFOLIO.copy()

# ---------------- PRICE ----------------
@st.cache_data(ttl=300)
def fetch_prices(portfolio_key):
    results = {}
    for name, d in st.session_state.portfolio.items():
        try:
            if d["ticker"] == "MANUAL":
                price = d.get("manual_price", 0)
            else:
                hist = yf.Ticker(d["ticker"]).history(period="2d")
                price = hist["Close"].iloc[-1]

            value = price * d["shares"]
            pnl = value - d["invested"]
            pnl_pct = (pnl / d["invested"]) * 100

            results[name] = {
                "price": round(price, 2),
                "pnl_pct": round(pnl_pct, 2)
            }
        except:
            continue
    return results

# ---------------- SENTIMENT (UPGRADED) ----------------
@st.cache_data(ttl=3600)
def fetch_sentiment():
    newsapi = NewsApiClient(api_key=NEWS_API_KEY)
    sia = SentimentIntensityAnalyzer()
    scores = {}

    for stock in DEFAULT_PORTFOLIO:
        try:
            articles = newsapi.get_everything(q=stock, page_size=5)
            vals = []

            for a in articles["articles"]:
                s = sia.polarity_scores(a["title"])
                vals.append(s["compound"])

            avg = np.mean(vals) if vals else 0
            scores[stock] = {"score": round(avg * 5)}

        except:
            scores[stock] = {"score": 0}

    return scores

# ---------------- RISK ENGINE ----------------
@st.cache_data(ttl=1800)
def fetch_risk_metrics():
    data = {}
    for name, d in st.session_state.portfolio.items():
        try:
            if d["ticker"] == "MANUAL":
                continue

            hist = yf.Ticker(d["ticker"]).history(period="6mo")
            returns = hist["Close"].pct_change().dropna()

            vol = returns.std() * np.sqrt(252)
            sharpe = returns.mean() / returns.std() if returns.std() != 0 else 0

            data[name] = {
                "volatility": round(vol, 2),
                "sharpe": round(sharpe, 2)
            }
        except:
            data[name] = {"volatility": 0, "sharpe": 0}
    return data

# ---------------- GEO ----------------
def get_geo_scores():
    scores = {}
    for stock, sector in STOCK_SECTORS.items():
        scores[stock] = sum(
            f["score"] for f in GEO_FACTORS.values()
            if sector in f["sectors"]
        )
    return scores

# ---------------- RECOMMENDATION ----------------
def get_recommendations(prices, sentiment, geo, risk):
    recs = {}

    for stock in prices:
        pnl = prices[stock]["pnl_pct"]
        sent = sentiment.get(stock, {}).get("score", 0)
        geo_s = geo.get(stock, 0)

        r = risk.get(stock, {})
        vol = r.get("volatility", 0)
        sharpe = r.get("sharpe", 0)

        risk_score = 0
        if vol > 0.6: risk_score -= 2
        elif vol > 0.4: risk_score -= 1
        elif vol < 0.25: risk_score += 1

        if sharpe > 1: risk_score += 2
        elif sharpe > 0.5: risk_score += 1
        elif sharpe < 0: risk_score -= 2

        ps = 3 if pnl > 30 else 2 if pnl > 10 else 1 if pnl > 0 else -2

        total = ps + sent + geo_s + risk_score

        if total >= 10:
            action = "STRONG BUY"
        elif total >= 7:
            action = "HOLD / ADD"
        elif total >= 4:
            action = "HOLD"
        elif total >= 1:
            action = "WATCH"
        elif total >= -2:
            action = "REDUCE"
        else:
            action = "EXIT"

        recs[stock] = {
            "action": action,
            "score": total,
            "volatility": vol,
            "sharpe": sharpe
        }

    return recs

# ---------------- RUN ----------------
init_portfolio()

portfolio_key = str(st.session_state.portfolio)

prices = fetch_prices(portfolio_key)
sentiment = fetch_sentiment()
geo = get_geo_scores()
risk = fetch_risk_metrics()

recs = get_recommendations(prices, sentiment, geo, risk)

st.title("AI Portfolio Analyser (Full + Upgraded)")

for s, r in recs.items():
    st.write(f"{s} → {r['action']} | Score: {r['score']} | Vol: {r['volatility']} | Sharpe: {r['sharpe']}")
