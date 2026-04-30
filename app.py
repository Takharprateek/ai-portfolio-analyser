# ============================================================
# AI PORTFOLIO ANALYSER — STREAMLIT WEB APP v3.0
# Co-founders: Takhar & Claude AI
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
import plotly.graph_objects as go

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
    .metric-card {
        background: linear-gradient(135deg, #1e2130, #2d3250);
        border-radius: 12px;
        padding: 16px;
        border: 1px solid #3d4266;
        text-align: center;
    }
    .section-header {
        font-size: 18px;
        font-weight: 700;
        color: #ccd6f6;
        border-bottom: 2px solid #3d4266;
        padding-bottom: 8px;
        margin: 20px 0 16px 0;
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

GEO_FACTORS = {
    "India-Pakistan Tensions":    {"sectors": ["Defence","Energy","Utilities"],               "score": 3,  "severity": "HIGH",   "impact": "POSITIVE for Defence | NEGATIVE for Banking"},
    "US-China Trade War":         {"sectors": ["Technology","Consumer Cyclical"],              "score": 2,  "severity": "HIGH",   "impact": "POSITIVE for Indian IT exports"},
    "Global Crude Oil Prices":    {"sectors": ["Utilities","Industrials","Consumer Defensive"],"score": -2, "severity": "MEDIUM", "impact": "HIGH crude = NEGATIVE for energy sectors"},
    "RBI Interest Rate Policy":   {"sectors": ["Financial Services","Utilities"],              "score": 2,  "severity": "MEDIUM", "impact": "Rate cuts POSITIVE for NBFCs"},
    "India Green Energy Push":    {"sectors": ["Utilities","Technology"],                      "score": 2,  "severity": "MEDIUM", "impact": "POSITIVE for renewables long term"},
    "India Infrastructure Spend": {"sectors": ["Industrials","Technology","Financial Services"],"score": 2, "severity": "MEDIUM", "impact": "POSITIVE for logistics and lending"},
}

NIFTY50 = {
    "Reliance Industries":     "RELIANCE.NS",
    "TCS":                     "TCS.NS",
    "HDFC Bank":               "HDFCBANK.NS",
    "Infosys":                 "INFY.NS",
    "ICICI Bank":              "ICICIBANK.NS",
    "Bharti Airtel":           "BHARTIARTL.NS",
    "State Bank of India":     "SBIN.NS",
    "Bajaj Finance":           "BAJFINANCE.NS",
    "HUL":                     "HINDUNILVR.NS",
    "ITC":                     "ITC.NS",
    "Larsen & Toubro":         "LT.NS",
    "Kotak Mahindra Bank":     "KOTAKBANK.NS",
    "Axis Bank":               "AXISBANK.NS",
    "Sun Pharma":              "SUNPHARMA.NS",
    "Maruti Suzuki":           "MARUTI.NS",
    "HCL Technologies":        "HCLTECH.NS",
    "Titan Company":           "TITAN.NS",
    "Power Grid":              "POWERGRID.NS",
    "Coal India":              "COALINDIA.NS",
    "Tech Mahindra":           "TECHM.NS",
    "Apollo Hospitals":        "APOLLOHOSP.NS",
    "Dr Reddy's":              "DRREDDY.NS",
    "Cipla":                   "CIPLA.NS",
    "BEL":                     "BEL.NS",
    "Hindalco":                "HINDALCO.NS",
}

SIP_RECS = [
    {"priority": 1, "fund": "Nifty 50 Index Fund (Direct)",
     "examples": "UTI / HDFC / Nippon Nifty 50",
     "amount": 1500, "risk": "🟢 LOW", "cagr": "12-14%",
     "action": "START IMMEDIATELY",
     "why": "Core anchor. Beats FD consistently over 5+ years."},
    {"priority": 2, "fund": "Nifty Next 50 Index Fund (Direct)",
     "examples": "UTI / ICICI Pru Nifty Next 50",
     "amount": 1000, "risk": "🟡 LOW-MEDIUM", "cagr": "14-16%",
     "action": "START IMMEDIATELY",
     "why": "Higher growth than Nifty 50 at moderate risk."},
    {"priority": 3, "fund": "Defence Index Fund — Increase",
     "examples": "Motilal Oswal Nifty India Defence (You own this)",
     "amount": 1000, "risk": "🟡 MEDIUM", "cagr": "18-22%",
     "action": "INCREASE EXISTING SIP",
     "why": "Already +15.5%. India-Pakistan tensions = strong tailwind."},
    {"priority": 4, "fund": "Balanced Advantage Fund (Direct)",
     "examples": "HDFC / ICICI Pru Balanced Advantage",
     "amount": 700, "risk": "🟢 LOW-MEDIUM", "cagr": "10-12%",
     "action": "START WITHIN 2 WEEKS",
     "why": "Auto-balances equity vs debt. Reduces volatility."},
    {"priority": 5, "fund": "Pharma & Healthcare Fund (Direct)",
     "examples": "Nippon / Mirae / SBI Healthcare",
     "amount": 500, "risk": "🟡 MEDIUM", "cagr": "15-18%",
     "action": "START WITHIN 1 MONTH",
     "why": "Missing from portfolio. Defensive sector."},
    {"priority": 6, "fund": "Gold ETF (Direct)",
     "examples": "Nippon / HDFC / Axis Gold Fund",
     "amount": 300, "risk": "🟢 LOW", "cagr": "8-10%",
     "action": "START WITHIN 1 MONTH",
     "why": "Inflation hedge. Geopolitical risk protection."},
]

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
                "price": 0, "value": details["invested"],
                "pnl": 0, "pnl_pct": 0,
                "invested": details["invested"],
                "shares": details["shares"]
            }
    return results

@st.cache_data(ttl=3600)
def fetch_sentiment():
    newsapi   = NewsApiClient(api_key=NEWS_API_KEY)
    pos_words = ['growth','profit','surge','rise','gain','strong',
                 'upgrade','record','expand','win','positive',
                 'increase','boost','rally','outperform','dividend','beat']
    neg_words = ['loss','fall','drop','decline','weak','sell',
                 'downgrade','concern','risk','crash','trouble',
                 'fraud','debt','default','cut','miss','below']
    queries = {
        "LG Electronics India":    "LG Electronics India",
        "Bajaj Housing Finance":   "Bajaj Housing Finance",
        "Adani Green Energy":      "Adani Green Energy",
        "Western Carriers":        "Western Carriers India",
        "RECL":                    "REC Limited India power",
        "IRFC":                    "IRFC Indian Railway Finance",
        "MIC Electronics":         "MIC Electronics India",
        "Best Agrolife":           "Best Agrolife India",
        "NHPC":                    "NHPC India hydropower",
        "Yes Bank":                "Yes Bank India",
        "Wipro":                   "Wipro India IT",
        "Orient Green Power":      "Orient Green Power India",
        "Ola Electric":            "Ola Electric India",
        "GTL Infrastructure":      "GTL Infrastructure India",
        "Bajaj Hindusthan Sugar":  "Bajaj Hindusthan Sugar",
        "NTPC":                    "NTPC India power",
        "Blue Cloud Softech":      "Blue Cloud Softech",
        "Seacoast Shipping":       "Seacoast Shipping India",
    }
    scores = {}
    for name, query in queries.items():
        try:
            articles = newsapi.get_everything(
                q=query, language='en', sort_by='publishedAt', page_size=5,
                from_param=(datetime.datetime.now() -
                           datetime.timedelta(days=7)).strftime('%Y-%m-%d')
            )
            score     = 0
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
                "pe":  round(info.get("trailingPE")  or 0, 2),
                "pb":  round(info.get("priceToBook") or 0, 2),
                "roe": round((info.get("returnOnEquity") or 0) * 100, 2),
                "de":  round(info.get("debtToEquity") or 0, 2),
                "eps": round(info.get("trailingEps")  or 0, 2),
            }
        except:
            data[name] = {"pe": 0, "pb": 0, "roe": 0, "de": 0, "eps": 0}
    return data

