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

# NEW: Sentiment Upgrade
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

# (UNCHANGED DATA STRUCTURES — SAME AS YOUR CODE)

# ---------------- INIT ----------------
def init_portfolio():
    if "portfolio" not in st.session_state:
        st.session_state.portfolio = DEFAULT_PORTFOLIO.copy()
    if "mutual_funds" not in st.session_state:
        st.session_state.mutual_funds = list(DEFAULT_MUTUAL_FUNDS)

# ---------------- PRICE FETCH ----------------
@st.cache_data(ttl=300)
def fetch_prices(portfolio_key):
    portfolio = st.session_state.portfolio
    results = {}
    for name, details in portfolio.items():
        try:
            if details["ticker"] == "MANUAL":
                price = details.get("manual_price", 0)
            else:
                hist = yf.Ticker(details["ticker"]).history(period="2d")
                price = round(hist["Close"].iloc[-1], 2) if not hist.empty else None

            if price:
                value = round(price * details["shares"], 2)
                pnl = round(value - details["invested"], 2)
                pnl_pct = round((pnl / details["invested"]) * 100, 2)
                avg_buy = round(details["invested"] / details["shares"], 2)

                results[name] = {
                    "price": price,
                    "value": value,
                    "pnl": pnl,
                    "pnl_pct": pnl_pct,
                    "invested": details["invested"],
                    "shares": details["shares"],
                    "avg_buy": avg_buy
                }
        except:
            continue
    return results

# ---------------- SENTIMENT (FIXED) ----------------
@st.cache_data(ttl=3600)
def fetch_sentiment():
    newsapi = NewsApiClient(api_key=NEWS_API_KEY)
    sia = SentimentIntensityAnalyzer()

    queries = {k: k for k in DEFAULT_PORTFOLIO.keys()}
    scores = {}

    for name, query in queries.items():
        try:
            articles = newsapi.get_everything(
                q=query,
                language='en',
                sort_by='publishedAt',
                page_size=5,
                from_param=(
                    datetime.datetime.now() - datetime.timedelta(days=7)
                ).strftime('%Y-%m-%d')
            )

            compound_scores = []
            headlines = []

            for article in articles.get('articles', []):
                title = article['title']
                headlines.append(title)

                sentiment = sia.polarity_scores(title)
                compound_scores.append(sentiment['compound'])

            avg_score = np.mean(compound_scores) if compound_scores else 0
            final_score = round(avg_score * 5)

            scores[name] = {
                "score": final_score,
                "raw": round(avg_score, 3),
                "headlines": headlines[:3]
            }

        except:
            scores[name] = {"score": 0, "raw": 0, "headlines": []}

    return scores

# ---------------- RISK ENGINE (NEW) ----------------
@st.cache_data(ttl=1800)
def fetch_risk_metrics():
    portfolio = st.session_state.portfolio
    risk_data = {}

    for name, details in portfolio.items():
        try:
            if details["ticker"] == "MANUAL":
                continue

            hist = yf.Ticker(details["ticker"]).history(period="6mo")
            if hist.empty:
                continue

            returns = hist["Close"].pct_change().dropna()

            volatility = returns.std() * np.sqrt(252)
            avg_return = returns.mean() * 252
            sharpe = avg_return / volatility if volatility != 0 else 0

            risk_data[name] = {
                "volatility": round(volatility, 2),
                "sharpe": round(sharpe, 2)
            }

        except:
            risk_data[name] = {"volatility": 0, "sharpe": 0}

    return risk_data

# ---------------- FUNDAMENTALS ----------------
@st.cache_data(ttl=3600)
def fetch_fundamentals():
    portfolio = st.session_state.portfolio
    data = {}
    for name, details in portfolio.items():
        try:
            if details["ticker"] == "MANUAL":
                continue

            info = yf.Ticker(details["ticker"]).info
            data[name] = {
                "pe": round(info.get("trailingPE") or 0, 2),
                "pb": round(info.get("priceToBook") or 0, 2),
                "roe": round((info.get("returnOnEquity") or 0) * 100, 2),
                "de": round(info.get("debtToEquity") or 0, 2),
                "eps": round(info.get("trailingEps") or 0, 2),
            }
        except:
            data[name] = {"pe": 0, "pb": 0, "roe": 0, "de": 0, "eps": 0}
    return data

# ---------------- FUND SCORE ----------------
def fund_score(pe, pb, de, eps, roe):
    s = 0
    if pe: s += 2 if pe < 15 else 1 if pe < 25 else -1
    if pb: s += 2 if pb < 1.5 else 1 if pb < 3 else -1
    if de: s += 2 if de < 30 else 1 if de < 100 else -2
    if eps: s += 2 if eps > 10 else 1 if eps > 0 else -2
    if roe: s += 2 if roe > 15 else 1 if roe > 8 else -1
    return s

# ---------------- RECOMMENDATION ENGINE (UPDATED) ----------------
def get_recommendations(prices, sentiment, fundamentals, geo_scores, risk_data):
    recs = {}

    for stock in prices:
        pnl = prices.get(stock, {}).get("pnl_pct", 0)
        sent = sentiment.get(stock, {}).get("score", 0)
        f = fundamentals.get(stock, {})
        fs = fund_score(f.get("pe"), f.get("pb"), f.get("de"), f.get("eps"), f.get("roe"))
        geo = geo_scores.get(stock, 0)

        # Risk Integration
        risk = risk_data.get(stock, {})
        vol = risk.get("volatility", 0)
        sharpe = risk.get("sharpe", 0)

        risk_score = 0
        if vol > 0.6:
            risk_score -= 2
        elif vol > 0.4:
            risk_score -= 1
        elif vol < 0.25:
            risk_score += 1

        if sharpe > 1:
            risk_score += 2
        elif sharpe > 0.5:
            risk_score += 1
        elif sharpe < 0:
            risk_score -= 2

        ps = 3 if pnl > 30 else 2 if pnl > 10 else 1 if pnl > 0 else -2

        total = ps + sent + fs + geo + risk_score

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
            "total": total,
            "risk_score": risk_score,
            "volatility": vol,
            "sharpe": sharpe
        }

    return recs

# ---------------- MAIN ----------------
init_portfolio()

portfolio_key = str(sorted([
    (k, v["shares"], v["invested"])
    for k, v in st.session_state.portfolio.items()
]))

prices = fetch_prices(portfolio_key)
sentiment = fetch_sentiment()
fundamentals = fetch_fundamentals()
risk_data = fetch_risk_metrics()

geo_scores = {k: 0 for k in prices}  # unchanged placeholder

recs = get_recommendations(prices, sentiment, fundamentals, geo_scores, risk_data)

st.title("AI Portfolio Analyser (Upgraded)")

for stock, r in recs.items():
    st.write(f"{stock} → {r['action']} | Score: {r['total']} | Risk: {r['risk_score']}")
    
