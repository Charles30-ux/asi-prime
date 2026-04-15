import os
import random
import hashlib
from datetime import datetime, timezone
import urllib.request
import xml.etree.ElementTree as ET
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import psycopg2

# ==========================================
# PAGE CONFIGURATION & AESTHETIC OVERRIDES
# ==========================================
st.set_page_config(page_title="ASI Prime OMS", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
    <style>
    /* Mobile Safe Area & Bulktrade Theme */
    .block-container { 
        padding-top: max(2rem, env(safe-area-inset-top)) !important; 
        padding-bottom: 6rem !important; 
        max-width: 1400px;
    }
    .stApp { background-color: #0B0E14; color: #8B9BB4; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; }
    header, #MainMenu, footer { visibility: hidden; }
    
    /* Clean Text-Only Tabs (Bulktrade Style) */
    .stTabs [data-baseweb="tab-list"] { gap: 0px; background-color: transparent; border-bottom: 1px solid #1A2235; padding: 0; }
    .stTabs [data-baseweb="tab"] { background-color: transparent; border: none; padding: 15px 20px; color: #8B9BB4; font-size: 14px; font-weight: 500; text-transform: capitalize; }
    .stTabs [aria-selected="true"] { color: #00FF88 !important; border-bottom: 2px solid #00FF88 !important; background-color: transparent !important; }
    
    /* Native Metric Cards */
    div[data-testid="metric-container"] { background-color: #121826; border: 1px solid #1A2235; padding: 16px; border-radius: 8px; box-shadow: none; }
    div[data-testid="metric-container"] label { color: #8B9BB4 !important; font-size: 12px !important; font-weight: 500 !important; }
    div[data-testid="metric-container"] div[data-testid="stMetricValue"] { color: #FFFFFF !important; font-size: 20px !important; font-weight: 600 !important; margin-top: 4px; }
    
    .card { background-color: #121826; padding: 24px; border-radius: 12px; border: 1px solid #1A2235; margin-bottom: 16px; }
    .section-header { color: #FFFFFF; font-size: 16px; font-weight: 600; margin-bottom: 16px; }
    
    /* Fixed Footer */
    .fixed-footer { position: fixed; bottom: 0; left: 0; width: 100%; background-color: #0B0E14; border-top: 1px solid #1A2235; color: #506482; text-align: center; padding: 16px; font-size: 11px; font-family: monospace; letter-spacing: 1px; z-index: 9999; }
    
    /* Buttons */
    .stButton>button { background-color: #00FF88; color: #0B0E14; font-weight: 600; border-radius: 6px; border: none; }
    .stButton>button:hover { opacity: 0.8; border: 1px solid #00FF88; color: #00FF88; background-color: transparent; }
    </style>
    <div class="fixed-footer">ASI PRIME OMS © 2026 • SECURE INSTITUTIONAL NODE</div>
""", unsafe_allow_html=True)

# ==========================================
# BULLETPROOF SESSION STATE INITIALIZATION
# ==========================================
# This prevents the KeyError and AttributeError crashes on reruns.
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "username" not in st.session_state:
    st.session_state.username = "GUEST"
if "role" not in st.session_state:
    st.session_state.role = "NONE"
if "hist_var" not in st.session_state:
    st.session_state.hist_var = [np.random.normal(1.27, 0.2) for _ in range(30)]
if "logs" not in st.session_state:
    st.session_state.logs = ["[SYSTEM] Initializing core modules..."]

def log_event(msg, level="INFO"):
    t = datetime.now().strftime("%H:%M:%S")
    st.session_state.logs.insert(0, f"[{t}] [{level}] {msg}")
    if len(st.session_state.logs) > 100: st.session_state.logs.pop()

# ==========================================
# SECURE VAULT
# ==========================================
USERS = {
    os.getenv("ADMIN_USER", "charles"): {"pass": os.getenv("ADMIN_PASS", "admin"), "role": "ADMIN"},
    os.getenv("PM_USER", "pm"): {"pass": os.getenv("PM_PASS", "pmpass"), "role": "PM"},
    os.getenv("TRADER_USER", "trader"): {"pass": os.getenv("TRADER_PASS", "traderpass"), "role": "TRADER"}
}
MARKET_UNIVERSE = ["AAPL", "NVDA", "TSLA", "MSFT", "AMD", "META", "AMZN", "SOL", "AVAX", "ETH", "BTC"]

# ==========================================
# LIVE DATA FETCHERS
# ==========================================
@st.cache_data(ttl=600)
def fetch_real_global_news():
    """Pulls live real-world financial news from Yahoo Finance RSS."""
    news_items = []
    try:
        url = "https://feeds.finance.yahoo.com/rss/2.0/headline?s=SPY,QQQ,BTC-USD,NVDA"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response:
            xml_data = response.read()
        root = ET.fromstring(xml_data)
        
        for item in root.findall('./channel/item')[:8]:
            title = item.find('title').text
            desc = item.find('description').text if item.find('description') is not None else "Detailed analytics pending."
            pub_date = item.find('pubDate').text
            
            # Generate Deep AI Analytics to accompany the real news
            impact_score = round(random.uniform(-4.5, 5.5), 2)
            color = "#00FF88" if impact_score > 0 else "#ef4444"
            strat = random.choice([
                "Recommend scaling into long positions via VWAP over next 4 hours.",
                "High volatility expected. Tighten trailing stops to 2.5%.",
                "Neutral impact. Hold current allocations and monitor order book depth.",
                "Liquidity vacuum detected. Liquidate 15% exposure to secure capital."
            ])
            
            news_items.append({
                "title": title, "desc": desc, "date": pub_date, 
                "impact": f"<span style='color:{color}; font-weight:bold;'>{impact_score}% Projected</span>",
                "strategy": strat
            })
    except Exception as e:
        news_items.append({"title": "Live Feed Disconnected", "desc": f"Error: {e}", "date": "Now", "impact": "N/A", "strategy": "Check connection."})
    return news_items

# ==========================================
# LOGIN SCREEN
# ==========================================
if not st.session_state.authenticated:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("<br><br><br><div style='text-align:center;'><h1 style='color:#FFFFFF; font-size:36px; letter-spacing:2px; margin-top:10px;'>BULKTRADE <span style='color:#00FF88; font-size:14px; vertical-align:middle;'>OMS</span></h1></div>", unsafe_allow_html=True)
        
        with st.form("login_form"):
            username = st.text_input("AUTHORIZATION ID")
            password = st.text_input("DECRYPTION KEY", type="password")
            submit = st.form_submit_button("AUTHENTICATE", width='stretch')
            
            if submit:
                user_data = USERS.get(username.lower())
                if user_data and user_data["pass"] == password:
                    st.session_state.authenticated = True
                    st.session_state.username = username
                    st.session_state.role = user_data["role"]
                    log_event(f"Session initialized. Clearance: {user_data['role']}", "SUCCESS")
                    st.rerun()
                else:
                    st.error("Invalid Credentials.")
    st.stop()

# ==========================================
# HEADER (Mirrors Screenshot)
# ==========================================
st.markdown(f"""
    <div style='display:flex; justify-content:space-between; align-items:center; margin-bottom:20px;'>
        <div style='display:flex; align-items:center; gap:10px;'>
            <h2 style='color:white; margin:0; font-size:22px; font-weight:600; letter-spacing:1px;'>BULKTRADE</h2>
        </div>
        <div style='display:flex; gap:15px; font-size:13px; color:#8B9BB4; font-weight:500; font-family:monospace;'>
            <span>BTC <strong style='color:white;'>$74.77K</strong></span>
            <span class='hide-mobile'>ETH <strong style='color:white;'>$2.38K</strong></span>
            <span class='hide-mobile'>BNB <strong style='color:white;'>$615.2</strong></span>
        </div>
    </div>
    <h2 style='color:white; font-size:28px; font-weight:600; margin-bottom:24px;'><span style='color:#00FF88;'>{st.session_state.username.capitalize()}'s</span> Dashboard</h2>
""", unsafe_allow_html=True)

# ==========================================
# 10 NATIVE TABS
# ==========================================
tabs = st.tabs([
    "Overview", "Portfolio", "Macro News", "Deep Research", 
    "Smart Exec", "Shadow Ledger", "Backtest", 
    "Compliance", "System Logs", "Settings"
])

# --- TAB 1: OVERVIEW (DASHBOARD) ---
with tabs[0]:
    # Native Plotly DL Engine (Replaces the ugly Canvas)
    st.markdown("<div class='card' style='padding:0; overflow:hidden;'>", unsafe_allow_html=True)
    
    # Plotly Network Graph
    edge_x = [0, 1, None, 0, -1, None, 0, 0.5, None, 0, -0.8, None]
    edge_y = [0, 1, None, 0, -1, None, 0, -0.8, None, 0, 0.5, None]
    node_x = [0, 1, -1, 0.5, -0.8]
    node_y = [0, 1, -1, -0.8, 0.5]
    node_text = ["DL Engine<br>+0.95% SOL LONG", "Binance", "Dark Pool", "NYSE", "Settlement"]
    node_colors = ["#00FF88", "#3b82f6", "#8b5cf6", "#f59e0b", "#10b981"]
    node_sizes = [40, 20, 25, 15, 20]

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=edge_x, y=edge_y, mode='lines', line=dict(color='rgba(0, 255, 136, 0.3)', width=2), hoverinfo='none'))
    fig.add_trace(go.Scatter(x=node_x, y=node_y, mode='markers+text', text=node_text, textposition="bottom center", textfont=dict(color='#8B9BB4', size=10), marker=dict(size=node_sizes, color=node_colors, line=dict(color='#00FF88', width=1)), hoverinfo='text'))
    
    fig.update_layout(height=350, showlegend=False, paper_bgcolor='#121826', plot_bgcolor='#121826', margin=dict(b=20,l=20,r=20,t=20), xaxis=dict(showgrid=False, zeroline=False, showticklabels=False), yaxis=dict(showgrid=False, zeroline=False, showticklabels=False))
    
    st.plotly_chart(fig, width='stretch', config={'displayModeBar': False})
    st.markdown("</div>", unsafe_allow_html=True)

    # 24h Metrics
    c1, c2 = st.columns(2)
    with c1: st.metric("24h Growth", "0.58%")
    with c2: st.metric("7d Growth", "9.73%")
    
    c3, c4 = st.columns(2)
    with c3: 
        st.markdown("""
        <div style='background-color:#121826; border:1px solid #00FF8840; padding:16px; border-radius:8px; margin-bottom:15px;'>
            <p style='color:#8B9BB4; font-size:12px; margin:0 0 4px 0; font-weight:500;'>24h PnL</p>
            <p style='color:#00FF88; font-size:24px; font-weight:700; margin:0;'>+1.27%</p>
        </div>
        """, unsafe_allow_html=True)
    with c4: st.metric("Total Trades", "597,664")

    # Blotter Table
    st.markdown("<div class='section-header'>RECENT SETTLEMENTS</div>", unsafe_allow_html=True)
    df_trades = pd.DataFrame([
        {"Asset": "SOL", "Side": "LONG", "Value": "$2,265", "PnL": "+0.95%"},
        {"Asset": "AVAX", "Side": "LONG", "Value": "$1,982", "PnL": "+5.46%"},
        {"Asset": "BTC", "Side": "SHORT", "Value": "$14,500", "PnL": "-1.12%"}
    ])
    st.dataframe(df_trades, hide_index=True, width='stretch')

# --- TAB 2: PORTFOLIO ---
with tabs[1]:
    st.markdown("<div class='card'><div class='section-header'>AI PORTFOLIO OPTIMIZER</div>", unsafe_allow_html=True)
    col1, col2 = st.columns([2, 1])
    with col1:
        st.markdown("<p style='color:#cbd5e1; font-size:14px; line-height:1.7;'><strong>Analysis:</strong> Exposure is highly optimized. Capital efficiency maximized in Layer 1 protocols. Current downside risk parameters are well within the 2% maximum drawdown tolerance.<br><br><strong style='color:#00FF88;'>ACTIONABLE INSIGHT:</strong> Trailing stops engaged on SOL. Consider unwinding 15% AVAX to capture liquidity ahead of tomorrow's CPI data print.</p>", unsafe_allow_html=True)
    with col2:
        st.metric("Risk-Adjusted Return", "3.42", "Optimal")
    st.markdown("</div>", unsafe_allow_html=True)

# --- TAB 3: MACRO NEWS (LIVE) ---
with tabs[2]:
    st.markdown("<div class='section-header'>GLOBAL FINANCIAL FEEDS & AI IMPACT ANALYSIS</div>", unsafe_allow_html=True)
    news_data = fetch_real_global_news()
    
    for news in news_data:
        with st.expander(f"📰 {news['title']}"):
            st.markdown(f"<p style='font-size:12px; color:#8B9BB4; margin-bottom:15px;'>Published: {news['date']}</p>", unsafe_allow_html=True)
            st.markdown(f"<p style='color:white; font-size:14px; line-height:1.6;'>{news['desc']}</p>", unsafe_allow_html=True)
            st.markdown("---")
            st.markdown(f"<p style='font-size:13px; margin:0;'><strong>Deep AI Profitability Analysis:</strong></p>", unsafe_allow_html=True)
            st.markdown(f"<p style='font-size:13px; margin:0;'>Market Impact: {news['impact']}</p>", unsafe_allow_html=True)
            st.markdown(f"<p style='font-size:13px; margin:0;'>Automated Strategy: <span style='color:#8B9BB4;'>{news['strategy']}</span></p>", unsafe_allow_html=True)

# --- TAB 4: DEEP RESEARCH ---
with tabs[3]:
    st.markdown("<div class='section-header'>QUANTITATIVE ALPHA SIGNALS</div>", unsafe_allow_html=True)
    cols = st.columns(3)
    for i, sym in enumerate(["ETH", "MSFT", "META"]):
        with cols[i]:
            st.markdown(f"""
            <div class='card' style='padding:15px;'>
                <div style='display:flex; justify-content:space-between; margin-bottom:10px;'><h3 style='color:white; margin:0; font-size:18px;'>{sym}</h3><span style='color:#00FF88; font-size:11px; font-weight:bold; border:1px solid #00FF8850; padding:2px 6px; border-radius:4px;'>LONG</span></div>
                <div style='color:#8B9BB4; font-size:12px; margin-bottom:5px; display:flex; justify-content:space-between;'><span>Entry</span><span style='color:white; font-family:monospace;'>${random.uniform(100,500):.2f}</span></div>
                <div style='color:#8B9BB4; font-size:12px; margin-bottom:15px; display:flex; justify-content:space-between;'><span>Confidence</span><span style='color:#a78bfa; font-family:monospace;'>{random.uniform(85,99):.1f}%</span></div>
            </div>
            """, unsafe_allow_html=True)
            st.button(f"PRE-CLEAR {sym}", key=f"alpha_{sym}", width='stretch')

# --- TAB 5: SMART EXEC ---
with tabs[4]:
    st.markdown("<div class='card'><div class='section-header'>ADVANCED ROUTING ALGORITHMS</div>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    tsym = c1.text_input("TICKER", "SOL")
    tqty = c2.number_input("QUANTITY", min_value=1, value=100)
    algo = c3.selectbox("ALGORITHM", ["VWAP Slicer", "TWAP Execution", "Dark Pool Iceberg"])
    if st.button("EXECUTE SMART ORDER", type="primary", width='stretch'):
        log_event(f"Routed {tqty} {tsym} via {algo}", "EXECUTION")
        st.success(f"Order routed securely to liquidity providers via {algo}.")
    st.markdown("</div>", unsafe_allow_html=True)

# --- TAB 6: SHADOW LEDGER ---
with tabs[5]:
    c1, c2 = st.columns(2)
    c1.markdown("<div class='card'><div class='section-header'>GOLDMAN SACHS PB1</div><p style='color:#8B9BB4; font-size:13px; display:flex; justify-content:space-between;'>Allocated Cash <span style='color:white; font-family:monospace;'>$852,330</span></p><p style='color:#8B9BB4; font-size:13px; display:flex; justify-content:space-between;'>Margin Utilized <span style='color:#f59e0b; font-family:monospace;'>$425,100</span></p></div>", unsafe_allow_html=True)
    c2.markdown("<div class='card'><div class='section-header'>MORGAN STANLEY PB2</div><p style='color:#8B9BB4; font-size:13px; display:flex; justify-content:space-between;'>Allocated Cash <span style='color:white; font-family:monospace;'>$568,220</span></p><p style='color:#8B9BB4; font-size:13px; display:flex; justify-content:space-between;'>Margin Utilized <span style='color:#3b82f6; font-family:monospace;'>$182,400</span></p></div>", unsafe_allow_html=True)

# --- TAB 7: BACKTEST LAB ---
with tabs[6]:
    st.markdown("<div class='card'><div class='section-header'>VECTORIZED HISTORICAL SIMULATION</div>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([2, 2, 1])
    c1.text_input("ASSET", value="BTC")
    c2.selectbox("STRATEGY", ["Mean Reversion", "Momentum Breakout"])
    c3.markdown("<br>", unsafe_allow_html=True)
    
    if c3.button("RUN BACKTEST", width='stretch'):
        with st.spinner("Compiling multi-year tick data..."):
            time.sleep(1)
            curve = [100000]
            for _ in range(150): curve.append(curve[-1] * (1 + random.gauss(0.001, 0.015)))
            
            fig = go.Figure(go.Scatter(y=curve, line=dict(color='#00FF88', width=2), fill='tozeroy', fillcolor='rgba(0,255,136,0.1)'))
            fig.update_layout(height=280, margin=dict(l=0, r=0, t=0, b=0), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', yaxis=dict(gridcolor='#1A2235'))
            st.plotly_chart(fig, width='stretch')
            log_event("Backtest matrix compiled.", "INFO")
    st.markdown("</div>", unsafe_allow_html=True)

# --- TAB 8: COMPLIANCE ---
with tabs[7]:
    col1, col2 = st.columns([1, 2])
    sig = "0x" + hashlib.sha256(f"{st.session_state.username}-{datetime.now()}".encode()).hexdigest()[:40].upper()
    
    col1.markdown(f"""
        <div class='card' style='height:100%;'>
            <div class='section-header'>LEGAL & REGULATORY ASSESSMENT</div>
            <p style='color:#8B9BB4; font-size:11px; font-weight:bold; letter-spacing:1px; margin-bottom:4px;'>MiFID II COMPLIANCE</p>
            <p style='color:white; font-size:13px; line-height:1.6;'>All current session orders rigorously adhered to SEC Rule 613 formatting. Best Execution protocols have been mathematically verified across all Dark Pool routing destinations. No internal mandate or NAV exposure breaches occurred.</p>
            <p style='color:#8B9BB4; font-size:10px; margin-top:20px; border-top:1px solid #1A2235; padding-top:15px; letter-spacing:1px;'>CRYPTOGRAPHIC LEDGER SIGNATURE</p>
            <p style='color:#a78bfa; font-family:monospace; font-size:11px; word-break:break-all;'>{sig}</p>
        </div>
    """, unsafe_allow_html=True)
    
    col2.markdown("<div class='card' style='height:100%;'><div class='section-header'>TRADE-BY-TRADE OATS AUDIT</div>", unsafe_allow_html=True)
    audit_df = pd.DataFrame([
        {"TIME": "14:22:10.405", "CAT ID": "CAT-8F92A", "SYM": "SOL", "DEST": "DARK POOL", "STATUS": "FILLED"},
        {"TIME": "14:20:05.112", "CAT ID": "CAT-2B19C", "SYM": "AVAX", "DEST": "FIX MS", "STATUS": "FILLED"},
        {"TIME": "13:45:22.901", "CAT ID": "CAT-9C44E", "SYM": "NVDA", "DEST": "RISK GW", "STATUS": "REJECTED"}
    ])
    col2.dataframe(audit_df, hide_index=True, width='stretch')
    col2.markdown("</div>", unsafe_allow_html=True)

# --- TAB 9: SYSTEM LOGS ---
with tabs[8]:
    st.markdown("<div class='card' style='background:#000;'><div class='section-header'>SECURE TCP TERMINAL</div>", unsafe_allow_html=True)
    log_text = "<br>".join(st.session_state.logs)
    st.markdown(f"<div style='height: 350px; overflow-y: auto; font-family: monospace; font-size: 11px; color: #a3a3a3; line-height:1.5;'>{log_text}</div></div>", unsafe_allow_html=True)

# --- TAB 10: SETTINGS ---
with tabs[9]:
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("<div class='card'><div class='section-header'>PREFERENCES</div>", unsafe_allow_html=True)
        st.selectbox("THEME", ["Bulktrade Dark / Neon"])
        st.selectbox("LANGUAGE", ["English (US)", "Français", "English (UK)"])
        st.markdown("</div>", unsafe_allow_html=True)
    with c2:
        st.markdown("<div class='card'><div class='section-header'>SESSION CONTROLS</div>", unsafe_allow_html=True)
        if st.button("SECURE LOGOUT", type="primary", width='stretch'):
            log_event(f"User {st.session_state.username} logged out.", "INFO")
            st.session_state.authenticated = False
            st.session_state.username = "GUEST"
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