def get_geo_scores():
    scores = {}
    for stock, sector in STOCK_SECTORS.items():
        scores[stock] = sum(
            d["score"] for d in GEO_FACTORS.values()
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
        ps   = (3 if pnl>30 else 2 if pnl>10 else 1 if pnl>0
                else -1 if pnl>-15 else -2 if pnl>-30 else -3)
        total = ps + sent + fs + geo
        if stock in ILLIQUID: total -= 5

        if total >= 10:   action, w, m, y = "🟢 STRONG BUY",  88, 85, 90
        elif total >= 7:  action, w, m, y = "🟢 HOLD / ADD",  75, 72, 80
        elif total >= 4:  action, w, m, y = "🟡 HOLD",        62, 64, 70
        elif total >= 1:  action, w, m, y = "🟡 WATCH",       52, 55, 60
        elif total >= -2: action, w, m, y = "🔴 REDUCE",      64, 62, 58
        else:             action, w, m, y = "🔴 EXIT",        78, 76, 72

        if stock in ILLIQUID: action += " ⚠️"

        recs[stock] = {
            "action": action, "total": total,
            "fund_score": fs, "geo": geo,
            "sentiment": sent, "pnl_pct": pnl,
            "week": w, "month": m, "year": y
        }
    return recs

@st.cache_data(ttl=1800)
def scan_nifty50():
    results = {}
    owned   = list(PORTFOLIO.keys())
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
            sector = info.get("sector","N/A")
            mcap   = info.get("marketCap", 0)
            w52    = round(((price-l52)/(h52-l52))*100,1) if (
                     h52 and l52 and price and h52!=l52) else 50

            score = 0
            if pe:  score += 3 if pe<15 else 2 if pe<20 else 1 if pe<30 else 0
            if pb:  score += 2 if pb<2  else 1 if pb<3.5 else 0
            if roe:
                r = roe*100
                score += 3 if r>20 else 2 if r>15 else 1 if r>10 else 0
            if de:  score += 2 if de<30 else 1 if de<80 else 0
            if eps: score += 2 if eps>50 else 1 if eps>10 else -2 if eps<0 else 0
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
                "price": price, "mcap": mcap, "already": already
            }
            time.sleep(0.1)
        except:
            results[name] = {"score": 0, "already": False,
                             "sector":"N/A","w52":50}
    return results

