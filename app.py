import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import datetime
import time
import warnings
warnings.filterwarnings('ignore')

from newsapi import NewsApiClient
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import plotly.graph_objects as go


# ── FIX: analyzer_score defined BEFORE any tab uses it ──────────────────────
def analyzer_score(text):
    try:
        _analyzer = SentimentIntensityAnalyzer()
        return _analyzer.polarity_scores(text)['compound']
    except Exception:
        return 0


st.set_page_config(
    page_title="AI Portfolio Analyser",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
.risk-card {
    background: linear-gradient(135deg, #1a1f35, #252b45);
    border-radius: 10px;
    padding: 15px;
    border: 1px solid #3d4266;
    margin: 5px 0;
}
.alloc-bar {
    height: 8px;
    border-radius: 4px;
    background: linear-gradient(90deg, #64ffda, #4fc3f7);
    margin: 4px 0;
}
</style>
""", unsafe_allow_html=True)

NEWS_API_KEY = "b27dc133689e4dff8b0ae65aba47511d"

DEFAULT_PORTFOLIO = {
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

DEFAULT_MUTUAL_FUNDS = [
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

GEO_FACTORS = {
    "India-Pakistan Tensions": {
        "sectors": ["Defence", "Energy", "Utilities"],
        "score": 3, "severity": "HIGH",
        "impact": "POSITIVE for Defence | NEGATIVE for Banking"
    },
    "US-China Trade War": {
        "sectors": ["Technology", "Consumer Cyclical"],
        "score": 2, "severity": "HIGH",
        "impact": "POSITIVE for Indian IT exports"
    },
    "Global Crude Oil Prices": {
        "sectors": ["Utilities", "Industrials", "Consumer Defensive"],
        "score": -2, "severity": "MEDIUM",
        "impact": "HIGH crude = NEGATIVE for energy sectors"
    },
    "RBI Interest Rate Policy": {
        "sectors": ["Financial Services", "Utilities"],
        "score": 2, "severity": "MEDIUM",
        "impact": "Rate cuts POSITIVE for NBFCs"
    },
    "India Green Energy Push": {
        "sectors": ["Utilities", "Technology"],
        "score": 2, "severity": "MEDIUM",
        "impact": "POSITIVE for renewables long term"
    },
    "India Infrastructure Spend": {
        "sectors": ["Industrials", "Technology", "Financial Services"],
        "score": 2, "severity": "MEDIUM",
        "impact": "POSITIVE for logistics and lending"
    },
}

NIFTY50 = {
    "Reliance Industries": "RELIANCE.NS",
    "TCS":                 "TCS.NS",
    "HDFC Bank":           "HDFCBANK.NS",
    "Infosys":             "INFY.NS",
    "ICICI Bank":          "ICICIBANK.NS",
    "Bharti Airtel":       "BHARTIARTL.NS",
    "State Bank of India": "SBIN.NS",
    "Bajaj Finance":       "BAJFINANCE.NS",
    "HUL":                 "HINDUNILVR.NS",
    "ITC":                 "ITC.NS",
    "Larsen & Toubro":     "LT.NS",
    "Kotak Mahindra Bank": "KOTAKBANK.NS",
    "Axis Bank":           "AXISBANK.NS",
    "Sun Pharma":          "SUNPHARMA.NS",
    "Maruti Suzuki":       "MARUTI.NS",
    "HCL Technologies":    "HCLTECH.NS",
    "Titan Company":       "TITAN.NS",
    "Power Grid":          "POWERGRID.NS",
    "Coal India":          "COALINDIA.NS",
    "Tech Mahindra":       "TECHM.NS",
    "Apollo Hospitals":    "APOLLOHOSP.NS",
    "Dr Reddys":           "DRREDDY.NS",
    "Cipla":               "CIPLA.NS",
    "BEL":                 "BEL.NS",
    "Hindalco":            "HINDALCO.NS",
}

SIP_RECS = [
    {"priority": 1, "fund": "Nifty 50 Index Fund (Direct)",
     "examples": "UTI / HDFC / Nippon Nifty 50",
     "amount": 1500, "risk": "LOW", "cagr": "12-14%",
     "action": "START IMMEDIATELY",
     "why": "Core anchor. Beats FD consistently over 5+ years."},
    {"priority": 2, "fund": "Nifty Next 50 Index Fund (Direct)",
     "examples": "UTI / ICICI Pru Nifty Next 50",
     "amount": 1000, "risk": "LOW-MEDIUM", "cagr": "14-16%",
     "action": "START IMMEDIATELY",
     "why": "Higher growth than Nifty 50 at moderate risk."},
    {"priority": 3, "fund": "Defence Index Fund - Increase",
     "examples": "Motilal Oswal Nifty India Defence (You own this)",
     "amount": 1000, "risk": "MEDIUM", "cagr": "18-22%",
     "action": "INCREASE EXISTING SIP",
     "why": "Already +15.5%. India-Pakistan tensions = strong tailwind."},
    {"priority": 4, "fund": "Balanced Advantage Fund (Direct)",
     "examples": "HDFC / ICICI Pru Balanced Advantage",
     "amount": 700, "risk": "LOW-MEDIUM", "cagr": "10-12%",
     "action": "START WITHIN 2 WEEKS",
     "why": "Auto-balances equity vs debt. Reduces volatility."},
    {"priority": 5, "fund": "Pharma & Healthcare Fund (Direct)",
     "examples": "Nippon / Mirae / SBI Healthcare",
     "amount": 500, "risk": "MEDIUM", "cagr": "15-18%",
     "action": "START WITHIN 1 MONTH",
     "why": "Missing from portfolio. Defensive sector."},
    {"priority": 6, "fund": "Gold ETF (Direct)",
     "examples": "Nippon / HDFC / Axis Gold Fund",
     "amount": 300, "risk": "LOW", "cagr": "8-10%",
     "action": "START WITHIN 1 MONTH",
     "why": "Inflation hedge. Geopolitical risk protection."},
]


def init_portfolio():
    if "portfolio" not in st.session_state:
        st.session_state.portfolio = {k: dict(v) for k, v in DEFAULT_PORTFOLIO.items()}
    if "mutual_funds" not in st.session_state:
        st.session_state.mutual_funds = [dict(m) for m in DEFAULT_MUTUAL_FUNDS]


@st.cache_data(ttl=300)
def fetch_prices(portfolio_key):
    portfolio = st.session_state.portfolio
    results   = {}
    for name, details in portfolio.items():
        try:
            if details["ticker"] == "MANUAL":
                price = details.get("manual_price", 0)
            else:
                hist  = yf.Ticker(details["ticker"]).history(period="2d")
                price = round(hist["Close"].iloc[-1], 2) if not hist.empty else None
            if price:
                value   = round(price * details["shares"], 2)
                pnl     = round(value - details["invested"], 2)
                pnl_pct = round((pnl / details["invested"]) * 100, 2)
                avg_buy = round(details["invested"] / max(details["shares"], 1), 2)
                results[name] = {
                    "price": price, "value": value,
                    "pnl": pnl, "pnl_pct": pnl_pct,
                    "invested": details["invested"],
                    "shares": details["shares"],
                    "avg_buy": avg_buy
                }
        except Exception:
            avg_buy = round(details["invested"] / max(details["shares"], 1), 2)
            results[name] = {
                "price": avg_buy, "value": details["invested"],
                "pnl": 0, "pnl_pct": 0,
                "invested": details["invested"],
                "shares": details["shares"],
                "avg_buy": avg_buy
            }
    return results


@st.cache_data(ttl=3600)
def fetch_sentiment_vader():
    newsapi  = NewsApiClient(api_key=NEWS_API_KEY)
    analyzer = SentimentIntensityAnalyzer()
    queries  = {
        "LG Electronics India":    "LG Electronics India stock",
        "Bajaj Housing Finance":   "Bajaj Housing Finance stock",
        "Adani Green Energy":      "Adani Green Energy stock",
        "Western Carriers":        "Western Carriers India logistics",
        "RECL":                    "REC Limited India power finance",
        "IRFC":                    "IRFC Indian Railway Finance",
        "MIC Electronics":         "MIC Electronics India",
        "Best Agrolife":           "Best Agrolife India agro",
        "NHPC":                    "NHPC India hydropower",
        "Yes Bank":                "Yes Bank India",
        "Wipro":                   "Wipro India IT results",
        "Orient Green Power":      "Orient Green Power India",
        "Ola Electric":            "Ola Electric India scooter",
        "GTL Infrastructure":      "GTL Infrastructure India telecom",
        "Bajaj Hindusthan Sugar":  "Bajaj Hindusthan Sugar India",
        "NTPC":                    "NTPC India power electricity",
        "Blue Cloud Softech":      "Blue Cloud Softech India",
        "Seacoast Shipping":       "Seacoast Shipping India",
    }
    scores = {}
    for name, query in queries.items():
        try:
            articles = newsapi.get_everything(
                q=query, language='en', sort_by='publishedAt', page_size=10,
                from_param=(datetime.datetime.now() - datetime.timedelta(days=7)).strftime('%Y-%m-%d')
            )
            compound_scores = []
            headlines       = []
            for article in articles.get('articles', []):
                title = article.get('title', '')
                desc  = article.get('description', '') or ''
                text  = title + ' ' + desc
                headlines.append(title)
                compound_scores.append(analyzer.polarity_scores(text)['compound'])

            if compound_scores:
                avg_compound = round(np.mean(compound_scores), 3)
                pos_count    = sum(1 for s in compound_scores if s > 0.05)
                neg_count    = sum(1 for s in compound_scores if s < -0.05)
                neu_count    = len(compound_scores) - pos_count - neg_count
                if avg_compound >= 0.05:
                    label     = "POSITIVE"
                    int_score = min(5, int(avg_compound * 10))
                elif avg_compound <= -0.05:
                    label     = "NEGATIVE"
                    int_score = max(-5, int(avg_compound * 10))
                else:
                    label     = "NEUTRAL"
                    int_score = 0
            else:
                avg_compound = 0
                int_score    = 0
                label        = "NEUTRAL"
                pos_count    = neg_count = neu_count = 0

            scores[name] = {
                "score": int_score, "compound": avg_compound,
                "label": label, "pos_count": pos_count,
                "neg_count": neg_count, "neu_count": neu_count,
                "headlines": headlines[:3],
                "total_articles": len(compound_scores)
            }
        except Exception:
            scores[name] = {
                "score": 0, "compound": 0, "label": "NEUTRAL",
                "pos_count": 0, "neg_count": 0, "neu_count": 0,
                "headlines": [], "total_articles": 0
            }
    return scores


@st.cache_data(ttl=3600)
def fetch_fundamentals():
    portfolio  = st.session_state.portfolio
    ticker_map = {k: v["ticker"] for k, v in portfolio.items() if v["ticker"] != "MANUAL"}
    ticker_map["Blue Cloud Softech"] = "BLUECLOUDS.BO"
    ticker_map["Seacoast Shipping"]  = "SEACOAST.BO"
    data = {}
    for name, ticker in ticker_map.items():
        try:
            info = yf.Ticker(ticker).info
            data[name] = {
                "pe":  round(info.get("trailingPE")  or 0, 2),
                "pb":  round(info.get("priceToBook") or 0, 2),
                "roe": round((info.get("returnOnEquity") or 0) * 100, 2),
                "de":  round(info.get("debtToEquity") or 0, 2),
                "eps": round(info.get("trailingEps")  or 0, 2),
            }
        except Exception:
            data[name] = {"pe": 0, "pb": 0, "roe": 0, "de": 0, "eps": 0}
    return data


@st.cache_data(ttl=3600)
def fetch_risk_metrics():
    portfolio  = st.session_state.portfolio
    nifty_hist = None
    try:
        nifty_data = yf.Ticker("^NSEI").history(period="1y")
        if not nifty_data.empty:
            nifty_hist = nifty_data["Close"].pct_change().dropna()
    except Exception:
        nifty_hist = None

    metrics = {}
    for name, details in portfolio.items():
        ticker = details["ticker"]
        if ticker == "MANUAL":
            metrics[name] = {
                "volatility": None, "sharpe": None, "beta": None,
                "max_drawdown": None, "risk_grade": "UNKNOWN",
                "risk_label": "Illiquid — no data"
            }
            continue
        try:
            hist = yf.Ticker(ticker).history(period="1y")
            if len(hist) < 30:
                raise ValueError("Insufficient data")
            returns    = hist["Close"].pct_change().dropna()
            volatility = round(returns.std() * np.sqrt(252) * 100, 2)
            avg_return = returns.mean() * 252
            sharpe     = round((avg_return - 0.065) / (returns.std() * np.sqrt(252) + 1e-10), 2)
            beta       = None
            if nifty_hist is not None:
                try:
                    aligned = pd.concat([returns, nifty_hist], axis=1).dropna()
                    if len(aligned) > 20:
                        aligned.columns = ["stock", "nifty"]
                        beta = round(aligned["stock"].cov(aligned["nifty"]) / (aligned["nifty"].var() + 1e-10), 2)
                except Exception:
                    beta = None
            roll_max     = hist["Close"].cummax()
            drawdown     = (hist["Close"] - roll_max) / (roll_max + 1e-10)
            max_drawdown = round(drawdown.min() * 100, 2)

            if volatility < 25:
                risk_grade, risk_label = "LOW",       "Low Risk — stable stock"
            elif volatility < 45:
                risk_grade, risk_label = "MEDIUM",    "Medium Risk — moderate volatility"
            elif volatility < 70:
                risk_grade, risk_label = "HIGH",      "High Risk — volatile stock"
            else:
                risk_grade, risk_label = "VERY HIGH", "Very High Risk — highly speculative"

            metrics[name] = {
                "volatility": volatility, "sharpe": sharpe,
                "beta": beta, "max_drawdown": max_drawdown,
                "risk_grade": risk_grade, "risk_label": risk_label
            }
        except Exception:
            metrics[name] = {
                "volatility": None, "sharpe": None, "beta": None,
                "max_drawdown": None, "risk_grade": "UNKNOWN",
                "risk_label": "Data unavailable"
            }
    return metrics


def get_geo_scores():
    return {
        stock: sum(d["score"] for d in GEO_FACTORS.values() if sector in d["sectors"])
        for stock, sector in STOCK_SECTORS.items()
    }


def fund_score(pe, pb, de, eps, roe):
    s = 0
    if pe:  s += 2 if pe < 15 else (1 if pe < 25 else (0 if pe < 40 else -1))
    if pb:  s += 2 if pb < 1.5 else (1 if pb < 3 else -1)
    if de:  s += 2 if de < 30 else (1 if de < 100 else (-1 if de < 300 else -2))
    if eps: s += 2 if eps > 10 else (1 if eps > 0 else -2)
    if roe: s += 2 if roe > 15 else (1 if roe > 8 else -1)
    return s


def risk_score_adjustment(risk_metrics, name):
    m   = risk_metrics.get(name, {})
    adj = 0
    vol    = m.get("volatility")
    sharpe = m.get("sharpe")
    if vol:
        if vol > 70:    adj -= 2
        elif vol > 45:  adj -= 1
        elif vol < 25:  adj += 1
    if sharpe:
        if sharpe > 1.0:    adj += 2
        elif sharpe > 0.5:  adj += 1
        elif sharpe < 0:    adj -= 1
        elif sharpe < -0.5: adj -= 2
    return adj


def get_recommendations(prices, sentiment, fundamentals, geo_scores, risk_metrics=None):
    recs = {}
    for stock in STOCK_SECTORS:
        pnl  = prices.get(stock, {}).get("pnl_pct", 0)
        sent = sentiment.get(stock, {}).get("score", 0)
        f    = fundamentals.get(stock, {})
        fs   = fund_score(f.get("pe"), f.get("pb"), f.get("de"), f.get("eps"), f.get("roe"))
        geo  = geo_scores.get(stock, 0)
        ps   = (3 if pnl > 30 else 2 if pnl > 10 else 1 if pnl > 0
                else -1 if pnl > -15 else -2 if pnl > -30 else -3)
        risk_adj = risk_score_adjustment(risk_metrics, stock) if risk_metrics else 0
        total    = ps + sent + fs + geo + risk_adj
        if stock in ILLIQUID: total -= 5

        if total >= 10:   action, w, m, y = "STRONG BUY",  88, 85, 90
        elif total >= 7:  action, w, m, y = "HOLD / ADD",  75, 72, 80
        elif total >= 4:  action, w, m, y = "HOLD",        62, 64, 70
        elif total >= 1:  action, w, m, y = "WATCH",       52, 55, 60
        elif total >= -2: action, w, m, y = "REDUCE",      64, 62, 58
        else:             action, w, m, y = "EXIT",        78, 76, 72

        recs[stock] = {
            "action": action, "total": total,
            "fund_score": fs, "geo": geo,
            "sentiment": sent, "pnl_pct": pnl,
            "risk_adj": risk_adj,
            "week": w, "month": m, "year": y
        }
    return recs


def capital_allocation_engine(recs, available_capital, risk_metrics=None):
    if available_capital <= 0:
        return {}
    conviction_map = {
        "STRONG BUY":  1.0, "HOLD / ADD": 0.7,
        "HOLD":        0.3, "WATCH":      0.1,
        "REDUCE":      0.0, "EXIT":       0.0,
    }
    raw_weights = {}
    for stock, rec in recs.items():
        conviction = conviction_map.get(rec["action"], 0)
        if risk_metrics:
            vol = risk_metrics.get(stock, {}).get("volatility")
            if vol and vol > 60:  conviction *= 0.5
            elif vol and vol > 40: conviction *= 0.8
        raw_weights[stock] = conviction
    total_weight = sum(raw_weights.values())
    if total_weight == 0:
        return {}
    allocations = {}
    for stock, weight in raw_weights.items():
        if weight > 0:
            pct    = round((weight / total_weight) * 100, 1)
            amount = round((weight / total_weight) * available_capital, 0)
            tier   = ("LARGE" if pct >= 25 else "SIGNIFICANT" if pct >= 15
                      else "MODERATE" if pct >= 8 else "SMALL" if pct >= 2 else "MINIMAL")
            allocations[stock] = {
                "pct": pct, "amount": amount,
                "tier": tier, "action": recs[stock]["action"]
            }
    return dict(sorted(allocations.items(), key=lambda x: x[1]["pct"], reverse=True))


def portfolio_intelligence(prices, risk_metrics):
    total_value = sum(d["value"] for d in prices.values())
    if total_value == 0:
        return {}

    sector_exposure = {}
    for stock, data in prices.items():
        sector = STOCK_SECTORS.get(stock, "Other")
        pct    = (data["value"] / total_value) * 100
        if sector not in sector_exposure:
            sector_exposure[sector] = {"pct": 0, "stocks": [], "value": 0}
        sector_exposure[sector]["pct"]   += pct
        sector_exposure[sector]["stocks"].append(stock)
        sector_exposure[sector]["value"] += data["value"]

    warnings_list = []
    for sector, data in sector_exposure.items():
        if data["pct"] > 35:
            warnings_list.append({
                "type": "OVEREXPOSED", "severity": "HIGH",
                "message": f"{sector} = {data['pct']:.1f}% of portfolio. Max recommended: 35%",
                "action":  f"Reduce exposure to {sector} on next opportunity"
            })
        elif data["pct"] > 25:
            warnings_list.append({
                "type": "CONCENTRATED", "severity": "MEDIUM",
                "message": f"{sector} = {data['pct']:.1f}% of portfolio. Watch this.",
                "action":  f"Monitor {sector} concentration. Diversify gradually."
            })

    loss_pct = sum(1 for d in prices.values() if d["pnl"] < 0) / len(prices) * 100
    if loss_pct > 75:
        warnings_list.append({
            "type": "HIGH LOSS RATIO", "severity": "HIGH",
            "message": f"{loss_pct:.0f}% of stocks are in loss. Portfolio needs rebalancing.",
            "action": "Focus on exiting/reducing weak positions before adding new ones"
        })

    illiquid_val = sum(prices.get(s, {}).get("value", 0) for s in ILLIQUID)
    illiquid_pct = (illiquid_val / total_value) * 100
    if illiquid_pct > 5:
        warnings_list.append({
            "type": "ILLIQUID HOLDINGS", "severity": "MEDIUM",
            "message": f"Rs {illiquid_val:,.0f} ({illiquid_pct:.1f}%) in illiquid stocks",
            "action": "Accept as potential write-offs. Do not average down."
        })

    if risk_metrics:
        high_risk_stocks = [n for n, m in risk_metrics.items()
                            if m.get("risk_grade") in ["HIGH", "VERY HIGH"]]
        high_risk_val  = sum(prices.get(s, {}).get("value", 0) for s in high_risk_stocks)
        high_risk_pct  = (high_risk_val / total_value) * 100
        if high_risk_pct > 40:
            warnings_list.append({
                "type": "HIGH RISK CONCENTRATION", "severity": "HIGH",
                "message": f"{high_risk_pct:.0f}% of portfolio in high-volatility stocks",
                "action": "Shift capital towards low-volatility, stable stocks"
            })

    health_score = 100
    for w in warnings_list:
        health_score -= 20 if w["severity"] == "HIGH" else 10
    if len(sector_exposure) < 3: health_score -= 15
    health_score = max(0, health_score)
    health_label = ("GOOD" if health_score >= 75 else "FAIR" if health_score >= 50
                    else "POOR" if health_score >= 25 else "CRITICAL")

    return {
        "sector_exposure": sector_exposure,
        "warnings":        warnings_list,
        "health_score":    health_score,
        "health_label":    health_label,
        "sector_count":    len(sector_exposure),
        "stock_count":     len(prices),
        "illiquid_pct":    illiquid_pct,
        "loss_pct":        loss_pct
    }


def calculate_averaging(current_price, avg_buy_price, shares_held,
                         total_invested, target_pct=0.0):
    if current_price >= avg_buy_price:
        return None
    current_loss   = (avg_buy_price - current_price) * shares_held
    loss_pct       = round((current_price - avg_buy_price) / avg_buy_price * 100, 2)
    results        = []
    for multiplier in [1, 2, 3]:
        extra_shares       = shares_held * multiplier
        new_total_shares   = shares_held + extra_shares
        new_total_invested = total_invested + (extra_shares * current_price)
        new_avg            = new_total_invested / new_total_shares
        reduction_pct      = round((avg_buy_price - new_avg) / avg_buy_price * 100, 1)
        investment_needed  = round(extra_shares * current_price, 2)
        new_loss_pct       = round((current_price - new_avg) / new_avg * 100, 2)
        results.append({
            "extra_shares":        extra_shares,
            "multiplier":          f"{multiplier}x",
            "new_avg_price":       round(new_avg, 2),
            "investment_needed":   investment_needed,
            "new_total_shares":    new_total_shares,
            "new_total_invested":  round(new_total_invested, 2),
            "reduction_pct":       reduction_pct,
            "new_loss_pct":        new_loss_pct,
            "breakeven_price":     round(new_avg, 2)
        })
    breakeven_shares = int(
        (avg_buy_price * shares_held - current_price * shares_held) /
        max(avg_buy_price - current_price, 0.01)
    )
    return {
        "current_price":    current_price,
        "avg_buy_price":    avg_buy_price,
        "shares_held":      shares_held,
        "current_loss":     round(current_loss, 2),
        "loss_pct":         loss_pct,
        "scenarios":        results,
        "breakeven_shares": breakeven_shares,
        "breakeven_avg":    round(current_price, 2)
    }


@st.cache_data(ttl=1800)
def scan_nifty50():
    results = {}
    owned   = list(st.session_state.portfolio.keys())
    for name, ticker in NIFTY50.items():
        try:
            info   = yf.Ticker(ticker).info
            pe     = info.get("trailingPE")
            pb     = info.get("priceToBook")
            roe    = info.get("returnOnEquity")
            de     = info.get("debtToEquity")
            eps    = info.get("trailingEps")
            price  = info.get("currentPrice") or info.get("regularMarketPrice")
            h52    = info.get("fiftyTwoWeekHigh")
            l52    = info.get("fiftyTwoWeekLow")
            div    = info.get("dividendYield")
            sector = info.get("sector", "N/A")
            mcap   = info.get("marketCap", 0)
            w52    = (round(((price - l52) / (h52 - l52)) * 100, 1)
                      if h52 and l52 and price and h52 != l52 else 50)
            score  = 0
            if pe:  score += 3 if pe < 15 else 2 if pe < 20 else 1 if pe < 30 else 0
            if pb:  score += 2 if pb < 2  else 1 if pb < 3.5 else 0
            if roe:
                r = roe * 100
                score += 3 if r > 20 else 2 if r > 15 else 1 if r > 10 else 0
            if de:  score += 2 if de < 30 else 1 if de < 80 else 0
            if eps: score += 2 if eps > 50 else 1 if eps > 10 else -2 if eps < 0 else 0
            if w52 < 25:   score += 3
            elif w52 < 40: score += 2
            elif w52 < 55: score += 1
            if div and div > 0.015: score += 1
            already = any(name.lower() in k.lower() or k.lower() in name.lower() for k in owned)
            results[name] = {
                "score": score, "pe": pe, "pb": pb,
                "roe": round(roe * 100, 1) if roe else None,
                "sector": sector, "w52": w52,
                "price": price, "mcap": mcap, "already": already
            }
            time.sleep(0.1)
        except Exception:
            results[name] = {"score": 0, "already": False, "sector": "N/A", "w52": 50}
    return results


# ── INIT ────────────────────────────────────────────────────────────────────
init_portfolio()

portfolio_key = str(sorted([
    (k, v["shares"], v["invested"])
    for k, v in st.session_state.portfolio.items()
]))

# ── SIDEBAR ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## AI Portfolio Analyser")
    st.markdown("**v4.0** | Takhar & Claude AI")
    st.divider()
    st.markdown(f"Date: **{datetime.datetime.now().strftime('%d %B %Y')}**")
    st.markdown(f"Time: **{datetime.datetime.now().strftime('%I:%M %p')}**")
    st.divider()

    if st.button("Refresh All Data", width='stretch', type="primary"):
        st.cache_data.clear()
        st.rerun()

    st.divider()
    st.markdown("### Settings")
    show_charts   = st.toggle("Show Charts",       value=True)
    show_news     = st.toggle("Show News",         value=True)
    include_risk  = st.toggle("Include Risk Layer", value=True)
    available_cap = st.number_input(
        "Available Capital for Allocation (Rs)",
        min_value=0, value=50000, step=5000
    )
    st.divider()
    total_inv_s = sum(d["invested"] for d in st.session_state.portfolio.values())
    st.metric("Total Invested", f"Rs {total_inv_s:,.0f}")
    mf_inv = sum(m["invested"] for m in st.session_state.mutual_funds)
    mf_cur = sum(m["current"]  for m in st.session_state.mutual_funds)
    mf_pnl = mf_cur - mf_inv
    st.metric("SIP Returns", f"+Rs {mf_pnl:,.0f}", f"+{round(mf_pnl/mf_inv*100,1)}%")
    st.divider()
    st.caption("Not SEBI registered. Personal research only. Not financial advice.")

# ── HEADER ───────────────────────────────────────────────────────────────────
st.title("AI Portfolio Analyser")
st.markdown("6-Layer Intelligence: Price | VADER Sentiment | Fundamentals | Geopolitical | Risk | Capital Allocation")
st.divider()

# ── LOAD DATA ────────────────────────────────────────────────────────────────
with st.spinner("Loading live market data..."):
    prices       = fetch_prices(portfolio_key)
    sentiment    = fetch_sentiment_vader()
    fundamentals = fetch_fundamentals()
    geo_scores   = get_geo_scores()

risk_metrics = {}
if include_risk:
    with st.spinner("Calculating risk metrics (volatility, Sharpe, Beta)..."):
        risk_metrics = fetch_risk_metrics()

recs        = get_recommendations(prices, sentiment, fundamentals, geo_scores, risk_metrics)
allocations = capital_allocation_engine(recs, available_cap, risk_metrics)
port_intel  = portfolio_intelligence(prices, risk_metrics)

total_invested = sum(d["invested"] for d in prices.values())
total_current  = sum(d["value"]    for d in prices.values())
total_pnl      = round(total_current - total_invested, 2)
total_pnl_pct  = round((total_pnl / total_invested) * 100, 2)

# ── TOP-LEVEL WARNINGS ───────────────────────────────────────────────────────
if port_intel.get("warnings"):
    for w in port_intel["warnings"]:
        if w["severity"] == "HIGH":
            st.error(f"**{w['type']}** | {w['message']} | Action: {w['action']}")
        else:
            st.warning(f"**{w['type']}** | {w['message']}")

# ── TABS ─────────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs([
    "Dashboard",
    "Recommendations",
    "Capital Allocation",
    "Risk Analysis",
    "Portfolio Intelligence",
    "Averaging Calculator",
    "Nifty 50 & SIPs",
    "Alerts & Settings"
])

# ── TAB 1: DASHBOARD ─────────────────────────────────────────────────────────
with tab1:
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    with c1: st.metric("Invested",      f"Rs {total_invested:,.0f}")
    with c2: st.metric("Current Value", f"Rs {total_current:,.0f}")
    with c3:
        st.metric("P&L", f"Rs {total_pnl:,.0f}", f"{total_pnl_pct:+.2f}%", delta_color="normal")
    with c4:
        profit_ct = sum(1 for d in prices.values() if d["pnl"] > 0)
        st.metric("Profit Stocks", f"{profit_ct}/{len(prices)}")
    with c5:
        sb = sum(1 for r in recs.values() if "STRONG BUY" in r["action"])
        st.metric("Strong Buy", f"{sb} stocks")
    with c6:
        health = port_intel.get("health_score", 0)
        label  = port_intel.get("health_label", "N/A")
        st.metric("Portfolio Health", f"{health}/100", label)

    st.divider()
    st.caption(
        f"Last updated: {datetime.datetime.now().strftime('%d %b %Y %I:%M %p')} | "
        f"VADER Sentiment Active | Risk Layer: {'ON' if include_risk else 'OFF'}"
    )

    if show_charts:
        col1, col2 = st.columns([2, 1])
        with col1:
            st.markdown("#### Portfolio P&L Overview")
            names  = list(prices.keys())
            pnls   = [prices[n]["pnl_pct"] for n in names]
            colors = ["#64ffda" if p > 0 else "#ff6b6b" for p in pnls]
            fig = go.Figure(go.Bar(
                x=pnls, y=names, orientation='h',
                marker_color=colors,
                text=[f"{p:+.1f}%" for p in pnls],
                textposition='outside'
            ))
            fig.update_layout(
                height=520,
                paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                font=dict(color='#ccd6f6', size=11),
                xaxis=dict(gridcolor='#3d4266', title="P&L %"),
                yaxis=dict(gridcolor='#3d4266'),
                margin=dict(l=0, r=70, t=10, b=0)
            )
            fig.add_vline(x=0, line_color="#8892b0", line_dash="dash")
            st.plotly_chart(fig, width='stretch')

        with col2:
            st.markdown("#### Sector Allocation")
            sector_vals = {}
            for name in st.session_state.portfolio:
                sec = STOCK_SECTORS.get(name, "Other")
                val = prices.get(name, {}).get("value", 0)
                sector_vals[sec] = sector_vals.get(sec, 0) + val
            fig2 = go.Figure(go.Pie(
                labels=list(sector_vals.keys()),
                values=list(sector_vals.values()),
                hole=0.4,
                marker=dict(colors=[
                    '#64ffda','#4fc3f7','#ffd700','#ffab40',
                    '#ff6b6b','#c792ea','#89ddff','#f07178'
                ])
            ))
            fig2.update_layout(
                height=280,
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(color='#ccd6f6', size=10),
                showlegend=True, legend=dict(font=dict(size=9)),
                margin=dict(l=0, r=0, t=10, b=0)
            )
            st.plotly_chart(fig2, width='stretch')
            st.markdown("#### SIP Performance")
            for mf in st.session_state.mutual_funds:
                pnl_mf = mf["current"] - mf["invested"]
                pnl_p  = round((pnl_mf / mf["invested"]) * 100, 1)
                st.metric(
                    mf["name"][:32] + "...", f"Rs {mf['current']:,.0f}",
                    f"{pnl_p:+.1f}%",
                    delta_color="normal" if pnl_mf > 0 else "inverse"
                )

    st.divider()
    st.markdown("#### Holdings Detail")
    table_rows = []
    for name, data in prices.items():
        rec  = recs.get(name, {})
        risk = risk_metrics.get(name, {})
        table_rows.append({
            "Stock":       name,
            "Shares":      data["shares"],
            "Avg Buy":     f"Rs {data['avg_buy']:,.2f}",
            "CMP":         f"Rs {data['price']:,.2f}",
            "Invested":    f"Rs {data['invested']:,.0f}",
            "Current":     f"Rs {data['value']:,.0f}",
            "P&L %":       f"{data['pnl_pct']:+.2f}%",
            "Volatility":  f"{risk.get('volatility','N/A')}%" if risk.get('volatility') else "N/A",
            "Sharpe":      str(risk.get('sharpe', 'N/A')),
            "Sentiment":   sentiment.get(name, {}).get("label", "N/A"),
            "Action":      rec.get("action", "")
        })
    st.dataframe(pd.DataFrame(table_rows), width='stretch', height=420)

# ── TAB 2: RECOMMENDATIONS ───────────────────────────────────────────────────
with tab2:
    st.markdown("### AI Recommendations — 5 Layer Analysis")
    st.caption("Price + VADER Sentiment + Fundamentals + Geopolitical + Risk Adjustment")
    st.divider()

    filter_action = st.selectbox(
        "Filter by Action",
        ["All", "STRONG BUY", "HOLD / ADD", "HOLD", "WATCH", "REDUCE", "EXIT"]
    )

    groups = {"STRONG BUY": [], "HOLD / ADD": [], "HOLD": [], "WATCH": [], "REDUCE": [], "EXIT": []}
    for stock, rec in recs.items():
        if rec["action"] in groups:
            groups[rec["action"]].append((stock, rec))

    for action_key, stocks_list in groups.items():
        if not stocks_list: continue
        if filter_action != "All" and filter_action != action_key: continue
        st.markdown(f"#### {action_key} ({len(stocks_list)} stocks)")

        for stock, rec in stocks_list:
            pdata = prices.get(stock, {})
            pnl   = pdata.get("pnl_pct", 0)
            sent  = sentiment.get(stock, {})
            risk  = risk_metrics.get(stock, {})

            c1, c2, c3, c4, c5 = st.columns([3, 2, 2, 2, 2])
            with c1:
                st.markdown(f"**{stock}**")
                st.caption(
                    f"{STOCK_SECTORS.get(stock,'N/A')} | "
                    f"Sentiment: {sent.get('label','N/A')} ({sent.get('compound',0):+.2f}) | "
                    f"Risk: {risk.get('risk_grade','N/A')}"
                )
            with c2:
                st.metric("P&L", f"{pnl:+.1f}%",
                          delta_color="normal" if pnl > 0 else "inverse")
            with c3: st.metric("1W Signal", f"{rec['week']}%")
            with c4: st.metric("1M Signal", f"{rec['month']}%")
            with c5: st.metric("1Y Signal", f"{rec['year']}%")

            with st.expander(f"Full Score Breakdown — Total: {rec['total']}"):
                sc1, sc2, sc3, sc4, sc5 = st.columns(5)
                ps = (3 if pnl > 30 else 2 if pnl > 10 else 1 if pnl > 0
                      else -1 if pnl > -15 else -2 if pnl > -30 else -3)
                with sc1: st.metric("Price",        f"{ps:+d}")
                with sc2:
                    st.metric("VADER Sentiment", f"{rec['sentiment']:+d}",
                              f"Compound: {sent.get('compound',0):+.2f}")
                with sc3: st.metric("Fundamentals", f"{rec['fund_score']:+d}")
                with sc4: st.metric("Geopolitical", f"{rec['geo']:+d}")
                with sc5:
                    st.metric("Risk Adj", f"{rec['risk_adj']:+d}",
                              f"Vol: {risk.get('volatility','N/A')}%")

                if show_news and sent.get("headlines"):
                    st.markdown("**VADER-Analysed Headlines:**")
                    for h in sent["headlines"][:2]:
                        vs   = analyzer_score(h)
                        icon = "🟢" if vs > 0.05 else ("🔴" if vs < -0.05 else "🟡")
                        st.caption(f"{icon} {h[:100]}")
            st.divider()

# ── TAB 3: CAPITAL ALLOCATION ────────────────────────────────────────────────
with tab3:
    st.markdown("### Capital Allocation Engine")
    st.caption(
        "Converts AI conviction scores into capital allocation amounts. "
        "Higher conviction + lower risk = more capital. "
        "This is a guide, not a guarantee."
    )
    st.divider()

    if not allocations:
        st.info("No strong buy or hold/add signals found for capital allocation.")
    else:
        total_alloc = sum(a["amount"] for a in allocations.values())
        c1, c2, c3, c4 = st.columns(4)
        with c1: st.metric("Available Capital",   f"Rs {available_cap:,.0f}")
        with c2: st.metric("Stocks to Deploy In", f"{len(allocations)}")
        with c3: st.metric("Total to Deploy",      f"Rs {total_alloc:,.0f}")
        with c4: st.metric("Cash to Reserve",      f"Rs {available_cap - total_alloc:,.0f}")

        st.divider()
        st.markdown("#### Allocation Breakdown")

        for stock, alloc in allocations.items():
            pnl  = prices.get(stock, {}).get("pnl_pct", 0)
            risk = risk_metrics.get(stock, {})
            c1, c2, c3, c4, c5 = st.columns([3, 2, 2, 2, 2])
            with c1:
                st.markdown(f"**{stock}**")
                st.caption(f"Action: {alloc['action']} | Tier: {alloc['tier']} | Risk: {risk.get('risk_grade','N/A')}")
            with c2: st.metric("Allocation %", f"{alloc['pct']:.1f}%")
            with c3: st.metric("Amount",       f"Rs {alloc['amount']:,.0f}")
            with c4:
                st.metric("Current P&L", f"{pnl:+.1f}%",
                          delta_color="normal" if pnl > 0 else "inverse")
            with c5:
                vol = risk.get("volatility")
                st.metric("Volatility", f"{vol:.1f}%" if vol else "N/A")

        if show_charts:
            st.divider()
            fig = go.Figure(go.Bar(
                x=list(allocations.keys()),
                y=[a["pct"] for a in allocations.values()],
                marker_color=[
                    "#64ffda" if a["tier"] in ["LARGE","SIGNIFICANT"]
                    else "#ffd700" if a["tier"] == "MODERATE" else "#8892b0"
                    for a in allocations.values()
                ],
                text=[f"Rs {a['amount']:,.0f}" for a in allocations.values()],
                textposition='outside'
            ))
            fig.update_layout(
                title="Capital Allocation by Stock", height=350,
                paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                font=dict(color='#ccd6f6', size=10),
                xaxis=dict(gridcolor='#3d4266', tickangle=-30),
                yaxis=dict(gridcolor='#3d4266', title="Allocation %"),
                margin=dict(l=0, r=0, t=40, b=80)
            )
            st.plotly_chart(fig, width='stretch')

        st.warning(
            "Disclaimer: Capital allocation is based on AI conviction scores. "
            "Flawed scoring = flawed allocation. Always apply your own judgment."
        )

# ── TAB 4: RISK ANALYSIS ─────────────────────────────────────────────────────
with tab4:
    st.markdown("### Risk Analysis — Volatility, Sharpe Ratio & Beta")
    st.caption("Sharpe > 1 = good risk-adjusted return. High volatility stocks penalise recommendation scores.")
    st.divider()

    if not risk_metrics:
        st.info("Enable Risk Layer in sidebar settings to view this analysis.")
    else:
        risk_rows = []
        for name, m in risk_metrics.items():
            pnl = prices.get(name, {}).get("pnl_pct", 0)
            risk_rows.append({
                "Stock":        name,
                "Volatility %": f"{m['volatility']:.1f}" if m.get("volatility") else "N/A",
                "Sharpe":       f"{m['sharpe']:.2f}"     if m.get("sharpe")     else "N/A",
                "Beta":         f"{m['beta']:.2f}"       if m.get("beta")       else "N/A",
                "Max Drawdown": f"{m['max_drawdown']:.1f}%" if m.get("max_drawdown") else "N/A",
                "Risk Grade":   m.get("risk_grade", "N/A"),
                "P&L %":        f"{pnl:+.1f}%"
            })
        st.dataframe(pd.DataFrame(risk_rows), width='stretch', height=420)

        if show_charts:
            st.divider()
            st.markdown("#### Risk vs Return Scatter")
            valid = [(n, m) for n, m in risk_metrics.items() if m.get("volatility") and m.get("sharpe")]
            if valid:
                names_v = [v[0] for v in valid]
                vols    = [v[1]["volatility"] for v in valid]
                sharpes = [v[1]["sharpe"] for v in valid]
                pnls_v  = [prices.get(v[0], {}).get("pnl_pct", 0) for v in valid]
                fig_r   = go.Figure(go.Scatter(
                    x=vols, y=sharpes, mode='markers+text',
                    text=names_v, textposition='top center',
                    textfont=dict(size=8),
                    marker=dict(size=12, color=pnls_v, colorscale='RdYlGn',
                                showscale=True, colorbar=dict(title="P&L %"))
                ))
                fig_r.update_layout(
                    title="Risk vs Sharpe (colour = P&L %)", height=400,
                    paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                    font=dict(color='#ccd6f6', size=10),
                    xaxis=dict(title="Volatility %", gridcolor='#3d4266'),
                    yaxis=dict(title="Sharpe Ratio",  gridcolor='#3d4266'),
                    margin=dict(l=0, r=0, t=40, b=0)
                )
                fig_r.add_hline(y=0, line_color="#ff6b6b", line_dash="dash",
                                annotation_text="Sharpe = 0")
                fig_r.add_hline(y=1, line_color="#64ffda", line_dash="dash",
                                annotation_text="Sharpe = 1 (good)")
                st.plotly_chart(fig_r, width='stretch')

# ── TAB 5: PORTFOLIO INTELLIGENCE ────────────────────────────────────────────
with tab5:
    st.markdown("### Portfolio Intelligence")
    st.caption("Big-picture portfolio health. Sector concentration, overexposure, diversification gaps.")
    st.divider()

    if not port_intel:
        st.info("Portfolio intelligence unavailable.")
    else:
        c1, c2, c3, c4 = st.columns(4)
        with c1: st.metric("Portfolio Health",   f"{port_intel['health_score']}/100", port_intel["health_label"])
        with c2: st.metric("Sectors Covered",    f"{port_intel['sector_count']}")
        with c3: st.metric("Loss Stock Ratio",   f"{port_intel['loss_pct']:.0f}%")
        with c4: st.metric("Illiquid Exposure",  f"{port_intel['illiquid_pct']:.1f}%")

        st.divider()
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("#### Sector Exposure Analysis")
            sector_rows = []
            for sector, data in sorted(port_intel["sector_exposure"].items(),
                                        key=lambda x: x[1]["pct"], reverse=True):
                status = ("OVEREXPOSED"  if data["pct"] > 35
                          else "CONCENTRATED" if data["pct"] > 25 else "NORMAL")
                sector_rows.append({
                    "Sector":     sector,
                    "Exposure %": f"{data['pct']:.1f}%",
                    "Value":      f"Rs {data['value']:,.0f}",
                    "Stocks":     len(data["stocks"]),
                    "Status":     status
                })
            st.dataframe(pd.DataFrame(sector_rows), width='stretch')

        with col2:
            if show_charts:
                st.markdown("#### Sector Distribution")
                sectors    = list(port_intel["sector_exposure"].keys())
                pcts       = [port_intel["sector_exposure"][s]["pct"] for s in sectors]
                bar_colors = ["#ff6b6b" if p > 35 else "#ffd700" if p > 25 else "#64ffda" for p in pcts]
                fig_s = go.Figure(go.Bar(
                    x=sectors, y=pcts, marker_color=bar_colors,
                    text=[f"{p:.1f}%" for p in pcts], textposition='outside'
                ))
                fig_s.add_hline(y=35, line_color="#ff6b6b", line_dash="dash",
                                annotation_text="35% Warning Limit")
                fig_s.update_layout(
                    height=320,
                    paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                    font=dict(color='#ccd6f6', size=10),
                    xaxis=dict(gridcolor='#3d4266', tickangle=-20),
                    yaxis=dict(gridcolor='#3d4266', title="% of Portfolio"),
                    margin=dict(l=0, r=0, t=10, b=60)
                )
                st.plotly_chart(fig_s, width='stretch')

        st.divider()
        st.markdown("#### Warnings & Recommended Actions")
        if port_intel["warnings"]:
            for w in port_intel["warnings"]:
                msg = f"**{w['type']}** — {w['message']}\n\nRecommended Action: {w['action']}"
                if w["severity"] == "HIGH": st.error(msg)
                else:                        st.warning(msg)
        else:
            st.success("No critical portfolio-level warnings detected.")

        st.divider()
        st.markdown("#### Diversification Recommendations")
        covered = set(port_intel["sector_exposure"].keys())
        missing = {"Healthcare","Consumer Staples","Real Estate","Communication Services","Energy"} - covered
        if missing:
            st.info(f"Missing sectors: **{', '.join(missing)}**. Consider adding via SIPs or Nifty stocks.")

# ── TAB 6: AVERAGING CALCULATOR ──────────────────────────────────────────────
with tab6:
    st.markdown("### Averaging Calculator")
    st.caption("Calculate shares to buy to reduce average cost and reach break-even.")
    st.divider()

    loss_stocks = {n: d for n, d in prices.items() if d["pnl_pct"] < 0 and d["price"] > 0}

    if not loss_stocks:
        st.success("All stocks are in profit — no averaging needed!")
    else:
        st.info(f"You have **{len(loss_stocks)} loss-making stocks**.")
        col1, col2 = st.columns([2, 1])
        with col1:
            selected_stock = st.selectbox(
                "Select Stock to Average Down",
                list(loss_stocks.keys()),
                format_func=lambda x: (
                    f"{x} | Loss: {loss_stocks[x]['pnl_pct']:+.1f}% "
                    f"| Avg Buy: Rs {loss_stocks[x]['avg_buy']:,.2f} "
                    f"| CMP: Rs {loss_stocks[x]['price']:,.2f}"
                )
            )
        with col2:
            target_exit = st.number_input(
                "Target Exit % above CMP",
                min_value=0.0, max_value=50.0, value=0.0, step=0.5
            )

        if selected_stock:
            data  = loss_stocks[selected_stock]
            avg_r = calculate_averaging(
                data["price"], data["avg_buy"],
                data["shares"], data["invested"], target_exit
            )

            if avg_r is None:
                st.success("This stock is at or above your average buy price.")
            else:
                c1, c2, c3, c4 = st.columns(4)
                with c1: st.metric("Avg Buy Price",  f"Rs {avg_r['avg_buy_price']:,.2f}")
                with c2: st.metric("Current Price",  f"Rs {avg_r['current_price']:,.2f}")
                with c3:
                    st.metric("Current Loss", f"Rs {avg_r['current_loss']:,.2f}",
                              f"{avg_r['loss_pct']:+.1f}%", delta_color="inverse")
                with c4: st.metric("Shares Held", f"{avg_r['shares_held']:,}")

                st.divider()
                st.markdown("#### Averaging Scenarios")
                for scenario in avg_r["scenarios"]:
                    with st.expander(
                        f"Scenario {scenario['multiplier']} — "
                        f"Buy {scenario['extra_shares']:,} more shares — "
                        f"New Avg: Rs {scenario['new_avg_price']:,.2f} "
                        f"(reduced by {scenario['reduction_pct']:.1f}%)",
                        expanded=(scenario["multiplier"] == "1x")
                    ):
                        s1, s2, s3, s4 = st.columns(4)
                        with s1: st.metric("Shares to Buy",     f"{scenario['extra_shares']:,}")
                        with s2: st.metric("Investment Needed", f"Rs {scenario['investment_needed']:,.0f}")
                        with s3: st.metric("New Average Price", f"Rs {scenario['new_avg_price']:,.2f}")
                        with s4: st.metric("Total After Avg",   f"Rs {scenario['new_total_invested']:,.0f}")
                        st.info(
                            f"Break-even price: **Rs {scenario['breakeven_price']:,.2f}** — "
                            f"stock must reach this to exit at no profit / no loss."
                        )

                if show_charts:
                    st.divider()
                    st.markdown("#### Averaging Down Chart")
                    extra_range = list(range(0, avg_r["shares_held"] * 4,
                                             max(1, avg_r["shares_held"] // 20)))
                    avg_prices  = []
                    for extra in extra_range:
                        new_s   = avg_r["shares_held"] + extra
                        new_inv = avg_r["avg_buy_price"] * avg_r["shares_held"] + extra * avg_r["current_price"]
                        avg_prices.append(new_inv / new_s)
                    fig3 = go.Figure()
                    fig3.add_trace(go.Scatter(
                        x=extra_range, y=avg_prices, mode='lines',
                        name='New Average Price', line=dict(color='#64ffda', width=2)
                    ))
                    fig3.add_hline(y=avg_r["current_price"], line_color="#ff6b6b", line_dash="dash",
                                   annotation_text=f"CMP: Rs {avg_r['current_price']}")
                    fig3.add_hline(y=avg_r["avg_buy_price"], line_color="#ffd700", line_dash="dash",
                                   annotation_text=f"Current Avg: Rs {avg_r['avg_buy_price']}")
                    fig3.update_layout(
                        title=f"Averaging Down — {selected_stock}", height=300,
                        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                        font=dict(color='#ccd6f6'),
                        xaxis=dict(title="Extra Shares Bought", gridcolor='#3d4266'),
                        yaxis=dict(title="Average Buy Price Rs", gridcolor='#3d4266'),
                        margin=dict(l=0, r=0, t=40, b=0)
                    )
                    st.plotly_chart(fig3, width='stretch')

                st.divider()
                st.markdown("#### AI Recommendation on Averaging")
                rec_action = recs.get(selected_stock, {}).get("action", "WATCH")
                risk_grade = risk_metrics.get(selected_stock, {}).get("risk_grade", "UNKNOWN")

                if rec_action in ["STRONG BUY","HOLD / ADD"] and risk_grade not in ["HIGH","VERY HIGH"]:
                    st.success(f"AI: **{rec_action}** | Risk: **{risk_grade}** | Averaging makes sense. Consider 1x scenario.")
                elif rec_action in ["STRONG BUY","HOLD / ADD"] and risk_grade in ["HIGH","VERY HIGH"]:
                    st.warning(f"AI: **{rec_action}** BUT Risk is **{risk_grade}**. Average cautiously — small position only.")
                elif rec_action in ["HOLD","WATCH"]:
                    st.warning(f"AI: **{rec_action}** | Wait for stronger signals before adding more capital.")
                else:
                    st.error(f"AI: **{rec_action}** | Do NOT average down. Consider exiting instead.")

# ── TAB 7: NIFTY 50 & SIPs ───────────────────────────────────────────────────
with tab7:
    sip_tab, nifty_tab = st.tabs(["SIP Suggestions", "Nifty 50 Scanner"])

    with sip_tab:
        st.markdown("### Personalized SIP Recommendations")
        st.divider()
        monthly = 5000
        rate    = 13 / 100 / 12
        fv      = monthly * (((1 + rate) ** 120 - 1) / rate) * (1 + rate)
        inv     = monthly * 120
        fv_fd   = inv * ((1 + 0.065) ** 10)
        c1, c2, c3, c4 = st.columns(4)
        with c1: st.metric("Monthly SIP",    f"Rs {monthly:,}")
        with c2: st.metric("10Y Projection", f"Rs {fv:,.0f}")
        with c3: st.metric("FD Value",       f"Rs {fv_fd:,.0f}")
        with c4: st.metric("Extra vs FD",    f"+Rs {fv - fv_fd:,.0f}")
        st.divider()
        if show_charts:
            months_r = list(range(1, 121))
            sip_vals = [monthly * (((1 + rate) ** m - 1) / rate) * (1 + rate) for m in months_r]
            fd_vals  = [monthly * m * (1 + 0.065) ** (m / 12) for m in months_r]
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=months_r, y=sip_vals,
                name="SIP (13% CAGR)", line=dict(color="#64ffda", width=2)))
            fig.add_trace(go.Scatter(x=months_r, y=fd_vals,
                name="FD (6.5%)", line=dict(color="#ff6b6b", width=2, dash='dash')))
            fig.update_layout(
                title="SIP vs FD — 10 Year Wealth Growth", height=260,
                paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                font=dict(color='#ccd6f6'),
                xaxis=dict(title="Months", gridcolor='#3d4266'),
                yaxis=dict(title="Value Rs", gridcolor='#3d4266'),
                legend=dict(bgcolor='rgba(0,0,0,0)'),
                margin=dict(l=0, r=0, t=40, b=0)
            )
            st.plotly_chart(fig, width='stretch')
        for sip in SIP_RECS:
            with st.expander(f"#{sip['priority']} {sip['fund']} — Rs {sip['amount']:,}/month | {sip['action']}"):
                c1, c2, c3 = st.columns(3)
                with c1: st.metric("Monthly", f"Rs {sip['amount']:,}")
                with c2: st.metric("Risk",    sip["risk"])
                with c3: st.metric("CAGR",    sip["cagr"])
                st.caption(f"Examples: {sip['examples']}")
                st.info(sip["why"])

    with nifty_tab:
        st.markdown("### Nifty 50 Opportunity Scanner")
        st.divider()
        if st.button("Scan Nifty 50 Now", type="primary"):
            with st.spinner("Scanning Nifty 50 stocks... (~2 mins)"):
                nifty_data = scan_nifty50()
            new_opps = {k: v for k, v in nifty_data.items()
                        if not v.get("already") and v.get("score", 0) >= 4}
            top10 = sorted(new_opps.items(), key=lambda x: x[1]["score"], reverse=True)[:10]
            st.success(f"Scan complete! Found {len(top10)} opportunities.")
            for rank, (name, data) in enumerate(top10, 1):
                score  = data.get("score", 0)
                w52    = data.get("w52", 50)
                rating = ("STRONG BUY" if score >= 12 else "BUY" if score >= 9
                          else "WATCH AND BUY ON DIP" if score >= 6 else "ON RADAR")
                with st.expander(f"#{rank} {name} — {rating} (Score: {score})"):
                    c1, c2, c3, c4, c5 = st.columns(5)
                    with c1: st.metric("Sector", data.get("sector","N/A"))
                    with c2: st.metric("PE",  f"{data['pe']:.1f}"  if data.get("pe")  else "N/A")
                    with c3: st.metric("PB",  f"{data['pb']:.1f}"  if data.get("pb")  else "N/A")
                    with c4: st.metric("ROE", f"{data['roe']:.1f}%" if data.get("roe") else "N/A")
                    with c5:
                        entry = ("Good entry" if w52 < 35 else "Wait for dip" if w52 < 60 else "Near 52W High")
                        st.metric("52W Position", f"{w52:.0f}%", entry)
        else:
            st.info("Click Scan Nifty 50 Now to find new investment opportunities.")

# ── TAB 8: ALERTS & SETTINGS ─────────────────────────────────────────────────
with tab8:
    alerts_tab, portfolio_tab, sip_edit_tab, geo_tab = st.tabs([
        "Alerts & News", "Update Portfolio", "Update SIPs", "Geopolitical"
    ])

    with alerts_tab:
        st.markdown("### Daily Action Alerts")
        st.divider()
        alerts = []
        for name, data in prices.items():
            p = data["pnl_pct"]
            if p <= -50:
                alerts.append(("CRITICAL EXIT", name, p, "Exit immediately — severe capital loss"))
            elif p <= -35:
                alerts.append(("EXIT ALERT", name, p, "Review urgently — significant loss"))
            elif p <= -25:
                alerts.append(("REVIEW", name, p, "Monitor closely"))
            elif p >= 50:
                alerts.append(("BOOK PROFIT", name, p, "Consider partial profit booking"))
            elif p >= 25:
                alerts.append(("WATCH PROFIT", name, p, "Good gain — watch for exit"))

        if alerts:
            for atype, name, pnl, note in alerts:
                msg = f"**{atype}** | {name} | {pnl:+.1f}% | {note}"
                if "CRITICAL" in atype or "EXIT ALERT" in atype: st.error(msg)
                elif "REVIEW" in atype:                           st.warning(msg)
                else:                                              st.success(msg)
        else:
            st.success("No critical alerts today.")

        if show_news:
            st.divider()
            st.markdown("#### VADER-Analysed News — Top Holdings")
            top5 = sorted(st.session_state.portfolio.items(),
                          key=lambda x: x[1]["invested"], reverse=True)[:5]
            for name, _ in top5:
                s = sentiment.get(name, {})
                with st.expander(
                    f"{name} | Sentiment: {s.get('label','N/A')} "
                    f"(compound: {s.get('compound',0):+.2f}) | "
                    f"Articles: {s.get('total_articles',0)}"
                ):
                    for h in (s.get("headlines", []) or ["No recent news found"]):
                        st.caption(f"-> {h}")

    with portfolio_tab:
        st.markdown("### Update Your Stock Holdings")
        st.caption("Update whenever you buy, sell, or average down.")
        st.divider()
        for name, details in list(st.session_state.portfolio.items()):
            with st.expander(f"{name} — {details['shares']} shares | Rs {details['invested']:,.0f}"):
                col1, col2, col3 = st.columns(3)
                with col1:
                    new_shares = st.number_input(
                        "Shares", min_value=0, value=int(details["shares"]),
                        key=f"shares_{name}"
                    )
                with col2:
                    new_invested = st.number_input(
                        "Total Invested (Rs)", min_value=0.0,
                        value=float(details["invested"]), step=100.0,
                        key=f"invested_{name}"
                    )
                with col3:
                    if details["ticker"] == "MANUAL":
                        new_manual = st.number_input(
                            "Manual Price (Rs)", min_value=0.0,
                            value=float(details.get("manual_price", 0)), step=0.1,
                            key=f"manual_{name}"
                        )
                    else:
                        st.text_input("Ticker", value=details["ticker"],
                                      disabled=True, key=f"ticker_{name}")
                        new_manual = None

                if st.button(f"Update {name}", key=f"update_{name}"):
                    st.session_state.portfolio[name]["shares"]   = new_shares
                    st.session_state.portfolio[name]["invested"] = new_invested
                    if new_manual is not None:
                        st.session_state.portfolio[name]["manual_price"] = new_manual
                    st.cache_data.clear()
                    st.success(f"Updated {name}")
                    st.rerun()

        st.divider()
        if st.button("Reset to Default Portfolio", type="secondary"):
            st.session_state.portfolio = {k: dict(v) for k, v in DEFAULT_PORTFOLIO.items()}
            st.cache_data.clear()
            st.success("Reset to defaults")
            st.rerun()

    with sip_edit_tab:
        st.markdown("### Update Your SIP Holdings")
        st.divider()
        for i, mf in enumerate(st.session_state.mutual_funds):
            with st.expander(mf["name"]):
                col1, col2 = st.columns(2)
                with col1:
                    new_inv = st.number_input(
                        "Total Invested (Rs)", min_value=0.0,
                        value=float(mf["invested"]), step=500.0,
                        key=f"mf_inv_{i}"
                    )
                with col2:
                    new_cur = st.number_input(
                        "Current Value (Rs)", min_value=0.0,
                        value=float(mf["current"]), step=500.0,
                        key=f"mf_cur_{i}"
                    )
                if st.button("Update SIP", key=f"update_mf_{i}"):
                    st.session_state.mutual_funds[i]["invested"] = new_inv
                    st.session_state.mutual_funds[i]["current"]  = new_cur
                    st.success(f"Updated {mf['name']}")
                    st.rerun()

    with geo_tab:
        st.markdown("### Geopolitical & Macro Factors")
        st.divider()
        for factor, details in GEO_FACTORS.items():
            with st.expander(f"{factor} — {details['severity']} Severity"):
                c1, c2, c3 = st.columns(3)
                with c1:
                    st.markdown("**Affected Sectors**")
                    st.caption(", ".join(details["sectors"]))
                with c2:
                    st.markdown("**Portfolio Impact**")
                    st.caption(details["impact"])
                with c3:
                    st.markdown("**Severity**")
                    st.caption(details["severity"])

        st.divider()
        st.markdown("#### Geopolitical Score Per Stock")
        geo_rows = []
        for stock, score in geo_scores.items():
            sig = ("Tailwind" if score > 2 else "Mild Tailwind" if score > 0
                   else "Neutral" if score == 0 else "Headwind")
            geo_rows.append({
                "Stock": stock, "Sector": STOCK_SECTORS.get(stock,"N/A"),
                "Geo Score": score, "Signal": sig
            })
        geo_df = pd.DataFrame(geo_rows).sort_values("Geo Score", ascending=False)
        st.dataframe(geo_df, width='stretch')

# ── FOOTER ────────────────────────────────────────────────────────────────────
st.divider()
st.caption(
    "AI Portfolio Analyser v4.0 | Built by Takhar & Claude AI | "
    "6-Layer Intelligence | Not SEBI registered | Personal research only | Not financial advice"
)