# ============================================================
# SIDEBAR
# ============================================================
with st.sidebar:
    st.markdown("## 🤖 AI Portfolio Analyser")
    st.markdown("**v3.0** | Takhar & Claude AI")
    st.divider()
    st.markdown(f"📅 **{datetime.datetime.now().strftime('%d %B %Y')}**")
    st.markdown(f"🕐 **{datetime.datetime.now().strftime('%I:%M %p')}**")
    st.divider()

    if st.button("🔄 Refresh All Data",
                 use_container_width=True, type="primary"):
        st.cache_data.clear()
        st.rerun()

    st.divider()
    st.markdown("### ⚙️ Settings")
    show_charts = st.toggle("Show Charts", value=True)
    show_news   = st.toggle("Show News",   value=True)
    st.divider()

    st.markdown("### 📊 Quick Stats")
    total_inv = sum(d["invested"] for d in PORTFOLIO.values())
    st.metric("Total Invested", f"₹{total_inv:,.0f}")
    mf_inv = sum(m["invested"] for m in MUTUAL_FUNDS)
    mf_cur = sum(m["current"]  for m in MUTUAL_FUNDS)
    mf_pnl = mf_cur - mf_inv
    st.metric("SIP Returns",
              f"+₹{mf_pnl:,.0f}",
              f"+{round(mf_pnl/mf_inv*100,1)}%")
    st.divider()

    st.markdown("""
    <div style='font-size:10px;color:#8892b0;text-align:center'>
    ⚠️ Not SEBI registered.<br>
    Personal research only.<br>
    Not financial advice.
    </div>
    """, unsafe_allow_html=True)

# ============================================================
# HEADER
# ============================================================
st.markdown("# 🤖 AI Portfolio Analyser")
st.markdown(
    "*5-Layer Intelligence: Price · Sentiment · "
    "Fundamentals · Geopolitical · ML*"
)
st.divider()

# ============================================================
# LOAD DATA
# ============================================================
with st.spinner("🔄 Loading live market data..."):
    prices       = fetch_prices()
    sentiment    = fetch_sentiment()
    fundamentals = fetch_fundamentals()
    geo_scores   = get_geo_scores()
    recs         = get_recommendations(
                       prices, sentiment, fundamentals, geo_scores)

total_invested = sum(d["invested"] for d in prices.values())
total_current  = sum(d["value"]    for d in prices.values())
total_pnl      = round(total_current - total_invested, 2)
total_pnl_pct  = round((total_pnl / total_invested) * 100, 2)

# ============================================================
# TABS — defined once, used below
# ============================================================
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "📊 Dashboard",
    "📋 Recommendations",
    "🔍 Nifty 50 Scanner",
    "💡 SIP Suggestions",
    "🌍 Geopolitical",
    "🚨 Alerts"
])

============================================================
# TAB 1 — DASHBOARD
# ============================================================
with tab1:
    c1,c2,c3,c4,c5,c6 = st.columns(6)
    with c1: st.metric("💰 Invested",     f"₹{total_invested:,.0f}")
    with c2: st.metric("📈 Current",      f"₹{total_current:,.0f}")
    with c3:
        st.metric("P&L",
                  f"₹{total_pnl:,.0f}",
                  f"{total_pnl_pct:+.2f}%",
                  delta_color="normal")
    with c4:
        profit_ct = sum(1 for d in prices.values() if d["pnl"] > 0)
        st.metric("✅ Profit Stocks", f"{profit_ct}/18")
    with c5:
        sb = sum(1 for r in recs.values() if "STRONG BUY" in r["action"])
        st.metric("🟢 Strong Buy", f"{sb} stocks")
    with c6:
        ex = sum(1 for r in recs.values()
                 if "EXIT" in r["action"] or "REDUCE" in r["action"])
        st.metric("🔴 Exit/Reduce", f"{ex} stocks")

    st.divider()

    if show_charts:
        col1, col2 = st.columns([2,1])

        with col1:
            st.markdown("#### 📊 Portfolio P&L Overview")
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
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font=dict(color='#ccd6f6', size=11),
                xaxis=dict(gridcolor='#3d4266', title="P&L %"),
                yaxis=dict(gridcolor='#3d4266'),
                margin=dict(l=0, r=70, t=10, b=0)
            )
            fig.add_vline(x=0, line_color="#8892b0", line_dash="dash")
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            st.markdown("#### 🥧 Sector Allocation")
            sector_vals = {}
            for name in PORTFOLIO:
                sec = STOCK_SECTORS.get(name,"Other")
                val = prices.get(name,{}).get("value",0)
                sector_vals[sec] = sector_vals.get(sec,0) + val

            fig2 = go.Figure(go.Pie(
                labels=list(sector_vals.keys()),
                values=list(sector_vals.values()),
                hole=0.4,
                marker=dict(colors=[
                    '#64ffda','#4fc3f7','#ffd700',
                    '#ffab40','#ff6b6b','#c792ea',
                    '#89ddff','#f07178'
                ])
            ))
            fig2.update_layout(
                height=280,
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(color='#ccd6f6', size=10),
                showlegend=True,
                legend=dict(font=dict(size=9)),
                margin=dict(l=0,r=0,t=10,b=0)
            )
            st.plotly_chart(fig2, use_container_width=True)

            st.markdown("#### 📈 SIP Performance")
            for mf in MUTUAL_FUNDS:
                pnl_mf = mf["current"] - mf["invested"]
                pnl_p  = round((pnl_mf/mf["invested"])*100,1)
                st.metric(
                    mf["name"][:32]+"...",
                    f"₹{mf['current']:,.0f}",
                    f"{pnl_p:+.1f}%",
                    delta_color="normal" if pnl_mf>0 else "inverse"
                )

    st.divider()
    st.markdown("#### 📋 Holdings Detail")

    table_rows = []
    for name, data in prices.items():
        rec = recs.get(name,{})
        table_rows.append({
            "Stock":      name,
            "Shares":     data["shares"],
            "Invested":   f"₹{data['invested']:,.0f}",
            "Current":    f"₹{data['value']:,.0f}",
            "P&L ₹":      f"₹{data['pnl']:,.0f}",
            "P&L %":      f"{data['pnl_pct']:+.2f}%",
            "Action":     rec.get("action","—")
        })

    df = pd.DataFrame(table_rows)
    st.dataframe(df, use_container_width=True, height=420)

# ============================================================
# TAB 2 — RECOMMENDATIONS
# ============================================================
with tab2:
    st.markdown("### 📋 AI Recommendations — 4 Layer Analysis")
    st.caption("Price + Sentiment + Fundamentals + Geopolitical")
    st.divider()

    filter_action = st.selectbox(
        "Filter by Action",
        ["All","Strong Buy","Hold/Add","Hold","Watch","Reduce","Exit"]
    )

    filter_map = {
        "Strong Buy": "STRONG BUY", "Hold/Add": "HOLD / ADD",
        "Hold": "HOLD", "Watch": "WATCH",
        "Reduce": "REDUCE", "Exit": "EXIT"
    }

    groups = {
        "🟢 STRONG BUY": [], "🟢 HOLD / ADD": [],
        "🟡 HOLD": [],       "🟡 WATCH": [],
        "🔴 REDUCE": [],     "🔴 EXIT": []
    }

    for stock, rec in recs.items():
        clean = rec["action"].replace(" ⚠️","")
        for key in groups:
            if key in clean:
                groups[key].append((stock, rec))
                break

    for action_type, stocks_list in groups.items():
        if not stocks_list: continue
        if filter_action != "All":
            if filter_map.get(filter_action,"") not in action_type:
                continue

        st.markdown(f"#### {action_type} ({len(stocks_list)} stocks)")

        for stock, rec in stocks_list:
            pdata = prices.get(stock,{})
            pnl   = pdata.get("pnl_pct",0)

            c1,c2,c3,c4,c5 = st.columns([3,2,2,2,2])
            with c1:
                st.markdown(f"**{stock}**")
                st.caption(STOCK_SECTORS.get(stock,"N/A"))
            with c2:
                st.metric("P&L",
                          f"{pnl:+.1f}%",
                          delta_color="normal" if pnl>0 else "inverse")
            with c3:
                st.metric("1W Signal", f"{rec['week']}%")
            with c4:
                st.metric("1M Signal", f"{rec['month']}%")
            with c5:
                st.metric("1Y Signal", f"{rec['year']}%")

            with st.expander(f"📊 Score Breakdown — Total: {rec['total']}"):
                sc1,sc2,sc3,sc4 = st.columns(4)
                ps = (3 if pnl>30 else 2 if pnl>10 else 1 if pnl>0
                      else -1 if pnl>-15 else -2 if pnl>-30 else -3)
                with sc1: st.metric("💰 Price",        f"{ps:+d}")
                with sc2: st.metric("📰 Sentiment",    f"{rec['sentiment']:+d}")
                with sc3: st.metric("📊 Fundamentals", f"{rec['fund_score']:+d}")
                with sc4: st.metric("🌍 Geopolitical", f"{rec['geo']:+d}")

                if show_news:
                    hl = sentiment.get(stock,{}).get("headlines",[])
                    if hl:
                        st.markdown("**Latest News:**")
                        for h in hl[:2]:
                            st.caption(f"→ {h[:100]}")
            st.divider()

# ============================================================
# TAB 3 — NIFTY 50 SCANNER
# ============================================================
with tab3:
    st.markdown("### 🔍 Nifty 50 Opportunity Scanner")
    st.caption("Find new stocks to invest in — not in your current portfolio")
    st.divider()

    if st.button("🔍 Scan Nifty 50 Now", type="primary"):
        with st.spinner("Scanning Nifty 50 stocks... (~2 mins)"):
            nifty_data = scan_nifty50()

        new_opps = {
            k: v for k,v in nifty_data.items()
            if not v.get("already") and v.get("score",0) >= 4
        }
        top10 = sorted(new_opps.items(),
                       key=lambda x: x[1]["score"],
                       reverse=True)[:10]

        st.success(f"✅ Scan complete! Found {len(top10)} opportunities.")
        st.divider()

        for rank, (name, data) in enumerate(top10, 1):
            score = data.get("score",0)
            w52   = data.get("w52",50)

            if score>=12:   rating, icon = "⭐⭐⭐ STRONG BUY", "🟢"
            elif score>=9:  rating, icon = "⭐⭐ BUY",          "🟢"
            elif score>=6:  rating, icon = "⭐ WATCH & BUY",   "🟡"
            else:           rating, icon = "👀 ON RADAR",       "⚪"

            with st.expander(
                f"{icon} #{rank} {name} — {rating} (Score: {score})"
            ):
                c1,c2,c3,c4,c5 = st.columns(5)
                with c1: st.metric("Sector", data.get("sector","N/A"))
                with c2:
                    st.metric("PE",
                              f"{data['pe']:.1f}" if data.get("pe") else "N/A")
                with c3:
                    st.metric("PB",
                              f"{data['pb']:.1f}" if data.get("pb") else "N/A")
                with c4:
                    st.metric("ROE",
                              f"{data['roe']:.1f}%" if data.get("roe") else "N/A")
                with c5:
                    entry = ("✅ Good entry" if w52<35 else
                             "🟡 Wait for dip" if w52<60 else
                             "⏳ Near 52W High")
                    st.metric("52W Pos", f"{w52:.0f}%", entry)
    else:
        st.info(
            "👆 Click **'Scan Nifty 50 Now'** to find new "
            "investment opportunities not in your portfolio."
        )

# ============================================================
# TAB 4 — SIP SUGGESTIONS
# ============================================================
with tab4:
    st.markdown("### 💡 Personalized SIP Recommendations")
    st.caption(
        "Based on: Risk Profile + Portfolio Gaps + "
        "Market Conditions + Geopolitical Signals"
    )
    st.divider()

    monthly = 5000
    rate    = 13/100/12
    months  = 120
    fv      = monthly * (((1+rate)**months - 1)/rate) * (1+rate)
    inv     = monthly * months
    fv_fd   = inv * ((1+0.065)**10)

    c1,c2,c3,c4 = st.columns(4)
    with c1: st.metric("Monthly SIP",    f"₹{monthly:,}")
    with c2: st.metric("10Y Projection", f"₹{fv:,.0f}")
    with c3: st.metric("FD Value",       f"₹{fv_fd:,.0f}")
    with c4: st.metric("Extra vs FD",    f"+₹{fv-fv_fd:,.0f}")

    st.divider()

    if show_charts:
        months_r  = list(range(1,121))
        sip_vals  = [monthly*(((1+rate)**m-1)/rate)*(1+rate)
                     for m in months_r]
        fd_vals   = [monthly*m*(1+0.065)**(m/12) for m in months_r]

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=months_r, y=sip_vals,
            name="SIP (13% CAGR)",
            line=dict(color="#64ffda", width=2)
        ))
        fig.add_trace(go.Scatter(
            x=months_r, y=fd_vals,
            name="FD (6.5%)",
            line=dict(color="#ff6b6b", width=2, dash='dash')
        ))
        fig.update_layout(
            title="SIP vs FD — 10 Year Wealth Growth",
            height=280,
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color='#ccd6f6'),
            xaxis=dict(title="Months", gridcolor='#3d4266'),
            yaxis=dict(title="Value ₹", gridcolor='#3d4266'),
            legend=dict(bgcolor='rgba(0,0,0,0)'),
            margin=dict(l=0,r=0,t=40,b=0)
        )
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("#### 🎯 Recommended SIPs")
    for sip in SIP_RECS:
        with st.expander(
            f"#{sip['priority']} {sip['fund']} — "
            f"₹{sip['amount']:,}/month | {sip['action']}"
        ):
            c1,c2,c3 = st.columns(3)
            with c1: st.metric("Monthly", f"₹{sip['amount']:,}")
            with c2: st.metric("Risk",    sip["risk"])
            with c3: st.metric("CAGR",    sip["cagr"])
            st.caption(f"**Examples:** {sip['examples']}")
            st.info(f"💡 {sip['why']}")

# ============================================================
# TAB 5 — GEOPOLITICAL
# ============================================================
with tab5:
    st.markdown("### 🌍 Geopolitical & Macro Factor Analysis")
    st.divider()

    for factor, details in GEO_FACTORS.items():
        sev   = details["severity"]
        icon  = "🔴" if sev=="HIGH" else "🟡"
        with st.expander(f"{icon} {factor} — {sev} Severity"):
            c1,c2,c3 = st.columns(3)
            with c1:
                st.markdown("**Affected Sectors**")
                st.caption(", ".join(details["sectors"]))
            with c2:
                st.markdown("**Portfolio Impact**")
                st.caption(details["impact"])
            with c3:
                st.markdown("**Severity**")
                st.caption(sev)

    st.divider()
    st.markdown("#### 📊 Geopolitical Score Per Stock")

    geo_rows = [
        {
            "Stock":      stock,
            "Sector":     STOCK_SECTORS.get(stock,"N/A"),
            "Geo Score":  score,
            "Signal":     ("🟢 Tailwind" if score>2 else
                           "🟢 Mild"     if score>0 else
                           "🟡 Neutral"  if score==0 else
                           "🔴 Headwind")
        }
        for stock, score in geo_scores.items()
    ]
    geo_df = pd.DataFrame(geo_rows).sort_values("Geo Score", ascending=False)
    st.dataframe(geo_df, use_container_width=True)

# ============================================================
# TAB 6 — ALERTS
# ============================================================
with tab6:
    st.markdown("### 🚨 Daily Action Alerts")
    st.divider()

    alerts = []
    for name, data in prices.items():
        p = data["pnl_pct"]
        if p <= -50:
            alerts.append(("🔴 CRITICAL EXIT",  name, p,
                           "Exit immediately — severe capital loss"))
        elif p <= -35:
            alerts.append(("🔴 EXIT ALERT",     name, p,
                           "Review urgently — significant loss"))
        elif p <= -25:
            alerts.append(("⚠️ REVIEW",         name, p,
                           "Monitor closely — notable underperformance"))
        elif p >= 50:
            alerts.append(("✅ BOOK PROFIT",    name, p,
                           "Consider partial profit booking"))
        elif p >= 25:
            alerts.append(("💰 WATCH PROFIT",   name, p,
                           "Good gain — watch for exit opportunity"))

    if alerts:
        for atype, name, pnl, note in alerts:
            msg = f"**{atype}** | {name} | {pnl:+.1f}% | {note}"
            if "CRITICAL" in atype or "EXIT ALERT" in atype:
                st.error(msg)
            elif "REVIEW" in atype:
                st.warning(msg)
            else:
                st.success(msg)
    else:
        st.success("✅ No critical alerts today — portfolio is stable")

    if show_news:
        st.divider()
        st.markdown("#### 📰 Latest News — Top 5 Holdings")
        top5 = sorted(PORTFOLIO.items(),
                      key=lambda x: x[1]["invested"],
                      reverse=True)[:5]
        for name, _ in top5:
            hl = sentiment.get(name,{}).get("headlines",[])
            with st.expander(f"📌 {name}"):
                if hl:
                    for h in hl[:3]:
                        st.caption(f"→ {h}")
                else:
                    st.caption("No recent news found")

# ============================================================
# FOOTER
# ============================================================
st.divider()
st.markdown("""
<div style='text-align:center;color:#8892b0;font-size:11px;padding:8px'>
    🤖 AI Portfolio Analyser v3.0 | Built by Takhar & Claude AI |
    ⚠️ Not SEBI registered | Personal research only |
    Not financial advice
</div>
""", unsafe_allow_html=True) 































































































































































































































































































































































